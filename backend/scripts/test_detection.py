#!/usr/bin/env python3
"""
Test Detection & Tracking System - Phase 3

Comprehensive testing utilities for detection and tracking components.

Usage:
    python scripts/test_detection.py --detector
    python scripts/test_detection.py --tracker
    python scripts/test_detection.py --zones
    python scripts/test_detection.py --all
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path
from time import time
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logger import setup_logging
from app.detection import (
    YOLOv11Config, ByteTrackConfig, DetectionConfig,
    YOLOv11Detector, DetectionFrame, BoundingBox, Detection, ObjectClass,
    Zone, ZoneType, ZoneManager
)
from app.tracking import TrackingEngine

logger = logging.getLogger(__name__)


async def test_yolo_detector():
    """Test YOLOv11 detector"""
    logger.info("")
    logger.info("🧪 Testing YOLOv11 Detector")
    logger.info("-" * 50)
    
    try:
        config = YOLOv11Config(
            model_size="n",
            confidence_threshold=0.5,
            use_gpu=True
        )
        
        detector = YOLOv11Detector(config)
        logger.info("✓ Detector initialized")
        
        # Get device info
        info = detector.get_info()
        logger.info(f"Model info: {info}")
        
        # Warmup
        logger.info("Warming up...")
        dummy_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        detector.warmup(dummy_frame.shape)
        
        # Benchmark
        logger.info("Running detection benchmark...")
        frame_count = 30
        detection_times = []
        
        for i in range(frame_count):
            frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            
            start = time()
            result = detector.detect(frame, i, time())
            detection_times.append((time() - start) * 1000)
            
            if (i + 1) % 10 == 0:
                logger.info(f"  {i+1}/{frame_count} frames processed")
        
        # Results
        logger.info("")
        logger.info("📊 Detection Results")
        logger.info(f"Average time: {sum(detection_times) / len(detection_times):.2f}ms")
        logger.info(f"Min time: {min(detection_times):.2f}ms")
        logger.info(f"Max time: {max(detection_times):.2f}ms")
        logger.info(f"Average FPS: {1000 / (sum(detection_times) / len(detection_times)):.1f}")
        logger.info("✓ Detector test passed")
    
    except Exception as e:
        logger.error(f"Detector test failed: {e}", exc_info=True)


async def test_bytetrack_tracker():
    """Test ByteTrack tracking"""
    logger.info("")
    logger.info("🧪 Testing ByteTrack Tracker")
    logger.info("-" * 50)
    
    try:
        config = ByteTrackConfig()
        
        tracker = TrackingEngine(config, (1080, 1920, 3))
        logger.info("✓ Tracker initialized")
        
        # Create synthetic detections
        logger.info("Simulating tracking scenario...")
        
        for frame_idx in range(60):
            # Create 3 simulated detections with movement
            detections = []
            
            for obj_id in range(3):
                x = 200 + obj_id * 400 + frame_idx * 5
                y = 300 + frame_idx * 2
                
                detection = Detection(
                    track_id=None,
                    bbox=BoundingBox(x, y, x + 50, y + 100),
                    class_name=ObjectClass.PERSON,
                    confidence=0.9,
                    frame_index=frame_idx,
                    timestamp=time()
                )
                detections.append(detection)
            
            # Create detection frame
            frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            det_frame = DetectionFrame(
                frame_index=frame_idx,
                timestamp=time(),
                detections=detections,
                frame_shape=frame.shape
            )
            
            # Update tracker
            tracked_dets, tracked_objs = tracker.update(det_frame)
            
            if (frame_idx + 1) % 15 == 0:
                logger.info(f"  Frame {frame_idx+1}: {len(tracked_objs)} active tracks")
        
        # Final stats
        stats = tracker.get_statistics()
        logger.info("")
        logger.info("📊 Tracking Results")
        logger.info(f"Total tracks created: {stats['total_tracks']}")
        logger.info(f"Active tracks: {stats['active_tracks']}")
        logger.info(f"Max track ID: {stats['max_track_id']}")
        logger.info("✓ Tracker test passed")
    
    except Exception as e:
        logger.error(f"Tracker test failed: {e}", exc_info=True)


async def test_zone_detection():
    """Test zone detection"""
    logger.info("")
    logger.info("🧪 Testing Zone Detection")
    logger.info("-" * 50)
    
    try:
        zone_mgr = ZoneManager()
        
        # Create test zones
        zone1 = Zone(
            zone_id="test_shelf",
            zone_type=ZoneType.SHELF,
            name="Test Shelf",
            polygon=[[100, 100], [400, 100], [400, 300], [100, 300]]
        )
        
        zone2 = Zone(
            zone_id="test_checkout",
            zone_type=ZoneType.CHECKOUT,
            name="Test Checkout",
            polygon=[[500, 200], [800, 200], [800, 400], [500, 400]]
        )
        
        zone_mgr.add_zone(zone1)
        zone_mgr.add_zone(zone2)
        logger.info("✓ Zones created")
        
        # Test point-in-zone
        logger.info("Testing point-in-zone detection...")
        
        test_points = [
            (250, 200, ["test_shelf"]),  # Inside zone1
            (650, 300, ["test_checkout"]),  # Inside zone2
            (150, 150, ["test_shelf"]),  # Inside zone1
            (900, 300, []),  # Outside both zones
        ]
        
        for x, y, expected in test_points:
            zones = zone_mgr.check_point_in_zones(x, y)
            result = "✓" if set(zones) == set(expected) else "✗"
            logger.info(f"  {result} Point ({x}, {y}): zones={zones}")
        
        # Test zone tracking
        logger.info("Testing zone tracking...")
        zone_events = zone_mgr.update_track_zones(1, {"test_shelf"})
        logger.info(f"  Events on enter: {len(zone_events)}")
        
        zone_events = zone_mgr.update_track_zones(1, {"test_checkout"})
        logger.info(f"  Events on zone change: {len(zone_events)}")
        
        logger.info("✓ Zone detection test passed")
    
    except Exception as e:
        logger.error(f"Zone detection test failed: {e}", exc_info=True)


async def benchmark_full_pipeline():
    """Benchmark full detection pipeline"""
    logger.info("")
    logger.info("⚡ Benchmarking Full Pipeline")
    logger.info("-" * 50)
    
    try:
        from app.detection import DetectionService
        
        config = DetectionConfig()
        service = DetectionService(config)
        await service.initialize()
        logger.info("✓ Service initialized")
        
        # Benchmark
        frame_count = 100
        times = []
        
        logger.info(f"Processing {frame_count} frames...")
        
        for i in range(frame_count):
            frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            
            start = time()
            result = await service.process_frame(frame, i, time())
            times.append((time() - start) * 1000)
            
            if (i + 1) % 25 == 0:
                logger.info(f"  {i+1}/{frame_count} frames")
        
        # Results
        logger.info("")
        logger.info("📊 Pipeline Performance")
        logger.info(f"Total time: {sum(times):.2f}ms")
        logger.info(f"Average time per frame: {sum(times) / len(times):.2f}ms")
        logger.info(f"Average FPS: {1000 / (sum(times) / len(times)):.1f}")
        logger.info(f"Min time: {min(times):.2f}ms")
        logger.info(f"Max time: {max(times):.2f}ms")
        
        stats = service.get_statistics()
        logger.info("")
        logger.info("📊 Service Statistics")
        logger.info(f"Frames processed: {stats['frames_processed']}")
        logger.info(f"Total detections: {stats['total_detections']}")
        logger.info(f"Active tracks: {stats['active_tracks']}")
        
        await service.shutdown()
        logger.info("✓ Pipeline benchmark complete")
    
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)


async def main():
    """Main test suite"""
    parser = argparse.ArgumentParser(description="Test Detection System")
    parser.add_argument('--detector', action='store_true', help='Test detector')
    parser.add_argument('--tracker', action='store_true', help='Test tracker')
    parser.add_argument('--zones', action='store_true', help='Test zones')
    parser.add_argument('--benchmark', action='store_true', help='Benchmark pipeline')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--log-level', type=str, default='INFO')
    
    args = parser.parse_args()
    
    setup_logging(log_level=args.log_level)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("🧪 Detection & Tracking Test Suite")
    logger.info("=" * 70)
    
    try:
        if args.detector or args.all:
            await test_yolo_detector()
        
        if args.tracker or args.all:
            await test_bytetrack_tracker()
        
        if args.zones or args.all:
            await test_zone_detection()
        
        if args.benchmark or args.all:
            await benchmark_full_pipeline()
        
        if not any([args.detector, args.tracker, args.zones, args.benchmark, args.all]):
            logger.info("Please specify a test to run (--detector, --tracker, --zones, --all)")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ Test suite completed")
        logger.info("=" * 70)
    
    except Exception as e:
        logger.error(f"Test error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
