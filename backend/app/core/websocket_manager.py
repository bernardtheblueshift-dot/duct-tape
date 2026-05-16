"""WebSocket connection manager for real-time job updates"""

from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections and job subscriptions"""

    def __init__(self) -> None:
        # user_id -> WebSocket
        self.connections: dict[str, WebSocket] = {}
        # user_id -> set of job_ids they're subscribed to
        self.subscriptions: dict[str, set[str]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """
        Accept WebSocket connection and register user.

        Args:
            user_id: User UUID as string
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.connections[user_id] = websocket
        self.subscriptions[user_id] = set()

    def disconnect(self, user_id: str) -> None:
        """
        Remove user's connection and subscriptions.

        Args:
            user_id: User UUID as string
        """
        self.connections.pop(user_id, None)
        self.subscriptions.pop(user_id, None)

    async def subscribe(self, user_id: str, job_id: str) -> None:
        """
        Subscribe user to job updates.

        Args:
            user_id: User UUID as string
            job_id: Job UUID as string
        """
        if user_id in self.subscriptions:
            self.subscriptions[user_id].add(job_id)

    async def unsubscribe(self, user_id: str, job_id: str) -> None:
        """
        Unsubscribe user from job updates.

        Args:
            user_id: User UUID as string
            job_id: Job UUID as string
        """
        if user_id in self.subscriptions:
            self.subscriptions[user_id].discard(job_id)

    async def broadcast_to_job(self, job_id: str, message: dict) -> None:
        """
        Broadcast message to all users subscribed to a job.

        Args:
            job_id: Job UUID as string
            message: JSON-serializable dict to send
        """
        disconnected_users = []

        for user_id, job_ids in self.subscriptions.items():
            if job_id in job_ids:
                websocket = self.connections.get(user_id)
                if websocket:
                    try:
                        await websocket.send_json(message)
                    except Exception:
                        # Connection broken - mark for cleanup
                        disconnected_users.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)


# Global singleton instance
manager = ConnectionManager()
