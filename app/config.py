import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

# Comma-separated extra origins (e.g. Vercel preview URLs). FRONTEND_URL is always included.
_cors_extra = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS = list(
    dict.fromkeys(
        [
            FRONTEND_URL,
            "http://localhost:5173",
            *[o.strip().rstrip("/") for o in _cors_extra.split(",") if o.strip()],
        ]
    )
)

# Max emails per Gmail tool call — keeps tool output within context limits
GMAIL_FETCH_MAX_RESULTS = int(os.getenv("GMAIL_FETCH_MAX_RESULTS", "15"))

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL", "")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
