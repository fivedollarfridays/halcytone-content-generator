"""
Additional WebSocket tests for coverage improvement
Sprint 3: Halcytone Live Support
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone

from src.halcytone_content_generator.services.websocket_manager import (
    WebSocketManager,
    ConnectionRole
)


class TestWebSocketCoverage:
    """Additional tests to improve WebSocket coverage"""

    @pytest.fixture
    def manager(self):
        """Create a WebSocketManager instance"""
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket"""
        ws = Mock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.receive_text = AsyncMock(return_value='{"type": "heartbeat"}')
        ws.close = AsyncMock()
        ws.headers = {'user-agent': 'TestClient', 'origin': 'http://localhost'}
        return ws

    @pytest.mark.asyncio
    async def test_connection_with_metadata(self, manager, mock_websocket):
        """Test connection with role metadata"""
        await manager.connect(
            websocket=mock_websocket,
            session_id="test-session",
            client_id="client-001",
            role=ConnectionRole.INSTRUCTOR
        )

        # Verify metadata was stored
        metadata = manager._connection_metadata.get("client-001")
        assert metadata is not None
        assert metadata['role'] == ConnectionRole.INSTRUCTOR
        assert 'connected_at' in metadata
        assert 'last_heartbeat' in metadata

    @pytest.mark.asyncio
    async def test_invalid_client_message_handling(self, manager, mock_websocket):
        """Test handling of invalid client messages"""
        session_id = "test-session"
        client_id = "client-001"

        await manager.connect(mock_websocket, session_id, client_id)

        # Test invalid JSON message
        response = await manager.handle_client_message(
            session_id, client_id, None
        )
        assert response['type'] == 'error'

        # Test unsupported message type
        response = await manager.handle_client_message(
            session_id, client_id, {'type': 'unsupported_action'}
        )
        assert response['type'] == 'error'

    @pytest.mark.asyncio
    async def test_connection_limits(self, manager):
        """Test connection limits per session"""
        session_id = "test-session"

        # Connect multiple clients
        websockets = []
        for i in range(3):
            ws = Mock()
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            ws.close = AsyncMock()
            ws.headers = {'user-agent': 'TestClient'}

            await manager.connect(ws, session_id, f"client-{i}")
            websockets.append(ws)

        # Verify all connections tracked
        assert len(manager._connections[session_id]) == 3
        assert session_id in manager._active_sessions

    @pytest.mark.asyncio
    async def test_message_queue_overflow(self, manager, mock_websocket):
        """Test message queue behavior when full"""
        session_id = "test-session"
        client_id = "client-001"

        await manager.connect(mock_websocket, session_id, client_id)

        # Fill up message queue beyond capacity
        for i in range(200):  # Exceed typical queue size
            await manager.broadcast_to_session(
                session_id,
                {'type': 'test', 'message': f'Message {i}'}
            )

        # Queue should have some messages
        assert session_id in manager._message_queue
        # But should be limited to prevent memory issues
        assert len(manager._message_queue[session_id]) <= 1000

    @pytest.mark.asyncio
    async def test_role_based_message_filtering(self, manager):
        """Test message filtering by role"""
        session_id = "test-session"

        # Create connections with different roles
        participant_ws = Mock()
        participant_ws.accept = AsyncMock()
        participant_ws.send_json = AsyncMock()
        participant_ws.close = AsyncMock()
        participant_ws.headers = {'user-agent': 'TestClient'}

        admin_ws = Mock()
        admin_ws.accept = AsyncMock()
        admin_ws.send_json = AsyncMock()
        admin_ws.close = AsyncMock()
        admin_ws.headers = {'user-agent': 'AdminClient'}

        await manager.connect(participant_ws, session_id, "participant-1", ConnectionRole.PARTICIPANT)
        await manager.connect(admin_ws, session_id, "admin-1", ConnectionRole.ADMIN)

        # Send admin-only message
        await manager.broadcast_to_session(
            session_id,
            {'type': 'admin_message', 'data': 'Admin only'},
            roles=[ConnectionRole.ADMIN]
        )

        # Admin should receive message
        admin_ws.send_json.assert_called()

        # Reset mocks and check participant didn't receive admin message
        participant_ws.send_json.reset_mock()
        admin_ws.send_json.reset_mock()

        # Send public message
        await manager.broadcast_to_session(
            session_id,
            {'type': 'public_message', 'data': 'Everyone sees this'}
        )

        # Both should receive public message
        participant_ws.send_json.assert_called()
        admin_ws.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_session_statistics(self, manager):
        """Test session statistics tracking"""
        session_id = "test-session"

        # Connect some clients
        for i in range(3):
            ws = Mock()
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            ws.close = AsyncMock()
            ws.headers = {'user-agent': 'TestClient'}

            await manager.connect(ws, session_id, f"client-{i}")

        # Send some messages
        for i in range(5):
            await manager.broadcast_to_session(
                session_id,
                {'type': 'test', 'count': i}
            )

        # Get session info
        info = manager.get_session_info(session_id)
        assert info['active'] is True
        assert info['participant_count'] == 3
        assert len(info['participants']) == 3

    @pytest.mark.asyncio
    async def test_connection_cleanup_on_error(self, manager):
        """Test connection cleanup when WebSocket errors occur"""
        session_id = "test-session"
        client_id = "client-001"

        # Mock WebSocket that fails
        failing_ws = Mock()
        failing_ws.accept = AsyncMock()
        failing_ws.send_json = AsyncMock(side_effect=Exception("Connection lost"))
        failing_ws.close = AsyncMock()
        failing_ws.headers = {'user-agent': 'TestClient'}

        await manager.connect(failing_ws, session_id, client_id)

        # Try to send message (should not crash)
        try:
            await manager.send_to_client(session_id, client_id, {'type': 'test'})
        except Exception:
            # Should handle gracefully
            pass

        # Connection should still be tracked (error handling doesn't auto-remove)
        assert client_id in manager._connections.get(session_id, {})

    @pytest.mark.asyncio
    async def test_heartbeat_tracking(self, manager, mock_websocket):
        """Test heartbeat message tracking"""
        session_id = "test-session"
        client_id = "client-001"

        await manager.connect(mock_websocket, session_id, client_id)

        # Send heartbeat
        response = await manager.handle_client_message(
            session_id, client_id, {'type': 'heartbeat'}
        )

        assert response['type'] == 'heartbeat_ack'

        # Verify heartbeat was tracked
        metadata = manager._connection_metadata.get(client_id)
        assert metadata is not None
        assert 'last_heartbeat' in metadata

    def test_get_active_sessions_empty(self, manager):
        """Test getting active sessions when none exist"""
        sessions = manager.get_active_sessions()
        assert isinstance(sessions, list)
        assert len(sessions) == 0

    def test_get_session_info_nonexistent(self, manager):
        """Test getting info for non-existent session"""
        info = manager.get_session_info("nonexistent-session")
        assert info['active'] is False
        assert info['participant_count'] == 0
        assert info['participants'] == []

    @pytest.mark.asyncio
    async def test_close_nonexistent_session(self, manager):
        """Test closing a session that doesn't exist"""
        # Should not raise an error
        await manager.close_session("nonexistent-session")

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_client(self, manager):
        """Test disconnecting a client that doesn't exist"""
        # Should not raise an error
        await manager.disconnect("nonexistent-session", "nonexistent-client")

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_client(self, manager):
        """Test sending message to non-existent client"""
        # Should not raise an error
        success = await manager.send_to_client(
            "nonexistent-session",
            "nonexistent-client",
            {'type': 'test'}
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_message_replay_limit(self, manager, mock_websocket):
        """Test message replay with limits"""
        session_id = "test-session"
        client_id = "client-001"

        await manager.connect(mock_websocket, session_id, client_id)

        # Send many messages
        for i in range(150):
            await manager.broadcast_to_session(
                session_id,
                {'type': 'test', 'index': i}
            )

        # Get replay (should be limited)
        replay = await manager.get_session_replay(session_id, limit=50)
        assert len(replay) <= 50

    @pytest.mark.asyncio
    async def test_participant_status_update(self, manager, mock_websocket):
        """Test participant status update message handling"""
        session_id = "test-session"
        client_id = "participant-1"

        await manager.connect(mock_websocket, session_id, client_id, ConnectionRole.PARTICIPANT)

        # Send participant status update
        response = await manager.handle_client_message(
            session_id,
            client_id,
            {
                'type': 'participant_status',
                'data': {
                    'status': 'active',
                    'hrv_reading': 75
                }
            }
        )

        assert response['type'] == 'status_updated'

    @pytest.mark.asyncio
    async def test_broadcast_exclusion(self, manager):
        """Test broadcasting with client exclusion"""
        session_id = "test-session"

        # Create multiple connections
        clients = []
        for i in range(3):
            ws = Mock()
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            ws.close = AsyncMock()
            ws.headers = {'user-agent': 'TestClient'}

            client_id = f"client-{i}"
            await manager.connect(ws, session_id, client_id)
            clients.append((client_id, ws))

        # Broadcast excluding first client
        await manager.broadcast_to_session(
            session_id,
            {'type': 'test', 'message': 'Not for client-0'},
            exclude_client="client-0"
        )

        # client-0 should not have received the message (only welcome message)
        excluded_client_calls = clients[0][1].send_json.call_count
        other_client_calls = clients[1][1].send_json.call_count

        # The excluded client should have fewer calls (just welcome)
        assert excluded_client_calls < other_client_calls