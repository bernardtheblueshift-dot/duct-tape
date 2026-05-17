"""WebSocket endpoint for real-time job updates"""

from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect
from app.core.security import decode_access_token
from app.core.websocket_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time updates.

    Authenticates via JWT token in query param (WebSocket can't use headers).
    Accepts subscribe/unsubscribe/ping actions.
    """
    # Authenticate via JWT token
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if not user_id:
            await websocket.close(code=1008)
            return
    except Exception:
        await websocket.close(code=1008)
        return

    await manager.connect(str(user_id), websocket)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                job_id = data.get("job_id")
                if job_id and tenant_id:
                    # Validate job belongs to user's tenant
                    from sqlalchemy import select, text
                    from app.database import AsyncSessionLocal
                    from app.models.job import Job
                    async with AsyncSessionLocal() as db:
                        await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))
                        result = await db.execute(select(Job.id).where(Job.id == job_id))
                        if result.scalar_one_or_none():
                            await manager.subscribe(str(user_id), job_id)

            elif action == "unsubscribe":
                job_id = data.get("job_id")
                if job_id:
                    await manager.unsubscribe(str(user_id), job_id)

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(str(user_id))
