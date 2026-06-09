import json
import logging
from typing import AsyncGenerator

from agent.graph import stream_agent_response
from db import firestore as db

logger = logging.getLogger(__name__)


async def stream_chat(
    uid: str,
    session_id: str | None,
    message: str,
) -> AsyncGenerator[str, None]:
    if session_id:
        session = db.get_session(uid, session_id)
        if session is None:
            raise ValueError("Session not found")
    else:
        title = message[:48] + ("..." if len(message) > 48 else "")
        session = db.create_session(uid, title=title)
        session_id = session["id"]
        yield json.dumps({"type": "session", "session_id": session_id, "title": session["title"]})

    history = db.list_messages(uid, session_id)
    db.add_message(uid, session_id, "user", message)
    history_with_current = history + [{"role": "user", "content": message}]

    assistant_text = ""
    had_error = False
    try:
        async for event in stream_agent_response(uid, session_id, history_with_current, message):
            if isinstance(event, dict):
                if event.get("type") == "error":
                    had_error = True
                yield json.dumps(event)
                continue
            assistant_text += event
            yield json.dumps({"type": "token", "content": event})
    except Exception as exc:
        logger.exception("Chat stream failed for uid=%s", uid)
        had_error = True
        yield json.dumps({"type": "error", "message": str(exc) or "Failed to generate response"})

    if assistant_text and not had_error:
        db.add_message(uid, session_id, "assistant", assistant_text)
    elif assistant_text and had_error:
        db.add_message(uid, session_id, "assistant", assistant_text)

    yield json.dumps({"type": "done", "session_id": session_id})
