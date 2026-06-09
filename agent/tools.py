import logging

from app.config import COMPOSIO_API_KEY
from services.integrations.composio_client import get_composio_langchain_client

logger = logging.getLogger(__name__)

GMAIL_DRIVE_TOOLS = [
    "GMAIL_FETCH_EMAILS",
    "GMAIL_SEND_EMAIL",
    "GMAIL_CREATE_EMAIL_DRAFT",
    "GOOGLEDRIVE_FIND_FILE",
    "GOOGLEDRIVE_UPLOAD_FILE",
    "GOOGLEDRIVE_GET_FILE_CONTENT",
]

_composio = None


def _get_composio_langchain():
    global _composio
    if not COMPOSIO_API_KEY:
        return None
    if _composio is None:
        _composio = get_composio_langchain_client()
    return _composio


def get_composio_tools(user_id: str) -> list:
    composio = _get_composio_langchain()
    if composio is None:
        logger.warning("COMPOSIO_API_KEY missing — running without tools")
        return []

    try:
        return composio.tools.get(user_id=user_id, tools=GMAIL_DRIVE_TOOLS)
    except Exception:
        logger.exception("Failed to load Composio tools for user %s", user_id)
        try:
            return composio.tools.get(user_id=user_id, toolkits=["GMAIL", "GOOGLEDRIVE"])
        except Exception:
            logger.exception("Failed to load Composio toolkits for user %s", user_id)
            return []
