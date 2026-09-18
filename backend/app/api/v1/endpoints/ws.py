from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.security import decode_token
from app.core.ws_manager import manager

router = APIRouter(tags=["Real-time Notifications"])


@router.websocket("/ws/notifications")
async def notifications_socket(websocket: WebSocket, token: str):
    """
    Browsers can't set custom Authorization headers on a WebSocket
    handshake, so the access token is passed as a query parameter instead:
    `wss://.../ws/notifications?token=<access_token>`.
    """
    try:
        payload = decode_token(token, token_type="access")
        user_id = payload["sub"]
    except (JWTError, KeyError):
        await websocket.close(code=4401)
        return

    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # client doesn't need to send anything; keeps connection alive
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception:
        manager.disconnect(user_id, websocket)
