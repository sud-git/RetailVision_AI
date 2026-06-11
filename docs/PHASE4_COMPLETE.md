# Phase 4: Shelf Interaction & Event Intelligence System

Complete documentation for the Phase 4 Retail Vision AI system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Architecture](#component-architecture)
3. [Event Intelligence System](#event-intelligence-system)
4. [Redis Integration](#redis-integration)
5. [Analytics Metrics](#analytics-metrics)
6. [Configuration Guide](#configuration-guide)
7. [API Reference](#api-reference)
8. [Running the System](#running-the-system)
9. [Performance Optimization](#performance-optimization)

---

## Architecture Overview

### Design Goals

- **Real-time Interaction Detection**: Detect customer-shelf interactions as they happen
- **Advanced Analytics**: Track dwell time, engagement metrics, and behavior patterns
- **Event Intelligence**: Generate actionable retail events and anomaly alerts
- **Redis Integration**: Publish events to streams for dashboard and analytics downstream consumers
- **Scalable Design**: Handle thousands of simultaneous customer interactions

### System Components

```
                   ┌─────────────────────────┐
                   │   Video Input Stream    │
                   └────────────┬────────────┘
                                │
                   ┌────────────▼────────────┐
                   │  Phase 3: Detection +   │
                   │      Tracking           │
                   └────────────┬────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
      ┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
      │  Interaction │  │ Dwell Time  │  │   Event     │
      │   Detector   │  │  Analytics  │  │ Intelligence│
      └───────┬──────┘  └──────┬──────┘  └──────┬──────┘
              │                 │                 │
      ┌───────▼─────────────────▼─────────────────▼──────┐
      │        Phase 4: Analytics & Event Engine         │
      └───────┬──────────────────┬──────────────────┬────┘
              │                  │                  │
      ┌───────▼──┐      ┌────────▼────┐    ┌──────▼──────┐
      │  Metrics │      │   Overlay   │    │Redis Stream │
      │  Engine  │      │  Renderer   │    │  Publisher  │
      └──────────┘      └─────────────┘    └─────────────┘
              │                 │                  │
              └─────────────────┼──────────────────┘
                                │
                        ┌───────▼────────┐
                        │  Output Video  │
                        │  +             │
                        │  Redis Events  │
                        └────────────────┘
```

### Data Flow

1. **Detection & Tracking** (Phase 3):
   - YOLOv11 detects persons in each frame
   - ByteTrack assigns persistent track IDs
   - Zone manager identifies which zones each person occupies

2. **Interaction Detection** (Phase 4):
   - Detects zone entry/exit events
   - Identifies prolonged engagement and interactions
   - Generates customer profiles with behavior classification

3. **Dwell Analytics** (Phase 4):
   - Tracks time spent in each zone per customer
   - Aggregates hourly and historical metrics
   - Computes engagement rates and popularity metrics

4. **Event Intelligence** (Phase 4):
   - Generates structured retail events (engagement, anomalies, crowd)
   - Detects suspicious behavior patterns
   - Publishes events to Redis Streams

5. **Metrics & Visualization** (Phase 4):
   - Computes zone and store-level metrics
   - Generates movement patterns and crowd analysis
   - Renders enhanced overlays with analytics data
   - Publishes metrics to Redis for dashboards

---

## Component Architecture

### 1. Interaction Detector

**File**: `backend/app/interactions/detector.py`

Detects customer-shelf interactions and maintains customer profiles.

```python
class InteractionDetector:
    def detect_interactions(track_id, current_zones, previous_zones, bbox_center, frame_index, timestamp):
        # Detects: zone_entry, zone_exit, engagement, compare, pickup
        # Returns: List[CustomerInteraction]
    
    def update_customer_profile(track_id, interactions, timestamp):
        # Updates profile with new interactions
        # Classifies behavior: browsing, comparing, purchasing, suspicious
        # Returns: CustomerProfile
```

**Key Features**:
- Zone entry/exit detection with ray-casting polygon containment
- Engagement duration tracking
- Behavior classification based on interaction patterns
- Anomaly flagging for suspicious activity
- Customer profile management with history tracking

**Data Structures**:
```python
@dataclass
class CustomerInteraction:
    interaction_id: str
    track_id: int
    zone_id: str
    interaction_type: InteractionType  # zone_entry, engagement, etc.
    timestamp: datetime
    duration_seconds: float
    intensity: float  # 0-1 engagement level
    confidence: float
    metadata: Dict

@dataclass
class CustomerProfile:
    track_id: int
    first_seen: datetime
    last_seen: datetime
    total_zones_visited: Set[str]
    interactions: List[CustomerInteraction]
    behavior_classification: CustomerBehavior
    anomaly_flags: List[str]
```

### 2. Dwell Analytics

**File**: `backend/app/analytics/dwell_analytics.py`

Advanced dwell time tracking and aggregation.

```python
class DwellAnalytics:
    def record_dwell_session(track_id, zone_id, session, timestamp):
        # Records completed session in zone
        # Updates per-zone, per-customer, and zone-customer metrics
    
    def get_top_zones_by_dwell(top_n):
        # Returns zones ranked by average dwell time
    
    def get_peak_hours(zone_id):
        # Returns hourly dwell time distribution
    
    def get_engagement_rate(zone_id, threshold_seconds):
        # Percentage of visitors with sufficient engagement time
```

**Metrics Tracked**:
- Per-zone: total time, visit count, avg/min/max duration, standard deviation
- Per-customer: total time, zones visited, engagement patterns
- Per-zone-per-customer: zone-specific dwell metrics
- Hourly aggregation: time-of-day heatmaps and peak hours
- Engagement rates: percentage of visitors with high engagement

### 3. Event Intelligence

**File**: `backend/app/events/intelligence.py`

Generates retail intelligence events and anomalies.

```python
class RetailEventIntelligence:
    def generate_interaction_event(...):
        # Creates structured retail event for interactions
    
    def detect_prolonged_engagement(...):
        # Identifies extended customer engagement
    
    def detect_suspicious_behavior(track_id, anomaly_type, confidence, ...):
        # Generates anomaly events for suspicious patterns
    
    def detect_crowd_event(zone_id, customer_count, ...):
        # Detects crowd density events
    
    def detect_loitering(track_id, zone_id, dwell_time, ...):
        # Flags extended loitering behavior
```

**Event Types**:
- `zone_entry`: Customer entered zone
- `zone_exit`: Customer left zone
- `prolonged_engagement`: Extended interaction (>threshold)
- `suspicious_behavior`: Anomalous patterns detected
- `loitering`: Extended presence without engagement
- `crowd_detected`: High density event
- `theft_risk`: Potential merchandise concern

**Anomaly Types**:
- `LOITERING`: Excessive time without interaction
- `SUSPICIOUS_BROWSING`: Unusual interaction patterns
- `RAPID_ZONE_CHANGES`: Abnormal movement patterns
- `REPEATED_ZONE_VISITS`: Excessive revisits to same zone
- `PACKAGE_CONCEALMENT`: Potential concealment detected

### 4. Redis Event Publisher

**File**: `backend/app/events/redis_publisher.py`

Asynchronous Redis Streams integration for event publishing.

```python
class RedisEventPublisher:
    async def publish_interaction(track_id, zone_id, interaction_type, ...):
        # Publishes to retail:interactions stream
    
    async def publish_anomaly(track_id, anomaly_type, confidence, ...):
        # Publishes to retail:anomalies stream
    
    async def publish_crowd_event(zone_id, customer_count, density_level, ...):
        # Publishes to retail:crowd_events stream
    
    async def publish_engagement_metric(...):
        # Publishes to retail:engagement stream
```

**Stream Architecture**:
```
retail:interactions    - Customer-shelf interaction events
retail:anomalies       - Suspicious behavior and alerts
retail:crowd_events    - Crowd density detection events
retail:engagement      - Customer engagement metrics
retail:analytics_metrics - Aggregated store-wide metrics
```

### 5. Analytics Metrics Engine

**File**: `backend/app/analytics/metrics_engine.py`

Aggregates and computes retail analytics metrics.

```python
class AnalyticsMetricsEngine:
    def compute_zone_metrics(zone_id):
        # Returns: ZoneMetrics with engagement, dwell, popularity
    
    def compute_store_metrics():
        # Returns: StoreMetrics with aggregated data
    
    def get_customer_segments():
        # Returns: Dict[segment] = List[track_ids]
        # Segments: browsers, comparers, purchasers, suspicious
    
    def get_movement_patterns():
        # Returns: zone transition graph and statistics
    
    def get_crowd_analysis():
        # Returns: per-zone crowd density patterns
```

**Metrics Computed**:
- Zone engagement rate (% of visitors with high engagement)
- Customer lifetime value (CLV) estimate
- Movement patterns (zone transitions)
- Crowd density analysis
- Peak hours identification
- Popular zone ranking
- Customer behavioral segments

### 6. Enhanced Overlay Renderer

**File**: `backend/app/analytics/overlay_renderer.py`

Visualizes all Phase 4 data on video frames.

```python
class Phase4OverlayRenderer:
    def render_frame(frame, zones, active_tracks, interactions, anomalies, ...):
        # Renders complete analytics overlay
        # Returns: annotated frame
```

**Rendered Elements**:
- Zone polygons with opacity based on crowd
- Track IDs with behavior color coding
- Interaction events (engagement, etc.)
- Anomaly alerts with confidence scores
- Crowd detection warnings
- Dwell time metrics
- Frame info (timestamp, track count)

**Color Coding**:
- Green: Normal browsing
- Magenta: Purchasing behavior
- Cyan: Engagement detected
- Orange: Loitering/suspicion
- Red: Alert/anomaly

### 7. Phase 4 Service Orchestrator

**File**: `backend/app/analytics/service.py`

Main service coordinating all Phase 4 components.

```python
class Phase4Service:
    async def process_frame(frame_index, timestamp, active_tracks, track_bboxes):
        # Main processing pipeline
        # 1. Process interactions per track
        # 2. Update customer profiles
        # 3. Check for anomalies
        # 4. Detect crowd events
        # 5. Flush events to Redis
        # 6. Cleanup inactive sessions
```

---

## Event Intelligence System

### Event Generation Pipeline

```
Interaction Detection
    ├─ zone_entry → RetailEvent
    ├─ zone_exit → RetailEvent
    └─ engagement → RetailEvent
            ↓
    Check for Anomalies
    ├─ loitering → AnomalyEvent
    ├─ suspicious_pattern → AnomalyEvent
    └─ rapid_movement → AnomalyEvent
            ↓
    Buffer Events
    └─ EventBuffer (batch mode)
            ↓
    Publish to Redis
    └─ XADD to appropriate stream
```

### Event Structure

```python
@dataclass
class RetailEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    track_id: Optional[int]
    zone_id: Optional[str]
    severity: EventSeverity  # info, warning, alert, critical
    message: str
    payload: Dict[str, Any]  # Event-specific data
    frame_index: int

@dataclass
class AnomalyEvent:
    anomaly_id: str
    track_id: int
    anomaly_type: str
    confidence: float
    timestamp: datetime
    zone_id: Optional[str]
    description: str
    metadata: Dict[str, Any]
```

### Event Publishing Strategy

**Batching**:
- Events buffered in memory
- Flush when buffer reaches `batch_size` (default: 50)
- Or flush after `batch_timeout_ms` (default: 1000ms)
- Reduces Redis write operations

**Retry Logic**:
- Configurable retry count (default: 3)
- Exponential backoff with configurable delay
- Failed events buffered for later retry

**Buffering**:
- Circular buffer (max 1000 events)
- Automatic persistence to file on overflow
- Replay on reconnection

---

## Redis Integration

### Stream Architecture

#### retail:interactions
Stores interaction events from customers.

**Schema**:
```json
{
  "track_id": "1",
  "zone_id": "dairy_shelf_1",
  "interaction_type": "zone_entry",
  "timestamp": "2024-01-15T10:30:45Z",
  "duration": "0",
  "confidence": "0.95",
  "intensity": "0.5"
}
```

**Consumer Pattern**:
```
Dashboard → Subscribe to retail:interactions
Analytics Engine → Aggregate interactions
Alert System → Filter high-confidence anomalies
```

#### retail:anomalies
Stores detected anomalies and suspicious behaviors.

**Schema**:
```json
{
  "track_id": "2",
  "anomaly_type": "loitering",
  "confidence": "0.85",
  "timestamp": "2024-01-15T10:35:20Z",
  "zone_id": "dairy_shelf_1",
  "description": "Customer loitering for 120+ seconds"
}
```

**Alert Thresholds**:
- `confidence > 0.8`: Alert level (red)
- `0.6 < confidence <= 0.8`: Warning level (yellow)
- `confidence <= 0.6`: Info level (blue)

#### retail:crowd_events
Stores crowd detection events.

**Schema**:
```json
{
  "zone_id": "checkout",
  "customer_count": "8",
  "density_level": "high",
  "timestamp": "2024-01-15T10:45:00Z"
}
```

**Density Levels**:
- High: customer_count > crowd_threshold × 2
- Medium: customer_count > crowd_threshold
- Low: customer_count <= crowd_threshold

#### retail:engagement
Stores customer engagement metrics.

**Schema**:
```json
{
  "track_id": "1",
  "zone_id": "dairy_shelf_1",
  "engagement_score": "0.85",
  "interaction_count": "5",
  "dwell_time": "45.3",
  "behavior_type": "comparing",
  "timestamp": "2024-01-15T10:50:12Z"
}
```

#### retail:analytics_metrics
Stores aggregated metrics (hourly/daily).

**Schema**:
```json
{
  "zone_metrics": "{...}",
  "store_metrics": "{...}",
  "timestamp": "2024-01-15T11:00:00Z"
}
```

### Consumer Implementation

**Python Consumer**:
```python
import redis

r = redis.Redis(host='localhost', port=6379)

# Read from interaction stream
events = r.xread({'retail:interactions': '0'}, block=0, count=10)

for stream, data in events:
    for event_id, event_data in data:
        print(f"Interaction: {event_data}")
```

**Stream Commands**:
```bash
# List all events in stream
redis-cli XRANGE retail:interactions - +

# Get recent events
redis-cli XREVRANGE retail:interactions + - COUNT 20

# Get stream length
redis-cli XLEN retail:interactions

# Trim stream to 10000 entries
redis-cli XTRIM retail:interactions MAXLEN 10000
```

---

## Analytics Metrics

### Zone-Level Metrics

```python
@dataclass
class ZoneMetrics:
    zone_id: str
    name: str
    total_visits: int                  # Number of times zone was entered
    total_interactions: int             # Total interaction events
    average_dwell_time: float          # Avg time per visit (seconds)
    max_dwell_time: float              # Maximum dwell time
    min_dwell_time: float              # Minimum dwell time
    unique_customers: int               # Unique customers visited
    engagement_rate: float              # % of visitors with high engagement
    peak_hours: List[int]              # Hours with most activity
```

### Store-Level Metrics

```python
@dataclass
class StoreMetrics:
    total_customers: int                # Unique customers observed
    average_store_time: float          # Avg time in store (seconds)
    popular_zones: List[str]           # Top 5 visited zones
    total_interactions: int             # Total interactions recorded
    anomaly_count: int                 # Anomalies detected
    crowd_events: int                  # Crowd detection events
    peak_hours: List[int]              # Peak hours overall
    zone_metrics: Dict[str, ZoneMetrics]
```

### Derived Metrics

**Engagement Rate**:
```
engagement_rate = (visitors_with_dwell > threshold) / total_visitors * 100
```

**Customer Lifetime Value (CLV)**:
```
clv_score = (zones_visited × interaction_count) / (avg_store_time / 60)
```

**Zone Popularity Score**:
```
popularity = (total_visits + engagement_rate) / 2
```

**Movement Pattern Score**:
```
For each customer:
  Calculate zone sequence
  Score based on: direct path, backtracking, clustering
```

---

## Configuration Guide

### Main Configuration File

**File**: `backend/scripts/phase4_config.json`

```json
{
  "analytics": {
    "interaction": {
      "min_engagement_duration": 2.0,
      "max_quick_browse_duration": 5.0,
      "min_comparing_duration": 10.0,
      "pickup_distance_threshold": 50,
      "suspicious_behavior_threshold": 0.8,
      "crowd_threshold": 5
    },
    "dwell_analytics": {
      "min_dwell_time": 1.0,
      "max_session_gap": 5.0,
      "aggregate_intervals": [60, 300, 3600],
      "track_history_size": 1000
    },
    "event_publishing": {
      "publish_interactions": true,
      "publish_anomalies": true,
      "publish_analytics": true,
      "batch_events": true,
      "batch_size": 50,
      "batch_timeout_ms": 1000,
      "retry_count": 3,
      "retry_delay_ms": 100
    },
    "overlay": {
      "show_zones": true,
      "show_interactions": true,
      "show_dwell_time": true,
      "show_alerts": true,
      "show_behavior": true,
      "zone_opacity": 0.3,
      "interaction_radius": 10,
      "text_scale": 0.6
    },
    "anomaly_detection_enabled": true,
    "crowd_detection_enabled": true,
    "heatmap_enabled": true,
    "log_level": "INFO"
  },
  "shelf_zones": [
    {
      "zone_id": "dairy_shelf_1",
      "name": "Dairy Section - Top Shelf",
      "store_section": "dairy",
      "shelf_level": "top",
      "polygon": [[100, 100], [400, 100], [400, 200], [100, 200]],
      "category": "milk",
      "product_count": 15
    }
  ],
  "redis": {
    "url": "redis://localhost:6379"
  }
}
```

### Zone Configuration

Each zone requires:
- **zone_id**: Unique identifier
- **name**: Display name
- **polygon**: List of [x, y] coordinates defining zone boundary
- **store_section**: Logical section (dairy, produce, etc.)
- **shelf_level**: top, middle, bottom, endcap
- **category**: Product category
- **product_count**: Number of items

### Interaction Thresholds

- **min_engagement_duration** (2.0s): Minimum time to classify as engagement
- **min_comparing_duration** (10.0s): Minimum time to classify as comparing
- **suspicious_behavior_threshold** (0.8): Confidence threshold for anomalies
- **crowd_threshold** (5): Minimum customers for crowd event

### Event Publishing Configuration

- **batch_size** (50): Number of events to batch before publishing
- **batch_timeout_ms** (1000): Max time to wait before flushing batch
- **retry_count** (3): Max retry attempts for failed publishes
- **retry_delay_ms** (100): Delay between retries

---

## API Reference

### Base URL
```
http://localhost:8000/api/v1/phase4
```

### Endpoints

#### GET /interactions
Get recent interactions.

**Query Parameters**:
- `track_id` (optional): Filter by track ID
- `zone_id` (optional): Filter by zone ID
- `limit` (optional, default: 100): Max results

**Response**:
```json
[
  {
    "event_id": "...",
    "event_type": "zone_entry",
    "track_id": 1,
    "zone_id": "dairy_shelf_1",
    "timestamp": "2024-01-15T10:30:45Z",
    "duration": 0,
    "confidence": 0.95
  }
]
```

#### GET /interactions/{track_id}
Get interactions for specific customer.

**Response**:
```json
{
  "track_id": 1,
  "total_interactions": 5,
  "zones_visited": ["dairy_shelf_1", "dairy_shelf_2"],
  "duration_in_store": 185.4,
  "behavior": "comparing",
  "interactions": [...]
}
```

#### GET /analytics
Get analytics snapshot.

**Response**:
```json
{
  "timestamp": "2024-01-15T10:55:00Z",
  "total_customers": 42,
  "total_interactions": 156,
  "zone_metrics": {...},
  "anomalies": [...]
}
```

#### GET /analytics/zones/{zone_id}
Get detailed analytics for a zone.

**Response**:
```json
{
  "zone_id": "dairy_shelf_1",
  "metrics": {
    "total_visits": 45,
    "unique_customers": 23,
    "average_dwell_time": 15.3,
    "engagement_rate": 0.68
  },
  "heatmap": {"hour_9": 5, "hour_10": 12, ...}
}
```

#### GET /analytics/customers/{track_id}
Get customer-specific analytics.

#### GET /dwell/zones/{zone_id}
Get dwell metrics for a zone.

#### GET /anomalies
Get detected anomalies.

#### GET /statistics
Get service statistics.

### Response Codes

- `200`: Success
- `404`: Resource not found
- `500`: Server error

---

## Running the System

### Prerequisites

1. **Python 3.8+**
2. **Redis Server** (optional for event publishing)
3. **CUDA 11.8+** (recommended for GPU acceleration)

### Dependencies

```bash
pip install -r requirements.txt
```

**Additional for Phase 4**:
```bash
pip install redis==5.0.1
pip install opencv-python==4.8.1.78
```

### Configuration

1. Copy template configuration:
```bash
cp backend/scripts/phase4_config.json.template backend/scripts/phase4_config.json
```

2. Edit zones in configuration file with your store layout

3. Adjust thresholds based on your store characteristics

### Running the Pipeline

#### Full Pipeline (Phase 3 + Phase 4)

```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source <video_file_or_camera_index> \
  --max-frames 3600 \
  --log-level INFO
```

**Example with Camera**:
```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source 0 \
  --log-level DEBUG
```

**Example with Video File**:
```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source /path/to/store_video.mp4 \
  --max-frames 10000 \
  --output /path/to/annotated_output.mp4
```

### Running Tests

```bash
python backend/scripts/test_phase4.py
```

**Expected Output**:
```
==================================================
PHASE 4 TEST SUITE
==================================================

✓ Interaction Detection: PASS
✓ Dwell Analytics: PASS
✓ Event Intelligence: PASS
✓ Anomaly Detection: PASS
✓ Metrics Engine: PASS
✓ Overlay Rendering: PASS
✓ Crowd Detection: PASS
✓ Redis Publisher: PASS

==================================================
TEST SUMMARY
==================================================
Total: 8 passed, 0 failed
```

### API Server

```bash
# Start FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Access API documentation
# http://localhost:8000/docs
```

### Monitoring Events

```bash
# Monitor interactions stream
redis-cli XREAD BLOCK 0 STREAMS retail:interactions $

# Monitor anomalies stream
redis-cli XREAD BLOCK 0 STREAMS retail:anomalies $

# Get summary
redis-cli INFO stats
```

---

## Performance Optimization

### Frame Processing Optimization

| Configuration | FPS | Latency | Memory |
|---|---|---|---|
| YOLOv11 Nano | 60+ | <17ms | ~400MB |
| YOLOv11 Small | 45-50 | <22ms | ~600MB |
| YOLOv11 Medium | 25-30 | <33ms | ~1GB |

### Batch Event Publishing

**Without Batching**:
- Redis writes/sec: 30-50
- CPU overhead: High

**With Batching (50 events, 1000ms timeout)**:
- Redis writes/sec: 3-5
- CPU overhead: Low
- Throughput: 3000-5000 events/sec

### Memory Optimization

- Circular event buffer (max 1000)
- Periodic cleanup of inactive sessions
- Configurable history retention
- Zone session caching

### Database Optimization

**Streaming Trimming**:
```python
# Auto-trim streams to prevent overflow
async def trim_streams():
    for stream in ['retail:interactions', 'retail:anomalies', ...]:
        await publisher.trim_stream(stream, max_len=10000)
```

### Parallelization

- Frame processing: Sequential (per-frame dependencies)
- Event publishing: Async with batching
- Redis writes: Batched async writes
- Metrics computation: Incremental per-frame

### Profiling

```bash
# Profile frame processing
python -m cProfile -s cumtime backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source test_video.mp4 \
  --max-frames 300

# Memory profiling
python -m memory_profiler backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source test_video.mp4
```

---

## Next Steps

1. **Dashboard Integration**: Build real-time dashboard consuming Redis streams
2. **ML Enhancement**: Add predictive models for customer behavior
3. **Multi-Store Support**: Extend to handle multiple store locations
4. **Advanced Analytics**: Add pattern mining and forecasting
5. **Mobile App**: Real-time alerts and insights on mobile

---

## Support & Troubleshooting

### Common Issues

1. **Redis Connection Failed**:
   ```bash
   # Check Redis server
   redis-cli ping
   
   # Start Redis if needed
   redis-server
   ```

2. **Low FPS**:
   - Use smaller YOLO model (nano/small)
   - Enable GPU acceleration
   - Reduce zone count
   - Lower confidence thresholds

3. **Memory Leaks**:
   - Monitor cleanup_inactive_sessions
   - Check circular buffer size limits
   - Enable periodic metrics export

### Debugging

Enable debug logging:
```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source test.mp4 \
  --log-level DEBUG
```

Check system statistics:
```python
from backend.app.analytics.service import get_phase4_service

service = get_phase4_service()
print(service.get_statistics())
```

---

## References

- [YOLOv11 Documentation](https://github.com/ultralytics/ultralytics)
- [ByteTrack Paper](https://arxiv.org/abs/2110.06864)
- [Redis Streams](https://redis.io/topics/streams-intro)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

