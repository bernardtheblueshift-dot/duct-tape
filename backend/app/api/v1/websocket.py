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
        if not user_id:
            await websocket.close(code=1008)  # Policy Violation
            return
    except Exception:
        # decode_access_token raises HTTPException, but WebSocket needs different handling
        await websocket.close(code=1008)  # Policy Violation
        return

    # Connect user to WebSocket manager
    await manager.connect(str(user_id), websocket)

    try:
        # Message handling loop
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                job_id = data.get("job_id")
                if job_id:
                    await manager.subscribe(str(user_id), job_id)

            elif action == "unsubscribe":
                job_id = data.get("job_id")
                if job_id:
                    await manager.unsubscribe(str(user_id), job_id)

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        # Client disconnected normally
        manager.disconnect(str(user_id))
