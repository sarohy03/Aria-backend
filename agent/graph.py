from collections.abc import AsyncGenerator
import logging

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_openai.chat_models.base import OpenAIContextOverflowError
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.message_trim import truncate_tool_message, trim_messages_for_llm

from agent.prompts import ARIA_SYSTEM_PROMPT
from agent.state import AgentState
from agent.tool_labels import tool_label
from agent.tools import get_composio_tools
from app.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

_memory = MemorySaver()
_apps: dict[str, object] = {}


async def _truncate_tool_output(request, execute):
    result = await execute(request)
    if isinstance(result, ToolMessage):
        return truncate_tool_message(result)
    if isinstance(result, list):
        return [
            truncate_tool_message(item) if isinstance(item, ToolMessage) else item
            for item in result
        ]
    return result


def _build_graph(tools: list):
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        streaming=True,
    )
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    async def agent_node(state: AgentState, config: RunnableConfig):
        trimmed = trim_messages_for_llm(state["messages"])
        response = await llm_with_tools.ainvoke(trimmed, config)
        return {"messages": [response]}

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)

    if tools:
        builder.add_node(
            "tools",
            ToolNode(tools, handle_tool_errors=True, awrap_tool_call=_truncate_tool_output),
        )
        builder.add_edge(START, "agent")
        builder.add_conditional_edges(
            "agent",
            tools_condition,
            {"tools": "tools", END: END},
        )
        builder.add_edge("tools", "agent")
    else:
        builder.add_edge(START, "agent")
        builder.add_edge("agent", END)

    return builder.compile(checkpointer=_memory)


def get_app(uid: str):
    if uid not in _apps:
        tools = get_composio_tools(uid)
        _apps[uid] = _build_graph(tools)
    return _apps[uid]


def reset_app(uid: str) -> None:
    _apps.pop(uid, None)


def reset_session(uid: str, session_id: str) -> None:
    """Clear bloated in-memory checkpoint for a thread."""
    app = _apps.get(uid)
    if app is None:
        return
    config = _thread_config(uid, session_id)
    try:
        app.update_state(config, {"messages": []})
    except Exception:
        logger.exception("Failed to reset session checkpoint %s:%s", uid, session_id)


def history_to_messages(history: list[dict]) -> list[BaseMessage]:
    messages: list[BaseMessage] = [SystemMessage(content=ARIA_SYSTEM_PROMPT)]
    for item in history:
        role = item.get("role")
        content = item.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def _extract_text(chunk: BaseMessage) -> str | None:
    if not isinstance(chunk, (AIMessage, AIMessageChunk)) or not chunk.content:
        return None
    text = chunk.content
    if isinstance(text, str):
        return text
    if isinstance(text, list):
        parts: list[str] = []
        for part in text:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
        joined = "".join(parts)
        return joined or None
    return None


def _thread_config(uid: str, session_id: str) -> dict:
    return {"configurable": {"thread_id": f"{uid}:{session_id}"}}


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, OpenAIContextOverflowError) or "context_length_exceeded" in str(exc):
        return (
            "That request returned too much data to process at once. "
            "Try asking for one email or a shorter summary."
        )
    message = str(exc)
    if "ConnectedAccountNotFound" in message or "No connected account" in message:
        return (
            "Gmail or Google Drive isn't connected yet. "
            "Use Connect in the sidebar, then try again."
        )
    if "ActionExecute" in message and "gmail" in message.lower():
        return "Couldn't access Gmail. Check that it's connected in the sidebar."
    if len(message) > 200:
        return "Something went wrong while running a tool. Please try again."
    return message or "Something went wrong. Please try again."


async def stream_agent_response(
    uid: str,
    session_id: str,
    history: list[dict],
    user_message: str,
) -> AsyncGenerator[str | dict, None]:
    app = get_app(uid)
    config = _thread_config(uid, session_id)

    snapshot = app.get_state(config)
    if snapshot.values.get("messages"):
        graph_input = {"messages": [HumanMessage(content=user_message)]}
    else:
        graph_input = {"messages": history_to_messages(history)}

    try:
        async for item in app.astream(
            graph_input,
            config=config,
            stream_mode=["messages", "updates"],
        ):
            if isinstance(item, tuple) and len(item) == 2:
                mode, payload = item
            elif isinstance(item, tuple) and len(item) == 3:
                _, mode, payload = item
            else:
                continue

            if mode == "updates":
                agent_update = payload.get("agent")
                if agent_update:
                    messages = agent_update.get("messages") or []
                    if messages:
                        last = messages[-1]
                        for call in getattr(last, "tool_calls", None) or []:
                            name = call.get("name", "tool")
                            yield {
                                "type": "tool",
                                "status": "start",
                                "name": name,
                                "label": tool_label(name),
                            }
                if "tools" in payload:
                    yield {"type": "tool", "status": "done"}
                continue

            if mode != "messages":
                continue

            chunk, metadata = payload
            if metadata.get("langgraph_node") != "agent":
                continue
            token = _extract_text(chunk)
            if token:
                yield token
    except Exception as exc:
        logger.exception("Agent stream failed for uid=%s session=%s", uid, session_id)
        if isinstance(exc, OpenAIContextOverflowError) or "context_length_exceeded" in str(exc):
            reset_session(uid, session_id)
        yield {"type": "error", "message": _friendly_error(exc)}
