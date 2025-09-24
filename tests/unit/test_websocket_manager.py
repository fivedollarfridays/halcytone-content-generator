"""
WebSocket connection tests
Sprint 3: Halcytone Live Support - WebSocket manager tests
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone

from src.halcytone_content_generator.services.websocket_manager import (
    WebSocketManager,
    ConnectionRole
)


class MockWebSocket:
    """Mock WebSocket for testing"""

    def __init__(self):
        self.accepted = False
        self.messages = []
        self.closed = False
        self.headers = {
            'user-agent': 'TestClient/1.0',
            'origin': 'http://localhost'
        }

    async def accept(self):
        self.accepted = True

    async def send_json(self, data):
        self.messages.append(data)

    async def receive_text(self):
        # Simulate receiving a message
        await asyncio.sleep(0.1)
        return '{"type": "heartbeat"}'

    async def close(self):
        self.closed = True


class TestWebSocketManager:
    """Test WebSocketManager functionality"""

    @pytest.fixture
    def manager(self):
        """Create a WebSocketManager instance"""
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket"""
        return MockWebSocket()

    @pytest.mark.asyncio
    async def test_connect_new_session(self, manager, mock_websocket):
        """Test connecting to a new session"""
        session_id = "test-session-001"
        client_id = "client-001"

        await manager.connect(
            websocket=mock_websocket,
            session_id=session_id,
            client_id=client_id,
            role=ConnectionRole.PARTICIPANT
        )

        # Verify WebSocket was accepted
        assert mock_websocket.accepted

        # Verify session was created
        assert session_id in manager._active_sessions

        # Verify connection was stored
        assert session_id in manager._connections
        assert client_id in manager._connections[session_id]

        # Verify welcome message was sent
        assert len(mock_websocket.messages) >= 1
        welcome_msg = mock_websocket.messages[0]
        assert welcome_msg['type'] == 'welcome'
        assert welcome_msg['session_id'] == session_id
        assert welcome_msg['client_id'] == client_id

    @pytest.mark.asyncio
    async def test_connect_with_role(self, manager, mock_websocket):
        """Test connecting with different roles"""
        await manager.connect(
            websocket=mock_websocket,
            session_id="test-session",
            client_id="instructor-001",
            role=ConnectionRole.INSTRUCTOR
        )

        # Verify role was stored
        metadata = manager._connection_metadata.get("instructor-001")
        assert metadata is not None
        assert metadata['role'] == ConnectionRole.INSTRUCTOR

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test disconnecting from a session"""
        session_id = "test-session"
        client_id = "client-001"

        # First connect
        await manager.connect(
            websocket=mock_websocket,
            session_id=session_id,
            client_id=client_id
        )

        # Then disconnect
        await manager.disconnect(session_id, client_id)

        # Verify connection was removed
        assert client_id not in manager._connections.get(session_id, {})

        # Verify metadata was cleaned up
        assert client_id not in manager._connection_metadata

    @pytest.mark.asyncio
    async def test_session_cleanup_on_last_disconnect(self, manager, mock_websocket):
        """Test session cleanup when last participant disconnects"""
        session_id = "test-session"
        client_id = "client-001"

        await manager.connect(
            websocket=mock_websocket,
            session_id=session_id,
            client_id=client_id
        )

        await manager.disconnect(session_id, client_id)

        # Session should be cleaned up
        assert session_id not in manager._connections
        assert session_id not in manager._active_sessions

    @pytest.mark.asyncio
    async def test_broadcast_to_session(self, manager):
        """Test broadcasting message to all connections in session"""
        session_id = "test-session"

        # Create multiple mock connections
        clients = []
        for i in range(3):
            mock_ws = MockWebSocket()
            client_id = f"client-{i}"
            await manager.connect(
                websocket=mock_ws,
                session_id=session_id,
                client_id=client_id
            )
            clients.append((client_id, mock_ws))

        # Broadcast a message
        test_message = {
            'type': 'test_broadcast',
            'data': 'Hello everyone!'
        }

        await manager.broadcast_to_session(session_id, test_message)

        # Verify all clients received the broadcast
        for client_id, mock_ws in clients:
            # Skip welcome messages and participant_joined messages
            broadcast_msgs = [
                msg for msg in mock_ws.messages
                if msg.get('type') == 'test_broadcast'
            ]
            assert len(broadcast_msgs) == 1
            assert broadcast_msgs[0]['data'] == 'Hello everyone!'

    @pytest.mark.asyncio
    async def test_broadcast_with_exclusion(self, manager):
        """Test broadcasting with client exclusion"""
        session_id = "test-session"

        # Create multiple connections
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()

        await manager.connect(mock_ws1, session_id, "client-1")
        await manager.connect(mock_ws2, session_id, "client-2")

        # Broadcast excluding client-1
        test_message = {'type': 'exclusive', 'data': 'Not for client-1'}
        await manager.broadcast_to_session(
            session_id,
            test_message,
            exclude_client="client-1"
        )

        # client-1 should not receive the exclusive message
        exclusive_msgs1 = [
            msg for msg in mock_ws1.messages
            if msg.get('type') == 'exclusive'
        ]
        assert len(exclusive_msgs1) == 0

        # client-2 should receive it
        exclusive_msgs2 = [
            msg for msg in mock_ws2.messages
            if msg.get('type') == 'exclusive'
        ]
        assert len(exclusive_msgs2) == 1

    @pytest.mark.asyncio
    async def test_broadcast_by_role(self, manager):
        """Test broadcasting to specific roles only"""
        session_id = "test-session"

        # Create connections with different roles
        participant_ws = MockWebSocket()
        instructor_ws = MockWebSocket()

        await manager.connect(
            participant_ws, session_id, "participant-1",
            role=ConnectionRole.PARTICIPANT
        )
        await manager.connect(
            instructor_ws, session_id, "instructor-1",
            role=ConnectionRole.INSTRUCTOR
        )

        # Broadcast to instructors only
        test_message = {'type': 'instructor_only', 'data': 'Secret info'}
        await manager.broadcast_to_session(
            session_id,
            test_message,
            roles=[ConnectionRole.INSTRUCTOR]
        )

        # Participant should not receive it
        instructor_msgs_participant = [
            msg for msg in participant_ws.messages
            if msg.get('type') == 'instructor_only'
        ]
        assert len(instructor_msgs_participant) == 0

        # Instructor should receive it
        instructor_msgs_instructor = [
            msg for msg in instructor_ws.messages
            if msg.get('type') == 'instructor_only'
        ]
        assert len(instructor_msgs_instructor) == 1

    @pytest.mark.asyncio
    async def test_send_to_client(self, manager, mock_websocket):
        """Test sending message to specific client"""
        session_id = "test-session"
        client_id = "client-001"

        await manager.connect(
            mock_websocket, session_id, client_id
        )

        # Send direct message
        test_message = {'type': 'direct', 'data': 'Just for you'}
        await manager.send_to_client(session_id, client_id, test_message)

        # Verify message was sent
        direct_msgs = [
            msg for msg in mock_websocket.messages
            if msg.get('type') == 'direct'
        ]
        assert len(direct_msgs) == 1
        assert direct_msgs[0]['data'] == 'Just for you'

    @pytest.mark.asyncio
    async def test_handle_heartbeat(self, manager, mock_websocket):
        """Test heartbeat message handling"""
        session_id = "test-session"
        client_id = "client-001"

        await manager.connect(
            mock_websocket, session_id, client_id
        )

        # Send heartbeat
        response = await manager.handle_client_message(
            session_id,
            client_id,
            {'type': 'heartbeat'}
        )

        assert response['type'] == 'heartbeat_ack'

        # Verify heartbeat was recorded
        metadata = manager._connection_metadata.get(client_id)
        assert metadata['last_heartbeat'] is not None

    @pytest.mark.asyncio
    async def test_handle_technique_feedback(self, manager, mock_websocket):
        """Test handling technique feedback from participants"""
        session_id = "test-session"

        # Create participant and instructor
        participant_ws = MockWebSocket()
        instructor_ws = MockWebSocket()

        await manager.connect(
            participant_ws, session_id, "participant-1",
            role=ConnectionRole.PARTICIPANT
        )
        await manager.connect(
            instructor_ws, session_id, "instructor-1",
            role=ConnectionRole.INSTRUCTOR
        )

        # Participant sends technique feedback
        response = await manager.handle_client_message(
            session_id,
            "participant-1",
            {
                'type': 'technique_feedback',
                'data': {
                    'technique': 'Box Breathing',
                    'difficulty': 3,
                    'effectiveness': 8
                }
            }
        )

        assert response['type'] == 'feedback_received'

        # Instructor should receive the feedback
        feedback_msgs = [
            msg for msg in instructor_ws.messages
            if msg.get('type') == 'technique_feedback'
        ]
        assert len(feedback_msgs) > 0

    @pytest.mark.asyncio
    async def test_message_queue(self, manager, mock_websocket):
        """Test message queuing for reliability"""
        session_id = "test-session"
        client_id = "client-001"

        await manager.connect(
            mock_websocket, session_id, client_id
        )

        # Send multiple messages
        for i in range(5):
            await manager.broadcast_to_session(
                session_id,
                {'type': 'test', 'index': i}
            )

        # Check message queue
        assert session_id in manager._message_queue
        assert len(manager._message_queue[session_id]) >= 5

    @pytest.mark.asyncio
    async def test_session_replay(self, manager, mock_websocket):
        """Test getting session replay for late joiners"""
        session_id = "test-session"
        client_id = "client-001"

        await manager.connect(
            mock_websocket, session_id, client_id
        )

        # Send some messages
        messages_sent = []
        for i in range(3):
            msg = {'type': 'update', 'index': i}
            await manager.broadcast_to_session(session_id, msg)
            messages_sent.append(msg)

        # Get replay
        replay = await manager.get_session_replay(session_id)

        # Should include all messages (including system messages)
        assert len(replay) >= 3

    @pytest.mark.asyncio
    async def test_get_session_info(self, manager):
        """Test getting session information"""
        session_id = "test-session"

        # Create multiple connections
        for i in range(3):
            mock_ws = MockWebSocket()
            await manager.connect(
                mock_ws, session_id, f"client-{i}"
            )

        info = manager.get_session_info(session_id)

        assert info['active'] is True
        assert info['session_id'] == session_id
        assert info['participant_count'] == 3
        assert len(info['participants']) == 3

    @pytest.mark.asyncio
    async def test_close_session(self, manager):
        """Test closing a session and disconnecting all participants"""
        session_id = "test-session"

        # Create multiple connections
        websockets = []
        for i in range(3):
            mock_ws = MockWebSocket()
            await manager.connect(
                mock_ws, session_id, f"client-{i}"
            )
            websockets.append(mock_ws)

        # Close the session
        await manager.close_session(session_id)

        # Verify session ending message was sent
        for ws in websockets:
            ending_msgs = [
                msg for msg in ws.messages
                if msg.get('type') == 'session_ending'
            ]
            assert len(ending_msgs) == 1

        # Verify session was closed
        assert session_id not in manager._active_sessions
        assert session_id not in manager._connections

    def test_get_active_sessions(self, manager):
        """Test getting list of active sessions"""
        # Initially no sessions
        assert len(manager.get_active_sessions()) == 0

        # Add some sessions (simulated)
        manager._active_sessions.add("session-1")
        manager._active_sessions.add("session-2")

        active = manager.get_active_sessions()
        assert len(active) == 2
        assert "session-1" in active
        assert "session-2" in active