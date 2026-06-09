import logging

from app.config import COMPOSIO_API_KEY
from services.integrations.composio_client import get_composio_langchain_client

logger = logging.getLogger(__name__)

GMAIL_TOOLS = [
    "GMAIL_FETCH_EMAILS",
    "GMAIL_SEND_EMAIL",
    "GMAIL_CREATE_EMAIL_DRAFT",
]

GOOGLEDOCS_TOOLS = [
    "GOOGLEDOCS_CREATE_DOCUMENT",
    "GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN",
    "GOOGLEDOCS_SEARCH_DOCUMENTS",
    "GOOGLEDOCS_GET_DOCUMENT_PLAINTEXT",
    "GOOGLEDOCS_GET_DOCUMENT_BY_ID",
    "GOOGLEDOCS_INSERT_TEXT_ACTION",
    "GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT",
    "GOOGLEDOCS_UPDATE_DOCUMENT_MARKDOWN",
    "GOOGLEDOCS_REPLACE_ALL_TEXT",
    "GOOGLEDOCS_UPDATE_DOCUMENT_BATCH",
    "GOOGLEDOCS_COPY_DOCUMENT",
]

ARIA_TOOLS = GMAIL_TOOLS + GOOGLEDOCS_TOOLS

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
        return composio.tools.get(user_id=user_id, tools=ARIA_TOOLS)
    except Exception:
        logger.exception("Failed to load Composio tools for user %s", user_id)
        try:
            return composio.tools.get(user_id=user_id, toolkits=["GMAIL", "GOOGLEDOCS"])
        except Exception:
            logger.exception("Failed to load Composio toolkits for user %s", user_id)
            return []
