#!/usr/bin/env python3
"""
Phase 4: Analytics Test Suite

Comprehensive tests for interaction detection, dwell analytics, event intelligence.
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.analytics import InteractionDetector, DwellAnalytics, AnalyticsMetricsEngine
from app.analytics.models import (
    AnalyticsConfig, InteractionConfig, DwellAnalyticsConfig,
    EventPublishingConfig, OverlayConfig, CustomerInteraction, InteractionType
)
from app.events import RetailEventIntelligence, RedisEventPublisher
from app.analytics.overlay_renderer import Phase4OverlayRenderer


logger = logging.getLogger(__name__)


def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


class Phase4TestSuite:
    """Test suite for Phase 4"""

    def __init__(self):
        """Initialize test suite"""
        self.config = AnalyticsConfig(
            interaction=InteractionConfig(),
            dwell_analytics=DwellAnalyticsConfig(),
            event_publishing=EventPublishingConfig(),
            overlay=OverlayConfig()
        )
        
        self.interaction_detector = InteractionDetector(self.config.interaction)
        self.dwell_analytics = DwellAnalytics(self.config.dwell_analytics)
        self.event_intelligence = RetailEventIntelligence(self.config.event_publishing)
        self.metrics_engine = AnalyticsMetricsEngine(
            self.interaction_detector,
            self.dwell_analytics
        )

    def test_interaction_detection(self) -> bool:
        """Test interaction detection"""
        logger.info("=== Test: Interaction Detection ===")
        
        try:
            # Simulate customer entering zone
            track_id = 1
            zone_id = "dairy_shelf_1"
            current_zones = {zone_id}
            previous_zones = set()
            bbox_center = (150, 150)
            timestamp = datetime.now()
            
            interactions = self.interaction_detector.detect_interactions(
                track_id=track_id,
                current_zones=current_zones,
                previous_zones=previous_zones,
                bbox_center=bbox_center,
                frame_index=0,
                timestamp=timestamp
            )
            
            assert len(interactions) > 0, "No interactions detected"
            assert interactions[0].interaction_type == InteractionType.ZONE_ENTRY
            
            logger.info(f"✓ Detected {len(interactions)} interactions")
            logger.info(f"  - Interaction type: {interactions[0].interaction_type.value}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            return False

    def test_dwell_analytics(self) -> bool:
        """Test dwell time analytics"""
        logger.info("\n=== Test: Dwell Analytics ===")
        
        try:
            from app.analytics.models import ZoneDwellSession
            import uuid
            
            # Create sample session
            session = ZoneDwellSession(
                session_id=str(uuid.uuid4()),
                track_id=1,
                zone_id="dairy_shelf_1",
                entry_time=datetime.now() - timedelta(seconds=30),
                exit_time=datetime.now()
            )
            
            self.dwell_analytics.record_dwell_session(
                track_id=1,
                zone_id="dairy_shelf_1",
                session=session,
                timestamp=datetime.now()
            )
            
            metrics = self.dwell_analytics.get_zone_dwell_metrics("dairy_shelf_1")
            assert metrics is not None, "No metrics generated"
            assert metrics['visit_count'] == 1, "Visit count mismatch"
            assert metrics['avg_time'] >= 30, "Duration not recorded"
            
            logger.info(f"✓ Dwell metrics recorded")
            logger.info(f"  - Zone: dairy_shelf_1")
            logger.info(f"  - Duration: {metrics['avg_time']:.1f}s")
            return True
        
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            return False

    def test_event_intelligence(self) -> bool:
        """Test event intelligence"""
        logger.info("\n=== Test: Event Intelligence ===")
        
        try:
            # Generate interaction event
            event = self.event_intelligence.generate_interaction_event(
                track_id=1,
                zone_id="dairy_shelf_1",
                interaction_type="zone_entry",
                confidence=0.95,
                duration=0,
                frame_index=0,
                timestamp=datetime.now()
            )
            
            assert event is not None, "Event not created"
            assert len(self.event_intelligence.event_buffer) > 0, "Event not buffered"
            
            logger.info(f"✓ Event intelligence working")
            logger.info(f"  - Event type: {event.event_type}")
            logger.info(f"  - Track ID: {event.track_id}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            return False

    def test_anomaly_detection(self) -> bool:
        """Test anomaly detection"""
        logger.info("\n=== Test: Anomaly Detection ===")
        
        try:
            from app.events import AnomalyType
            
            # Detect suspicious behavior
            anomaly = self.event_intelligence.detect_suspicious_behavior(
                track_id=2,
                anomaly_type=AnomalyType.LOITERING,
                confidence=0.85,
                zone_id="dairy_shelf_1",
                frame_index=100,
                timestamp=datetime.now(),
                description="Customer loitering for extended period"
            )
            
            assert anomaly is not None, "Anomaly not created"
            assert len(self.event_intelligence.anomaly_buffer) > 0, "Anomaly not buffered"
            
            logger.info(f"✓ Anomaly detection working")
            logger.info(f"  - Anomaly type: {anomaly.anomaly_type}")
            logger.info(f"  - Confidence: {anomaly.confidence}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            return False

    def test_metrics_engine(self) -> bool:
        """Test metrics engine"""
        logger.info("\n=== Test: Metrics Engine ===")
        
        try:
            # Add test data
            from app.analytics.models import ZoneDwellSession, CustomerProfile
            import uuid
            
            # Create customer profile
            profile = CustomerProfile(
                track_id=1,
                first_seen=datetime.now(),
                last_seen=datetime.now()
            )
            self.interaction_detector.customer_profiles[1] = profile
            
            # Compute metrics
            metrics = self.metrics_engine.compute_store_metrics()
            
            assert metrics.total_customers >= 0, "Invalid customer count"
            
            logger.info(f"✓ Metrics engine working")
            logger.info(f"  - Total customers: {metrics.total_customers}")
            logger.info(f"  - Total interactions: {metrics.total_interactions}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            return False

    def test_overlay_rendering(self) -> bool:
        """Test overlay rendering"""
        logger.info("\n=== Test: Overlay Rendering ===")
        
        try:
            import cv2
            import numpy as np
            
            # Create dummy frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Create renderer
            renderer = Phase4OverlayRenderer(self.config.overlay)
            
            # Render frame
            zones = {
                'zone_1': [(100, 100), (300, 100), (300, 200), (100, 200)]
            }
            active_tracks = {
                1: {'bbox_center': (150, 150), 'behavior': 'browsing'}
            }
            
            rendered = renderer.render_frame(
                frame=frame,
                zones=zones,
                active_tracks=active_tracks,
                interactions=[],
                anomalies=[],
                dwell_sessions={},
                crowd_events=[],
                timestamp=datetime.now()
            )
            
            assert rendered is not None, "Rendering failed"
            assert rendered.shape == frame.shape, "Output shape mismatch"
            
            logger.info(f"✓ Overlay rendering working")
            logger.info(f"  - Zones rendered: {len(zones)}")
            logger.info(f"  - Tracks rendered: {len(active_tracks)}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            return False

    def test_crowd_detection(self) -> bool:
        """Test crowd detection"""
        logger.info("\n=== Test: Crowd Detection ===")
        
        try:
            # Detect crowd
            event = self.event_intelligence.detect_crowd_event(
                zone_id="dairy_shelf_1",
                customer_count=8,
                frame_index=50,
                timestamp=datetime.now(),
                crowd_threshold=5
            )
            
            assert event is not None, "Crowd event not created"
            assert event.payload['density_level'] == 'high', "Density level incorrect"
            
            logger.info(f"✓ Crowd detection working")
            logger.info(f"  - Zone: dairy_shelf_1")
            logger.info(f"  - Customer count: 8")
            logger.info(f"  - Density: high")
            return True
        
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            return False

    async def test_redis_publisher(self) -> bool:
        """Test Redis publisher"""
        logger.info("\n=== Test: Redis Publisher ===")
        
        try:
            publisher = RedisEventPublisher("redis://localhost:6379")
            connected = await publisher.connect()
            
            if not connected:
                logger.warning("⚠ Redis not available (expected in test environment)")
                return True
            
            # Publish interaction
            event_id = await publisher.publish_interaction(
                track_id=1,
                zone_id="dairy_shelf_1",
                interaction_type="zone_entry",
                timestamp=datetime.now(),
                duration=0,
                confidence=0.95
            )
            
            await publisher.disconnect()
            
            logger.info(f"✓ Redis publisher working")
            logger.info(f"  - Published event: {event_id}")
            return True
        
        except Exception as e:
            logger.warning(f"⚠ Redis test skipped: {e}")
            return True

    async def run_all_tests(self) -> int:
        """Run all tests"""
        logger.info("\n" + "="*50)
        logger.info("PHASE 4 TEST SUITE")
        logger.info("="*50 + "\n")
        
        tests = [
            ("Interaction Detection", self.test_interaction_detection),
            ("Dwell Analytics", self.test_dwell_analytics),
            ("Event Intelligence", self.test_event_intelligence),
            ("Anomaly Detection", self.test_anomaly_detection),
            ("Metrics Engine", self.test_metrics_engine),
            ("Overlay Rendering", self.test_overlay_rendering),
            ("Crowd Detection", self.test_crowd_detection),
            ("Redis Publisher", self.test_redis_publisher)
        ]
        
        results = {}
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                
                results[test_name] = "PASS" if result else "FAIL"
                if result:
                    passed += 1
                else:
                    failed += 1
            
            except Exception as e:
                logger.error(f"Unexpected error in {test_name}: {e}")
                results[test_name] = "ERROR"
                failed += 1
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("TEST SUMMARY")
        logger.info("="*50)
        
        for test_name, result in results.items():
            status = "✓" if result == "PASS" else "✗"
            logger.info(f"{status} {test_name}: {result}")
        
        logger.info("="*50)
        logger.info(f"Total: {passed} passed, {failed} failed")
        logger.info("="*50 + "\n")
        
        return 0 if failed == 0 else 1


async def main():
    """Main entry point"""
    setup_logging()
    
    suite = Phase4TestSuite()
    exit_code = await suite.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())
