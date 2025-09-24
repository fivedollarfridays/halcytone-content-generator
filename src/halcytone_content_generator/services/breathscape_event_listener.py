"""
Breathscape Event Listener
Sprint 3: Halcytone Live Support - Listen to and process Breathscape platform events
"""
import logging
import asyncio
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone
from enum import Enum

from .websocket_manager import websocket_manager
from .session_summary_generator import SessionSummaryGenerator

logger = logging.getLogger(__name__)


class BreathscapeEventType(str, Enum):
    """Types of Breathscape platform events"""
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"
    TECHNIQUE_CHANGED = "technique.changed"
    PARTICIPANT_JOINED = "participant.joined"
    PARTICIPANT_LEFT = "participant.left"
    HRV_MILESTONE = "hrv.milestone"
    ACHIEVEMENT_UNLOCKED = "achievement.unlocked"
    INSTRUCTOR_MESSAGE = "instructor.message"
    SYSTEM_ALERT = "system.alert"
    SESSION_METRICS_UPDATE = "session.metrics_update"


class BreathscapeEventListener:
    """
    Listens to events from the Breathscape platform and transforms them into content updates
    Integrates with WebSocket manager for real-time distribution
    """

    def __init__(self):
        self.event_handlers: Dict[BreathscapeEventType, List[Callable]] = {}
        self.session_generator = SessionSummaryGenerator()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._event_queue: asyncio.Queue = asyncio.Queue()

    def register_handler(self, event_type: BreathscapeEventType, handler: Callable):
        """
        Register an event handler for specific event type

        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type}")

    async def start_listening(self, breathscape_url: Optional[str] = None):
        """
        Start listening for Breathscape events

        Args:
            breathscape_url: Optional WebSocket URL for Breathscape platform
        """
        if self._running:
            logger.warning("Event listener is already running")
            return

        self._running = True
        logger.info("Starting Breathscape event listener")

        # Register default handlers
        self._register_default_handlers()

        # Start event processing task
        asyncio.create_task(self._process_event_queue())

        # If URL provided, connect to Breathscape platform
        if breathscape_url:
            asyncio.create_task(self._connect_to_breathscape(breathscape_url))
        else:
            # For development: simulate events
            asyncio.create_task(self._simulate_events())

    async def stop_listening(self):
        """Stop listening for events"""
        self._running = False
        logger.info("Stopping Breathscape event listener")

    async def process_event(self, event: Dict[str, Any]):
        """
        Process incoming Breathscape event

        Args:
            event: Event data from Breathscape platform
        """
        event_type = event.get('type')

        if not event_type:
            logger.warning(f"Event missing type: {event}")
            return

        # Add to queue for processing
        await self._event_queue.put(event)

    async def _process_event_queue(self):
        """Process events from the queue"""
        while self._running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )

                event_type = BreathscapeEventType(event.get('type'))

                # Transform event data
                transformed_event = await self._transform_event(event)

                # Call registered handlers
                handlers = self.event_handlers.get(event_type, [])
                for handler in handlers:
                    try:
                        await handler(transformed_event)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _transform_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Breathscape event into content-ready format

        Args:
            event: Raw event from Breathscape

        Returns:
            Transformed event data
        """
        event_type = BreathscapeEventType(event.get('type'))
        session_id = event.get('session_id')
        timestamp = event.get('timestamp', datetime.now(timezone.utc).isoformat())

        # Base transformation
        transformed = {
            'type': event_type.value,
            'session_id': session_id,
            'timestamp': timestamp,
            'data': event.get('data', {})
        }

        # Type-specific transformations
        if event_type == BreathscapeEventType.SESSION_STARTED:
            transformed['content'] = {
                'title': f"🎉 Live Session Started: {event.get('data', {}).get('title', 'Breathing Session')}",
                'message': f"Join now for guided breathing with {event.get('data', {}).get('instructor', 'our instructor')}",
                'call_to_action': 'Join Session'
            }

        elif event_type == BreathscapeEventType.HRV_MILESTONE:
            hrv_data = event.get('data', {})
            transformed['content'] = {
                'title': '💗 HRV Milestone Reached!',
                'message': f"Group HRV improvement: +{hrv_data.get('improvement', 0)}%",
                'achievement': True
            }

        elif event_type == BreathscapeEventType.TECHNIQUE_CHANGED:
            technique_data = event.get('data', {})
            transformed['content'] = {
                'title': f"🌬️ Now Practicing: {technique_data.get('technique', 'New Technique')}",
                'message': f"Duration: {technique_data.get('duration', 5)} minutes",
                'instruction': technique_data.get('instruction', '')
            }

        elif event_type == BreathscapeEventType.ACHIEVEMENT_UNLOCKED:
            achievement_data = event.get('data', {})
            transformed['content'] = {
                'title': '🏆 Achievement Unlocked!',
                'message': achievement_data.get('description', 'New achievement earned'),
                'badge': achievement_data.get('badge_url'),
                'celebration': True
            }

        return transformed

    def _register_default_handlers(self):
        """Register default event handlers"""

        # Session started handler
        async def handle_session_started(event: Dict[str, Any]):
            session_id = event.get('session_id')

            # Track active session
            self.active_sessions[session_id] = {
                'started_at': event.get('timestamp'),
                'data': event.get('data', {}),
                'participants': [],
                'metrics': {}
            }

            # Broadcast to WebSocket clients
            await websocket_manager.broadcast_session_update(
                session_id,
                'session_started',
                event.get('content', {})
            )

        self.register_handler(BreathscapeEventType.SESSION_STARTED, handle_session_started)

        # Session ended handler
        async def handle_session_ended(event: Dict[str, Any]):
            session_id = event.get('session_id')

            if session_id in self.active_sessions:
                # Generate session summary
                session_data = self.active_sessions[session_id]

                # Broadcast session ending
                await websocket_manager.broadcast_session_update(
                    session_id,
                    'session_ended',
                    {
                        'message': 'Session completed successfully!',
                        'duration': event.get('data', {}).get('duration'),
                        'summary_available': True
                    }
                )

                # Clean up
                del self.active_sessions[session_id]

                # Close WebSocket connections after delay
                await asyncio.sleep(10)
                await websocket_manager.close_session(session_id)

        self.register_handler(BreathscapeEventType.SESSION_ENDED, handle_session_ended)

        # Participant joined handler
        async def handle_participant_joined(event: Dict[str, Any]):
            session_id = event.get('session_id')
            participant_data = event.get('data', {})

            if session_id in self.active_sessions:
                self.active_sessions[session_id]['participants'].append(participant_data)

            # Broadcast update
            await websocket_manager.broadcast_session_update(
                session_id,
                'participant_joined',
                {
                    'name': participant_data.get('name', 'Anonymous'),
                    'count': len(self.active_sessions.get(session_id, {}).get('participants', []))
                }
            )

        self.register_handler(BreathscapeEventType.PARTICIPANT_JOINED, handle_participant_joined)

        # HRV milestone handler
        async def handle_hrv_milestone(event: Dict[str, Any]):
            session_id = event.get('session_id')

            # Update session metrics
            if session_id in self.active_sessions:
                metrics = event.get('data', {})
                self.active_sessions[session_id]['metrics'].update(metrics)

            # Broadcast achievement
            await websocket_manager.broadcast_session_update(
                session_id,
                'hrv_milestone',
                event.get('content', {})
            )

        self.register_handler(BreathscapeEventType.HRV_MILESTONE, handle_hrv_milestone)

        # Technique changed handler
        async def handle_technique_changed(event: Dict[str, Any]):
            session_id = event.get('session_id')

            # Broadcast technique change
            await websocket_manager.broadcast_session_update(
                session_id,
                'technique_changed',
                event.get('content', {})
            )

        self.register_handler(BreathscapeEventType.TECHNIQUE_CHANGED, handle_technique_changed)

    async def _connect_to_breathscape(self, url: str):
        """
        Connect to Breathscape platform WebSocket

        Args:
            url: Breathscape WebSocket URL
        """
        # This would implement actual WebSocket client to Breathscape
        # For now, it's a placeholder for production implementation
        logger.info(f"Would connect to Breathscape at: {url}")

        # In production, this would:
        # 1. Establish WebSocket connection to Breathscape
        # 2. Authenticate with API credentials
        # 3. Subscribe to relevant events
        # 4. Forward events to process_event()

    async def _simulate_events(self):
        """Simulate Breathscape events for development/testing"""
        await asyncio.sleep(2)  # Initial delay

        if not self._running:
            return

        # Simulate session start
        await self.process_event({
            'type': BreathscapeEventType.SESSION_STARTED.value,
            'session_id': 'sim-session-001',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'title': 'Morning Mindfulness Session',
                'instructor': 'Sarah Chen',
                'scheduled_duration': 1800,  # 30 minutes
                'max_participants': 50
            }
        })

        await asyncio.sleep(5)

        # Simulate participants joining
        for i in range(3):
            if not self._running:
                break

            await self.process_event({
                'type': BreathscapeEventType.PARTICIPANT_JOINED.value,
                'session_id': 'sim-session-001',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': {
                    'participant_id': f'user-{i+1:03d}',
                    'name': f'Participant {i+1}'
                }
            })
            await asyncio.sleep(2)

        await asyncio.sleep(5)

        # Simulate technique change
        techniques = ['Box Breathing', '4-7-8 Breathing', 'Coherent Breathing']
        for technique in techniques:
            if not self._running:
                break

            await self.process_event({
                'type': BreathscapeEventType.TECHNIQUE_CHANGED.value,
                'session_id': 'sim-session-001',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': {
                    'technique': technique,
                    'duration': 300,  # 5 minutes
                    'instruction': f'Follow along with {technique} for optimal relaxation'
                }
            })
            await asyncio.sleep(10)

        # Simulate HRV milestone
        await self.process_event({
            'type': BreathscapeEventType.HRV_MILESTONE.value,
            'session_id': 'sim-session-001',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'improvement': 12.5,
                'average_hrv': 65,
                'milestone': '10% improvement reached!'
            }
        })

        await asyncio.sleep(5)

        # Simulate session end
        await self.process_event({
            'type': BreathscapeEventType.SESSION_ENDED.value,
            'session_id': 'sim-session-001',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'duration': 1800,
                'total_participants': 25,
                'average_hrv_improvement': 15.3,
                'techniques_completed': 3
            }
        })

        logger.info("Simulation completed")

    def get_active_sessions_info(self) -> Dict[str, Any]:
        """Get information about currently active sessions"""
        return {
            'count': len(self.active_sessions),
            'sessions': [
                {
                    'session_id': session_id,
                    'started_at': data.get('started_at'),
                    'participant_count': len(data.get('participants', [])),
                    'current_metrics': data.get('metrics', {})
                }
                for session_id, data in self.active_sessions.items()
            ]
        }


# Global event listener instance
breathscape_event_listener = BreathscapeEventListener()