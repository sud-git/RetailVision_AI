"""
Detection System Exceptions - Phase 3

Custom exception hierarchy for detection and tracking system.
"""


class DetectionException(Exception):
    """Base exception for detection system"""
    pass


class ModelException(DetectionException):
    """Model-related errors"""
    pass


class ModelNotLoadedException(ModelException):
    """Model not loaded or failed to load"""
    pass


class ModelInferenceException(ModelException):
    """Error during model inference"""
    pass


class TrackingException(DetectionException):
    """Tracking-related errors"""
    pass


class TrackingInitializationException(TrackingException):
    """Failed to initialize tracking"""
    pass


class ZoneException(DetectionException):
    """Zone detection errors"""
    pass


class InvalidZoneException(ZoneException):
    """Invalid zone configuration"""
    pass


class DwellTrackingException(DetectionException):
    """Dwell time tracking errors"""
    pass


class ConfigurationException(DetectionException):
    """Configuration errors"""
    pass


class GPUException(DetectionException):
    """GPU-related errors"""
    pass


class GPUNotAvailableException(GPUException):
    """GPU not available for inference"""
    pass


class EventPublishingException(DetectionException):
    """Error publishing events"""
    pass
