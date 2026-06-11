"""
Video Ingestion Module - Complete video source management

Exports:
- VideoSourceRegistry - Central source management
- StreamManager - Individual stream lifecycle
- FrameExtractor - Frame extraction from sources
- AsyncQueue - Intelligent frame buffering
- GPUOptimizer - GPU acceleration support
- Models, Exceptions, etc.
"""

from .models import (
    VideoSourceType,
    VideoSourceConfig,
    StreamStatus,
    StreamEvent,
    StreamHealth,
    FrameMetadata,
    FrameData,
    VideoIngestionConfig,
)

from .frame_extractor import FrameExtractor
from .async_queue import AsyncQueue
from .stream_manager import StreamManager
from .source_registry import VideoSourceRegistry
from .gpu_optimizer import GPUOptimizer, get_gpu_optimizer
from .exceptions import (
    VideoIngestionException,
    ConnectionException,
    FrameExtractionException,
    SourceNotFoundException,
)

__all__ = [
    # Models
    "VideoSourceType",
    "VideoSourceConfig",
    "StreamStatus",
    "StreamEvent",
    "StreamHealth",
    "FrameMetadata",
    "FrameData",
    "VideoIngestionConfig",
    # Components
    "FrameExtractor",
    "AsyncQueue",
    "StreamManager",
    "VideoSourceRegistry",
    "GPUOptimizer",
    "get_gpu_optimizer",
    # Exceptions
    "VideoIngestionException",
    "ConnectionException",
    "FrameExtractionException",
    "SourceNotFoundException",
]
