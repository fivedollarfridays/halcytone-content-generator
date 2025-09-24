"""
WebSocket Manager for Real-time Content Updates
Sprint 3: Halcytone Live Support - Managing WebSocket connections for live session updates
"""
import logging
import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionRole(str, Enum):
    """Types of WebSocket connections"""
    PARTICIPANT = "participant"
    INSTRUCTOR = "instructor"
    OBSERVER = "observer"
    ADMIN = "admin"


class WebSocketManager:
    """
    Manages WebSocket connections for real-time session updates
    Handles connection lifecycle, message broadcasting, and room management
    """

    def __init__(self):
        # Store active connections by session_id
        self._connections: Dict[str, Dict[str, WebSocket]] = {}
        # Store connection metadata
        self._connection_metadata: Dict[str, Dict[str, Any]] = {}
        # Track session states
        self._active_sessions: Set[str] = set()
        # Message queue for reliability
        self._message_queue: Dict[str, List[Dict[str, Any]]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        client_id: str,
        role: ConnectionRole = ConnectionRole.PARTICIPANT,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Accept and register a new WebSocket connection

        Args:
            websocket: FastAPI WebSocket instance
            session_id: Session to join
            client_id: Unique client identifier
            role: Client role in the session
            metadata: Additional client metadata
        """
        await websocket.accept()

        # Initialize session room if needed
        if session_id not in self._connections:
            self._connections[session_id] = {}
            self._message_queue[session_id] = []
            self._active_sessions.add(session_id)
            logger.info(f"Created new session room: {session_id}")

        # Store connection
        self._connections[session_id][client_id] = websocket

        # Store metadata
        self._connection_metadata[client_id] = {
            'session_id': session_id,
            'role': role,
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata or {},
            'last_heartbeat': datetime.now(timezone.utc)
        }

        logger.info(f"Client {client_id} connected to session {session_id} as {role}")

        # Send welcome message
        await self._send_welcome_message(websocket, session_id, client_id, role)

        # Notify others about new participant
        await self._broadcast_participant_joined(session_id, client_id, role)

    async def disconnect(self, session_id: str, client_id: str):
        """
        Remove a WebSocket connection

        Args:
            session_id: Session ID
            client_id: Client identifier to remove
        """
        if session_id in self._connections and client_id in self._connections[session_id]:
            del self._connections[session_id][client_id]
            logger.info(f"Client {client_id} disconnected from session {session_id}")

            # Clean up metadata
            if client_id in self._connection_metadata:
                del self._connection_metadata[client_id]

            # Notify others about participant leaving
            await self._broadcast_participant_left(session_id, client_id)

            # Clean up empty sessions
            if not self._connections[session_id]:
                del self._connections[session_id]
                self._active_sessions.discard(session_id)
                if session_id in self._message_queue:
                    del self._message_queue[session_id]
                logger.info(f"Session room {session_id} closed (no connections)")

    async def broadcast_to_session(
        self,
        session_id: str,
        message: Dict[str, Any],
        exclude_client: Optional[str] = None,
        roles: Optional[List[ConnectionRole]] = None
    ):
        """
        Broadcast message to all connections in a session

        Args:
            session_id: Target session
            message: Message to broadcast
            exclude_client: Optional client to exclude from broadcast
            roles: Optional list of roles to target
        """
        if session_id not in self._connections:
            logger.warning(f"No active connections for session {session_id}")
            return

        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now(timezone.utc).isoformat()

        # Queue message for reliability
        self._queue_message(session_id, message)

        # Get target connections
        target_connections = []
        for client_id, websocket in self._connections[session_id].items():
            if exclude_client and client_id == exclude_client:
                continue

            # Filter by role if specified
            if roles:
                client_role = self._connection_metadata.get(client_id, {}).get('role')
                if client_role not in roles:
                    continue

            target_connections.append((client_id, websocket))

        # Send to all target connections
        disconnected_clients = []
        for client_id, websocket in target_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(session_id, client_id)

    async def send_to_client(
        self,
        session_id: str,
        client_id: str,
        message: Dict[str, Any]
    ):
        """
        Send message to specific client

        Args:
            session_id: Session ID
            client_id: Target client
            message: Message to send
        """
        if (session_id in self._connections and
            client_id in self._connections[session_id]):

            websocket = self._connections[session_id][client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                await self.disconnect(session_id, client_id)

    async def broadcast_session_update(
        self,
        session_id: str,
        update_type: str,
        data: Dict[str, Any]
    ):
        """
        Broadcast a session update to all participants

        Args:
            session_id: Session ID
            update_type: Type of update
            data: Update data
        """
        message = {
            'type': 'session_update',
            'update_type': update_type,
            'session_id': session_id,
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        await self.broadcast_to_session(session_id, message)

    async def handle_client_message(
        self,
        session_id: str,
        client_id: str,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process incoming message from client

        Args:
            session_id: Session ID
            client_id: Sender client ID
            message: Received message

        Returns:
            Optional response message
        """
        message_type = message.get('type')
        logger.debug(f"Received {message_type} from {client_id} in session {session_id}")

        # Handle different message types
        if message_type == 'heartbeat':
            return await self._handle_heartbeat(client_id)

        elif message_type == 'technique_feedback':
            return await self._handle_technique_feedback(session_id, client_id, message.get('data', {}))

        elif message_type == 'hrv_update':
            return await self._handle_hrv_update(session_id, client_id, message.get('data', {}))

        elif message_type == 'chat':
            return await self._handle_chat_message(session_id, client_id, message.get('data', {}))

        else:
            logger.warning(f"Unknown message type: {message_type}")
            return {'type': 'error', 'message': f'Unknown message type: {message_type}'}

    async def _send_welcome_message(
        self,
        websocket: WebSocket,
        session_id: str,
        client_id: str,
        role: ConnectionRole
    ):
        """Send welcome message to newly connected client"""
        participant_count = len(self._connections.get(session_id, {}))

        welcome = {
            'type': 'welcome',
            'session_id': session_id,
            'client_id': client_id,
            'role': role.value,
            'participant_count': participant_count,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': f'Welcome to session {session_id}!'
        }

        try:
            await websocket.send_json(welcome)
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")

    async def _broadcast_participant_joined(
        self,
        session_id: str,
        client_id: str,
        role: ConnectionRole
    ):
        """Notify session about new participant"""
        participant_count = len(self._connections.get(session_id, {}))

        message = {
            'type': 'participant_joined',
            'client_id': client_id,
            'role': role.value,
            'participant_count': participant_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        await self.broadcast_to_session(session_id, message, exclude_client=client_id)

    async def _broadcast_participant_left(self, session_id: str, client_id: str):
        """Notify session about participant leaving"""
        participant_count = len(self._connections.get(session_id, {}))

        message = {
            'type': 'participant_left',
            'client_id': client_id,
            'participant_count': participant_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        await self.broadcast_to_session(session_id, message)

    async def _handle_heartbeat(self, client_id: str) -> Dict[str, Any]:
        """Handle heartbeat from client"""
        if client_id in self._connection_metadata:
            self._connection_metadata[client_id]['last_heartbeat'] = datetime.now(timezone.utc)

        return {
            'type': 'heartbeat_ack',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    async def _handle_technique_feedback(
        self,
        session_id: str,
        client_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle breathing technique feedback from participant"""
        # Broadcast to instructors and admins
        feedback_message = {
            'type': 'technique_feedback',
            'client_id': client_id,
            'technique': data.get('technique'),
            'difficulty': data.get('difficulty'),
            'effectiveness': data.get('effectiveness'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        await self.broadcast_to_session(
            session_id,
            feedback_message,
            roles=[ConnectionRole.INSTRUCTOR, ConnectionRole.ADMIN]
        )

        return {'type': 'feedback_received', 'status': 'ok'}

    async def _handle_hrv_update(
        self,
        session_id: str,
        client_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle HRV update from participant"""
        # Store and aggregate HRV data
        hrv_value = data.get('hrv_value')

        # Broadcast aggregated update
        await self.broadcast_session_update(
            session_id,
            'hrv_update',
            {
                'client_id': client_id,
                'hrv_value': hrv_value,
                'improvement': data.get('improvement')
            }
        )

        return {'type': 'hrv_received', 'status': 'ok'}

    async def _handle_chat_message(
        self,
        session_id: str,
        client_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle chat message from participant"""
        chat_message = {
            'type': 'chat_message',
            'client_id': client_id,
            'message': data.get('message', ''),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        # Broadcast to all participants
        await self.broadcast_to_session(session_id, chat_message, exclude_client=client_id)

        return {'type': 'message_sent', 'status': 'ok'}

    def _queue_message(self, session_id: str, message: Dict[str, Any]):
        """Queue message for reliability and replay"""
        if session_id not in self._message_queue:
            self._message_queue[session_id] = []

        # Keep last 100 messages
        self._message_queue[session_id].append(message)
        if len(self._message_queue[session_id]) > 100:
            self._message_queue[session_id].pop(0)

    async def get_session_replay(
        self,
        session_id: str,
        since_timestamp: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get replay of session messages

        Args:
            session_id: Session ID
            since_timestamp: Optional timestamp to get messages after

        Returns:
            List of queued messages
        """
        if session_id not in self._message_queue:
            return []

        messages = self._message_queue[session_id]

        if since_timestamp:
            try:
                since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
                messages = [
                    msg for msg in messages
                    if datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00')) > since_dt
                ]
            except (ValueError, KeyError):
                logger.warning(f"Invalid timestamp for replay: {since_timestamp}")

        return messages

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a session"""
        if session_id not in self._connections:
            return {'active': False}

        participants = []
        for client_id in self._connections[session_id]:
            metadata = self._connection_metadata.get(client_id, {})
            participants.append({
                'client_id': client_id,
                'role': metadata.get('role', ConnectionRole.PARTICIPANT),
                'connected_at': metadata.get('connected_at'),
                'last_heartbeat': metadata.get('last_heartbeat').isoformat() if metadata.get('last_heartbeat') else None
            })

        return {
            'active': True,
            'session_id': session_id,
            'participant_count': len(participants),
            'participants': participants,
            'message_queue_size': len(self._message_queue.get(session_id, []))
        }

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self._active_sessions)

    async def close_session(self, session_id: str):
        """Close a session and disconnect all participants"""
        if session_id not in self._connections:
            return

        # Send session ending message
        ending_message = {
            'type': 'session_ending',
            'message': 'This session is ending. Thank you for participating!',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        await self.broadcast_to_session(session_id, ending_message)

        # Disconnect all clients
        clients_to_disconnect = list(self._connections[session_id].keys())
        for client_id in clients_to_disconnect:
            await self.disconnect(session_id, client_id)

        logger.info(f"Session {session_id} closed")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()