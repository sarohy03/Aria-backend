from fastapi import APIRouter, Depends, HTTPException

from agent.graph import reset_app
from auth.firebase import get_current_uid
from schemas.integrations import ConnectResponse
from services.integrations import composio_service

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/status")
def integration_status(uid: str = Depends(get_current_uid)):
    try:
        return composio_service.get_integration_status(uid)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/connect/{toolkit}", response_model=ConnectResponse)
def connect_toolkit(toolkit: str, uid: str = Depends(get_current_uid)):
    try:
        return composio_service.start_connection(uid, toolkit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/refresh")
def refresh_integrations(uid: str = Depends(get_current_uid)):
    reset_app(uid)
    try:
        return composio_service.get_integration_status(uid)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
