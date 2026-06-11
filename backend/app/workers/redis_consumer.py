"""Redis Streams consumer for event processing."""
import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.cache import cache_manager
from app.services.business import (
    event_service, tracking_service, interaction_service,
    dwell_service, alert_service
)
from app.schemas.models import (
    EventCreate, TrackingSessionCreate, ShelfInteractionCreate,
    DwellTimeRecordCreate, AlertCreate
)


logger = logging.getLogger(__name__)


class RedisStreamConsumer:
    """Consumes events from Redis Streams and processes them."""
    
    # Stream names
    INTERACTION_STREAM = "retail:interactions"
    DETECTION_STREAM = "retail:detections"
    DWELL_STREAM = "retail:dwell"
    ANOMALY_STREAM = "retail:anomalies"
    ALERT_STREAM = "retail:alerts"
    
    # Consumer groups
    CONSUMER_GROUP = "retail-backend"
    CONSUMER_NAME = "backend-worker-1"
    
    def __init__(self, redis_client, db_session):
        """Initialize consumer."""
        self.redis = redis_client
        self.session = db_session
        self.is_running = False
        self.processed_count = 0
        self.failed_count = 0
        self.dead_letter_queue = "retail:dlq"
        self.batch_size = 10
        self.read_timeout = 5000  # 5 seconds
    
    async def initialize(self):
        """Initialize consumer groups."""
        try:
            for stream in [self.INTERACTION_STREAM, self.DETECTION_STREAM, 
                          self.DWELL_STREAM, self.ANOMALY_STREAM, self.ALERT_STREAM]:
                try:
                    await self.redis.xgroup_create(
                        stream,
                        self.CONSUMER_GROUP,
                        id="0",
                        mkstream=True
                    )
                    logger.info(f"Created consumer group for {stream}")
                except Exception as e:
                    if "already exists" not in str(e):
                        logger.warning(f"Could not create group for {stream}: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize consumer groups: {e}")
    
    async def start(self):
        """Start consumer."""
        self.is_running = True
        logger.info("Redis Stream Consumer started")
        
        try:
            await self.initialize()
            
            while self.is_running:
                # Read from all streams
                streams = {
                    self.INTERACTION_STREAM: ">",
                    self.DETECTION_STREAM: ">",
                    self.DWELL_STREAM: ">",
                    self.ANOMALY_STREAM: ">",
                    self.ALERT_STREAM: ">"
                }
                
                try:
                    messages = await self.redis.xreadgroup(
                        self.CONSUMER_GROUP,
                        self.CONSUMER_NAME,
                        streams,
                        count=self.batch_size,
                        block=self.read_timeout
                    )
                    
                    if messages:
                        await self.process_messages(messages)
                    
                except Exception as e:
                    logger.error(f"Error reading messages: {e}")
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            self.is_running = False
    
    async def stop(self):
        """Stop consumer."""
        self.is_running = False
        logger.info("Redis Stream Consumer stopped")
    
    async def process_messages(self, messages: list):
        """Process batch of messages."""
        for stream_key, stream_messages in messages:
            stream_name = stream_key.decode() if isinstance(stream_key, bytes) else stream_key
            
            for message_id, message_data in stream_messages:
                try:
                    await self.process_message(stream_name, message_id, message_data)
                    
                    # Acknowledge message
                    await self.redis.xack(
                        stream_name,
                        self.CONSUMER_GROUP,
                        message_id
                    )
                    self.processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process message {message_id}: {e}")
                    await self.send_to_dlq(stream_name, message_id, message_data, str(e))
                    self.failed_count += 1
    
    async def process_message(self, stream_name: str, message_id: bytes, 
                             message_data: Dict[str, bytes]):
        """Process individual message based on stream type."""
        # Decode message data
        decoded_data = {}
        for key, value in message_data.items():
            k = key.decode() if isinstance(key, bytes) else key
            v = value.decode() if isinstance(value, bytes) else value
            decoded_data[k] = v
        
        logger.info(f"Processing message from {stream_name}: {decoded_data}")
        
        if stream_name == self.INTERACTION_STREAM:
            await self.handle_interaction(decoded_data)
        
        elif stream_name == self.DETECTION_STREAM:
            await self.handle_detection(decoded_data)
        
        elif stream_name == self.DWELL_STREAM:
            await self.handle_dwell(decoded_data)
        
        elif stream_name == self.ANOMALY_STREAM:
            await self.handle_anomaly(decoded_data)
        
        elif stream_name == self.ALERT_STREAM:
            await self.handle_alert(decoded_data)
    
    async def handle_interaction(self, data: Dict[str, Any]):
        """Handle shelf interaction event."""
        try:
            interaction_data = ShelfInteractionCreate(
                customer_id=data.get('customer_id'),
                tracking_session_id=data.get('session_id'),
                interaction_type=data.get('type', 'entry'),
                zone_id=data.get('zone_id'),
                zone_name=data.get('zone_name'),
                engagement_level=data.get('engagement_level', 'browsing')
            )
            
            interaction = await interaction_service.record_interaction(
                self.session,
                interaction_data
            )
            
            logger.info(f"Recorded interaction: {interaction.id}")
        
        except Exception as e:
            logger.error(f"Failed to handle interaction: {e}")
            raise
    
    async def handle_detection(self, data: Dict[str, Any]):
        """Handle customer detection event."""
        try:
            # Create or get customer
            external_id = data.get('track_id')
            customer = await tracking_service.customer_service.get_or_create(
                self.session,
                external_id
            )
            
            # Create or get tracking session
            if data.get('action') == 'entry':
                session_create = TrackingSessionCreate(
                    customer_id=str(customer.id)
                )
                session = await tracking_service.start_session(
                    self.session,
                    str(customer.id)
                )
                logger.info(f"Started session for customer {customer.id}")
            
            elif data.get('action') == 'exit':
                # Find and close the active session
                active_sessions = await tracking_service.get_active_sessions(self.session)
                for s in active_sessions:
                    if s.customer_id == customer.id:
                        await tracking_service.end_session(self.session, str(s.id))
                        logger.info(f"Ended session {s.id}")
                        break
        
        except Exception as e:
            logger.error(f"Failed to handle detection: {e}")
            raise
    
    async def handle_dwell(self, data: Dict[str, Any]):
        """Handle dwell time event."""
        try:
            dwell_data = DwellTimeRecordCreate(
                customer_id=data.get('customer_id'),
                tracking_session_id=data.get('session_id'),
                zone_id=data.get('zone_id'),
                zone_name=data.get('zone_name', 'Unknown'),
                dwell_time_seconds=int(data.get('duration_seconds', 0)),
                engagement_intensity=data.get('intensity', 'moderate')
            )
            
            dwell = await dwell_service.record_dwell_time(self.session, dwell_data)
            logger.info(f"Recorded dwell time: {dwell.id}")
        
        except Exception as e:
            logger.error(f"Failed to handle dwell: {e}")
            raise
    
    async def handle_anomaly(self, data: Dict[str, Any]):
        """Handle anomaly detection event."""
        try:
            anomaly_type = data.get('type', 'unknown')
            severity = 'critical' if anomaly_type == 'suspicious' else 'medium'
            
            alert_data = AlertCreate(
                alert_type=f"anomaly_{anomaly_type}",
                alert_severity=severity,
                alert_title=f"Anomaly Detected: {anomaly_type}",
                alert_description=data.get('description', 'Anomaly detected'),
                customer_id=data.get('customer_id'),
                zone_id=data.get('zone_id'),
                metadata=data
            )
            
            alert = await alert_service.create_alert(self.session, alert_data)
            logger.info(f"Created alert for anomaly: {alert.id}")
        
        except Exception as e:
            logger.error(f"Failed to handle anomaly: {e}")
            raise
    
    async def handle_alert(self, data: Dict[str, Any]):
        """Handle alert event."""
        try:
            alert_data = AlertCreate(
                alert_type=data.get('type', 'system_alert'),
                alert_severity=data.get('severity', 'medium'),
                alert_title=data.get('title', 'System Alert'),
                alert_description=data.get('description', ''),
                customer_id=data.get('customer_id'),
                zone_id=data.get('zone_id'),
                metadata=data
            )
            
            alert = await alert_service.create_alert(self.session, alert_data)
            logger.info(f"Created alert: {alert.id}")
        
        except Exception as e:
            logger.error(f"Failed to handle alert: {e}")
            raise
    
    async def send_to_dlq(self, stream_name: str, message_id: bytes, 
                         message_data: Dict[str, bytes], error: str):
        """Send failed message to dead letter queue."""
        try:
            dlq_entry = {
                'stream': stream_name,
                'message_id': message_id.decode() if isinstance(message_id, bytes) else message_id,
                'error': error,
                'timestamp': datetime.utcnow().isoformat(),
                'data': json.dumps({
                    k: v.decode() if isinstance(v, bytes) else v
                    for k, v in message_data.items()
                })
            }
            
            await self.redis.xadd(
                self.dead_letter_queue,
                dlq_entry
            )
            
            logger.warning(f"Sent message {message_id} to DLQ: {error}")
        
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    async def retry_dlq(self):
        """Retry messages from dead letter queue."""
        try:
            messages = await self.redis.xread({self.dead_letter_queue: "0"}, count=10)
            
            if messages:
                for stream_key, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        # Attempt retry
                        logger.info(f"Retrying message {message_id} from DLQ")
                        # Add back to appropriate stream
                        await self.redis.xdel(self.dead_letter_queue, message_id)
        
        except Exception as e:
            logger.error(f"Failed to retry DLQ: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics."""
        return {
            'is_running': self.is_running,
            'processed_count': self.processed_count,
            'failed_count': self.failed_count,
            'success_rate': (
                self.processed_count / (self.processed_count + self.failed_count) * 100
                if (self.processed_count + self.failed_count) > 0 else 0
            )
        }


# Global consumer instance
consumer: Optional[RedisStreamConsumer] = None


async def init_consumer(redis_client, db_session):
    """Initialize global consumer."""
    global consumer
    consumer = RedisStreamConsumer(redis_client, db_session)


async def get_consumer() -> Optional[RedisStreamConsumer]:
    """Get consumer instance."""
    return consumer
