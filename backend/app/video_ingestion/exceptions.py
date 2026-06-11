"""
Video Ingestion Exceptions - Custom exceptions for video processing

Provides specific exception types for different failure scenarios
in the video ingestion pipeline.
"""


class VideoIngestionException(Exception):
    """Base exception for video ingestion errors"""
    pass


class VideoSourceException(VideoIngestionException):
    """Exception related to video source access"""
    pass


class ConnectionException(VideoIngestionException):
    """Exception for connection failures"""
    pass


class RTSPConnectionException(ConnectionException):
    """Exception for RTSP stream connection failures"""
    pass


class WebcamAccessException(ConnectionException):
    """Exception for webcam access failures"""
    pass


class LocalFileException(ConnectionException):
    """Exception for local file access failures"""
    pass


class FrameExtractionException(VideoIngestionException):
    """Exception during frame extraction"""
    pass


class GPUException(VideoIngestionException):
    """Exception related to GPU operations"""
    pass


class GPUNotAvailableException(GPUException):
    """GPU requested but not available"""
    pass


class BufferException(VideoIngestionException):
    """Exception related to frame buffer"""
    pass


class BufferOverflowException(BufferException):
    """Frame buffer exceeded capacity"""
    pass


class RegistryException(VideoIngestionException):
    """Exception from source registry"""
    pass


class SourceNotFoundException(RegistryException):
    """Requested source not found"""
    pass


class DuplicateSourceException(RegistryException):
    """Source with ID already exists"""
    pass


class HealthCheckException(VideoIngestionException):
    """Exception during health check"""
    pass


class ConfigurationException(VideoIngestionException):
    """Invalid configuration"""
    pass
