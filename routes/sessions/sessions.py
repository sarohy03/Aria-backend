from fastapi import APIRouter, Depends, HTTPException

from auth.firebase import get_current_uid
from db import firestore as db
from schemas.chat import SessionCreate

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _serialize_session(session: dict) -> dict:
    return {
        "id": session["id"],
        "title": session.get("title", "New chat"),
        "created_at": session.get("created_at").isoformat() if session.get("created_at") else None,
        "updated_at": session.get("updated_at").isoformat() if session.get("updated_at") else None,
    }


def _serialize_message(message: dict) -> dict:
    return {
        "id": message["id"],
        "role": message["role"],
        "content": message["content"],
        "created_at": message.get("created_at").isoformat() if message.get("created_at") else None,
    }


@router.get("")
def list_sessions(uid: str = Depends(get_current_uid)):
    sessions = db.list_sessions(uid)
    return [_serialize_session(s) for s in sessions]


@router.post("")
def create_session(body: SessionCreate, uid: str = Depends(get_current_uid)):
    session = db.create_session(uid, title=body.title)
    return _serialize_session(session)


@router.get("/{session_id}")
def get_session_messages(session_id: str, uid: str = Depends(get_current_uid)):
    session = db.get_session(uid, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = db.list_messages(uid, session_id)
    return {
        "session": _serialize_session(session),
        "messages": [_serialize_message(m) for m in messages],
    }


@router.delete("/{session_id}")
def delete_session(session_id: str, uid: str = Depends(get_current_uid)):
    session = db.get_session(uid, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete_session(uid, session_id)
    return {"ok": True}
