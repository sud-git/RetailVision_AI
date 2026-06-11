"""
Video Ingestion Models - Data structures for video source management

Defines all Pydantic models for video source configuration,
frame metadata, stream health, and events.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import numpy as np


class VideoSourceType(str, Enum):
    """Supported video source types"""
    RTSP = "RTSP"
    WEBCAM = "WEBCAM"
    LOCAL_FILE = "LOCAL_FILE"


class FrameFormat(str, Enum):
    """Supported frame formats"""
    BGR = "BGR"          # OpenCV default
    RGB = "RGB"          # Common for ML
    GRAY = "GRAY"        # Single channel


class StreamStatus(str, Enum):
    """Stream connection status"""
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class StreamEventType(str, Enum):
    """Types of stream events"""
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    FRAME_DROPPED = "FRAME_DROPPED"
    BUFFER_OVERFLOW = "BUFFER_OVERFLOW"
    RECONNECTION_ATTEMPT = "RECONNECTION_ATTEMPT"
    RECONNECTION_SUCCESS = "RECONNECTION_SUCCESS"


class VideoSourceConfig(BaseModel):
    """Configuration for a video source"""
    
    # Identification
    id: str = Field(..., description="Unique source identifier")
    name: Optional[str] = Field(None, description="Human-readable source name")
    type: VideoSourceType = Field(..., description="Source type")
    
    # Connection parameters
    url: Optional[str] = Field(None, description="RTSP URL or file path")
    device_id: Optional[int] = Field(0, description="Webcam device ID")
    username: Optional[str] = Field(None, description="RTSP authentication username")
    password: Optional[str] = Field(None, description="RTSP authentication password")
    
    # Processing parameters
    fps: float = Field(30, ge=1, le=60, description="Target frames per second")
    resolution: Optional[List[int]] = Field([1920, 1080], description="Frame resolution [width, height]")
    format: FrameFormat = Field(FrameFormat.BGR, description="Output frame format")
    
    # Buffer configuration
    buffer_capacity: int = Field(1000, ge=10, le=5000, description="Max frames in queue")
    
    # Connection parameters
    connect_timeout_seconds: int = Field(10, ge=5, le=60, description="Connection timeout")
    read_timeout_seconds: int = Field(30, ge=10, le=120, description="Read timeout")
    
    # Retry configuration
    reconnect_attempts: int = Field(5, ge=1, le=20, description="Max reconnection attempts")
    reconnect_delay_ms: int = Field(2000, ge=500, le=30000, description="Initial delay between retries (ms)")
    reconnect_backoff_factor: float = Field(1.5, ge=1.0, le=2.0, description="Exponential backoff multiplier")
    
    # Optimization
    enable_frame_dedup: bool = Field(True, description="Enable frame deduplication")
    enable_keyframe_priority: bool = Field(True, description="Prioritize keyframes in buffer")
    
    # Monitoring
    health_check_interval_seconds: int = Field(30, ge=5, le=300, description="Health check interval")
    
    # Optional: Video looping for local files
    loop: bool = Field(False, description="Loop video file (local only)")
    
    class Config:
        use_enum_values = False

    @validator("resolution")
    def validate_resolution(cls, v):
        """Validate resolution is 2 elements"""
        if v and len(v) != 2:
            raise ValueError("Resolution must be [width, height]")
        return v


class FrameMetadata(BaseModel):
    """Metadata associated with a video frame"""
    
    source_id: str = Field(..., description="Source identifier")
    frame_index: int = Field(..., description="Frame index in source")
    timestamp: float = Field(..., description="UNIX timestamp (seconds)")
    
    # Frame properties
    width: int = Field(..., description="Frame width in pixels")
    height: int = Field(..., description="Frame height in pixels")
    format: FrameFormat = Field(..., description="Frame color format")
    
    # Timing
    extraction_time_ms: float = Field(0, description="Time to extract frame (ms)")
    queue_age_ms: float = Field(0, description="Age in queue (ms)")
    
    # Quality indicators
    is_keyframe: bool = Field(False, description="Is this a keyframe")
    brightness_estimate: Optional[float] = Field(None, description="Average brightness (0-255)")
    
    class Config:
        use_enum_values = False


class StreamHealth(BaseModel):
    """Health status of a video stream"""
    
    source_id: str = Field(..., description="Source identifier")
    status: StreamStatus = Field(..., description="Current stream status")
    
    # Counters
    frames_processed: int = Field(0, description="Total frames extracted")
    frames_dropped: int = Field(0, description="Total frames dropped")
    errors_count: int = Field(0, description="Total errors encountered")
    reconnect_attempts: int = Field(0, description="Reconnection attempts made")
    
    # Performance metrics
    current_fps: float = Field(0, description="Current frames per second")
    buffer_occupancy: int = Field(0, description="Current frames in buffer")
    latency_ms: float = Field(0, description="Frame extraction latency")
    
    # Timing
    uptime_seconds: float = Field(0, description="Total uptime in seconds")
    last_frame_time: Optional[datetime] = Field(None, description="Last frame extraction time")
    last_error_time: Optional[datetime] = Field(None, description="Last error time")
    last_error_message: Optional[str] = Field(None, description="Last error message")
    
    # GPU info (if available)
    gpu_used: bool = Field(False, description="GPU acceleration active")
    gpu_memory_mb: Optional[float] = Field(None, description="GPU memory used (MB)")
    
    class Config:
        use_enum_values = False


class StreamEvent(BaseModel):
    """Event from a video stream"""
    
    source_id: str = Field(..., description="Source identifier")
    event_type: StreamEventType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    
    message: str = Field(..., description="Event description")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional event details")
    
    class Config:
        use_enum_values = False


class FrameData(BaseModel):
    """Complete frame with data and metadata"""
    
    data: Optional[Any] = Field(None, description="Frame data (numpy array)")  # Not serialized in JSON
    metadata: FrameMetadata = Field(..., description="Frame metadata")
    
    class Config:
        arbitrary_types_allowed = True


class StreamMetricsSnapshot(BaseModel):
    """Snapshot of stream metrics for monitoring"""
    
    source_id: str = Field(..., description="Source identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Snapshot timestamp")
    
    # Current state
    status: StreamStatus = Field(..., description="Current stream status")
    current_fps: float = Field(0, description="Current frames per second")
    buffer_size: int = Field(0, description="Current buffer occupancy")
    
    # Rates
    frames_per_minute: float = Field(0, description="Frames extracted per minute")
    error_rate: float = Field(0, description="Error rate percentage")
    
    # Efficiency
    frames_processed: int = Field(0, description="Total frames processed")
    frames_dropped: int = Field(0, description="Total frames dropped")
    
    # Resource usage (if GPU)
    gpu_utilization_percent: Optional[float] = Field(None, description="GPU utilization percentage")
    gpu_memory_mb: Optional[float] = Field(None, description="GPU memory used (MB)")
    
    class Config:
        use_enum_values = False


class VideoIngestionConfig(BaseModel):
    """Overall video ingestion configuration"""
    
    sources: List[VideoSourceConfig] = Field(default_factory=list, description="List of video sources")
    
    # GPU configuration
    gpu_acceleration: bool = Field(True, description="Enable GPU acceleration if available")
    gpu_device_id: int = Field(0, description="GPU device ID to use")
    gpu_memory_fraction: float = Field(0.5, ge=0.1, le=1.0, description="Fraction of GPU memory to allocate")
    
    # Global limits
    max_concurrent_sources: int = Field(10, ge=1, le=100, description="Max concurrent video sources")
    
    # Monitoring
    health_check_interval_seconds: int = Field(30, ge=5, le=300, description="Global health check interval")
    metrics_publish_interval_seconds: int = Field(10, ge=5, le=60, description="Metrics publication interval")
    
    # Logging
    log_level: str = Field("INFO", description="Logging level")
    
    class Config:
        use_enum_values = False
