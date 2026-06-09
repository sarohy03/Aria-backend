import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY, FIREBASE_PROJECT_ID

_bearer = HTTPBearer(auto_error=False)
_app_initialized = False


def init_firebase() -> None:
    global _app_initialized
    if _app_initialized or firebase_admin._apps:
        _app_initialized = True
        return

    if not all([FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY]):
        raise RuntimeError("Firebase Admin credentials missing in environment")

    cred = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": FIREBASE_PROJECT_ID,
            "private_key": FIREBASE_PRIVATE_KEY,
            "client_email": FIREBASE_CLIENT_EMAIL,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )
    firebase_admin.initialize_app(cred)
    _app_initialized = True


def verify_token(token: str) -> str:
    init_firebase()
    decoded = auth.verify_id_token(token)
    return decoded["uid"]


async def get_current_uid(
    credentials_header: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if credentials_header is None or credentials_header.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    try:
        return verify_token(credentials_header.credentials)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
