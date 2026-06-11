# Phase 3: EXACT COMMANDS TO RUN DETECTION SYSTEM

**Copy-paste these commands to run the RetailVision AI detection and tracking system.**

---

## 🚨 TL;DR - Just Want to Run It?

```bash
# Setup (one-time)
cd backend
pip install -r requirements.txt

# Run detection
python scripts/start_detection.py --create-sample

# That's it! 🚀
```

Press `q` to quit. Done.

---

## 📋 Complete Step-by-Step Guide

### Step 1: Navigate to Backend

```bash
cd backend
```

### Step 2: Install Dependencies (First Time Only)

```bash
pip install -r requirements.txt
```

**Verify installation**:
```bash
python -c "from app.detection import DetectionService; print('✓ Detection OK')"
```

### Step 3: Choose Your Command

---

## 🎯 Common Use Cases

### Use Case 1: Quick Test (30 seconds)

**What it does**: Runs detection on 600 frames with default config

```bash
python scripts/start_detection.py --create-sample --max-frames 600
```

**Output**:
- Real-time video display with overlays
- Console output showing FPS and detections
- Press `q` to quit

---

### Use Case 2: Process CCTV Video (Full Workflow)

**What it does**: Takes CCTV footage and generates annotated video with all detections/tracks

**Command sequence**:

```bash
# Terminal 1: Start video ingestion
python -m app.services.video_ingestion_service

# Terminal 2: Add your CCTV video as source
curl -X POST http://localhost:8000/api/video-ingestion/sources \
  -H "Content-Type: application/json" \
  -d '{
    "type": "FILE",
    "url": "/path/to/your/cctv_video.mp4",
    "fps": 30,
    "name": "MyStore"
  }'

# Terminal 3: Run detection and save output
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --output detection_results.mp4 \
  --max-frames 3000

# Wait for completion...
# Output saved to: detection_results.mp4
```

---

### Use Case 3: Real-Time Monitoring (No Recording)

```bash
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --no-display
```

Runs in background without showing video window

---

### Use Case 4: Performance Benchmarking

```bash
python scripts/start_detection.py --benchmark-fps 30
```

**Output**: FPS, latency, GPU utilization

---

### Use Case 5: Test All Components

```bash
python scripts/test_detection.py --all
```

**Tests**:
- YOLOv11 detector
- ByteTrack tracker
- Zone detection
- Full pipeline benchmark

---

## 🎬 Detailed CCTV Processing Workflow

### Prepare Your Video

```bash
# Convert video to MP4 (if needed)
ffmpeg -i input_video.avi -c:v libx264 -crf 23 output.mp4
```

### Start Services (in order)

**Terminal 1 - Video Ingestion Service**:
```bash
cd backend
python -m app.services.video_ingestion_service
```
Expected output: `INFO: Uvicorn running on http://0.0.0.0:8000`

**Terminal 2 - Register Video**:
```bash
curl -X POST http://localhost:8000/api/video-ingestion/sources \
  -H "Content-Type: application/json" \
  -d '{
    "type": "FILE",
    "url": "/absolute/path/to/your/video.mp4",
    "fps": 30
  }'
```
Expected response: `{"status": "created", "source_id": "..."`

**Terminal 3 - Start Detection**:
```bash
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --output analysis_results.mp4
```

### Monitor Progress

**Terminal 4 - Watch Metrics** (optional):
```bash
watch -n 1 'curl -s http://localhost:8000/api/detection/statistics | jq'
```

### When Done

- Detection completes automatically
- Output video saved to `analysis_results.mp4`
- All files ready in terminal 3

---

## ⚙️ Configuration Presets

### Fast Configuration (High FPS)

Edit the command:
```bash
python scripts/start_detection.py \
  --config <(cat <<'EOF'
{
  "yolo_config": {
    "model_size": "n",
    "confidence_threshold": 0.6
  },
  "bytetrack_config": {
    "track_buffer": 20
  },
  "max_concurrent_frames": 1
}
EOF
)
```

Result: 60+ FPS, less accurate

---

### Accurate Configuration (High Quality)

```bash
python scripts/start_detection.py \
  --config <(cat <<'EOF'
{
  "yolo_config": {
    "model_size": "m",
    "confidence_threshold": 0.4
  },
  "bytetrack_config": {
    "track_buffer": 60
  },
  "max_concurrent_frames": 5
}
EOF
)
```

Result: 20-30 FPS, more accurate

---

### Balanced Configuration (Default - Recommended)

```bash
python scripts/start_detection.py \
  --config scripts/detection_config.json
```

Result: 30-40 FPS, balanced quality

---

## 📊 API Queries (While Running)

### Check if detection is running

```bash
curl http://localhost:8000/api/detection/status | jq
```

### Get all statistics

```bash
curl http://localhost:8000/api/detection/statistics | jq
```

### List active tracks

```bash
curl http://localhost:8000/api/detection/tracks | jq
```

### Get specific track details

```bash
curl http://localhost:8000/api/detection/tracks/5 | jq
```

### List detection zones

```bash
curl http://localhost:8000/api/detection/zones | jq
```

### View dwell sessions

```bash
curl http://localhost:8000/api/detection/dwell-sessions | jq
```

---

## 🧪 Testing Commands

### Test detector

```bash
python scripts/test_detection.py --detector
```

### Test tracker

```bash
python scripts/test_detection.py --tracker
```

### Test zones

```bash
python scripts/test_detection.py --zones
```

### Test everything

```bash
python scripts/test_detection.py --all
```

### Benchmark pipeline

```bash
python scripts/test_detection.py --benchmark
```

---

## 🔧 Troubleshooting Commands

### Check GPU availability

```bash
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"
```

If `False`, use `--config` with `"use_gpu": false`

### Run with debug logging

```bash
python scripts/start_detection.py --log-level DEBUG
```

### Check Redis connection

```bash
redis-cli ping
```
Response should be: `PONG`

### View detection events in Redis

```bash
redis-cli XREAD STREAMS detection:events 0
```

### Monitor memory usage

```bash
watch -n 1 'ps aux | grep start_detection'
```

---

## 🎬 Advanced: Custom Zones

Create a JSON file with your store layout:

```json
{
  "zones": [
    {
      "id": "produce",
      "type": "shelf",
      "name": "Produce Section",
      "polygon": [
        [100, 200],
        [400, 200],
        [400, 500],
        [100, 500]
      ]
    },
    {
      "id": "checkout",
      "type": "checkout",
      "name": "Checkout Area",
      "polygon": [
        [500, 300],
        [800, 300],
        [800, 500],
        [500, 500]
      ]
    }
  ],
  "yolo_config": {
    "model_size": "s"
  }
}
```

Then run:
```bash
python scripts/start_detection.py --config /path/to/zones.json --output output.mp4
```

---

## 📈 Performance Optimization

### If Running Slow (Low FPS)

**Option 1: Smaller Model**
```bash
python scripts/start_detection.py --config <(cat <<'EOF'
{"yolo_config": {"model_size": "n"}}
EOF
)
```

**Option 2: Lower Resolution**
- Preprocess video to 640×480 instead of 1920×1080

**Option 3: Disable Features**
```bash
python scripts/start_detection.py --config <(cat <<'EOF'
{
  "publish_all_detections": false,
  "publish_zone_events": false,
  "max_concurrent_frames": 1
}
EOF
)
```

### If Low Accuracy (Missing Detections)

```bash
python scripts/start_detection.py --config <(cat <<'EOF'
{
  "yolo_config": {
    "model_size": "m",
    "confidence_threshold": 0.3
  }
}
EOF
)
```

---

## 🚀 Production Commands

### Run as Service

```bash
# Create systemd service
sudo tee /etc/systemd/system/retail-detection.service > /dev/null <<'EOF'
[Unit]
Description=RetailVision Detection
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/backend
ExecStart=/usr/bin/python scripts/start_detection.py --no-display --config scripts/detection_config.json
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl start retail-detection
sudo systemctl status retail-detection

# View logs
sudo journalctl -fu retail-detection
```

---

## 🐳 Docker Commands

### Build

```bash
docker build -t retail-detection:latest .
```

### Run

```bash
docker run -d \
  --name retail-detection \
  --gpus all \
  -v /path/to/videos:/videos \
  -p 8000:8000 \
  retail-detection:latest
```

### Check logs

```bash
docker logs -f retail-detection
```

---

## ✅ Validation Checklist

After running, verify:

- [ ] Console shows "FPS: 20+" (or higher)
- [ ] Detection bounding boxes visible in output
- [ ] Track IDs remain stable for same objects
- [ ] Output video saved successfully
- [ ] API endpoints respond with data
- [ ] No CUDA out-of-memory errors

---

## 📖 More Help

For more information:

1. **Architecture details**: `docs/PHASE3_DETECTION.md`
2. **Troubleshooting**: `docs/RUN_DETECTION.md`
3. **All commands**: `docs/COMMANDS_REFERENCE.md`
4. **Summary**: `docs/PHASE3_SUMMARY.md`

---

## 🎯 Start Here

**First Time?** Run this:
```bash
cd backend
python scripts/start_detection.py --create-sample --max-frames 600
```

**Have CCTV Video?** Follow the workflow above.

**Want to Test?** Run:
```bash
python scripts/test_detection.py --all
```

**Need Help?** Check the docs listed above.

---

**Ready? Let's go! 🚀**

```bash
cd backend
python scripts/start_detection.py --create-sample
```

Press `q` to quit when done.

---

**Next Steps**:
1. Run basic test ✓
2. Process real CCTV video
3. Tune configuration for your store
4. Integrate with Phase 4 (Analytics)
5. Deploy to production

Good luck! 🎬
