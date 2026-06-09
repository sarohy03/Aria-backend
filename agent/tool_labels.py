TOOL_LABELS = {
    "GMAIL_FETCH_EMAILS": "Fetching your emails…",
    "GMAIL_SEND_EMAIL": "Sending email…",
    "GMAIL_CREATE_EMAIL_DRAFT": "Creating draft…",
    "GOOGLEDOCS_CREATE_DOCUMENT": "Creating Google Doc…",
    "GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN": "Creating Google Doc…",
    "GOOGLEDOCS_SEARCH_DOCUMENTS": "Searching your docs…",
    "GOOGLEDOCS_GET_DOCUMENT_PLAINTEXT": "Reading document…",
    "GOOGLEDOCS_GET_DOCUMENT_BY_ID": "Opening document…",
    "GOOGLEDOCS_INSERT_TEXT_ACTION": "Writing to document…",
    "GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT": "Updating document…",
    "GOOGLEDOCS_UPDATE_DOCUMENT_MARKDOWN": "Updating document…",
    "GOOGLEDOCS_REPLACE_ALL_TEXT": "Editing document…",
    "GOOGLEDOCS_UPDATE_DOCUMENT_BATCH": "Updating document…",
    "GOOGLEDOCS_COPY_DOCUMENT": "Copying document…",
    "save_user_memory": "Saving to memory…",
}


def tool_label(name: str) -> str:
    if name.startswith("GOOGLEDOCS_"):
        return TOOL_LABELS.get(name, "Working on Google Doc…")
    return TOOL_LABELS.get(name, "Working on it…")
