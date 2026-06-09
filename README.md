# Aria — Backend

> **One chat. Your entire work life.**

FastAPI service powering **Aria**, an AI Chief of Staff for small business owners. It verifies Firebase auth, runs a LangGraph agent with OpenAI, executes Gmail and Google Drive actions via Composio, persists chat history in Firestore, and streams responses to the client.

---


## Overview

The backend is the brain of Aria. For each user message it:

1. Verifies the Firebase ID token
2. Loads recent chat history from Firestore
3. Runs a **LangGraph ReAct agent** (OpenAI GPT-4o + Composio tools)
4. Streams the response back via **Server-Sent Events (SSE)**
5. Saves the new messages to Firestore

### What Aria can do

| User says | Backend action |
|---|---|
| *"What emails did I get today?"* | Composio → Gmail fetch + summarize |
| *"Draft a reply to Ahmed's invoice email"* | Read email → LLM draft |
| *"Send that reply"* | Composio → Gmail send |
| *"Find my dog photos"* | Composio → Drive search |
| *"Save this summary to my Drive"* | Composio → Drive upload |
| *"Find the contract John emailed and save to Drive"* | Cross-tool: Gmail → Drive |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python 3.10) |
| Agent | LangGraph (ReAct tool-calling loop) |
| LLM | OpenAI GPT-4o (`langchain-openai`) |
| Integrations | Composio (Gmail + Google Drive) |
| Auth | Firebase Admin SDK (token verification) |
| Database | Firestore (chat history) |
| Deployment | Render |

---

## Architecture

```
Client (React)
    │  Authorization: Bearer <firebase_id_token>
    ▼
FastAPI
    ├── Auth middleware (Firebase Admin)
    ├── Firestore (sessions + messages)
    └── LangGraph Agent
            ├── OpenAI GPT-4o
            ├── Composio Gmail tools
            └── Composio Google Drive tools
```

### Agent loop

```
User message + chat history
        ↓
   [Agent Node] ── should use tool? ──► [Tool Node] → Composio → Gmail/Drive
        │                                      │
        └──────────── synthesize response ◄────┘
        ↓
   Stream SSE to client
```

### Firestore schema

```
/users/{uid}/sessions/{session_id}/messages/{message_id}
```

Each session stores ordered messages. On every request, the last N messages are loaded as context for the agent.

---

## Project Structure

```
backend/
├── app/
│   └── main.py              # FastAPI app, routes, CORS (current)
├── agent/                   # Planned
│   ├── graph.py             # LangGraph agent definition
│   ├── tools.py             # Composio tool setup
│   └── prompts.py           # Aria system prompt
├── auth/                    # Planned
│   └── firebase.py          # Token verification middleware
├── db/                      # Planned
│   └── firestore.py         # Chat history CRUD
├── .venv/                   # Python 3.10 virtual environment
├── requirements.txt
├── .env.example
└── README.md
```

> **Note:** `agent/`, `auth/`, and `db/` reflect the target layout from the project blueprint. Core scaffolding exists in `app/main.py`; agent and persistence layers are next.

---

## Prerequisites

- Python 3.10 or 3.11
- Firebase project with Admin SDK credentials
- OpenAI API key
- Composio account with Gmail + Google Drive connected

---

## Getting Started

### 1. Create and activate the virtual environment

```bash
python3.10 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

```env
OPENAI_API_KEY=
COMPOSIO_API_KEY=
FIREBASE_PROJECT_ID=
FIREBASE_PRIVATE_KEY=
FIREBASE_CLIENT_EMAIL=
```

Never commit `.env` or service account keys to version control.

### 4. Run the development server

```bash
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | No | Health check |
| `POST` | `/chat` | Yes | Send message, stream SSE response |
| `GET` | `/sessions` | Yes | List user's chat sessions |
| `GET` | `/sessions/{id}` | Yes | Get messages in a session |
| `DELETE` | `/sessions/{id}` | Yes | Delete a session |

### Streaming chat (`POST /chat`)

Request body:

```json
{
  "message": "What emails did I get today?",
  "session_id": "optional-session-id"
}
```

Response: `text/event-stream` — tokens streamed as SSE events.

Headers required:

```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

---

## Composio Tools

**Gmail**
- `GMAIL_FETCH_EMAILS` — fetch with filters (date, sender, read status)
- `GMAIL_SEND_EMAIL` — send an email
- `GMAIL_CREATE_EMAIL_DRAFT` — create a draft

**Google Drive**
- `GOOGLEDRIVE_FIND_FILE` — search by name, type, date
- `GOOGLEDRIVE_UPLOAD_FILE` — upload or create a file
- `GOOGLEDRIVE_GET_FILE_CONTENT` — read file contents

---

## Aria System Prompt (summary)

Aria is a professional, concise AI Chief of Staff with access to the user's Gmail and Drive. Key rules:

- Check today's date before fetching emails
- Summarize emails clearly (sender, subject, one-line summary)
- Confirm before sending replies
- Never invent emails or files
- Remember full in-session conversation history

Full prompt lives in `agent/prompts.py` (planned).

---

## Build Checklist

### Day 1 — Backend + Agent Core

- [x] FastAPI project setup
- [x] CORS configured for frontend dev server
- [x] `/health` endpoint
- [ ] Firebase Admin token verification middleware
- [ ] Firestore chat history CRUD
- [ ] Composio account setup + Gmail + Drive connected
- [ ] LangGraph agent with Composio tools
- [ ] `/chat` endpoint with streaming SSE
- [ ] `/sessions` CRUD endpoints
- [ ] Test agent in isolation (curl / Postman)

### Day 2 — Integration + Deploy

- [ ] Connect frontend auth flow
- [ ] End-to-end test with real Gmail + Drive
- [ ] Deploy to Render
- [ ] Production env vars and Firebase credentials

---

## Deployment (Render)

Full guide: [DEPLOY.md](./DEPLOY.md)

### Render Web Service

| Setting | Value |
|---|---|
| Build | `pip install -r requirements.txt` |
| Start | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 75` |
| Health check | `/health` |

Or deploy via `render.yaml` (Blueprint).

### Required env vars

`OPENAI_API_KEY`, `COMPOSIO_API_KEY`, `FRONTEND_URL` (your Vercel URL), `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY`

`FRONTEND_URL` controls CORS and Composio OAuth callbacks. Optional `CORS_ORIGINS` for extra origins (comma-separated).

---

## Local Testing

```bash
# Health check
curl http://localhost:8000/health

# Chat (once auth + agent are implemented)
curl -N -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <firebase_id_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What emails did I get today?"}'
```

---

## Related

- [Frontend README](../frontend/README.md)
- [Project Blueprint](../Scope.md)
