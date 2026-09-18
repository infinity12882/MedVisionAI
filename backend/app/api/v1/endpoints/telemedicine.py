"""
WebRTC signaling relay for telemedicine video calls.

This is a real, working signaling server: two participants (patient and
doctor) connect to the same room (keyed by appointment id) over
WebSocket, and the server simply relays SDP offers/answers and ICE
candidates between them. The actual audio/video stream is peer-to-peer
(WebRTC) — no media ever passes through this server, so it scales fine
and needs no third-party video infrastructure (Twilio/Agora/etc.) to
function for a 1:1 call. A TURN server would be needed in production for
clients behind restrictive NATs; STUN-only (Google's public STUN server)
is configured on the frontend for development/most home networks.
"""
from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.security import decode_token

router = APIRouter(prefix="/telemedicine", tags=["Appointments & Telemedicine"])

# room_id -> list of connected websockets (max 2 for a 1:1 consultation)
_rooms: dict[str, list[WebSocket]] = defaultdict(list)


@router.websocket("/ws/{room_id}")
async def signaling_room(websocket: WebSocket, room_id: str, token: str = None):
    if not token:
        await websocket.close(code=4001)
        return
    try:
        decode_token(token)
    except Exception:
        await websocket.close(code=4001)
        return
    await websocket.accept()
    participants = _rooms[room_id]

    if len(participants) >= 2:
        await websocket.send_json({"type": "room-full"})
        await websocket.close()
        return

    participants.append(websocket)
    await websocket.send_json({"type": "joined", "participant_count": len(participants)})

    # Let the other participant (if any) know someone joined, so they can initiate the offer.
    for peer in participants:
        if peer is not websocket:
            await peer.send_json({"type": "peer-joined"})

    try:
        while True:
            message = await websocket.receive_json()
            # Relay signaling payloads (offer/answer/ice-candidate/hangup) to the other peer.
            for peer in participants:
                if peer is not websocket:
                    await peer.send_json(message)
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in participants:
            participants.remove(websocket)
        for peer in participants:
            await peer.send_json({"type": "peer-left"})
        if not participants:
            _rooms.pop(room_id, None)
