#!/usr/bin/env python3
"""
Phase 4: Analytics & Event Intelligence Startup Script

Runs complete detection + analytics pipeline with interaction detection,
dwell analytics, event intelligence, and Redis publishing.
"""

import sys
import os
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.detection.service import initialize_detection_service, shutdown_detection_service, get_detection_service
from app.analytics.service import initialize_phase4_service, shutdown_phase4_service, Phase4Config
from app.analytics.models import AnalyticsConfig
from app.video.ingestion import VideoIngestionService
from app.cache.manager import CacheManager


logger = logging.getLogger(__name__)


class Phase4Pipeline:
    """Complete Phase 3 + Phase 4 pipeline"""

    def __init__(self, config_path: str):
        """Initialize pipeline"""
        self.config_path = config_path
        self.config = self._load_config()
        self.setup_logging()
        
        self.detection_service = None
        self.phase4_service = None
        self.video_service = None
        self.cache_manager = CacheManager()

    def setup_logging(self):
        """Setup logging"""
        log_level = self.config.get('analytics', {}).get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _load_config(self) -> dict:
        """Load configuration"""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    async def initialize(self):
        """Initialize all services"""
        
        logger.info("Initializing Phase 3 Detection Service...")
        self.detection_service = await initialize_detection_service()
        
        logger.info("Initializing Phase 4 Analytics Service...")
        analytics_config = AnalyticsConfig(**self.config.get('analytics', {}))
        phase4_config = Phase4Config(
            config=analytics_config,
            redis_url=self.config.get('redis', {}).get('url', 'redis://localhost:6379'),
            enable_redis=True
        )
        self.phase4_service = await initialize_phase4_service(phase4_config)
        
        logger.info("Initializing Video Ingestion Service...")
        self.video_service = VideoIngestionService()
        
        logger.info("✓ All services initialized")

    async def shutdown(self):
        """Shutdown all services"""
        logger.info("Shutting down services...")
        
        if self.detection_service:
            await shutdown_detection_service()
        if self.phase4_service:
            await shutdown_phase4_service()
        
        logger.info("✓ All services shutdown")

    async def process_video_stream(
        self,
        source: str,
        output_path: str = None,
        max_frames: int = None,
        display: bool = True
    ):
        """
        Process video stream with Phase 3 + Phase 4
        
        Args:
            source: Video source (file path or camera index)
            output_path: Optional output video path
            max_frames: Max frames to process
            display: Whether to display output
        """
        
        logger.info(f"Starting video processing: {source}")
        
        try:
            # Open video source
            stream = self.video_service.open_stream(source)
            if not stream:
                logger.error(f"Failed to open stream: {source}")
                return
            
            frame_count = 0
            event_count = 0
            
            logger.info("Processing frames...")
            
            while True:
                # Read frame
                success, frame = stream.read()
                if not success:
                    logger.info("End of stream or error reading frame")
                    break
                
                if max_frames and frame_count >= max_frames:
                    logger.info(f"Reached max frames: {max_frames}")
                    break
                
                frame_count += 1
                timestamp = datetime.now()
                
                # Phase 3: Detection + Tracking
                detection_result = await self.detection_service.process_frame(
                    frame=frame,
                    frame_index=frame_count,
                    timestamp=timestamp
                )
                
                # Extract tracking data for Phase 4
                active_tracks = {}
                track_bboxes = {}
                
                if 'tracking_objects' in detection_result:
                    for track in detection_result['tracking_objects']:
                        track_id = track.id
                        zones = self.cache_manager.get(f"track_zones:{track_id}", set())
                        
                        active_tracks[track_id] = zones
                        bbox = track.bbox
                        track_bboxes[track_id] = (bbox.center[0], bbox.center[1])
                
                # Phase 4: Analytics
                if active_tracks:
                    analytics_result = await self.phase4_service.process_frame(
                        frame_index=frame_count,
                        timestamp=timestamp,
                        active_tracks=active_tracks,
                        track_bboxes=track_bboxes
                    )
                    event_count += analytics_result.get('interactions_detected', 0)
                
                # Display progress
                if frame_count % 30 == 0:
                    logger.info(
                        f"Frame {frame_count} | "
                        f"Tracks: {len(active_tracks)} | "
                        f"Total events: {event_count}"
                    )
                
                # Optional: Display frame
                if display:
                    import cv2
                    cv2.imshow('Phase 3 + 4 Pipeline', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            
            logger.info(f"✓ Processing complete: {frame_count} frames, {event_count} events")
            
            # Print statistics
            detection_stats = self.detection_service.get_statistics()
            phase4_stats = self.phase4_service.get_statistics()
            
            logger.info("\n=== Detection Statistics ===")
            logger.info(f"Detections: {detection_stats.get('total_detections', 0)}")
            logger.info(f"Tracks: {detection_stats.get('total_tracks', 0)}")
            
            logger.info("\n=== Phase 4 Statistics ===")
            logger.info(f"Active customers: {phase4_stats.get('active_customers', 0)}")
            logger.info(f"Interactions: {phase4_stats.get('interactions_detected', 0)}")
            logger.info(f"Events: {phase4_stats.get('events_published', 0)}")
            logger.info(f"Anomalies: {phase4_stats.get('anomalies_detected', 0)}")
            
            logger.info("\n=== Analytics Snapshot ===")
            analytics = self.phase4_service.get_analytics()
            logger.info(json.dumps(analytics, indent=2, default=str))
        
        finally:
            stream.release()
            if display:
                import cv2
                cv2.destroyAllWindows()


async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Phase 3 + Phase 4 Retail Vision Pipeline'
    )
    parser.add_argument(
        '--config',
        required=True,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--source',
        required=True,
        help='Video source (file path or camera index)'
    )
    parser.add_argument(
        '--output',
        help='Optional output video path'
    )
    parser.add_argument(
        '--max-frames',
        type=int,
        help='Max frames to process'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Disable display output'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = Phase4Pipeline(args.config)
    
    try:
        # Initialize
        await pipeline.initialize()
        
        # Process video
        await pipeline.process_video_stream(
            source=args.source,
            output_path=args.output,
            max_frames=args.max_frames,
            display=not args.no_display
        )
    
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
    finally:
        await pipeline.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
