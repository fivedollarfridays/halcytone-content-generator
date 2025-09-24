"""
WebSocket Endpoints for Real-time Updates
Sprint 3: Halcytone Live Support - WebSocket API for live session content
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from datetime import datetime, timezone
import uuid

from ..services.websocket_manager import websocket_manager, ConnectionRole
from ..services.breathscape_event_listener import breathscape_event_listener
from ..services.session_summary_generator import SessionSummaryGenerator
from ..schemas.content_types import SessionContentStrict
from ..config import Settings, get_settings

logger = logging.getLogger(__name__)

# Create WebSocket router
router = APIRouter(tags=["websocket"], prefix="/ws")


@router.websocket("/live-updates")
async def websocket_live_updates(
    websocket: WebSocket,
    session_id: str = Query(..., description="Session ID to join"),
    client_id: Optional[str] = Query(None, description="Client identifier"),
    role: Optional[str] = Query("participant", description="Client role")
):
    """
    WebSocket endpoint for real-time session updates

    Query Parameters:
        - session_id: The breathing session to join
        - client_id: Optional client identifier (will be generated if not provided)
        - role: Client role (participant, instructor, observer, admin)

    Message Format:
        Incoming:
        {
            "type": "heartbeat" | "technique_feedback" | "hrv_update" | "chat",
            "data": {...}
        }

        Outgoing:
        {
            "type": "welcome" | "session_update" | "participant_joined" | etc.,
            "data": {...},
            "timestamp": "ISO 8601 timestamp"
        }
    """
    # Generate client ID if not provided
    if not client_id:
        client_id = f"ws-{uuid.uuid4().hex[:8]}"

    # Validate and convert role
    try:
        connection_role = ConnectionRole(role.lower())
    except ValueError:
        connection_role = ConnectionRole.PARTICIPANT

    logger.info(f"WebSocket connection attempt: session={session_id}, client={client_id}, role={connection_role}")

    try:
        # Connect to session
        await websocket_manager.connect(
            websocket=websocket,
            session_id=session_id,
            client_id=client_id,
            role=connection_role,
            metadata={
                'user_agent': websocket.headers.get('user-agent'),
                'origin': websocket.headers.get('origin')
            }
        )

        # Main message loop
        while True:
            try:
                # Receive message from client
                raw_message = await websocket.receive_text()

                try:
                    message = json.loads(raw_message)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    })
                    continue

                # Process the message
                response = await websocket_manager.handle_client_message(
                    session_id=session_id,
                    client_id=client_id,
                    message=message
                )

                # Send response if any
                if response:
                    await websocket.send_json(response)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {e}")
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Internal server error'
                })

    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        # Clean up connection
        await websocket_manager.disconnect(session_id, client_id)
        logger.info(f"WebSocket disconnected: client={client_id}")


@router.websocket("/session/{session_id}/events")
async def websocket_session_events(
    websocket: WebSocket,
    session_id: str,
    api_key: Optional[str] = Query(None, description="API key for authentication")
):
    """
    WebSocket endpoint for pushing Breathscape events to content generator
    This endpoint is used by the Breathscape platform to send events

    Path Parameters:
        - session_id: The session sending events

    Query Parameters:
        - api_key: Authentication key for Breathscape platform

    Expected Message Format:
    {
        "type": "session.started" | "technique.changed" | "hrv.milestone" | etc.,
        "session_id": "session-123",
        "timestamp": "2024-03-21T10:00:00Z",
        "data": {
            ...event-specific data...
        }
    }
    """
    # Simple API key validation (in production, use proper auth)
    # if api_key != "expected_api_key":
    #     await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    #     return

    await websocket.accept()
    logger.info(f"Breathscape platform connected for session {session_id}")

    try:
        while True:
            # Receive event from Breathscape
            raw_event = await websocket.receive_text()

            try:
                event = json.loads(raw_event)

                # Ensure session_id is in event
                if 'session_id' not in event:
                    event['session_id'] = session_id

                # Process the event
                await breathscape_event_listener.process_event(event)

                # Acknowledge receipt
                await websocket.send_json({
                    'type': 'ack',
                    'status': 'received',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })

            except json.JSONDecodeError:
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                })
            except Exception as e:
                logger.error(f"Error processing Breathscape event: {e}")
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Event processing failed'
                })

    except WebSocketDisconnect:
        logger.info(f"Breathscape platform disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error with Breathscape platform: {e}")


# HTTP endpoints for WebSocket management

@router.get("/sessions/active")
async def get_active_sessions(settings: Settings = Depends(get_settings)):
    """
    Get list of active sessions with WebSocket connections

    Returns:
        List of active session IDs and participant counts
    """
    active_sessions = websocket_manager.get_active_sessions()

    sessions_info = []
    for session_id in active_sessions:
        info = websocket_manager.get_session_info(session_id)
        sessions_info.append({
            'session_id': session_id,
            'participant_count': info.get('participant_count', 0),
            'active': info.get('active', False)
        })

    return {
        'count': len(active_sessions),
        'sessions': sessions_info
    }


@router.get("/sessions/{session_id}/info")
async def get_session_info(
    session_id: str,
    settings: Settings = Depends(get_settings)
):
    """
    Get detailed information about a specific session

    Path Parameters:
        - session_id: Session to query

    Returns:
        Session details including participants and message queue size
    """
    info = websocket_manager.get_session_info(session_id)

    if not info.get('active'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or not active"
        )

    return info


@router.post("/sessions/{session_id}/broadcast")
async def broadcast_to_session(
    session_id: str,
    message: Dict[str, Any],
    settings: Settings = Depends(get_settings)
):
    """
    Broadcast a message to all participants in a session

    Path Parameters:
        - session_id: Target session

    Body:
        - message: Message to broadcast

    Returns:
        Broadcast status
    """
    # Check if session exists
    if session_id not in websocket_manager.get_active_sessions():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    # Broadcast the message
    await websocket_manager.broadcast_to_session(session_id, message)

    return {
        'status': 'broadcasted',
        'session_id': session_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


@router.post("/sessions/{session_id}/close")
async def close_session(
    session_id: str,
    settings: Settings = Depends(get_settings)
):
    """
    Close a session and disconnect all participants

    Path Parameters:
        - session_id: Session to close

    Returns:
        Closure status
    """
    if session_id not in websocket_manager.get_active_sessions():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    # Close the session
    await websocket_manager.close_session(session_id)

    return {
        'status': 'closed',
        'session_id': session_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


@router.get("/sessions/{session_id}/replay")
async def get_session_replay(
    session_id: str,
    since: Optional[str] = Query(None, description="Get messages since this timestamp"),
    settings: Settings = Depends(get_settings)
):
    """
    Get replay of session messages for recovery or late joining

    Path Parameters:
        - session_id: Session to replay

    Query Parameters:
        - since: Optional timestamp to get messages after

    Returns:
        List of session messages
    """
    messages = await websocket_manager.get_session_replay(session_id, since)

    return {
        'session_id': session_id,
        'message_count': len(messages),
        'messages': messages
    }


@router.post("/events/start-listener")
async def start_event_listener(
    breathscape_url: Optional[str] = None,
    settings: Settings = Depends(get_settings)
):
    """
    Start the Breathscape event listener

    Body:
        - breathscape_url: Optional WebSocket URL for Breathscape platform

    Returns:
        Listener status
    """
    await breathscape_event_listener.start_listening(breathscape_url)

    return {
        'status': 'started',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'active_sessions': breathscape_event_listener.get_active_sessions_info()
    }


@router.post("/events/stop-listener")
async def stop_event_listener(settings: Settings = Depends(get_settings)):
    """
    Stop the Breathscape event listener

    Returns:
        Listener status
    """
    await breathscape_event_listener.stop_listening()

    return {
        'status': 'stopped',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


@router.get("/events/active-sessions")
async def get_active_event_sessions(settings: Settings = Depends(get_settings)):
    """
    Get information about sessions being tracked by the event listener

    Returns:
        Active sessions from event listener perspective
    """
    return breathscape_event_listener.get_active_sessions_info()


# Initialize event listener on module load
async def initialize_websocket_services():
    """Initialize WebSocket services on startup"""
    logger.info("Initializing WebSocket services")

    # Start event listener in simulation mode for development
    await breathscape_event_listener.start_listening()

    logger.info("WebSocket services initialized")


# Cleanup on shutdown
async def cleanup_websocket_services():
    """Cleanup WebSocket services on shutdown"""
    logger.info("Cleaning up WebSocket services")

    # Stop event listener
    await breathscape_event_listener.stop_listening()

    # Close all active sessions
    for session_id in websocket_manager.get_active_sessions():
        await websocket_manager.close_session(session_id)

    logger.info("WebSocket services cleaned up")