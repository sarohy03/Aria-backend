import logging

from app.config import FRONTEND_URL
from services.integrations.composio_client import get_composio_client

logger = logging.getLogger(__name__)

TOOLKITS = {
    "gmail": {"label": "Gmail", "slug": "gmail"},
    "googledocs": {"label": "Google Docs", "slug": "googledocs"},
}

ACTIVE_STATUSES = {"ACTIVE", "INITIATED"}


def _get_auth_config_id(toolkit_slug: str) -> str:
    composio = get_composio_client()
    auth_configs = composio.auth_configs.list(toolkit_slug=toolkit_slug)
    if auth_configs.items:
        newest = sorted(auth_configs.items, key=lambda x: x.created_at, reverse=True)[0]
        return newest.id

    created = composio.auth_configs.create(
        toolkit_slug,
        {
            "type": "use_composio_managed_auth",
            "tool_access_config": {"tools_for_connected_account_creation": []},
        },
    )
    return created.id


def _normalize_toolkit_slug(slug: str) -> str:
    normalized = slug.lower().replace("-", "").replace("_", "").replace(" ", "")
    aliases = {
        "gmail": "gmail",
        "googledocs": "googledocs",
        "googledrive": "googledocs",
    }
    if normalized in aliases:
        return aliases[normalized]
    if slug in TOOLKITS:
        return TOOLKITS[slug]["slug"]
    raise ValueError(f"Unsupported toolkit: {slug}")


def get_integration_status(uid: str) -> dict:
    composio = get_composio_client()
    accounts = composio.connected_accounts.list(user_ids=[uid])

    by_toolkit: dict[str, str] = {}
    for account in accounts.items:
        slug = account.toolkit.slug
        status = account.status
        if slug not in by_toolkit or status == "ACTIVE":
            by_toolkit[slug] = status

    integrations = []
    for key, meta in TOOLKITS.items():
        slug = meta["slug"]
        status = by_toolkit.get(slug, "NOT_CONNECTED")
        integrations.append(
            {
                "id": key,
                "label": meta["label"],
                "slug": slug,
                "status": status,
                "connected": status == "ACTIVE",
            }
        )

    return {
        "integrations": integrations,
        "all_connected": all(item["connected"] for item in integrations),
    }


def start_connection(uid: str, toolkit: str) -> dict:
    toolkit_slug = _normalize_toolkit_slug(toolkit)
    composio = get_composio_client()
    auth_config_id = _get_auth_config_id(toolkit_slug)
    callback_url = f"{FRONTEND_URL}/chat?connected={toolkit_slug}"

    request = composio.connected_accounts.link(
        user_id=uid,
        auth_config_id=auth_config_id,
        callback_url=callback_url,
    )

    if not request.redirect_url:
        raise RuntimeError("Composio did not return a redirect URL")

    return {
        "redirect_url": request.redirect_url,
        "connection_id": request.id,
        "toolkit": toolkit_slug,
    }
