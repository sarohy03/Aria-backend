TOOL_LABELS = {
    "GMAIL_FETCH_EMAILS": "Fetching your emails…",
    "GMAIL_SEND_EMAIL": "Sending email…",
    "GMAIL_CREATE_EMAIL_DRAFT": "Creating draft…",
    "GOOGLEDRIVE_FIND_FILE": "Searching Google Drive…",
    "GOOGLEDRIVE_UPLOAD_FILE": "Uploading to Drive…",
    "GOOGLEDRIVE_GET_FILE_CONTENT": "Reading file from Drive…",
}


def tool_label(name: str) -> str:
    return TOOL_LABELS.get(name, "Working on it…")
