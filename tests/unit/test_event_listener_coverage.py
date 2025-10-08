"""
Additional Breathscape Event Listener tests for coverage improvement
Sprint 3: Halcytone Live Support
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from halcytone_content_generator.services.breathscape_event_listener import (
    BreathscapeEventListener,
    BreathscapeEventType
)


class TestEventListenerCoverage:
    """Additional tests to improve event listener coverage"""

    @pytest.fixture
    def listener(self):
        """Create a BreathscapeEventListener instance"""
        return BreathscapeEventListener()

    @pytest.mark.asyncio
    async def test_connect_to_breathscape_url(self, listener):
        """Test connection to Breathscape with URL"""
        # This is a placeholder implementation, should not crash
        await listener._connect_to_breathscape("ws://test.breathscape.com/ws")

    @pytest.mark.asyncio
    async def test_start_stop_listening(self, listener):
        """Test start and stop listening lifecycle"""
        # Start listening
        listener_task = asyncio.create_task(listener.start_listening())

        # Let it run briefly
        await asyncio.sleep(0.1)
        assert listener._running is True

        # Stop listening
        await listener.stop_listening()
        assert listener._running is False

        # Wait for task to complete
        try:
            await asyncio.wait_for(listener_task, timeout=1.0)
        except asyncio.TimeoutError:
            listener_task.cancel()

    @pytest.mark.asyncio
    async def test_start_simulation(self, listener):
        """Test simulation mode"""
        # Start simulation
        simulation_task = asyncio.create_task(listener.start_simulation())

        # Let it run briefly
        await asyncio.sleep(0.2)

        # Stop simulation
        await listener.stop_listening()

        # Wait for simulation to complete
        try:
            await asyncio.wait_for(simulation_task, timeout=2.0)
        except asyncio.TimeoutError:
            simulation_task.cancel()

    @pytest.mark.asyncio
    async def test_process_invalid_event(self, listener):
        """Test processing invalid event data"""
        # Process event without type
        await listener.process_event({'session_id': 'test'})

        # Process event with invalid type
        await listener.process_event({
            'type': 'invalid.event.type',
            'session_id': 'test'
        })

        # Should not crash

    @pytest.mark.asyncio
    async def test_session_started_event_processing(self, listener):
        """Test session started event processing"""
        listener._register_default_handlers()

        event = {
            'type': BreathscapeEventType.SESSION_STARTED.value,
            'session_id': 'test-session',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'title': 'Test Session',
                'instructor': 'Test Instructor',
                'participants': []
            }
        }

        await listener.process_event(event)

        # Session should be tracked
        assert 'test-session' in listener.active_sessions

    @pytest.mark.asyncio
    async def test_session_ended_event_processing(self, listener):
        """Test session ended event processing"""
        listener._register_default_handlers()

        # First add a session
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
                'total_participants': 10,
                'average_hrv_improvement': 8.5
            }
        }

        # Mock the WebSocket manager to avoid actual broadcast
        with patch('halcytone_content_generator.services.breathscape_event_listener.websocket_manager') as mock_ws:
            mock_ws.broadcast_session_update = AsyncMock()
            mock_ws.close_session = AsyncMock()

            await listener.process_event(event)

            # Session should be removed
            assert 'test-session' not in listener.active_sessions

    @pytest.mark.asyncio
    async def test_participant_left_transformation(self, listener):
        """Test participant left event transformation"""
        raw_event = {
            'type': BreathscapeEventType.PARTICIPANT_LEFT.value,
            'session_id': 'test-session',
            'data': {
                'participant_id': 'user-123',
                'name': 'John Doe',
                'reason': 'disconnected'
            }
        }

        transformed = await listener._transform_event(raw_event)

        assert 'content' in transformed
        assert 'title' in transformed['content']
        assert 'message' in transformed['content']

    @pytest.mark.asyncio
    async def test_system_alert_transformation(self, listener):
        """Test system alert event transformation"""
        raw_event = {
            'type': BreathscapeEventType.SYSTEM_ALERT.value,
            'session_id': 'test-session',
            'data': {
                'alert_type': 'warning',
                'message': 'High server load detected'
            }
        }

        transformed = await listener._transform_event(raw_event)

        assert 'content' in transformed
        assert 'System Alert' in transformed['content']['title']
        assert 'High server load detected' in transformed['content']['message']

    @pytest.mark.asyncio
    async def test_instructor_message_transformation(self, listener):
        """Test instructor message event transformation"""
        raw_event = {
            'type': BreathscapeEventType.INSTRUCTOR_MESSAGE.value,
            'session_id': 'test-session',
            'data': {
                'instructor_name': 'Sarah Chen',
                'message': 'Great work everyone!',
                'priority': 'normal'
            }
        }

        transformed = await listener._transform_event(raw_event)

        assert 'content' in transformed
        assert 'Sarah Chen' in transformed['content']['title']
        assert 'Great work everyone!' in transformed['content']['message']

    @pytest.mark.asyncio
    async def test_session_metrics_update_transformation(self, listener):
        """Test session metrics update transformation"""
        raw_event = {
            'type': BreathscapeEventType.SESSION_METRICS_UPDATE.value,
            'session_id': 'test-session',
            'data': {
                'average_hrv': 78.5,
                'completion_rate': 0.92,
                'engagement_score': 4.3
            }
        }

        transformed = await listener._transform_event(raw_event)

        assert 'content' in transformed
        assert 'metrics' in transformed['content']
        assert transformed['content']['metrics']['average_hrv'] == 78.5

    @pytest.mark.asyncio
    async def test_unknown_event_type_transformation(self, listener):
        """Test transformation of unknown event type"""
        raw_event = {
            'type': 'unknown.event.type',
            'session_id': 'test-session',
            'data': {}
        }

        # Should not crash, should return basic transformation
        transformed = await listener._transform_event(raw_event)
        assert 'type' in transformed
        assert 'session_id' in transformed

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.services.breathscape_event_listener.websocket_manager')
    async def test_hrv_milestone_handler(self, mock_ws_manager, listener):
        """Test HRV milestone event handler"""
        mock_ws_manager.broadcast_session_update = AsyncMock()

        listener._register_default_handlers()

        event = {
            'type': BreathscapeEventType.HRV_MILESTONE.value,
            'session_id': 'test-session',
            'data': {
                'improvement': 15.5,
                'milestone': 'Excellent progress!'
            }
        }

        transformed = await listener._transform_event(event)

        # Execute handler
        handlers = listener.event_handlers[BreathscapeEventType.HRV_MILESTONE]
        for handler in handlers:
            await handler(transformed)

        # Verify broadcast was called
        mock_ws_manager.broadcast_session_update.assert_called_once()

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.services.breathscape_event_listener.websocket_manager')
    async def test_achievement_unlocked_handler(self, mock_ws_manager, listener):
        """Test achievement unlocked event handler"""
        mock_ws_manager.broadcast_session_update = AsyncMock()

        listener._register_default_handlers()

        event = {
            'type': BreathscapeEventType.ACHIEVEMENT_UNLOCKED.value,
            'session_id': 'test-session',
            'data': {
                'description': 'Perfect breathing cycle achieved!',
                'badge_url': 'https://example.com/badge.png'
            }
        }

        transformed = await listener._transform_event(event)

        # Execute handler
        handlers = listener.event_handlers[BreathscapeEventType.ACHIEVEMENT_UNLOCKED]
        for handler in handlers:
            await handler(transformed)

        # Verify broadcast was called
        mock_ws_manager.broadcast_session_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_handler_error_handling(self, listener):
        """Test error handling in event handlers"""
        # Register a handler that throws an exception
        async def failing_handler(event):
            raise Exception("Handler failed")

        listener.register_handler(BreathscapeEventType.SESSION_STARTED, failing_handler)

        event = {
            'type': BreathscapeEventType.SESSION_STARTED.value,
            'session_id': 'test-session',
            'data': {}
        }

        # Should not crash, should handle exception gracefully
        await listener.process_event(event)

    def test_get_active_sessions_info_empty(self, listener):
        """Test getting active sessions info when none exist"""
        info = listener.get_active_sessions_info()
        assert info['count'] == 0
        assert info['sessions'] == []

    def test_get_active_sessions_info_with_sessions(self, listener):
        """Test getting active sessions info with existing sessions"""
        # Add some mock sessions
        listener.active_sessions['session-1'] = {
            'started_at': '2024-03-21T10:00:00Z',
            'participants': ['user-1', 'user-2'],
            'metrics': {'hrv_improvement': 12.5}
        }
        listener.active_sessions['session-2'] = {
            'started_at': '2024-03-21T11:00:00Z',
            'participants': ['user-3'],
            'metrics': {'hrv_improvement': 8.0}
        }

        info = listener.get_active_sessions_info()
        assert info['count'] == 2
        assert len(info['sessions']) == 2

        # Check session details
        session_ids = [s['session_id'] for s in info['sessions']]
        assert 'session-1' in session_ids
        assert 'session-2' in session_ids

    @pytest.mark.asyncio
    async def test_queue_timeout_handling(self, listener):
        """Test queue timeout handling in event processing"""
        listener._running = True

        # Create a task that will timeout on empty queue
        process_task = asyncio.create_task(listener._process_event_queue())

        # Let it run briefly and timeout
        await asyncio.sleep(0.1)

        # Stop processing
        listener._running = False

        try:
            await asyncio.wait_for(process_task, timeout=1.0)
        except asyncio.TimeoutError:
            process_task.cancel()

    @pytest.mark.asyncio
    async def test_multiple_event_types_simulation(self, listener):
        """Test processing multiple event types in sequence"""
        events_processed = []

        async def tracking_handler(event):
            events_processed.append(event['type'])

        # Register handler for multiple event types
        for event_type in [
            BreathscapeEventType.SESSION_STARTED,
            BreathscapeEventType.TECHNIQUE_CHANGED,
            BreathscapeEventType.HRV_MILESTONE
        ]:
            listener.register_handler(event_type, tracking_handler)

        # Process different event types
        events = [
            {
                'type': BreathscapeEventType.SESSION_STARTED.value,
                'session_id': 'test',
                'data': {}
            },
            {
                'type': BreathscapeEventType.TECHNIQUE_CHANGED.value,
                'session_id': 'test',
                'data': {'technique': 'Box Breathing', 'duration': 300}
            },
            {
                'type': BreathscapeEventType.HRV_MILESTONE.value,
                'session_id': 'test',
                'data': {'improvement': 10}
            }
        ]

        for event in events:
            await listener.process_event(event)

        # All events should have been processed
        assert len(events_processed) == 3
        assert BreathscapeEventType.SESSION_STARTED.value in events_processed
        assert BreathscapeEventType.TECHNIQUE_CHANGED.value in events_processed
        assert BreathscapeEventType.HRV_MILESTONE.value in events_processed