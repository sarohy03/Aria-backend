# Integrations service

Composio OAuth for Gmail and Google Docs. Uses the Firebase `uid` as Composio `user_id` so connections map to the logged-in user.

| File | Purpose |
|---|---|
| `composio_client.py` | Shared Composio SDK client |
| `composio_service.py` | OAuth link generation + connection status |
