import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGIN_REGEX, CORS_ORIGINS
from auth.firebase import init_firebase
from routes.chat.chat import router as chat_router
from routes.integrations.integrations import router as integrations_router
from routes.sessions.sessions import router as sessions_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Aria API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(integrations_router)
app.include_router(sessions_router)


@app.on_event("startup")
def on_startup() -> None:
    """Fail fast in production if Firebase Admin credentials are missing."""
    try:
        init_firebase()
        logger.info("Firebase Admin initialized")
    except Exception:
        logger.exception("Firebase Admin failed to initialize — check env vars")
        raise

    logger.info("CORS origins: %s", CORS_ORIGINS)


@app.get("/health")
def health_check():
    return {"status": "ok"}
