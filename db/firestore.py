from datetime import datetime, timezone
from uuid import uuid4

from firebase_admin import firestore

from auth.firebase import init_firebase

_db = None


def get_db():
    global _db
    init_firebase()
    if _db is None:
        _db = firestore.client()
    return _db


def _now():
    return datetime.now(timezone.utc)


def _sessions(uid: str):
    return get_db().collection("users").document(uid).collection("sessions")


def _messages(uid: str, session_id: str):
    return _sessions(uid).document(session_id).collection("messages")


def list_sessions(uid: str) -> list[dict]:
    docs = _sessions(uid).order_by("updated_at", direction=firestore.Query.DESCENDING).stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]


def create_session(uid: str, title: str = "New chat") -> dict:
    session_id = str(uuid4())
    now = _now()
    data = {
        "title": title,
        "created_at": now,
        "updated_at": now,
    }
    _sessions(uid).document(session_id).set(data)
    return {"id": session_id, **data}


def get_session(uid: str, session_id: str) -> dict | None:
    doc = _sessions(uid).document(session_id).get()
    if not doc.exists:
        return None
    return {"id": doc.id, **doc.to_dict()}


def delete_session(uid: str, session_id: str) -> None:
    messages_ref = _messages(uid, session_id)
    for doc in messages_ref.stream():
        doc.reference.delete()
    _sessions(uid).document(session_id).delete()


def list_messages(uid: str, session_id: str) -> list[dict]:
    docs = _messages(uid, session_id).order_by("created_at").stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]


def add_message(uid: str, session_id: str, role: str, content: str) -> dict:
    message_id = str(uuid4())
    now = _now()
    data = {
        "role": role,
        "content": content,
        "created_at": now,
    }
    _messages(uid, session_id).document(message_id).set(data)
    _sessions(uid).document(session_id).update({"updated_at": now})
    return {"id": message_id, **data}


def update_session_title(uid: str, session_id: str, title: str) -> None:
    _sessions(uid).document(session_id).update(
        {"title": title, "updated_at": _now()}
    )
