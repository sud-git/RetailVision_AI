#!/usr/bin/env python3
"""
Start Video Ingestion Pipeline - Initialize and run video source streaming

Usage:
    python scripts/start_video_ingestion.py --config config.json
    python scripts/start_video_ingestion.py --source-rtsp "rtsp://camera.local/stream"
"""

import asyncio
import json
import logging
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.logger import setup_logging
from app.cache import init_redis, get_cache_manager
from app.video_ingestion import VideoSourceConfig, VideoIngestionConfig, VideoSourceType
from app.services.video_ingestion_service import (
    get_video_ingestion_service,
    shutdown_video_ingestion_service
)

logger = logging.getLogger(__name__)


async def load_config(config_path: str) -> VideoIngestionConfig:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        # Convert source dicts to VideoSourceConfig objects
        sources = []
        for source_dict in config_dict.get('sources', []):
            sources.append(VideoSourceConfig(**source_dict))
        
        config_dict['sources'] = sources
        return VideoIngestionConfig(**config_dict)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        raise


def create_sample_config() -> VideoIngestionConfig:
    """Create sample configuration for testing"""
    return VideoIngestionConfig(
        sources=[
            # Example RTSP source (requires real camera)
            # VideoSourceConfig(
            #     id="front_entrance",
            #     type=VideoSourceType.RTSP,
            #     url="rtsp://192.168.1.100:554/stream",
            #     fps=30,
            #     resolution=[1920, 1080],
            # ),
            
            # Webcam source (if available)
            VideoSourceConfig(
                id="webcam_main",
                type=VideoSourceType.WEBCAM,
                device_id=0,
                fps=15,
                resolution=[1280, 720],
            ),
        ],
        gpu_acceleration=True,
        max_concurrent_sources=10,
        health_check_interval_seconds=30,
        metrics_publish_interval_seconds=10,
    )


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Start RetailVision AI Video Ingestion Pipeline"
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to video sources configuration JSON file'
    )
    parser.add_argument(
        '--source-rtsp',
        type=str,
        help='Add RTSP stream source'
    )
    parser.add_argument(
        '--source-webcam',
        action='store_true',
        help='Add webcam source'
    )
    parser.add_argument(
        '--source-file',
        type=str,
        help='Add local video file source'
    )
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='Create and use sample configuration'
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
    logger.info("=" * 70)
    logger.info("🎬 RetailVision AI - Video Ingestion Pipeline")
    logger.info("=" * 70)
    
    try:
        # Load or create configuration
        if args.create_sample or not args.config:
            logger.info("Creating sample configuration...")
            config = create_sample_config()
            
            # Add CLI-specified sources
            if args.source_rtsp:
                config.sources.append(VideoSourceConfig(
                    id="rtsp_cli",
                    type=VideoSourceType.RTSP,
                    url=args.source_rtsp,
                    fps=30,
                ))
            
            if args.source_webcam:
                config.sources.append(VideoSourceConfig(
                    id="webcam_cli",
                    type=VideoSourceType.WEBCAM,
                    fps=15,
                ))
            
            if args.source_file:
                config.sources.append(VideoSourceConfig(
                    id="local_file_cli",
                    type=VideoSourceType.LOCAL_FILE,
                    url=args.source_file,
                    fps=30,
                ))
        else:
            logger.info(f"Loading configuration from: {args.config}")
            config = await load_config(args.config)
        
        logger.info(f"Configured sources: {len(config.sources)}")
        for source in config.sources:
            logger.info(f"  - {source.id} ({source.type.value}): {source.fps} FPS")
        
        # Initialize Redis
        logger.info("Initializing Redis connection...")
        settings = get_settings()
        await init_redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
        )
        logger.info("✓ Redis connected")
        
        # Initialize video ingestion service
        logger.info("Initializing video ingestion service...")
        cache_manager = get_cache_manager()
        service = await get_video_ingestion_service(cache_manager)
        
        success = await service.initialize(config)
        if not success:
            logger.error("Failed to initialize video ingestion service")
            return
        
        logger.info(f"✓ Video ingestion service initialized with {len(config.sources)} sources")
        logger.info("")
        logger.info("📊 Metrics available at:")
        logger.info("  - http://localhost:8000/api/video-ingestion/sources")
        logger.info("  - http://localhost:8000/api/video-ingestion/metrics")
        logger.info("")
        logger.info("Press Ctrl+C to stop...")
        logger.info("")
        
        # Keep service running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n📛 Stopping video ingestion pipeline...")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        # Cleanup
        await shutdown_video_ingestion_service()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
