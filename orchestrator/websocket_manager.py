"""
WebSocket Manager - Real-time updates for frontend using WebSockets.
Manages WebSocket connections and broadcasts pipeline events to connected clients.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosedError, WebSocketException

from orchestrator.event_bus import EventBus, Event

logger = logging.getLogger(__name__)

@dataclass
class WSClient:
    """WebSocket client connection info."""
    websocket: websockets.WebSocketServerProtocol
    user_id: str
    connected_at: datetime
    subscriptions: Set[str]

class WebSocketManager:
    """WebSocket manager for real-time frontend updates."""

    def __init__(self, event_bus: EventBus, host: str = "0.0.0.0", port: int = 8003):
        self.event_bus = event_bus
        self.host = host
        self.port = port
        self.server: Optional[websockets.WebSocketServer] = None
        self.clients: Dict[str, WSClient] = {}  # client_id -> WSClient
        self._running = False

        # Event subscriptions
        self._setup_event_subscriptions()

    def _setup_event_subscriptions(self):
        """Set up event bus subscriptions for broadcasting."""
        # Pipeline events
        asyncio.create_task(self.event_bus.subscribe('pipeline.started', self._broadcast_pipeline_event))
        asyncio.create_task(self.event_bus.subscribe('pipeline.state_changed', self._broadcast_pipeline_event))
        asyncio.create_task(self.event_bus.subscribe('pipeline.completed', self._broadcast_pipeline_event))
        asyncio.create_task(self.event_bus.subscribe('pipeline.failed', self._broadcast_pipeline_event))

        # Specific pipeline step events
        asyncio.create_task(self.event_bus.subscribe('pipeline.upload_completed', self._broadcast_pipeline_event))
        asyncio.create_task(self.event_bus.subscribe('pipeline.caption_generated', self._broadcast_pipeline_event))
        asyncio.create_task(self.event_bus.subscribe('pipeline.scheduled', self._broadcast_pipeline_event))
        asyncio.create_task(self.event_bus.subscribe('pipeline.posted', self._broadcast_pipeline_event))
        asyncio.create_task(self.event_bus.subscribe('pipeline.analyzed', self._broadcast_pipeline_event))

        # System events
        asyncio.create_task(self.event_bus.subscribe('system.health_check', self._broadcast_system_event))
        asyncio.create_task(self.event_bus.subscribe('system.service_down', self._broadcast_system_event))
        asyncio.create_task(self.event_bus.subscribe('system.service_recovered', self._broadcast_system_event))

    async def start(self):
        """Start the WebSocket server."""
        self._running = True

        try:
            self.server = await websockets.serve(
                self._handle_connection,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5
            )
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

            # Start cleanup task
            asyncio.create_task(self._cleanup_disconnected_clients())

        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise

    async def stop(self):
        """Stop the WebSocket server."""
        self._running = False

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Close all client connections
        for client in self.clients.values():
            try:
                await client.websocket.close()
            except Exception:
                pass

        self.clients.clear()
        logger.info("WebSocket server stopped")

    async def _handle_connection(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        user_id = None

        try:
            # Wait for authentication message
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            auth_data = json.loads(auth_message)

            if auth_data.get('type') != 'auth':
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Authentication required'
                }))
                await websocket.close()
                return

            user_id = auth_data.get('user_id')
            if not user_id:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Invalid user_id'
                }))
                await websocket.close()
                return

            # Create client
            client = WSClient(
                websocket=websocket,
                user_id=user_id,
                connected_at=datetime.now(datetime.UTC),
                subscriptions=set()
            )

            self.clients[client_id] = client

            logger.info(f"WebSocket client connected: {client_id} (user: {user_id})")

            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'connected',
                'client_id': client_id,
                'timestamp': datetime.now(datetime.UTC).isoformat()
            }))

            # Handle client messages
            await self._handle_client_messages(client_id, client)

        except asyncio.TimeoutError:
            logger.warning(f"Authentication timeout for client {client_id}")
            await websocket.close()
        except (ConnectionClosedError, WebSocketException) as e:
            logger.info(f"WebSocket connection closed for client {client_id}: {e}")
        except Exception as e:
            logger.error(f"Error handling WebSocket connection {client_id}: {e}")
        finally:
            # Clean up client
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"WebSocket client disconnected: {client_id}")

    async def _handle_client_messages(self, client_id: str, client: WSClient):
        """Handle messages from a connected client."""
        try:
            async for message in client.websocket:
                try:
                    data = json.loads(message)

                    if data['type'] == 'subscribe':
                        # Handle subscription request
                        event_types = data.get('event_types', [])
                        client.subscriptions.update(event_types)
                        logger.debug(f"Client {client_id} subscribed to: {event_types}")

                        await client.websocket.send(json.dumps({
                            'type': 'subscribed',
                            'event_types': list(client.subscriptions)
                        }))

                    elif data['type'] == 'unsubscribe':
                        # Handle unsubscription request
                        event_types = data.get('event_types', [])
                        client.subscriptions.difference_update(event_types)
                        logger.debug(f"Client {client_id} unsubscribed from: {event_types}")

                        await client.websocket.send(json.dumps({
                            'type': 'unsubscribed',
                            'event_types': list(client.subscriptions)
                        }))

                    elif data['type'] == 'ping':
                        # Handle ping
                        await client.websocket.send(json.dumps({
                            'type': 'pong',
                            'timestamp': datetime.now(datetime.UTC).isoformat()
                        }))

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON message from client {client_id}")
                except Exception as e:
                    logger.error(f"Error processing message from client {client_id}: {e}")

        except (ConnectionClosedError, WebSocketException):
            pass  # Connection closed normally

    async def _broadcast_pipeline_event(self, event: Event):
        """Broadcast pipeline events to subscribed clients."""
        await self._broadcast_event(event, 'pipeline')

    async def _broadcast_system_event(self, event: Event):
        """Broadcast system events to subscribed clients."""
        await self._broadcast_event(event, 'system')

    async def _broadcast_event(self, event: Event, category: str):
        """Broadcast an event to all subscribed clients."""
        message = {
            'type': 'event',
            'category': category,
            'event_type': event.event_type,
            'data': event.data,
            'timestamp': event.timestamp.isoformat(),
            'source': event.source
        }

        disconnected_clients = []

        for client_id, client in self.clients.items():
            try:
                # Check if client is subscribed to this event type or category
                if (event.event_type in client.subscriptions or
                    category in client.subscriptions or
                    'all' in client.subscriptions):

                    await client.websocket.send(json.dumps(message))

            except (ConnectionClosedError, WebSocketException):
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"Removed disconnected client: {client_id}")

    async def broadcast_to_user(self, user_id: str, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all clients of a specific user."""
        message = {
            'type': 'event',
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now(datetime.UTC).isoformat(),
            'source': 'orchestrator'
        }

        disconnected_clients = []

        for client_id, client in self.clients.items():
            if client.user_id == user_id:
                try:
                    await client.websocket.send(json.dumps(message))
                except (ConnectionClosedError, WebSocketException):
                    disconnected_clients.append(client_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id} client {client_id}: {e}")
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"Removed disconnected user client: {client_id}")

    async def broadcast_to_all(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all connected clients."""
        message = {
            'type': 'event',
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now(datetime.UTC).isoformat(),
            'source': 'orchestrator'
        }

        disconnected_clients = []

        for client_id, client in self.clients.items():
            try:
                await client.websocket.send(json.dumps(message))
            except (ConnectionClosedError, WebSocketException):
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"Removed disconnected client: {client_id}")

    async def _cleanup_disconnected_clients(self):
        """Periodically clean up disconnected clients."""
        while self._running:
            await asyncio.sleep(60)  # Check every minute

            disconnected_clients = []

            for client_id, client in self.clients.items():
                try:
                    # Try to send a ping
                    await client.websocket.ping()
                except Exception:
                    disconnected_clients.append(client_id)

            # Clean up disconnected clients
            for client_id in disconnected_clients:
                if client_id in self.clients:
                    del self.clients[client_id]
                    logger.info(f"Cleaned up disconnected client: {client_id}")

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        total_clients = len(self.clients)
        user_counts = {}

        for client in self.clients.values():
            user_counts[client.user_id] = user_counts.get(client.user_id, 0) + 1

        return {
            'total_connections': total_clients,
            'unique_users': len(user_counts),
            'connections_per_user': user_counts,
            'server_running': self._running
        }

    async def send_pipeline_progress(self, task_id: str, user_id: str,
                                   progress: float, status: str, details: Dict[str, Any] = None):
        """Send pipeline progress update to specific user."""
        data = {
            'task_id': task_id,
            'progress': progress,
            'status': status,
            'details': details or {}
        }

        await self.broadcast_to_user(user_id, 'pipeline.progress', data)
