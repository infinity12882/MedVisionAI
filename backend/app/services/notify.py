from __future__ import annotations

import asyncio

from sqlalchemy.orm import Session

from app.core.ws_manager import manager
from app.models.system import Notification


try:
    _main_loop = asyncio.get_event_loop()
except RuntimeError:
    _main_loop = None

def notify(db: Session, *, user_id: str, title: str, message: str, category: str = "info") -> Notification:
    notification = Notification(user_id=user_id, title=title, message=message, category=category)
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Best-effort real-time push; never let a missing event loop break the calling request.
    try:
        coro = manager.send_to_user(
            user_id,
            "notification",
            {
                "id": notification.id,
                "title": title,
                "message": message,
                "category": category,
                "created_at": notification.created_at.isoformat(),
            },
        )
        if _main_loop and _main_loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, _main_loop)
        else:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(coro)
            except RuntimeError:
                pass
    except Exception:
        pass

    return notification
