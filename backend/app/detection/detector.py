"""
YOLOv11 Detector Engine - Phase 3

Real-time object detection using YOLOv11 with GPU/CPU support.
Handles model loading, inference, and result parsing.
"""

import logging
from typing import Optional, List, Tuple
import numpy as np
import cv2

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

from .models import (
    Detection, DetectionFrame, BoundingBox, ObjectClass,
    YOLOv11Config
)
from .exceptions import (
    ModelNotLoadedException, ModelInferenceException,
    GPUNotAvailableException, ConfigurationException
)

logger = logging.getLogger(__name__)


class YOLOv11Detector:
    """YOLOv11 object detector with GPU support"""
    
    # Map YOLO class IDs to our ObjectClass enum
    YOLO_CLASS_MAPPING = {
        0: ObjectClass.PERSON,  # person
    }
    
    def __init__(self, config: YOLOv11Config):
        """
        Initialize YOLOv11 detector
        
        Args:
            config: YOLOv11Config with model settings
            
        Raises:
            ConfigurationException: If YOLO not available
            GPUNotAvailableException: If GPU requested but not available
        """
        if not YOLO_AVAILABLE:
            raise ConfigurationException("ultralytics package not installed")
        
        self.config = config
        self.model: Optional[YOLO] = None
        self.device = None
        
        # Detect device
        if config.use_gpu:
            try:
                import torch
                if torch.cuda.is_available():
                    self.device = f"cuda:{config.gpu_device_id}"
                    logger.info(
                        f"GPU available: {torch.cuda.get_device_name(config.gpu_device_id)}"
                    )
                else:
                    logger.warning("GPU requested but not available, using CPU")
                    self.device = "cpu"
            except Exception as e:
                logger.warning(f"GPU detection failed: {e}, using CPU")
                self.device = "cpu"
        else:
            self.device = "cpu"
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load YOLOv11 model"""
        try:
            model_name = f"yolov11{self.config.model_size}.pt"
            logger.info(f"Loading YOLOv11 model: {model_name}")
            
            self.model = YOLO(model_name)
            self.model.to(self.device)
            
            logger.info(f"Model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load YOLOv11 model: {e}")
            raise ModelNotLoadedException(f"Failed to load model: {e}")
    
    def detect(
        self,
        frame: np.ndarray,
        frame_index: int,
        timestamp: float
    ) -> DetectionFrame:
        """
        Run detection on frame
        
        Args:
            frame: Input frame (HxWx3, BGR)
            frame_index: Frame number
            timestamp: Frame timestamp
            
        Returns:
            DetectionFrame with detections
            
        Raises:
            ModelNotLoadedException: Model not loaded
            ModelInferenceException: Inference failed
        """
        if self.model is None:
            raise ModelNotLoadedException("Model not loaded")
        
        try:
            # Run inference
            results = self.model.predict(
                frame,
                conf=self.config.confidence_threshold,
                iou=self.config.iou_threshold,
                max_det=self.config.max_detections,
                verbose=False
            )
            
            detections: List[Detection] = []
            
            if results and len(results) > 0:
                result = results[0]
                
                # Parse detections
                if result.boxes is not None:
                    for i, box in enumerate(result.boxes):
                        # Get coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Get class
                        class_id = int(box.cls[0].item())
                        class_name = self.YOLO_CLASS_MAPPING.get(
                            class_id,
                            ObjectClass.PERSON
                        )
                        
                        # Get confidence
                        confidence = float(box.conf[0].item())
                        
                        # Create detection
                        detection = Detection(
                            track_id=None,  # Will be assigned by tracker
                            bbox=BoundingBox(
                                x1=float(x1),
                                y1=float(y1),
                                x2=float(x2),
                                y2=float(y2)
                            ),
                            class_name=class_name,
                            confidence=confidence,
                            frame_index=frame_index,
                            timestamp=timestamp
                        )
                        detections.append(detection)
            
            return DetectionFrame(
                frame_index=frame_index,
                timestamp=timestamp,
                detections=detections,
                frame_shape=frame.shape
            )
        
        except Exception as e:
            logger.error(f"Inference error: {e}")
            raise ModelInferenceException(f"Inference failed: {e}")
    
    def warmup(self, frame_shape: Tuple[int, int, int]) -> None:
        """
        Warmup model with dummy input
        
        Args:
            frame_shape: Expected frame shape (H, W, 3)
        """
        try:
            logger.info("Warming up model...")
            dummy_frame = np.zeros(frame_shape, dtype=np.uint8)
            self.detect(dummy_frame, frame_index=0, timestamp=0.0)
            logger.info("Model warmup complete")
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")
    
    def get_info(self) -> dict:
        """Get model information"""
        return {
            "model_size": self.config.model_size,
            "device": self.device,
            "confidence_threshold": self.config.confidence_threshold,
            "iou_threshold": self.config.iou_threshold
        }


class DetectorPool:
    """Pool of detectors for concurrent processing"""
    
    def __init__(self, config: YOLOv11Config, pool_size: int = 1):
        """
        Initialize detector pool
        
        Args:
            config: YOLOv11 configuration
            pool_size: Number of detectors in pool
        """
        self.config = config
        self.pool_size = pool_size
        self.detectors: List[YOLOv11Detector] = []
        self.current_idx = 0
        
        # Create detectors
        for i in range(pool_size):
            detector = YOLOv11Detector(config)
            self.detectors.append(detector)
            logger.info(f"Created detector {i+1}/{pool_size}")
    
    def get_detector(self) -> YOLOv11Detector:
        """Get next detector from pool (round-robin)"""
        detector = self.detectors[self.current_idx]
        self.current_idx = (self.current_idx + 1) % self.pool_size
        return detector
    
    def detect_batch(
        self,
        frames: List[Tuple[np.ndarray, int, float]]
    ) -> List[DetectionFrame]:
        """
        Detect on batch of frames using pool
        
        Args:
            frames: List of (frame, frame_index, timestamp) tuples
            
        Returns:
            List of DetectionFrames
        """
        results = []
        for frame, frame_idx, timestamp in frames:
            detector = self.get_detector()
            result = detector.detect(frame, frame_idx, timestamp)
            results.append(result)
        return results
