from composio import Composio
from composio_langchain import LangchainProvider

from app.config import COMPOSIO_API_KEY

_client: Composio | None = None
_langchain_client: Composio | None = None


def get_composio_client() -> Composio:
    global _client
    if not COMPOSIO_API_KEY:
        raise RuntimeError("COMPOSIO_API_KEY is not configured")
    if _client is None:
        _client = Composio(api_key=COMPOSIO_API_KEY)
    return _client


def get_composio_langchain_client() -> Composio:
    global _langchain_client
    if not COMPOSIO_API_KEY:
        raise RuntimeError("COMPOSIO_API_KEY is not configured")
    if _langchain_client is None:
        _langchain_client = Composio(
            api_key=COMPOSIO_API_KEY,
            provider=LangchainProvider(),
        )
    return _langchain_client
