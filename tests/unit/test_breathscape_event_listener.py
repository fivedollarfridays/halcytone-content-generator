"""
Event handling tests for BreathscapeEventListener
Sprint 3: Halcytone Live Support - Event processing tests
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from src.halcytone_content_generator.services.breathscape_event_listener import (
    BreathscapeEventListener,
    BreathscapeEventType
)


class TestBreathscapeEventListener:
    """Test BreathscapeEventListener functionality"""

    @pytest.fixture
    def listener(self):
        """Create a BreathscapeEventListener instance"""
        return BreathscapeEventListener()

    @pytest.mark.asyncio
    async def test_event_handler_registration(self, listener):
        """Test registering event handlers"""
        handler_called = False

        async def test_handler(event):
            nonlocal handler_called
            handler_called = True

        listener.register_handler(
            BreathscapeEventType.SESSION_STARTED,
            test_handler
        )

        # Verify handler was registered
        assert BreathscapeEventType.SESSION_STARTED in listener.event_handlers
        assert test_handler in listener.event_handlers[BreathscapeEventType.SESSION_STARTED]

    @pytest.mark.asyncio
    async def test_process_event(self, listener):
        """Test processing an event"""
        test_event = {
            'type': BreathscapeEventType.SESSION_STARTED.value,
            'session_id': 'test-session-001',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'title': 'Test Session',
                'instructor': 'Test Instructor'
            }
        }

        # Process the event
        await listener.process_event(test_event)

        # Event should be added to queue
        assert not listener._event_queue.empty()

    @pytest.mark.asyncio
    async def test_event_transformation(self, listener):
        """Test event transformation to content-ready format"""
        # Test session started event
        raw_event = {
            'type': BreathscapeEventType.SESSION_STARTED.value,
            'session_id': 'test-session',
            'data': {
                'title': 'Morning Session',
                'instructor': 'Sarah Chen'
            }
        }

        transformed = await listener._transform_event(raw_event)

        assert transformed['type'] == BreathscapeEventType.SESSION_STARTED.value
        assert transformed['session_id'] == 'test-session'
        assert 'content' in transformed
        assert 'Live Session Started' in transformed['content']['title']
        assert 'Sarah Chen' in transformed['content']['message']

    @pytest.mark.asyncio
    async def test_hrv_milestone_transformation(self, listener):
        """Test HRV milestone event transformation"""
        raw_event = {
            'type': BreathscapeEventType.HRV_MILESTONE.value,
            'session_id': 'test-session',
            'data': {
                'improvement': 15.5,
                'milestone': '15% improvement reached!'
            }
        }

        transformed = await listener._transform_event(raw_event)

        assert 'HRV Milestone Reached' in transformed['content']['title']
        assert '+15.5%' in transformed['content']['message']
        assert transformed['content']['achievement'] is True

    @pytest.mark.asyncio
    async def test_technique_changed_transformation(self, listener):
        """Test technique change event transformation"""
        raw_event = {
            'type': BreathscapeEventType.TECHNIQUE_CHANGED.value,
            'session_id': 'test-session',
            'data': {
                'technique': 'Box Breathing',
                'duration': 300,
                'instruction': 'Follow the 4-4-4-4 pattern'
            }
        }

        transformed = await listener._transform_event(raw_event)

        assert 'Box Breathing' in transformed['content']['title']
        assert '5 minutes' in transformed['content']['message']
        assert transformed['content']['instruction'] == 'Follow the 4-4-4-4 pattern'

    @pytest.mark.asyncio
    async def test_default_handlers(self, listener):
        """Test default event handlers are registered"""
        listener._register_default_handlers()

        # Verify default handlers are registered
        assert BreathscapeEventType.SESSION_STARTED in listener.event_handlers
        assert BreathscapeEventType.SESSION_ENDED in listener.event_handlers
        assert BreathscapeEventType.PARTICIPANT_JOINED in listener.event_handlers
        assert BreathscapeEventType.HRV_MILESTONE in listener.event_handlers
        assert BreathscapeEventType.TECHNIQUE_CHANGED in listener.event_handlers

    @pytest.mark.asyncio
    @patch('src.halcytone_content_generator.services.breathscape_event_listener.websocket_manager')
    async def test_session_started_handler(self, mock_ws_manager, listener):
        """Test session started event handler"""
        mock_ws_manager.broadcast_session_update = AsyncMock()

        listener._register_default_handlers()

        event = {
            'type': BreathscapeEventType.SESSION_STARTED.value,
            'session_id': 'test-session',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'title': 'Test Session',
                'instructor': 'Test Instructor'
            }
        }

        # Transform and process event
        transformed = await listener._transform_event(event)

        # Find and execute handler
        handlers = listener.event_handlers[BreathscapeEventType.SESSION_STARTED]
        for handler in handlers:
            await handler(transformed)

        # Verify session was tracked
        assert 'test-session' in listener.active_sessions

        # Verify WebSocket broadcast was called
        mock_ws_manager.broadcast_session_update.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.halcytone_content_generator.services.breathscape_event_listener.websocket_manager')
    async def test_session_ended_handler(self, mock_ws_manager, listener):
        """Test session ended event handler"""
        mock_ws_manager.broadcast_session_update = AsyncMock()
        mock_ws_manager.close_session = AsyncMock()

        listener._register_default_handlers()

        # First start a session
        listener.active_sessions['test-session'] = {
            'started_at': datetime.now(timezone.utc).isoformat(),
            'data': {},
            'participants': [],
            'metrics': {}
        }

        event = {
            'type': BreathscapeEventType.SESSION_ENDED.value,
            'session_id': 'test-session',
            'data': {
                'duration': 1800,
                'total_participants': 25,
                'average_hrv_improvement': 12.5
            }
        }

        transformed = await listener._transform_event(event)

        # Execute handler
        handlers = listener.event_handlers[BreathscapeEventType.SESSION_ENDED]
        for handler in handlers:
            await handler(transformed)

        # Verify broadcast was called
        mock_ws_manager.broadcast_session_update.assert_called_once_with(
            'test-session',
            'session_ended',
            {
                'message': 'Session completed successfully!',
                'duration': 1800,
                'summary_available': True
            }
        )

    @pytest.mark.asyncio
    @patch('src.halcytone_content_generator.services.breathscape_event_listener.websocket_manager')
    async def test_participant_joined_handler(self, mock_ws_manager, listener):
        """Test participant joined event handler"""
        mock_ws_manager.broadcast_session_update = AsyncMock()

        listener._register_default_handlers()

        # Create active session
        listener.active_sessions['test-session'] = {
            'participants': []
        }

        event = {
            'type': BreathscapeEventType.PARTICIPANT_JOINED.value,
            'session_id': 'test-session',
            'data': {
                'participant_id': 'user-001',
                'name': 'Alice'
            }
        }

        transformed = await listener._transform_event(event)

        # Execute handler
        handlers = listener.event_handlers[BreathscapeEventType.PARTICIPANT_JOINED]
        for handler in handlers:
            await handler(transformed)

        # Verify participant was added
        assert len(listener.active_sessions['test-session']['participants']) == 1

        # Verify broadcast
        mock_ws_manager.broadcast_session_update.assert_called_once()
        call_args = mock_ws_manager.broadcast_session_update.call_args
        assert call_args[0][1] == 'participant_joined'
        assert call_args[0][2]['name'] == 'Alice'

    @pytest.mark.asyncio
    async def test_start_listening(self, listener):
        """Test starting the event listener"""
        # Start in simulation mode (no URL)
        await listener.start_listening()

        assert listener._running is True

        # Stop listening
        await listener.stop_listening()

        assert listener._running is False

    @pytest.mark.asyncio
    async def test_multiple_handler_execution(self, listener):
        """Test multiple handlers for same event"""
        handler1_called = False
        handler2_called = False

        async def handler1(event):
            nonlocal handler1_called
            handler1_called = True

        async def handler2(event):
            nonlocal handler2_called
            handler2_called = True

        listener.register_handler(BreathscapeEventType.SESSION_STARTED, handler1)
        listener.register_handler(BreathscapeEventType.SESSION_STARTED, handler2)

        # Process an event
        event = {
            'type': BreathscapeEventType.SESSION_STARTED.value,
            'session_id': 'test-session',
            'data': {}
        }

        # Manually trigger handlers
        transformed = await listener._transform_event(event)
        for handler in listener.event_handlers[BreathscapeEventType.SESSION_STARTED]:
            await handler(transformed)

        assert handler1_called
        assert handler2_called

    def test_get_active_sessions_info(self, listener):
        """Test getting active sessions information"""
        # Add some active sessions
        listener.active_sessions['session-1'] = {
            'started_at': '2024-03-21T10:00:00Z',
            'participants': ['user-1', 'user-2'],
            'metrics': {'hrv_improvement': 10.5}
        }

        listener.active_sessions['session-2'] = {
            'started_at': '2024-03-21T11:00:00Z',
            'participants': ['user-3'],
            'metrics': {'hrv_improvement': 8.0}
        }

        info = listener.get_active_sessions_info()

        assert info['count'] == 2
        assert len(info['sessions']) == 2

        # Verify session details
        session_ids = [s['session_id'] for s in info['sessions']]
        assert 'session-1' in session_ids
        assert 'session-2' in session_ids

    @pytest.mark.asyncio
    async def test_achievement_unlocked_transformation(self, listener):
        """Test achievement unlocked event transformation"""
        raw_event = {
            'type': BreathscapeEventType.ACHIEVEMENT_UNLOCKED.value,
            'session_id': 'test-session',
            'data': {
                'description': 'First perfect breathing cycle!',
                'badge_url': 'https://example.com/badge.png'
            }
        }

        transformed = await listener._transform_event(raw_event)

        assert transformed['content']['title'] == '🏆 Achievement Unlocked!'
        assert transformed['content']['message'] == 'First perfect breathing cycle!'
        assert transformed['content']['badge'] == 'https://example.com/badge.png'
        assert transformed['content']['celebration'] is True

    @pytest.mark.asyncio
    async def test_event_queue_processing(self, listener):
        """Test event queue processing with timeout"""
        # Start processing (will timeout quickly since no events)
        listener._running = True
        process_task = asyncio.create_task(listener._process_event_queue())

        # Let it run briefly
        await asyncio.sleep(0.2)

        # Stop and clean up
        listener._running = False
        await asyncio.wait_for(process_task, timeout=2.0)

        # Should complete without errors
        assert not listener._running