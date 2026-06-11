"""
Tracking Module - Phase 3

Multi-object tracking with ByteTrack integration.
"""

from .bytetrack import (
    ByteTrackWrapper,
    TrackingEngine
)

__all__ = [
    "ByteTrackWrapper",
    "TrackingEngine"
]
