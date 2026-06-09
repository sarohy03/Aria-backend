import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from auth.firebase import get_current_uid
from schemas.chat import ChatRequest
from services.chat.chat_service import stream_chat as stream_chat_events

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest, uid: str = Depends(get_current_uid)):
    async def event_stream():
        try:
            async for event in stream_chat_events(uid, request.session_id, request.message):
                yield f"data: {event}\n\n"
        except ValueError as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
        except Exception as exc:
            logger.exception("Chat endpoint failed for uid=%s", uid)
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc) or 'Failed to generate response'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
