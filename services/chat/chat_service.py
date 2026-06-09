import json
import logging
from typing import AsyncGenerator

from agent.doc_artifacts import artifact_to_markdown
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
    artifacts_by_id: dict[str, dict] = {}
    had_error = False
    try:
        async for event in stream_agent_response(uid, session_id, history_with_current, message):
            if isinstance(event, dict):
                if event.get("type") == "error":
                    had_error = True
                elif event.get("type") == "artifact" and event.get("artifact"):
                    art = event["artifact"]
                    key = art.get("id") or f"anon-{len(artifacts_by_id)}"
                    if key in artifacts_by_id:
                        artifacts_by_id[key] = {**artifacts_by_id[key], **art}
                    else:
                        artifacts_by_id[key] = art
                yield json.dumps(event)
                continue
            assistant_text += event
            yield json.dumps({"type": "token", "content": event})
    except Exception as exc:
        logger.exception("Chat stream failed for uid=%s", uid)
        had_error = True
        yield json.dumps({"type": "error", "message": str(exc) or "Failed to generate response"})

    if assistant_text or artifacts_by_id:
        saved = assistant_text
        final_artifacts = [
            art for art in artifacts_by_id.values() if art.get("status") != "loading"
        ]
        if final_artifacts:
            blocks = [artifact_to_markdown(art) for art in final_artifacts]
            saved = (saved + "\n\n" if saved else "") + "\n\n".join(blocks)
        db.add_message(uid, session_id, "assistant", saved)

    yield json.dumps({"type": "done", "session_id": session_id})
