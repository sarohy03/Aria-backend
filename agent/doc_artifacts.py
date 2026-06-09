import json
import re
from typing import Any

PREVIEW_MAX = 1200
DOC_URL_RE = re.compile(r"/document/d/([a-zA-Z0-9_-]+)")
GENERIC_TITLES = frozenset({"Untitled document", "Document", "Google Doc", "New document"})

CREATE_TOOLS = {
    "GOOGLEDOCS_CREATE_DOCUMENT",
    "GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN",
    "GOOGLEDOCS_COPY_DOCUMENT",
}

READ_TOOLS = {
    "GOOGLEDOCS_GET_DOCUMENT_PLAINTEXT",
    "GOOGLEDOCS_GET_DOCUMENT_BY_ID",
}

SEARCH_TOOLS = {"GOOGLEDOCS_SEARCH_DOCUMENTS"}

EDIT_TOOLS = {
    "GOOGLEDOCS_INSERT_TEXT_ACTION",
    "GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT",
    "GOOGLEDOCS_UPDATE_DOCUMENT_MARKDOWN",
    "GOOGLEDOCS_REPLACE_ALL_TEXT",
    "GOOGLEDOCS_UPDATE_DOCUMENT_BATCH",
}


def _parse_payload(content: Any) -> dict | list | str | None:
    if content is None:
        return None
    if isinstance(content, (dict, list)):
        return content
    text = str(content).strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _unwrap_composio_payload(payload: dict | list | str) -> dict | list | str:
    """Composio tools return { successful, data, error? } — unwrap to inner payload."""
    if not isinstance(payload, dict):
        return payload

    if "data" in payload and ("successful" in payload or "error" in payload):
        inner = payload["data"]
        if isinstance(inner, str):
            try:
                inner = json.loads(inner)
            except json.JSONDecodeError:
                return inner
        return _unwrap_composio_payload(inner) if isinstance(inner, dict) else inner

    return payload


def _collect_document_items(payload: dict | list | str) -> list[dict]:
    payload = _unwrap_composio_payload(payload)

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    for key in (
        "documents",
        "files",
        "results",
        "items",
        "documentList",
        "document_list",
    ):
        items = payload.get(key)
        if isinstance(items, list) and items:
            return [item for item in items if isinstance(item, dict)]

    # Single document object
    if _extract_doc_id(payload) or _extract_title(payload, fallback="") != "":
        if payload.get("name") or payload.get("title") or payload.get("documentId"):
            return [payload]

    return []


def _id_from_value(val: str) -> str | None:
    val = val.strip()
    if not val:
        return None
    match = DOC_URL_RE.search(val)
    if match:
        return match.group(1)
    return val


def _apply_tool_context(artifact: dict, tool_args: dict | None) -> dict:
    args = tool_args or {}

    if not artifact.get("document_id"):
        for key in ("documentId", "document_id", "id", "fileId", "file_id"):
            val = args.get(key)
            if isinstance(val, str) and val.strip():
                artifact["document_id"] = _id_from_value(val)
                break

    doc_id = artifact.get("document_id")
    if doc_id and not artifact.get("url"):
        artifact["url"] = _doc_url(doc_id)

    title = (artifact.get("title") or "").strip()
    if not title or title in GENERIC_TITLES:
        for key in ("title", "name", "documentTitle"):
            val = args.get(key)
            if isinstance(val, str) and val.strip():
                artifact["title"] = val.strip()
                break

    return artifact


def _clip(text: str | None, limit: int = PREVIEW_MAX) -> str | None:
    if not text:
        return None
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def _extract_doc_id(data: dict) -> str | None:
    for key in ("documentId", "document_id", "id", "fileId", "file_id"):
        val = data.get(key)
        if isinstance(val, str) and val:
            return val
    doc = data.get("document")
    if isinstance(doc, dict):
        return doc.get("documentId") or doc.get("id")
    return None


def _extract_title(data: dict, fallback: str = "Untitled document") -> str:
    for key in ("title", "name", "documentTitle", "document_title"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    doc = data.get("document")
    if isinstance(doc, dict):
        title = doc.get("title") or doc.get("name")
        if isinstance(title, str) and title.strip():
            return title.strip()
    return fallback


def _extract_modified(data: dict) -> str | None:
    for key in ("modifiedTime", "modified_time", "lastModified", "updated_at"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _doc_url(document_id: str | None, data: dict | None = None) -> str | None:
    if data:
        for key in ("webViewLink", "web_view_link", "url", "alternateLink"):
            val = data.get(key)
            if isinstance(val, str) and val.startswith("http"):
                return val
    if not document_id:
        return None
    return f"https://docs.google.com/document/d/{document_id}/edit"


def _extract_body(data: dict | str) -> str | None:
    if isinstance(data, str):
        return _clip(data)
    for key in ("text", "content", "body", "markdown_text", "markdownText", "plainText", "plain_text"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return _clip(val.strip())
    return None


def loading_artifact(tool_name: str, tool_call_id: str, tool_args: dict | None = None) -> dict:
    args = tool_args or {}
    title = args.get("title") or args.get("name") or args.get("query") or "Google Doc"
    if tool_name in SEARCH_TOOLS:
        return {
            "type": "doc-search",
            "id": tool_call_id,
            "status": "loading",
            "query": args.get("query") or args.get("title") or "documents",
        }
    if tool_name in READ_TOOLS:
        return {
            "type": "doc-preview",
            "id": tool_call_id,
            "status": "loading",
            "title": title if isinstance(title, str) else "Document",
        }
    action = "Creating" if tool_name in CREATE_TOOLS else "Updating"
    return {
        "type": "doc",
        "id": tool_call_id,
        "status": "loading",
        "action": action,
        "title": title if isinstance(title, str) else "Google Doc",
    }


def artifact_from_tool_result(
    tool_name: str,
    tool_call_id: str,
    content: Any,
    tool_args: dict | None = None,
) -> dict | None:
    payload = _parse_payload(content)
    if payload is None:
        return None

    if isinstance(payload, dict):
        payload = _unwrap_composio_payload(payload)

    artifact: dict | None = None
    if tool_name in SEARCH_TOOLS:
        artifact = _search_artifact(tool_call_id, payload)
    elif tool_name in READ_TOOLS:
        artifact = _preview_artifact(tool_call_id, payload)
    elif tool_name in CREATE_TOOLS:
        artifact = _create_artifact(tool_call_id, payload, tool_name)
    elif tool_name in EDIT_TOOLS:
        artifact = _edit_artifact(tool_call_id, payload)
    elif isinstance(tool_name, str) and tool_name.startswith("GOOGLEDOCS_"):
        artifact = _generic_doc_artifact(tool_call_id, payload)

    if artifact and tool_args:
        return _apply_tool_context(artifact, tool_args)
    return artifact


def _search_artifact(tool_call_id: str, payload: dict | list | str) -> dict:
    docs: list[dict] = []
    items = _collect_document_items(payload)
    for item in items[:20]:
        doc_id = _extract_doc_id(item)
        modified = _extract_modified(item)
        entry: dict = {
            "title": _extract_title(item),
            "document_id": doc_id,
            "url": _doc_url(doc_id, item),
        }
        if modified:
            entry["modified"] = modified
        docs.append(entry)

    query = None
    if isinstance(payload, dict):
        query = payload.get("query") or payload.get("search_query")

    return {
        "type": "doc-search",
        "id": tool_call_id,
        "status": "ready",
        "query": query,
        "documents": docs,
        "title": f"{len(docs)} document{'s' if len(docs) != 1 else ''} found",
    }


def _preview_artifact(tool_call_id: str, payload: dict | str) -> dict:
    if isinstance(payload, str):
        return {
            "type": "doc-preview",
            "id": tool_call_id,
            "status": "ready",
            "title": "Document",
            "preview": _clip(payload),
        }
    doc_id = _extract_doc_id(payload)
    body = _extract_body(payload)
    return {
        "type": "doc-preview",
        "id": tool_call_id,
        "status": "ready",
        "title": _extract_title(payload),
        "document_id": doc_id,
        "url": _doc_url(doc_id, payload),
        "preview": body,
    }


def _create_artifact(tool_call_id: str, payload: dict | str, tool_name: str) -> dict:
    if isinstance(payload, str):
        return {
            "type": "doc",
            "id": tool_call_id,
            "status": "ready",
            "action": "Created",
            "title": "New document",
            "preview": _clip(payload),
        }
    doc_id = _extract_doc_id(payload)
    body = _extract_body(payload)
    return {
        "type": "doc",
        "id": tool_call_id,
        "status": "ready",
        "action": "Created" if tool_name != "GOOGLEDOCS_COPY_DOCUMENT" else "Copied",
        "title": _extract_title(payload),
        "document_id": doc_id,
        "url": _doc_url(doc_id, payload),
        "preview": body,
    }


def _edit_artifact(tool_call_id: str, payload: dict | str) -> dict:
    if isinstance(payload, str):
        return {
            "type": "doc",
            "id": tool_call_id,
            "status": "ready",
            "action": "Updated",
            "title": "Document",
            "preview": _clip(payload),
        }
    doc_id = _extract_doc_id(payload)
    return {
        "type": "doc",
        "id": tool_call_id,
        "status": "ready",
        "action": "Updated",
        "title": _extract_title(payload),
        "document_id": doc_id,
        "url": _doc_url(doc_id, payload),
        "preview": _extract_body(payload),
    }


def _generic_doc_artifact(tool_call_id: str, payload: dict | str) -> dict:
    if isinstance(payload, str):
        return {
            "type": "doc",
            "id": tool_call_id,
            "status": "ready",
            "action": "Updated",
            "title": "Google Doc",
            "preview": _clip(payload),
        }
    doc_id = _extract_doc_id(payload)
    return {
        "type": "doc",
        "id": tool_call_id,
        "status": "ready",
        "action": "Updated",
        "title": _extract_title(payload),
        "document_id": doc_id,
        "url": _doc_url(doc_id, payload),
        "preview": _extract_body(payload),
    }


def artifact_to_markdown(artifact: dict) -> str:
    return f"```aria-artifact\n{json.dumps(artifact, ensure_ascii=False)}\n```"
