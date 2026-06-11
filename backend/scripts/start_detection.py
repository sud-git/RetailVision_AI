#!/usr/bin/env python3
"""
Start Detection & Tracking Pipeline - Phase 3

Real-time customer detection and tracking system with frame visualization.

Usage:
    python scripts/start_detection.py --config scripts/detection_config.json
    python scripts/start_detection.py --create-sample
    python scripts/start_detection.py --benchmark-fps 30
"""

import asyncio
import logging
import sys
import argparse
import json
from pathlib import Path
from time import time
from typing import Optional
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logger import setup_logging
from app.detection import (
    DetectionConfig, initialize_detection_service, get_detection_service
)
from app.video_ingestion import get_video_ingestion_service
from app.cache import CacheManager

logger = logging.getLogger(__name__)


async def process_video_stream(
    video_source_id: str,
    output_video_path: Optional[str] = None,
    display: bool = True,
    max_frames: Optional[int] = None
):
    """
    Process video stream with detection and tracking
    
    Args:
        video_source_id: Video source ID from video ingestion
        output_video_path: Optional path to save output video
        display: Display frames with overlays
        max_frames: Max frames to process (None for infinite)
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("🎥 Detection & Tracking Pipeline Started")
    logger.info("=" * 70)
    
    detection_service = await get_detection_service()
    video_service = await get_video_ingestion_service()
    
    if not detection_service or not video_service:
        logger.error("Services not initialized")
        return
    
    # Video writer setup
    video_writer = None
    if output_video_path:
        logger.info(f"Output video will be saved to: {output_video_path}")
    
    try:
        frame_count = 0
        start_time = time()
        detection_times = []
        
        while True:
            # Check max frames
            if max_frames and frame_count >= max_frames:
                logger.info(f"Reached max frames: {max_frames}")
                break
            
            # Get frame from video ingestion
            result = await video_service.get_frame(video_source_id, timeout_seconds=5.0)
            
            if not result:
                await asyncio.sleep(0.01)
                continue
            
            frame, metadata = result
            
            # Run detection
            frame_start = time()
            detection_result = await detection_service.process_frame(
                frame,
                metadata.frame_index,
                metadata.timestamp
            )
            detection_time = (time() - frame_start) * 1000  # ms
            detection_times.append(detection_time)
            
            # Render detections
            rendered_frame = detection_service.render_detections(
                frame,
                detection_result["detections"],
                detection_result["tracked_objects"]
            )
            
            # Save video if requested
            if output_video_path:
                if video_writer is None:
                    h, w = rendered_frame.shape[:2]
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    video_writer = cv2.VideoWriter(
                        output_video_path,
                        fourcc,
                        30.0,
                        (w, h)
                    )
                    logger.info(f"Video writer created: {w}x{h}")
                
                video_writer.write(rendered_frame)
            
            # Display frame if requested
            if display:
                cv2.imshow("Detection & Tracking", rendered_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("User pressed 'q' to quit")
                    break
            
            frame_count += 1
            
            # Print progress
            if frame_count % 30 == 0:
                elapsed = time() - start_time
                fps = frame_count / elapsed
                avg_det_time = sum(detection_times[-30:]) / min(30, len(detection_times))
                
                stats = detection_service.get_statistics()
                logger.info(
                    f"Frames: {frame_count} | FPS: {fps:.1f} | "
                    f"Detections: {stats['total_detections']} | "
                    f"Active tracks: {stats['active_tracks']} | "
                    f"Detection time: {avg_det_time:.2f}ms"
                )
    
    except Exception as e:
        logger.error(f"Error processing stream: {e}", exc_info=True)
    
    finally:
        # Cleanup
        if video_writer:
            video_writer.release()
            logger.info(f"✓ Video saved to {output_video_path}")
        
        cv2.destroyAllWindows()
        
        # Final stats
        elapsed = time() - start_time
        stats = detection_service.get_statistics()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("📊 Detection Pipeline Statistics")
        logger.info("=" * 70)
        logger.info(f"Total frames processed: {frame_count}")
        logger.info(f"Total time: {elapsed:.1f} seconds")
        logger.info(f"Average FPS: {frame_count / elapsed:.1f}")
        logger.info(f"Total detections: {stats['total_detections']}")
        logger.info(f"Active tracks: {stats['active_tracks']}")
        logger.info(f"Events published: {stats['events_published']}")
        logger.info(f"Average detection time: {sum(detection_times) / len(detection_times):.2f}ms")
        logger.info("=" * 70)


async def benchmark_detection(fps_limit: int = 30):
    """Benchmark detection performance"""
    logger.info("")
    logger.info("⚡ Benchmarking Detection Pipeline")
    logger.info("-" * 70)
    
    detection_service = await get_detection_service()
    
    if not detection_service:
        logger.error("Detection service not initialized")
        return
    
    try:
        # Create dummy frames
        frame_shape = (1080, 1920, 3)
        frame_count = 100
        detection_times = []
        
        logger.info(f"Testing with {frame_count} frames ({frame_shape})")
        logger.info("Warming up...")
        
        # Warmup
        for i in range(5):
            dummy_frame = np.zeros(frame_shape, dtype=np.uint8)
            await detection_service.process_frame(dummy_frame, i, time())
        
        logger.info("Running benchmark...")
        start_time = time()
        
        for i in range(frame_count):
            # Create random frame
            dummy_frame = np.random.randint(0, 255, frame_shape, dtype=np.uint8)
            
            frame_start = time()
            result = await detection_service.process_frame(dummy_frame, i, time())
            detection_times.append((time() - frame_start) * 1000)
            
            if (i + 1) % 20 == 0:
                logger.info(f"  Progress: {i+1}/{frame_count}")
        
        elapsed = time() - start_time
        
        # Statistics
        logger.info("")
        logger.info("📊 Benchmark Results")
        logger.info("-" * 70)
        logger.info(f"Total frames: {frame_count}")
        logger.info(f"Total time: {elapsed:.2f}s")
        logger.info(f"Average FPS: {frame_count / elapsed:.1f}")
        logger.info(f"Min time: {min(detection_times):.2f}ms")
        logger.info(f"Max time: {max(detection_times):.2f}ms")
        logger.info(f"Avg time: {sum(detection_times) / len(detection_times):.2f}ms")
        logger.info("-" * 70)
    
    except Exception as e:
        logger.error(f"Benchmark error: {e}", exc_info=True)


async def create_sample_config():
    """Create sample configuration"""
    logger.info("Creating sample detection configuration...")
    
    config = DetectionConfig(
        publish_all_detections=True,
        publish_zone_events=True,
        publish_dwell_events=True
    )
    
    logger.info("✓ Sample configuration created")
    return config


async def main():
    """Main detection pipeline"""
    parser = argparse.ArgumentParser(
        description="RetailVision AI - Detection & Tracking Pipeline"
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to detection configuration file'
    )
    parser.add_argument(
        '--source',
        type=str,
        default="store_front",
        help='Video source ID from ingestion pipeline'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output video file path'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Disable frame display'
    )
    parser.add_argument(
        '--max-frames',
        type=int,
        help='Maximum frames to process'
    )
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='Create sample configuration'
    )
    parser.add_argument(
        '--benchmark-fps',
        type=int,
        help='Run detection benchmark'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("🎬 RetailVision AI - Phase 3: Detection & Tracking")
    logger.info("=" * 70)
    
    try:
        # Load configuration
        if args.create_sample:
            config = await create_sample_config()
        elif args.config:
            logger.info(f"Loading configuration: {args.config}")
            with open(args.config, 'r') as f:
                config_dict = json.load(f)
            config = DetectionConfig(**config_dict)
        else:
            logger.info("Using default configuration")
            config = DetectionConfig()
        
        logger.info(f"✓ Configuration loaded")
        
        # Initialize cache manager
        logger.info("Initializing cache manager...")
        cache_manager = CacheManager()
        await cache_manager.connect()
        logger.info("✓ Cache manager connected")
        
        # Initialize detection service
        logger.info("Initializing detection service...")
        detection_service = await initialize_detection_service(config, cache_manager)
        logger.info("✓ Detection service initialized")
        
        # Initialize video ingestion service
        logger.info("Initializing video ingestion service...")
        try:
            from app.services.video_ingestion_service import get_video_ingestion_service
            video_service = await get_video_ingestion_service()
            if not video_service:
                logger.warning("Video ingestion service not available")
        except:
            logger.warning("Video ingestion service not available")
        
        # Run pipeline
        if args.benchmark_fps:
            await benchmark_detection(args.benchmark_fps)
        else:
            await process_video_stream(
                video_source_id=args.source,
                output_video_path=args.output,
                display=not args.no_display,
                max_frames=args.max_frames
            )
        
        logger.info("")
        logger.info("✅ Detection pipeline completed successfully")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        # Cleanup
        try:
            from app.detection import shutdown_detection_service
            await shutdown_detection_service()
            await cache_manager.disconnect()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
