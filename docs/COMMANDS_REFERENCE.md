# Phase 3: Quick Commands Reference

Copy-paste ready commands to run RetailVision AI detection and tracking system.

---

## 🚀 Essential Commands

### 1. Start Detection Service (Simplest)

```bash
cd backend
python scripts/start_detection.py --create-sample
```

**What it does**: Loads default config, initializes detection service, starts processing frames

---

### 2. Start with Custom Configuration

```bash
cd backend
python scripts/start_detection.py --config scripts/detection_config.json
```

**What it does**: Uses retail store zones and tuned parameters from config file

---

### 3. Save Detection Output Video

```bash
cd backend
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --output detection_results.mp4 \
  --max-frames 2000
```

**What it does**: Processes 2000 frames and saves video with all overlays to file

---

### 4. Server Mode (No Display)

```bash
cd backend
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --no-display \
  --max-frames 5000
```

**What it does**: Runs in background without showing video window

---

### 5. Benchmark Performance

```bash
cd backend
python scripts/start_detection.py --benchmark-fps 30
```

**What it does**: Tests detection speed with 100 frames, reports FPS and latency

---

## 🧪 Testing Commands

### Run All Tests

```bash
cd backend
python scripts/test_detection.py --all
```

**Tests**: Detector, Tracker, Zones, Full pipeline

### Test Specific Components

```bash
# Test YOLOv11 detector only
python scripts/test_detection.py --detector

# Test ByteTrack tracker only
python scripts/test_detection.py --tracker

# Test zone detection only
python scripts/test_detection.py --zones

# Benchmark entire pipeline
python scripts/test_detection.py --benchmark
```

---

## 📹 CCTV Footage Processing

### Full Workflow

```bash
# Terminal 1: Start video ingestion service
cd backend
python -m app.services.video_ingestion_service

# Terminal 2: Add CCTV video source
curl -X POST http://localhost:8000/api/video-ingestion/sources \
  -H "Content-Type: application/json" \
  -d '{
    "type": "FILE",
    "url": "/absolute/path/to/cctv_video.mp4",
    "fps": 30,
    "name": "CCTV_Store"
  }'

# Terminal 3: Start detection
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --source cctv_1 \
  --output cctv_analysis.mp4

# Terminal 4: Monitor metrics (optional)
watch -n 1 'curl -s http://localhost:8000/api/detection/statistics | jq'
```

---

## 🎯 Performance Tuning Commands

### Maximum Speed (Live Camera)

```bash
python scripts/start_detection.py \
  --config <(cat <<'EOF'
{
  "yolo_config": {
    "model_size": "n",
    "confidence_threshold": 0.6,
    "use_gpu": true
  },
  "bytetrack_config": {
    "track_buffer": 20
  },
  "max_concurrent_frames": 1
}
EOF
)
```

**Result**: 60+ FPS, less accurate

### Maximum Accuracy (Archive Processing)

```bash
python scripts/start_detection.py \
  --config <(cat <<'EOF'
{
  "yolo_config": {
    "model_size": "m",
    "confidence_threshold": 0.4,
    "use_gpu": true
  },
  "bytetrack_config": {
    "track_buffer": 60
  },
  "max_concurrent_frames": 5,
  "publish_all_detections": true
}
EOF
)
```

**Result**: 20-30 FPS, more accurate

### Balanced Config (Recommended)

```bash
python scripts/start_detection.py \
  --config <(cat <<'EOF'
{
  "yolo_config": {
    "model_size": "s",
    "confidence_threshold": 0.5,
    "use_gpu": true
  },
  "bytetrack_config": {
    "track_buffer": 30
  },
  "max_concurrent_frames": 3
}
EOF
)
```

**Result**: 30-40 FPS, balanced quality

---

## 📊 API Queries

### Check Service Status

```bash
curl http://localhost:8000/api/detection/status | jq
```

### Get Detection Statistics

```bash
curl http://localhost:8000/api/detection/statistics | jq
```

### List Active Zones

```bash
curl http://localhost:8000/api/detection/zones | jq
```

### List Active Tracks

```bash
curl http://localhost:8000/api/detection/tracks | jq
```

### Get Track Details

```bash
curl http://localhost:8000/api/detection/tracks/1 | jq
```

### View Dwell Sessions

```bash
curl http://localhost:8000/api/detection/dwell-sessions | jq
```

### Get Interaction History

```bash
curl http://localhost:8000/api/detection/interaction-history/5 | jq
```

### Reset Statistics

```bash
curl -X POST http://localhost:8000/api/detection/reset-statistics | jq
```

### Health Check

```bash
curl http://localhost:8000/api/detection/health | jq
```

---

## 🔧 Advanced Usage

### Process Multiple Videos

```bash
# Add multiple sources
for video in /path/to/videos/*.mp4; do
  curl -X POST http://localhost:8000/api/video-ingestion/sources \
    -H "Content-Type: application/json" \
    -d "{
      \"type\": \"FILE\",
      \"url\": \"$video\",
      \"fps\": 30,
      \"name\": \"$(basename $video)\"
    }"
done

# Process them sequentially
python scripts/start_detection.py --max-frames 10000 --no-display
```

### Continuous Monitoring

```bash
# Run detection service in background
nohup python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --no-display > detection.log 2>&1 &

# Monitor in real-time
tail -f detection.log

# Watch metrics
watch -n 1 'curl -s http://localhost:8000/api/detection/statistics | jq ".active_tracks"'
```

### Custom Zone Configuration

```bash
# Create zones for your store layout
cat > /tmp/zones_config.json <<'EOF'
{
  "zones": [
    {
      "id": "produce_1",
      "type": "shelf",
      "name": "Produce Section",
      "polygon": [[100, 200], [400, 200], [400, 500], [100, 500]],
      "metadata": {"dept": "produce"}
    },
    {
      "id": "checkout_1",
      "type": "checkout",
      "name": "Checkout Area",
      "polygon": [[500, 300], [800, 300], [800, 500], [500, 500]],
      "metadata": {"priority": "high"}
    }
  ]
}
EOF

# Start with custom zones
python scripts/start_detection.py --config /tmp/zones_config.json
```

### Profiling & Performance Analysis

```bash
# Profile CPU usage
python -m cProfile -s cumtime scripts/start_detection.py \
  --max-frames 100 > profile.txt

# View results
head -50 profile.txt

# Memory profiling
python -m memory_profiler scripts/start_detection.py --max-frames 50
```

---

## 🐛 Troubleshooting Commands

### Check GPU Availability

```bash
python -c "import torch; print(f'GPU: {torch.cuda.is_available()}')"
```

### Check CUDA Version

```bash
python -c "import torch; print(torch.version.cuda)"
```

### Run with CPU Only

```bash
python scripts/start_detection.py \
  --config <(cat <<'EOF'
{"yolo_config": {"use_gpu": false}}
EOF
)
```

### Enable Debug Logging

```bash
python scripts/start_detection.py \
  --log-level DEBUG
```

### Check Redis Connection

```bash
redis-cli ping
# Response: PONG (if working)

# View detection events in Redis
redis-cli XREAD STREAMS detection:events 0
```

### Monitor Memory Usage

```bash
# Watch in real-time
watch -n 1 'ps aux | grep start_detection'

# Or with more detail
watch -n 1 'top -p $(pgrep -f start_detection) -b -n 1'
```

---

## 🚀 One-Liners for Quick Testing

### Minimal Test (20 seconds)

```bash
cd backend && python scripts/start_detection.py --create-sample --max-frames 600
```

### Full Performance Test

```bash
cd backend && python scripts/test_detection.py --all
```

### Quick Benchmark

```bash
cd backend && python scripts/start_detection.py --benchmark-fps 30
```

### Stream Real-time Events

```bash
redis-cli XREAD BLOCK 0 STREAMS detection:events $
```

### Export Detection Stats to CSV

```bash
curl -s http://localhost:8000/api/detection/statistics | \
  jq -r '.[] | keys[] as $k | "\($k),\(.[$k])"' | \
  column -t -s','
```

---

## 📋 Setup & Installation

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt

# Or manually
pip install ultralytics>=8.0.0 opencv-python>=4.8.0 torch>=2.0.0 boxmot>=10.0.0
```

### Verify Installation

```bash
python -c "from app.detection import DetectionService; print('✓ Detection module OK')"
python -c "from app.tracking import TrackingEngine; print('✓ Tracking module OK')"
```

### Create Default Config

```bash
cd backend
python -c "
import json
config = {
    'yolo_config': {'model_size': 'n', 'confidence_threshold': 0.5},
    'bytetrack_config': {'track_buffer': 30},
    'zones': [],
    'publish_all_detections': True
}
with open('scripts/detection_config_default.json', 'w') as f:
    json.dump(config, f, indent=2)
print('Default config created')
"
```

---

## 🎬 Production Ready Commands

### Start as Service (Systemd)

```bash
# Create service file
sudo tee /etc/systemd/system/retail-detection.service > /dev/null <<'EOF'
[Unit]
Description=RetailVision Detection Service
After=network.target redis.service

[Service]
Type=simple
WorkingDirectory=/path/to/backend
ExecStart=/usr/bin/python scripts/start_detection.py --config scripts/detection_config.json --no-display
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable retail-detection
sudo systemctl start retail-detection

# Check status
sudo systemctl status retail-detection
```

### Docker Deployment

```bash
# Build image
docker build -t retail-detection:latest .

# Run container
docker run -d \
  --name retail-detection \
  --gpus all \
  -e USE_GPU=true \
  -v /path/to/videos:/videos \
  -v /path/to/config:/app/config \
  retail-detection:latest
```

---

## 📈 Continuous Integration

### GitHub Actions Example

```yaml
name: Test Detection

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run detection tests
        run: cd backend && python scripts/test_detection.py --all
```

---

## 🔗 Integration Examples

### Consume Events in Python

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379)

# Listen to detection events
for message in r.xread({'detection:events': '0'}, block=0):
    stream, data = message
    for event_id, event_data in data:
        event = {k.decode(): v.decode() for k, v in event_data.items()}
        print(f"Detection: {event}")
```

### Webhooks to External System

```bash
# Forward detection events to HTTP endpoint
redis-cli XREAD STREAMS detection:events 0 | \
  while read line; do
    curl -X POST http://external-system/events -d "$line"
  done
```

---

## ✨ Summary

| Goal | Command |
|------|---------|
| **Quick start** | `python scripts/start_detection.py --create-sample` |
| **Full test** | `python scripts/test_detection.py --all` |
| **Process video** | `python scripts/start_detection.py --output output.mp4` |
| **Benchmark** | `python scripts/start_detection.py --benchmark-fps 30` |
| **Check status** | `curl http://localhost:8000/api/detection/status` |
| **Monitor** | `watch -n 1 'curl http://localhost:8000/api/detection/statistics \| jq'` |
| **Debug** | `python scripts/start_detection.py --log-level DEBUG` |
| **Production** | `sudo systemctl start retail-detection` |

---

🎯 **Ready to run!** Copy any command and execute.

For detailed documentation, see [PHASE3_DETECTION.md](PHASE3_DETECTION.md) and [RUN_DETECTION.md](RUN_DETECTION.md)
