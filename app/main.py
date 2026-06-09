from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.chat.chat import router as chat_router
from routes.integrations.integrations import router as integrations_router
from routes.sessions.sessions import router as sessions_router

app = FastAPI(title="Aria API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(integrations_router)
app.include_router(sessions_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
