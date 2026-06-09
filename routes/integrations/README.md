# Integrations routes

`GET /integrations/status` — Gmail/Drive connection state for the current user.

`POST /integrations/connect/{toolkit}` — returns Composio OAuth URL (`gmail` or `googledrive`).

`POST /integrations/refresh` — clears agent tool cache and re-checks status (call after OAuth return).
