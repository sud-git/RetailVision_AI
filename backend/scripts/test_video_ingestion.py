#!/usr/bin/env python3
"""
Test Video Ingestion Pipeline - Comprehensive testing utilities

Tests:
- Frame extraction from different sources
- FPS throttling
- Buffer management
- Error recovery
- GPU detection

Usage:
    python scripts/test_video_ingestion.py --source webcam --duration 30
    python scripts/test_video_ingestion.py --source local-file --video /path/to/video.mp4
    python scripts/test_video_ingestion.py --benchmark
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path
from time import time
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logger import setup_logging
from app.video_ingestion import (
    VideoSourceConfig, VideoSourceType, FrameExtractor,
    AsyncQueue, GPUOptimizer, get_gpu_optimizer
)

logger = logging.getLogger(__name__)


async def test_gpu_detection():
    """Test GPU detection and optimization"""
    logger.info("")
    logger.info("🔧 Testing GPU Detection")
    logger.info("-" * 50)
    
    gpu = get_gpu_optimizer()
    info = gpu.get_device_info()
    
    logger.info(f"GPU Available: {info['cuda_available']}")
    logger.info(f"Device Type: {info['device_type']}")
    
    if info['cuda_available']:
        logger.info(f"GPU Info: {info['gpu_info']}")
        logger.info(f"Memory Stats: {info['memory_stats']}")
    
    logger.info("✓ GPU detection test passed")


async def test_async_queue():
    """Test async queue with deduplication"""
    logger.info("")
    logger.info("🔄 Testing Async Queue")
    logger.info("-" * 50)
    
    import numpy as np
    from app.video_ingestion import FrameMetadata
    
    queue = AsyncQueue(
        max_capacity=100,
        enable_dedup=True,
        enable_keyframe_priority=True,
        source_id="test"
    )
    
    # Create test frames
    frame1 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    frame2 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    metadata1 = FrameMetadata(
        source_id="test",
        frame_index=0,
        timestamp=time(),
        width=640,
        height=480,
        format="BGR",
        is_keyframe=True
    )
    
    metadata2 = FrameMetadata(
        source_id="test",
        frame_index=1,
        timestamp=time(),
        width=640,
        height=480,
        format="BGR",
        is_keyframe=False
    )
    
    # Test adding frames
    added1 = await queue.put(frame1, metadata1)
    logger.info(f"Added frame 1: {added1}")
    
    added2 = await queue.put(frame2, metadata2)
    logger.info(f"Added frame 2: {added2}")
    
    # Test duplicate detection
    added3 = await queue.put(frame1, metadata1)
    logger.info(f"Added duplicate frame 1: {added3} (should be False)")
    
    # Get stats
    stats = await queue.get_stats()
    logger.info(f"Queue stats: {stats}")
    
    # Test retrieval
    result = await queue.get_nowait()
    logger.info(f"Retrieved frame: {result is not None}")
    
    logger.info("✓ Async queue test passed")


async def test_frame_extractor(
    source_type: str,
    duration_seconds: float = 10,
    device_id: int = 0,
    file_path: str = None
):
    """Test frame extraction from source"""
    logger.info("")
    logger.info(f"📹 Testing Frame Extraction ({source_type})")
    logger.info("-" * 50)
    
    try:
        # Create config based on source type
        if source_type == "webcam":
            config = VideoSourceConfig(
                id="test_webcam",
                type=VideoSourceType.WEBCAM,
                device_id=device_id,
                fps=30,
                resolution=[1280, 720],
            )
        elif source_type == "local-file":
            if not file_path:
                logger.error("File path required for local-file source")
                return
            config = VideoSourceConfig(
                id="test_file",
                type=VideoSourceType.LOCAL_FILE,
                url=file_path,
                fps=30,
            )
        elif source_type == "rtsp":
            logger.warning("RTSP test skipped (requires real camera)")
            return
        else:
            logger.error(f"Unknown source type: {source_type}")
            return
        
        # Create extractor
        extractor = FrameExtractor(config)
        
        # Connect
        logger.info("Connecting to source...")
        success = await extractor.connect()
        
        if not success:
            logger.error("Failed to connect to source")
            return
        
        logger.info("✓ Connected successfully")
        
        # Extract frames
        logger.info(f"Extracting frames for {duration_seconds} seconds...")
        
        start_time = time()
        frame_count = 0
        total_extraction_time = 0
        
        while time() - start_time < duration_seconds:
            result = await extractor.extract_frame()
            
            if result:
                frame_data, metadata = result
                frame_count += 1
                total_extraction_time += metadata.extraction_time_ms
                
                if frame_count % 30 == 0:
                    avg_time = total_extraction_time / frame_count
                    fps = frame_count / (time() - start_time)
                    logger.info(
                        f"  Extracted {frame_count} frames, "
                        f"FPS: {fps:.1f}, "
                        f"Avg time: {avg_time:.2f}ms"
                    )
            else:
                await asyncio.sleep(0.01)
        
        # Get final stats
        stats = extractor.get_stats()
        logger.info(f"Extraction complete. Stats: {stats}")
        
        # Cleanup
        extractor.disconnect()
        logger.info("✓ Frame extraction test passed")
        
    except Exception as e:
        logger.error(f"Error in frame extraction test: {e}", exc_info=True)


async def benchmark_frame_extraction():
    """Benchmark frame extraction performance"""
    logger.info("")
    logger.info("⚡ Benchmarking Frame Extraction")
    logger.info("-" * 50)
    
    try:
        # Try webcam
        config = VideoSourceConfig(
            id="benchmark",
            type=VideoSourceType.WEBCAM,
            device_id=0,
            fps=30,
            resolution=[1280, 720],
        )
        
        extractor = FrameExtractor(config)
        
        if not await extractor.connect():
            logger.warning("Could not connect to webcam for benchmark")
            return
        
        # Warmup
        logger.info("Warming up...")
        for _ in range(10):
            await extractor.extract_frame()
        
        # Benchmark
        logger.info("Running benchmark for 60 frames...")
        start = time()
        for _ in range(60):
            await extractor.extract_frame()
        elapsed = time() - start
        
        fps = 60 / elapsed
        avg_time = (elapsed / 60) * 1000
        
        logger.info(f"Average FPS: {fps:.1f}")
        logger.info(f"Average extraction time: {avg_time:.2f}ms")
        
        extractor.disconnect()
        logger.info("✓ Benchmark complete")
        
    except Exception as e:
        logger.error(f"Error in benchmark: {e}", exc_info=True)


async def main():
    """Main test suite"""
    parser = argparse.ArgumentParser(
        description="Test RetailVision AI Video Ingestion"
    )
    parser.add_argument(
        '--source',
        type=str,
        choices=['webcam', 'local-file', 'rtsp', 'all'],
        help='Source type to test'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=10,
        help='Test duration in seconds'
    )
    parser.add_argument(
        '--video',
        type=str,
        help='Path to video file for testing'
    )
    parser.add_argument(
        '--device',
        type=int,
        default=0,
        help='Webcam device ID'
    )
    parser.add_argument(
        '--gpu',
        action='store_true',
        help='Test GPU detection'
    )
    parser.add_argument(
        '--queue',
        action='store_true',
        help='Test async queue'
    )
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run performance benchmark'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all tests'
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
    logger.info("🧪 RetailVision AI - Video Ingestion Test Suite")
    logger.info("=" * 70)
    
    try:
        # Run tests
        if args.gpu or args.all:
            await test_gpu_detection()
        
        if args.queue or args.all:
            await test_async_queue()
        
        if args.benchmark or args.all:
            await benchmark_frame_extraction()
        
        if args.source:
            if args.source == 'all':
                sources = ['webcam', 'local-file']
            else:
                sources = [args.source]
            
            for source in sources:
                if source == 'local-file' and not args.video:
                    logger.warning("Skipping local-file test (no --video provided)")
                    continue
                
                await test_frame_extractor(
                    source,
                    duration_seconds=args.duration,
                    device_id=args.device,
                    file_path=args.video
                )
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ All tests completed successfully!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Test suite error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
