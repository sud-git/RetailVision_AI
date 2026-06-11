# Phase 4: Exact Working Commands
## Copy & Paste Ready Commands for RetailVision AI

**Last Updated**: May 2026

---

## Quick Start (5 Minutes)

### 1. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or if installed locally
redis-server &

# Verify
redis-cli ping
```

**Expected Output**:
```
PONG
```

### 2. Run Tests

```bash
cd backend
python scripts/test_phase4.py
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
✓ Redis Publisher: PASS
✓ Overlay Rendering: PASS

==================================================
TEST SUMMARY
==================================================
Total: 6 passed, 0 failed
Time: 2.34s

✅ All Phase 4 tests PASSED
```

### 3. Run Pipeline (Simple)

```bash
# Using test video file
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source backend/scripts/test_video.mp4 \
  --max-frames 3600
```

**Expected Output**:
```
2024-05-15 10:30:45,123 - INFO - Initializing Phase 3 Detection Service...
2024-05-15 10:30:46,234 - INFO - Initializing Phase 4 Analytics Service...
2024-05-15 10:30:47,345 - INFO - Initializing Video Ingestion Service...
2024-05-15 10:30:48,456 - INFO - ✓ All services initialized
2024-05-15 10:30:50,567 - INFO - Starting video processing...
2024-05-15 10:30:50,678 - INFO - Frame 0: 0 detections, 0 interactions
2024-05-15 10:30:51,789 - INFO - Frame 30: 5 detections, 3 interactions
2024-05-15 10:30:52,890 - INFO - Frame 60: 5 detections, 5 interactions
...
```

---

## Full Production Setup (15 Minutes)

### Step 1: Navigate to Project

```bash
cd /path/to/RetailVision\ AI
```

### Step 2: Start Services (Docker Compose)

```bash
# Start all services
docker-compose -f docker-compose.yml up -d

# Or for development
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose ps
```

**Expected Output**:
```
NAME                 STATUS              PORTS
retailvision-backend  Up 2 minutes       0.0.0.0:8000->8000/tcp
retailvision-redis    Up 2 minutes       0.0.0.0:6379->6379/tcp
retailvision-db       Up 2 minutes       0.0.0.0:5432->5432/tcp
retailvision-frontend Up 2 minutes       0.0.0.0:3000->3000/tcp
```

### Step 3: Verify Services

```bash
# API Health
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Redis
redis-cli PING

# Database
psql -h localhost -U retailvision
```

### Step 4: Run Phase 4 Pipeline

```bash
# Option A: From Host (if dependencies installed)
cd backend
python scripts/start_phase4_pipeline.py \
  --config scripts/phase4_config.json \
  --source 0 \
  --display true

# Option B: From Docker
docker exec -it retailvision-backend python scripts/start_phase4_pipeline.py \
  --config scripts/phase4_config.json \
  --source /path/to/video.mp4 \
  --max-frames 10000
```

### Step 5: Monitor Events (New Terminal)

```bash
# Watch interactions
redis-cli XREAD BLOCK 0 STREAMS retail:interactions $

# In another terminal, watch anomalies
redis-cli XREAD BLOCK 0 STREAMS retail:anomalies $
```

**Expected Event Output**:
```
1) 1) "retail:interactions"
   2) 1) 1) "1715858045123-0"
         2) "track_id"
            "1"
            "zone_id"
            "dairy_shelf_1"
            "interaction_type"
            "zone_entry"
            "timestamp"
            "2024-05-15T10:30:45.123Z"
            "confidence"
            "0.95"
```

---

## Common Scenarios

### Scenario 1: Test with Webcam (Real-Time)

```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source 0 \
  --display true \
  --log-level DEBUG
```

**Keys**:
- `q` - Quit
- `p` - Pause/Resume
- `s` - Save current frame

### Scenario 2: Process RTSP Stream

```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source "rtsp://192.168.1.100:554/stream" \
  --display false \
  --log-level INFO
```

### Scenario 3: Batch Video Processing

```bash
# Process video and save output
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source input_video.mp4 \
  --output output_annotated.mp4 \
  --max-frames 108000 \
  --log-level INFO

# Play result
ffplay output_annotated.mp4
```

### Scenario 4: Process Multiple Videos

```bash
#!/bin/bash
for video in videos/*.mp4; do
  echo "Processing: $video"
  python backend/scripts/start_phase4_pipeline.py \
    --config backend/scripts/phase4_config.json \
    --source "$video" \
    --output "output_$(basename $video)" \
    --max-frames 50000 \
    --log-level INFO
done
```

### Scenario 5: Extract Statistics

```bash
# Get store metrics
curl http://localhost:8000/api/v1/analytics/store

# Get zone metrics
curl http://localhost:8000/api/v1/analytics/zones/dairy_shelf_1

# Get customer interactions
curl http://localhost:8000/api/v1/analytics/interactions?limit=50

# Get anomalies
curl http://localhost:8000/api/v1/analytics/anomalies
```

---

## Redis Monitoring Commands

### Watch Events in Real-Time

```bash
# All interactions (follow)
redis-cli XREAD BLOCK 0 STREAMS retail:interactions $

# All anomalies (follow)
redis-cli XREAD BLOCK 0 STREAMS retail:anomalies $

# All crowd events (follow)
redis-cli XREAD BLOCK 0 STREAMS retail:crowd_events $

# All engagement metrics (follow)
redis-cli XREAD BLOCK 0 STREAMS retail:engagement $

# All analytics metrics (follow)
redis-cli XREAD BLOCK 0 STREAMS retail:analytics_metrics $
```

### Get Recent Events

```bash
# Last 20 interactions
redis-cli XREVRANGE retail:interactions + - COUNT 20

# Last 10 anomalies
redis-cli XREVRANGE retail:anomalies + - COUNT 10

# Last 5 crowd events
redis-cli XREVRANGE retail:crowd_events + - COUNT 5

# All events in stream
redis-cli XRANGE retail:interactions - +
```

### Stream Info

```bash
# Count interactions
redis-cli XLEN retail:interactions

# Count anomalies
redis-cli XLEN retail:anomalies

# Count crowd events
redis-cli XLEN retail:crowd_events

# Stream info
redis-cli XINFO STREAM retail:interactions

# Consumer groups
redis-cli XINFO GROUPS retail:interactions
```

### Stream Maintenance

```bash
# Trim streams to max 10000 entries
redis-cli XTRIM retail:interactions MAXLEN 10000
redis-cli XTRIM retail:anomalies MAXLEN 10000
redis-cli XTRIM retail:crowd_events MAXLEN 10000

# Clear all streams
redis-cli FLUSHDB

# Check memory usage
redis-cli INFO memory
redis-cli MEMORY STATS
```

---

## API Commands

### Health & Status

```bash
# API health check
curl http://localhost:8000/health

# API ready check
curl http://localhost:8000/ready

# API docs
open http://localhost:8000/docs
```

### Analytics Endpoints

```bash
# Get store metrics
curl http://localhost:8000/api/v1/analytics/store

# Get zone metrics (replace zone_id)
curl http://localhost:8000/api/v1/analytics/zones/dairy_shelf_1

# Get zone metrics (all zones)
for zone in dairy_shelf_1 dairy_shelf_2 produce_display checkout; do
  curl http://localhost:8000/api/v1/analytics/zones/$zone | jq .
done

# Get recent interactions (limit 20)
curl "http://localhost:8000/api/v1/analytics/interactions?limit=20"

# Get interactions for specific customer
curl "http://localhost:8000/api/v1/analytics/interactions/1"

# Get interactions for specific zone
curl "http://localhost:8000/api/v1/analytics/interactions?zone_id=dairy_shelf_1"

# Get anomalies
curl http://localhost:8000/api/v1/analytics/anomalies

# Get events summary
curl http://localhost:8000/api/v1/analytics/events
```

### Pretty Print JSON

```bash
# Add jq for readable output
curl http://localhost:8000/api/v1/analytics/store | jq .

# Save to file
curl http://localhost:8000/api/v1/analytics/store | jq . > metrics.json

# Filter specific fields
curl http://localhost:8000/api/v1/analytics/store | jq '.zone_metrics | keys'
```

---

## Debugging & Troubleshooting

### Enable Debug Logging

```bash
# Method 1: Command line
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source 0 \
  --log-level DEBUG

# Method 2: Update config
# Edit backend/scripts/phase4_config.json
# Set "log_level": "DEBUG"
```

### Check Redis Connection

```bash
# Test connection
python -c "
import redis
r = redis.Redis.from_url('redis://localhost:6379')
print('Connection test:', r.ping())
print('Redis info:', r.info()['redis_version'])
"

# Monitor Redis activity
redis-cli MONITOR

# Check Redis memory
redis-cli MEMORY USAGE retail:interactions
```

### Check GPU/CUDA

```bash
# Check GPU availability
python -c "
import torch
print('CUDA available:', torch.cuda.is_available())
print('CUDA devices:', torch.cuda.device_count())
if torch.cuda.is_available():
    print('GPU:', torch.cuda.get_device_name(0))
"

# Monitor GPU in real-time
nvidia-smi watch -n 1

# Check GPU memory
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,nounits,noheader
```

### Check Disk Space

```bash
# Check available disk
df -h

# Check specific directory
du -sh backend/
du -sh frontend/

# Find large files
find . -type f -size +100M
```

### System Resource Monitor

```bash
# CPU & Memory
top -p $(pgrep -f start_phase4_pipeline.py)

# Process list
ps aux | grep start_phase4_pipeline

# Kill process
kill $(pgrep -f start_phase4_pipeline.py)

# Watch system resources
watch -n 1 'ps aux | grep start_phase4_pipeline'
```

### Docker Commands

```bash
# View logs
docker-compose logs -f backend

# Execute command in container
docker exec -it retailvision-backend bash

# Check container status
docker-compose ps

# Restart specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Clean up (warning: removes data)
docker-compose down -v
```

---

## Event Examples

### Zone Entry Event

```json
{
  "stream_id": "1715858045123-0",
  "data": {
    "track_id": "1",
    "zone_id": "dairy_shelf_1",
    "interaction_type": "zone_entry",
    "timestamp": "2024-05-15T10:30:45.123Z",
    "duration": "0",
    "confidence": "0.95",
    "intensity": "0.5"
  }
}
```

### Engagement Event

```json
{
  "stream_id": "1715858047456-1",
  "data": {
    "track_id": "1",
    "zone_id": "dairy_shelf_1",
    "interaction_type": "engagement",
    "timestamp": "2024-05-15T10:30:50.456Z",
    "duration": "5.2",
    "confidence": "0.88",
    "intensity": "0.7"
  }
}
```

### Anomaly Event

```json
{
  "stream_id": "1715858052789-2",
  "data": {
    "track_id": "2",
    "anomaly_type": "loitering",
    "confidence": "0.85",
    "timestamp": "2024-05-15T10:35:52.789Z",
    "zone_id": "dairy_shelf_1",
    "description": "Customer loitering for 120+ seconds without engagement"
  }
}
```

### Crowd Event

```json
{
  "stream_id": "1715858055012-3",
  "data": {
    "zone_id": "checkout",
    "customer_count": "8",
    "density_level": "high",
    "timestamp": "2024-05-15T10:40:55.012Z"
  }
}
```

### Store Metrics

```json
{
  "stream_id": "1715858058335-4",
  "data": {
    "timestamp": "2024-05-15T11:00:00Z",
    "total_customers": 42,
    "average_store_time": 185.4,
    "popular_zones": ["checkout", "dairy_shelf_1", "produce_display"],
    "total_interactions": 156,
    "anomaly_count": 3,
    "crowd_events": 2
  }
}
```

---

## Python Examples

### Read Events Programmatically

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get recent interactions
interactions = r.xrevrange('retail:interactions', count=10)
for msg_id, msg_data in interactions:
    event = json.loads(msg_data['data']) if isinstance(msg_data.get('data'), str) else msg_data
    print(f"Track {event.get('track_id')} {event.get('interaction_type')} in {event.get('zone_id')}")

# Get anomalies
anomalies = r.xrevrange('retail:anomalies', count=5)
for msg_id, msg_data in anomalies:
    event = json.loads(msg_data['data']) if isinstance(msg_data.get('data'), str) else msg_data
    print(f"Anomaly: {event.get('anomaly_type')} (confidence: {event.get('confidence')})")
```

### Consume Events in Real-Time

```python
import redis
import json
import time

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def consume_events(stream='retail:interactions', timeout=300):
    last_id = '0'
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        messages = r.xread({stream: last_id}, block=1000)
        
        if messages:
            for stream_name, data in messages:
                for msg_id, msg_data in data:
                    event = json.loads(msg_data['data'])
                    print(f"[{msg_id}] {event}")
                    last_id = msg_id
        else:
            print("No new events...")

# Usage
consume_events()
```

### Export Events to CSV

```python
import redis
import json
import csv

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Export interactions to CSV
interactions = r.xrange('retail:interactions')
with open('interactions.csv', 'w', newline='') as f:
    if interactions:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'track_id', 'zone_id', 'type'])
        writer.writeheader()
        
        for msg_id, msg_data in interactions:
            event = json.loads(msg_data['data'])
            writer.writerow({
                'timestamp': event.get('timestamp'),
                'track_id': event.get('track_id'),
                'zone_id': event.get('zone_id'),
                'type': event.get('interaction_type')
            })

print("Exported interactions to interactions.csv")
```

---

## Performance Testing

### Measure FPS

```bash
# Run with FPS output
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source test.mp4 \
  --max-frames 3000 \
  --log-level INFO | grep -i fps
```

### Profile CPU Usage

```bash
# Python profiler
python -m cProfile -s cumtime backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source test.mp4 \
  --max-frames 300 | head -20
```

### Monitor Memory

```bash
# Top monitoring (in another terminal)
watch -n 1 'top -p $(pgrep -f start_phase4_pipeline.py) -b -n 1'

# Or python memory profiler
pip install memory-profiler
python -m memory_profiler backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source test.mp4 \
  --max-frames 100
```

---

## Common Errors & Solutions

### Error: "Redis connection refused"

```bash
# Solution 1: Start Redis
redis-server &

# Solution 2: Start Redis in Docker
docker run -d -p 6379:6379 redis:7-alpine

# Verify
redis-cli PING  # Should output: PONG
```

### Error: "No module named 'ultralytics'"

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Or individual package
pip install ultralytics
```

### Error: "CUDA out of memory"

```bash
# Solution 1: Use CPU
# Edit config, set gpu_device_id: -1

# Solution 2: Use smaller model
# Edit config, set model_size: "n"  # nano instead of small/medium

# Solution 3: Clear cache
python -c "import torch; torch.cuda.empty_cache()"
```

### Error: "Video file not found"

```bash
# Verify file path
ls -lh /path/to/video.mp4

# Use absolute path
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source /absolute/path/to/video.mp4
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `redis-cli XLEN retail:interactions` | Count interactions |
| `redis-cli XREVRANGE retail:anomalies + - COUNT 10` | Get recent anomalies |
| `curl http://localhost:8000/api/v1/analytics/store` | Get store metrics |
| `python scripts/test_phase4.py` | Run all tests |
| `docker-compose ps` | Check service status |
| `docker-compose logs -f backend` | View backend logs |

---

**Phase 4: Ready to Deploy** ✅
✓ Crowd Detection: PASS
✓ Redis Publisher: PASS

==================================================
TEST SUMMARY
==================================================
Total: 8 passed, 0 failed
==================================================
```

---

## Running the Pipeline

### Command 1: Basic Pipeline with Video File

```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source backend/test_data/sample_store_video.mp4 \
  --max-frames 1000 \
  --log-level INFO
```

**What it does**:
- Loads configuration from `phase4_config.json`
- Processes up to 1000 frames from video file
- Initializes Phase 3 detection + Phase 4 analytics
- Processes frames in real-time
- Publishes events to Redis
- Displays progress every 30 frames

### Command 2: Live Camera Input

```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source 0 \
  --log-level INFO
```

**Parameters**:
- `--source 0`: Use default camera (change to 1, 2, etc. for other cameras)
- `--config`: Path to configuration file
- `--log-level INFO`: Verbose logging

**Exit**: Press `q` in the display window

### Command 3: Save Annotated Output

```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source backend/test_data/sample_video.mp4 \
  --output backend/output/annotated_output.mp4 \
  --max-frames 5000
```

**Creates**: Annotated video with overlays at `backend/output/annotated_output.mp4`

### Command 4: Debug Mode with Detailed Logging

```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source backend/test_data/store_footage.mp4 \
  --max-frames 2000 \
  --log-level DEBUG
```

**Output includes**:
- Frame-by-frame processing details
- Interaction detection debug info
- Event publishing status
- Anomaly detection scoring

### Command 5: Process Multiple Videos Sequentially

```bash
# Create batch processing script
cat > process_videos.sh << 'EOF'
#!/bin/bash

for video in backend/test_data/*.mp4; do
  echo "Processing: $video"
  python backend/scripts/start_phase4_pipeline.py \
    --config backend/scripts/phase4_config.json \
    --source "$video" \
    --output "backend/output/$(basename $video)" \
    --max-frames 3600 \
    --log-level INFO
done
EOF

# Make executable and run
chmod +x process_videos.sh
./process_videos.sh
```

---

## API Server Commands

### Command 1: Start FastAPI Server

```bash
cd backend
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --log-level info
```

**Access**:
- API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Command 2: Run with Production Settings

```bash
cd backend
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --log-level warning
```

### Command 3: Query Endpoints

```bash
# Get analytics snapshot
curl http://localhost:8000/api/v1/phase4/analytics

# Get specific zone analytics
curl http://localhost:8000/api/v1/phase4/analytics/zones/dairy_shelf_1

# Get customer profile
curl http://localhost:8000/api/v1/phase4/analytics/customers/1

# Get recent anomalies
curl http://localhost:8000/api/v1/phase4/anomalies?limit=20

# Get interactions
curl http://localhost:8000/api/v1/phase4/interactions?limit=50

# Get service statistics
curl http://localhost:8000/api/v1/phase4/statistics
```

### Command 4: Pretty-Print JSON Responses

```bash
# Get analytics and format nicely
curl http://localhost:8000/api/v1/phase4/analytics | python -m json.tool

# Get specific zone with formatting
curl http://localhost:8000/api/v1/phase4/analytics/zones/dairy_shelf_1 | python -m json.tool

# Get with jq (if installed)
curl http://localhost:8000/api/v1/phase4/analytics | jq '.store_metrics | keys'
```

### Command 5: Export Metrics

```bash
# Export current metrics snapshot
curl http://localhost:8000/api/v1/phase4/export \
  -H "Content-Type: application/json" \
  > metrics_snapshot.json

# View the exported data
cat metrics_snapshot.json | python -m json.tool
```

---

## Redis Stream Commands

### Command 1: Monitor Interactions in Real-Time

```bash
# Watch interaction stream live
redis-cli XREAD BLOCK 0 STREAMS retail:interactions $
```

**Output**:
```
Reading messages... (press Ctrl-C to quit)
1705325445000-0
 1) "retail:interactions"
 2) 1) 1) "1705325445000-0"
       2) 1) "track_id"
          2) "1"
          3) "zone_id"
          4) "dairy_shelf_1"
          5) "interaction_type"
          6) "zone_entry"
          ...
```

### Command 2: Monitor Anomalies

```bash
redis-cli XREAD BLOCK 0 STREAMS retail:anomalies $
```

### Command 3: Get Recent Events from Stream

```bash
# Last 10 interaction events
redis-cli XREVRANGE retail:interactions + - COUNT 10

# Last 5 anomalies with full details
redis-cli XREVRANGE retail:anomalies + - COUNT 5

# All events from last hour (approximate)
redis-cli XRANGE retail:interactions "-" "+"
```

### Command 4: Stream Statistics

```bash
# Get interaction stream length
redis-cli XLEN retail:interactions

# Get anomaly stream length
redis-cli XLEN retail:anomalies

# Get all stream lengths
redis-cli COMMAND INFO XLEN
redis-cli KEYS "retail:*" | xargs -I {} redis-cli XLEN {}
```

### Command 5: Clean up Old Streams

```bash
# Trim interaction stream to last 10000 entries
redis-cli XTRIM retail:interactions MAXLEN 10000

# Trim all streams
for stream in $(redis-cli KEYS "retail:*"); do
  redis-cli XTRIM "$stream" MAXLEN 10000
done

# Delete entire stream
redis-cli DEL retail:interactions
```

### Command 6: Consumer Groups (Advanced)

```bash
# Create consumer group for interactions
redis-cli XGROUP CREATE retail:interactions mygroup $ MKSTREAM

# Read as consumer
redis-cli XREADGROUP GROUP mygroup consumer1 STREAMS retail:interactions >

# Acknowledge processing
redis-cli XACK retail:interactions mygroup <message-id>
```

---

## Configuration Management

### Command 1: Validate Configuration

```bash
python -c "
import json
with open('backend/scripts/phase4_config.json') as f:
    config = json.load(f)
    print('Configuration valid!')
    print(f'Zones: {len(config[\"shelf_zones\"])}')
    print(f'Redis URL: {config[\"redis\"][\"url\"]}')
"
```

### Command 2: Generate Configuration Template

```bash
python << 'EOF'
import json

template = {
    "analytics": {
        "interaction": {
            "min_engagement_duration": 2.0,
            "max_quick_browse_duration": 5.0,
            "min_comparing_duration": 10.0,
            "pickup_distance_threshold": 50,
            "putback_confidence_threshold": 0.7,
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
            "publish_interactions": True,
            "publish_anomalies": True,
            "publish_analytics": True,
            "batch_events": True,
            "batch_size": 50,
            "batch_timeout_ms": 1000,
            "retry_count": 3,
            "retry_delay_ms": 100
        },
        "overlay": {
            "show_zones": True,
            "show_interactions": True,
            "show_dwell_time": True,
            "show_alerts": True,
            "show_behavior": True,
            "zone_opacity": 0.3
        }
    }
}

with open('backend/scripts/phase4_config_template.json', 'w') as f:
    json.dump(template, f, indent=2)
print("Template created!")
EOF
```

---

## Data Analysis Commands

### Command 1: Export and Analyze Interaction Data

```bash
python << 'EOF'
import redis
import json
from datetime import datetime

r = redis.Redis(host='localhost', port=6379)

# Get all interactions
interactions = []
cursor = 0
while True:
    cursor, keys = r.scan(cursor, match='retail:interactions*', count=100)
    for key in keys:
        for event_id, data in r.xrange(key):
            interactions.append(data)
    if cursor == 0:
        break

# Analyze
zones = {}
for interaction in interactions:
    zone = interaction.get(b'zone_id', b'unknown').decode()
    zones[zone] = zones.get(zone, 0) + 1

print("Zone interactions summary:")
for zone, count in sorted(zones.items(), key=lambda x: x[1], reverse=True):
    print(f"  {zone}: {count} interactions")
EOF
```

### Command 2: Generate Anomaly Report

```bash
python << 'EOF'
import redis
from collections import defaultdict

r = redis.Redis(host='localhost', port=6379)

# Count anomalies by type
anomaly_types = defaultdict(int)
for event_id, data in r.xrange('retail:anomalies'):
    anomaly_type = data.get(b'anomaly_type', b'unknown').decode()
    anomaly_types[anomaly_type] += 1

print("Anomaly Summary:")
for atype, count in sorted(anomaly_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {atype}: {count}")
EOF
```

### Command 3: Customer Behavior Analysis

```bash
python << 'EOF'
import redis
from collections import defaultdict

r = redis.Redis(host='localhost', port=6379)

# Track customer behavior
customer_behavior = defaultdict(lambda: {"zones": set(), "events": 0})
for event_id, data in r.xrange('retail:interactions'):
    track_id = data.get(b'track_id', b'unknown').decode()
    zone = data.get(b'zone_id', b'unknown').decode()
    customer_behavior[track_id]["zones"].add(zone)
    customer_behavior[track_id]["events"] += 1

# Print top customers
print("Top Customers:")
for customer_id, behavior in sorted(
    customer_behavior.items(),
    key=lambda x: x[1]["events"],
    reverse=True
)[:10]:
    print(f"  Customer {customer_id}: {behavior['events']} events, "
          f"{len(behavior['zones'])} zones visited")
EOF
```

---

## Monitoring and Diagnostics

### Command 1: Real-Time Performance Monitoring

```bash
python << 'EOF'
import asyncio
from backend.app.analytics.service import get_phase4_service

async def monitor():
    try:
        service = get_phase4_service()
        stats = service.get_statistics()
        
        print("\n=== Phase 4 Service Statistics ===")
        print(f"Frames Processed:        {stats['frames_processed']}")
        print(f"Active Customers:        {stats['active_customers']}")
        print(f"Total Interactions:      {stats['interactions_detected']}")
        print(f"Events Published:        {stats['events_published']}")
        print(f"Anomalies Detected:      {stats['anomalies_detected']}")
        print(f"Event Buffer Size:       {stats['event_buffer_size']}")
        print(f"Redis Connected:         {stats['redis_connected']}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(monitor())
EOF
```

### Command 2: CPU/Memory Profiling

```bash
# Profile frame processing performance
python -m cProfile -s cumulative backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source backend/test_data/sample.mp4 \
  --max-frames 300 \
  2>&1 | head -50
```

### Command 3: Memory Usage Monitoring

```bash
# Watch memory usage during processing
watch -n 1 'ps aux | grep "start_phase4_pipeline.py" | grep -v grep'
```

### Command 4: Check GPU Usage

```bash
# Monitor GPU (NVIDIA)
nvidia-smi -l 1

# Check PyTorch GPU
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'GPU Name: {torch.cuda.get_device_name(0)}')"
```

---

## Logging and Debugging

### Command 1: Enable Detailed Logging to File

```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source backend/test_data/video.mp4 \
  --log-level DEBUG \
  2>&1 | tee backend/logs/phase4_run_$(date +%Y%m%d_%H%M%S).log
```

### Command 2: Filter Logs

```bash
# Show only errors
cat backend/logs/phase4_run.log | grep ERROR

# Show Phase 4 service logs
cat backend/logs/phase4_run.log | grep "Phase 4"

# Show Redis connection logs
cat backend/logs/phase4_run.log | grep -i redis
```

### Command 3: Parse Event Timestamps

```bash
# Extract and count events by hour
redis-cli XRANGE retail:interactions - + | grep -o '[0-9]\{10\}' | \
  while read ts; do date -d @$((ts/1000)) +"%H:00"; done | sort | uniq -c
```

---

## Example Workflows

### Workflow 1: Full End-to-End Test

```bash
#!/bin/bash

echo "Starting Phase 4 End-to-End Test..."

# 1. Start Redis
echo "Starting Redis..."
redis-server --daemonize yes

# 2. Clear previous data
echo "Clearing previous data..."
redis-cli FLUSHDB

# 3. Run tests
echo "Running test suite..."
python backend/scripts/test_phase4.py

# 4. Start pipeline
echo "Starting pipeline..."
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source backend/test_data/sample_video.mp4 \
  --max-frames 1000 \
  --log-level INFO

# 5. Check results
echo "Checking results..."
redis-cli XLEN retail:interactions
redis-cli XLEN retail:anomalies

echo "Test complete!"
```

### Workflow 2: Production Deployment

```bash
#!/bin/bash

# Start all services
cd /opt/retailvision

# Start Redis
systemctl start redis-server

# Start Phase 4 pipeline
nohup python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source 0 \
  --log-level INFO \
  > backend/logs/phase4_production.log 2>&1 &

# Start API server
nohup uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  > backend/logs/api_server.log 2>&1 &

# Monitor
echo "Monitoring service..."
watch -n 5 'redis-cli KEYS "retail:*" | xargs -I {} redis-cli XLEN {}'
```

---

## Troubleshooting Commands

### Command 1: Verify Setup

```bash
#!/bin/bash

echo "=== Phase 4 Setup Verification ==="

echo -n "Python: "
python --version

echo -n "PyTorch: "
python -c "import torch; print(torch.__version__)"

echo -n "OpenCV: "
python -c "import cv2; print(cv2.__version__)"

echo -n "Redis: "
redis-cli ping

echo -n "GPU Available: "
python -c "import torch; print(torch.cuda.is_available())"

echo "=== Verification Complete ==="
```

### Command 2: Reset System

```bash
# Clear all Redis data
redis-cli FLUSHALL

# Kill any running processes
pkill -f "start_phase4_pipeline.py"
pkill -f "uvicorn"

# Restart
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source 0 \
  --log-level INFO
```

### Command 3: Check Error Logs

```bash
# Show recent errors
tail -100 backend/logs/phase4_run.log | grep -i error

# Count errors
grep -c ERROR backend/logs/phase4_run.log

# Show context around errors
grep -B5 -A5 ERROR backend/logs/phase4_run.log | head -50
```

---

## Performance Benchmarking

### Command 1: Benchmark FPS

```bash
python backend/scripts/start_phase4_pipeline.py \
  --config backend/scripts/phase4_config.json \
  --source backend/test_data/benchmark_video.mp4 \
  --max-frames 1000 \
  2>&1 | grep -E "Frame [0-9]+ |FPS:"
```

### Command 2: Memory Baseline

```bash
python << 'EOF'
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Initial Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")

# Import Phase 4
from app.analytics.service import Phase4Service, Phase4Config

print(f"After imports: {process.memory_info().rss / 1024 / 1024:.1f} MB")
EOF
```

### Command 3: Event Throughput

```bash
python << 'EOF'
import redis
import time

r = redis.Redis()

# Benchmark publishing
start = time.time()
for i in range(10000):
    r.xadd('retail:interactions', {'test': 'data'})
elapsed = time.time() - start

print(f"10,000 events in {elapsed:.2f}s = {10000/elapsed:.0f} events/sec")
EOF
```

---

## Additional Resources

- Full documentation: `docs/PHASE4_COMPLETE.md`
- Configuration guide: `docs/PHASE4_CONFIG.md`
- API documentation: `docs/PHASE4_API.md`
- Event schemas: `docs/PHASE4_EVENTS.md`

