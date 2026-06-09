# Deployment Guide — Aria

Frontend on **Vercel**, backend on **Render**. Each folder (`frontend/`, `backend/`) is its own git repo.

---

## 1. Firebase (do this first)

In [Firebase Console](https://console.firebase.google.com/):

1. **Authentication → Sign-in method** — enable Google
2. **Authentication → Settings → Authorized domains** — add:
   - `your-app.vercel.app`
   - `localhost` (for local dev)
3. **Project settings → Service accounts** — generate a new private key for the backend
4. Copy values into backend env vars (see below)

---

## 2. Backend — Render Web Service

### Create service

1. [Render Dashboard](https://dashboard.render.com/) → **New → Web Service**
2. Connect the **backend** repository
3. Settings:

| Setting | Value |
|---|---|
| **Root Directory** | *(leave empty — repo root is backend)* |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 75` |
| **Health Check Path** | `/health` |

Or use **New → Blueprint** and point at `render.yaml` in the backend repo.

### Environment variables

| Variable | Required | Notes |
|---|---|---|
| `OPENAI_API_KEY` | Yes | |
| `OPENAI_MODEL` | No | Default `gpt-5` |
| `COMPOSIO_API_KEY` | Yes | |
| `FRONTEND_URL` | Yes | `https://your-app.vercel.app` (no trailing slash) |
| `FIREBASE_PROJECT_ID` | Yes | |
| `FIREBASE_CLIENT_EMAIL` | Yes | From service account JSON |
| `FIREBASE_PRIVATE_KEY` | Yes | Full key; use `\n` for line breaks in Render UI |
| `GMAIL_FETCH_MAX_RESULTS` | No | Default `15` |
| `CORS_ORIGINS` | No | Extra origins, comma-separated (e.g. Vercel preview URLs) |

**`FIREBASE_PRIVATE_KEY` on Render:** paste the key with literal `\n` characters between lines, or paste the multiline key in Render's secret field.

### Verify

```bash
curl https://YOUR-SERVICE.onrender.com/health
# → {"status":"ok"}
```

Note your Render URL — e.g. `https://aria-api.onrender.com`.

---

## 3. Frontend — Vercel

### Create project

1. [Vercel Dashboard](https://vercel.com/) → **Add New → Project**
2. Import the **frontend** repository
3. Settings:

| Setting | Value |
|---|---|
| **Framework Preset** | Vite |
| **Root Directory** | *(repo root)* |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

`vercel.json` already configures SPA routing and `Cross-Origin-Opener-Policy` for Google sign-in.

### Environment variables

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://YOUR-SERVICE.onrender.com` |
| `VITE_FIREBASE_API_KEY` | From Firebase web app config |
| `VITE_FIREBASE_AUTH_DOMAIN` | `your-project.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | |
| `VITE_FIREBASE_STORAGE_BUCKET` | |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | |
| `VITE_FIREBASE_APP_ID` | |

Redeploy after setting env vars (Vite bakes them at build time).

### Verify

1. Open `https://your-app.vercel.app`
2. Sign in with Google
3. Connect Google account in sidebar
4. Send a test message

---

## 4. Wire backend ↔ frontend

After Vercel deploys, update Render:

```
FRONTEND_URL=https://your-app.vercel.app
```

This is used for:
- **CORS** (allowed browser origin)
- **Composio OAuth callback** (`/chat?connected=composio`)

Redeploy or restart the Render service after changing `FRONTEND_URL`.

---

## 5. Composio OAuth callback

Composio redirects users back to:

```
{FRONTEND_URL}/chat?connected=composio
```

No extra Composio dashboard callback config is needed when using Composio managed auth — just ensure `FRONTEND_URL` matches your live Vercel URL exactly.

---

## 6. Troubleshooting

| Issue | Fix |
|---|---|
| CORS error in browser | Set `FRONTEND_URL` on Render to exact Vercel URL (https, no trailing slash) |
| 401 on API calls | Check Firebase authorized domains; token may be expired — sign out/in |
| Firebase startup crash on Render | Verify all three `FIREBASE_*` vars; private key newlines as `\n` |
| SSE stream stalls | Render free tier sleeps after inactivity — first request may be slow (~30s) |
| Google sign-in popup blocked | `vercel.json` sets `Cross-Origin-Opener-Policy: same-origin-allow-popups` |
| Composio connect fails | Confirm `COMPOSIO_API_KEY` and `FRONTEND_URL` on Render |

---

## 7. Local production-like test

```bash
# Terminal 1 — backend
cd backend && source .venv/bin/activate
FRONTEND_URL=http://localhost:5173 uvicorn app.main:app --port 8000

# Terminal 2 — frontend (point at local API, not proxy)
cd frontend
VITE_API_URL=http://localhost:8000 npm run dev
```
