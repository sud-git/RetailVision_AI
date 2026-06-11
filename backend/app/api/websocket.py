"""WebSocket manager for live event streaming."""
import asyncio
import logging
import json
from datetime import datetime
from typing import Set, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        """Initialize manager."""
        self.active_connections: Set[WebSocket] = set()
        self.subscription_map: Dict[WebSocket, Set[str]] = {}  # ws -> {channel1, channel2, ...}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscription_map[websocket] = set()
        self.connection_metadata[websocket] = {
            'client_id': client_id,
            'connected_at': datetime.utcnow(),
            'subscriptions': []
        }
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Unregister connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            metadata = self.connection_metadata.pop(websocket, {})
            self.subscription_map.pop(websocket, None)
            logger.info(f"Client {metadata.get('client_id', 'unknown')} disconnected")
    
    async def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe to a channel."""
        if websocket not in self.subscription_map:
            return
        
        self.subscription_map[websocket].add(channel)
        self.connection_metadata[websocket]['subscriptions'].append(channel)
        
        logger.info(f"Client subscribed to {channel}")
        
        await websocket.send_json({
            'type': 'subscription',
            'channel': channel,
            'action': 'subscribed',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """Unsubscribe from a channel."""
        if websocket not in self.subscription_map:
            return
        
        self.subscription_map[websocket].discard(channel)
        
        if 'subscriptions' in self.connection_metadata[websocket]:
            self.connection_metadata[websocket]['subscriptions'].remove(channel)
        
        logger.info(f"Client unsubscribed from {channel}")
    
    async def broadcast(self, message: Dict[str, Any], channel: Optional[str] = None):
        """Broadcast message to all connections (optionally filtered by channel)."""
        if not self.active_connections:
            return
        
        message['timestamp'] = datetime.utcnow().isoformat()
        message_json = json.dumps(message)
        
        disconnected = set()
        
        for ws in self.active_connections:
            try:
                # If channel specified, only send to subscribers
                if channel:
                    if channel not in self.subscription_map.get(ws, set()):
                        continue
                
                await ws.send_text(message_json)
            
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.add(ws)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)
    
    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific connection."""
        try:
            message['timestamp'] = datetime.utcnow().isoformat()
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    def get_connection_count(self) -> int:
        """Get total connections."""
        return len(self.active_connections)
    
    def get_channel_subscribers(self, channel: str) -> int:
        """Get subscriber count for channel."""
        count = 0
        for subscriptions in self.subscription_map.values():
            if channel in subscriptions:
                count += 1
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        channels = {}
        for subscriptions in self.subscription_map.values():
            for channel in subscriptions:
                channels[channel] = channels.get(channel, 0) + 1
        
        return {
            'total_connections': len(self.active_connections),
            'total_channels': len(channels),
            'channels': channels
        }


class EventBroadcaster:
    """Broadcasts events through WebSocket."""
    
    def __init__(self, manager: ConnectionManager):
        """Initialize broadcaster."""
        self.manager = manager
        self.event_queue: asyncio.Queue = asyncio.Queue()
    
    async def send_event(self, event_type: str, data: Dict[str, Any], 
                        channel: str = "events"):
        """Queue event for broadcasting."""
        message = {
            'type': 'event',
            'event_type': event_type,
            'channel': channel,
            'data': data
        }
        await self.event_queue.put(message)
    
    async def send_interaction_event(self, interaction: Dict[str, Any]):
        """Send interaction event."""
        await self.send_event(
            'shelf_interaction',
            interaction,
            channel='interactions'
        )
    
    async def send_detection_event(self, detection: Dict[str, Any]):
        """Send detection event."""
        await self.send_event(
            'customer_detected',
            detection,
            channel='detections'
        )
    
    async def send_anomaly_event(self, anomaly: Dict[str, Any]):
        """Send anomaly event."""
        await self.send_event(
            'anomaly_detected',
            anomaly,
            channel='anomalies'
        )
    
    async def send_alert(self, alert: Dict[str, Any]):
        """Send alert."""
        await self.send_event(
            'alert',
            alert,
            channel='alerts'
        )
    
    async def send_analytics_update(self, analytics: Dict[str, Any]):
        """Send analytics update."""
        await self.send_event(
            'analytics_update',
            analytics,
            channel='analytics'
        )
    
    async def broadcast_loop(self):
        """Main broadcast loop - processes queued events."""
        logger.info("Event broadcaster started")
        
        try:
            while True:
                try:
                    # Get event from queue with timeout
                    message = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=5.0
                    )
                    
                    # Broadcast to subscribers
                    channel = message.get('channel', 'events')
                    await self.manager.broadcast(message, channel=channel)
                    
                    # Batch processing - get more events if available
                    batch = [message]
                    while not self.event_queue.empty() and len(batch) < 10:
                        try:
                            batch.append(self.event_queue.get_nowait())
                        except asyncio.QueueEmpty:
                            break
                    
                    if len(batch) > 1:
                        logger.debug(f"Broadcasted batch of {len(batch)} events")
                
                except asyncio.TimeoutError:
                    # No events - continue
                    continue
                except Exception as e:
                    logger.error(f"Broadcast loop error: {e}")
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Broadcast loop crashed: {e}")
    
    def get_queue_depth(self) -> int:
        """Get number of queued events."""
        return self.event_queue.qsize()


# Global instances
connection_manager: Optional[ConnectionManager] = None
event_broadcaster: Optional[EventBroadcaster] = None


def init_websocket():
    """Initialize WebSocket components."""
    global connection_manager, event_broadcaster
    connection_manager = ConnectionManager()
    event_broadcaster = EventBroadcaster(connection_manager)
    logger.info("WebSocket components initialized")


def get_connection_manager() -> ConnectionManager:
    """Get connection manager."""
    return connection_manager


def get_event_broadcaster() -> EventBroadcaster:
    """Get event broadcaster."""
    return event_broadcaster
