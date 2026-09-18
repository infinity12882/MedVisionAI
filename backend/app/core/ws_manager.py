"""
In-memory WebSocket connection manager for real-time push: notifications,
direct messages, and appointment status changes. Single-process design
(documented like the rate limiter) — for multi-worker deployments, back
this with a Redis pub/sub channel instead of the in-memory dict.
"""
from __future__ import annotations

import json
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        if websocket in self.active_connections[user_id]:
            self.active_connections[user_id].remove(websocket)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, event_type: str, payload: dict) -> None:
        connections = self.active_connections.get(user_id, [])
        message = json.dumps({"type": event_type, "data": payload})
        stale = []
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(user_id, ws)


manager = ConnectionManager()
