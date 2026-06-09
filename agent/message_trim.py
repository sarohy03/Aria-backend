from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

MAX_TOOL_CONTENT_CHARS = 28_000
MAX_MESSAGES = 24


def _content_to_str(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
        return "".join(parts)
    return str(content)


def _truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    omitted = len(text) - limit
    return (
        text[:limit]
        + f"\n\n[… truncated {omitted:,} characters of tool output to stay within context limits]"
    )


def truncate_tool_message(message: ToolMessage) -> ToolMessage:
    text = _content_to_str(message.content)
    if len(text) <= MAX_TOOL_CONTENT_CHARS:
        return message
    return ToolMessage(
        content=_truncate_text(text, MAX_TOOL_CONTENT_CHARS),
        name=message.name,
        tool_call_id=message.tool_call_id,
        status=getattr(message, "status", None),
    )


def trim_messages_for_llm(messages: list[BaseMessage]) -> list[BaseMessage]:
    if not messages:
        return messages

    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

    trimmed: list[BaseMessage] = []
    for msg in other_msgs:
        if isinstance(msg, ToolMessage):
            trimmed.append(truncate_tool_message(msg))
        else:
            trimmed.append(msg)

    if len(trimmed) > MAX_MESSAGES:
        trimmed = trimmed[-MAX_MESSAGES:]

    if system_msgs:
        return [system_msgs[0], *trimmed]
    return [SystemMessage(content="You are a helpful assistant."), *trimmed]
