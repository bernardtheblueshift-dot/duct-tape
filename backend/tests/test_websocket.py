"""Tests for WebSocket endpoint and ConnectionManager"""

import pytest
from starlette.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.main import app
from app.core.websocket_manager import ConnectionManager


def test_websocket_connect_with_valid_token(admin_token: str):
    """WebSocket connection succeeds with valid JWT token"""
    client = TestClient(app)

    with client.websocket_connect(f"/ws?token={admin_token}") as websocket:
        # Connection should be established without error
        # Send ping to verify connection is active
        websocket.send_json({"action": "ping"})
        response = websocket.receive_json()
        assert response["type"] == "pong"


def test_websocket_connect_invalid_token():
    """WebSocket connection closes with invalid token"""
    client = TestClient(app)

    # Attempt connection with invalid token
    with pytest.raises(Exception):  # WebSocket will raise exception on close
        with client.websocket_connect("/ws?token=invalid_token_xyz") as websocket:
            # Should not reach here - connection should close immediately
            pass


def test_websocket_subscribe(admin_token: str, test_job):
    """WebSocket subscribe action adds user to job subscriptions"""
    client = TestClient(app)

    with client.websocket_connect(f"/ws?token={admin_token}") as websocket:
        # Subscribe to job
        websocket.send_json({
            "action": "subscribe",
            "job_id": str(test_job.id),
        })

        # No response expected (fire-and-forget)
        # But connection should remain open - verify with ping
        websocket.send_json({"action": "ping"})
        response = websocket.receive_json()
        assert response["type"] == "pong"


def test_websocket_ping_pong(admin_token: str):
    """WebSocket ping action returns pong response"""
    client = TestClient(app)

    with client.websocket_connect(f"/ws?token={admin_token}") as websocket:
        websocket.send_json({"action": "ping"})
        response = websocket.receive_json()
        assert response == {"type": "pong"}


@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    """ConnectionManager broadcasts messages to subscribed users"""
    manager = ConnectionManager()

    # Create mock WebSocket
    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()

    # Connect two users
    await manager.connect("user1", mock_ws1)
    await manager.connect("user2", mock_ws2)

    # Subscribe user1 to job
    await manager.subscribe("user1", "job123")

    # Broadcast to job
    test_message = {"type": "message", "data": {"content": "Hello"}}
    await manager.broadcast_to_job("job123", test_message)

    # user1 should receive message
    mock_ws1.send_json.assert_called_once_with(test_message)

    # user2 should NOT receive message (not subscribed)
    mock_ws2.send_json.assert_not_called()


@pytest.mark.asyncio
async def test_connection_manager_disconnect():
    """ConnectionManager removes user on disconnect"""
    manager = ConnectionManager()

    mock_ws = AsyncMock()
    await manager.connect("user1", mock_ws)
    await manager.subscribe("user1", "job123")

    # Verify user is connected
    assert "user1" in manager.connections
    assert "user1" in manager.subscriptions

    # Disconnect user
    manager.disconnect("user1")

    # Verify user is removed
    assert "user1" not in manager.connections
    assert "user1" not in manager.subscriptions


@pytest.mark.asyncio
async def test_connection_manager_cleanup_on_error():
    """ConnectionManager cleans up broken connections during broadcast"""
    manager = ConnectionManager()

    # Create mock WebSocket that raises exception
    mock_ws = AsyncMock()
    mock_ws.send_json.side_effect = Exception("Connection broken")

    await manager.connect("user1", mock_ws)
    await manager.subscribe("user1", "job123")

    # Broadcast should handle error and clean up user
    await manager.broadcast_to_job("job123", {"type": "test"})

    # User should be disconnected
    assert "user1" not in manager.connections
    assert "user1" not in manager.subscriptions
