# Phase 3: How to Run Detection & Tracking System

Quick start guide for running the detection and tracking pipeline.

---

## 📦 Prerequisites

### Install Dependencies

```bash
# Navigate to backend
cd backend

# Install detection dependencies
pip install -r requirements.txt

# Key packages:
# - ultralytics>=8.0.0     # YOLOv11
# - opencv-python>=4.8.0   # Computer vision
# - boxmot>=10.0.0         # ByteTrack
# - torch>=2.0.0           # PyTorch (GPU support)
```

### Verify GPU (Optional)

```bash
# Check if GPU is available
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"

# If GPU not found, run without GPU:
# Edit detection_config.json: "use_gpu": false
```

---

## 🚀 Quick Start (5 minutes)

### 1. Minimal Example (Default Config)

```bash
cd backend

# Run detection with default settings
python scripts/start_detection.py --create-sample

# Press 'q' in the display window to quit
```

**What happens**:
- Initializes YOLOv11 nano model
- Sets up ByteTrack tracker
- Processes frames from video source
- Displays real-time detections
- Publishes events to Redis

### 2. With Custom Configuration

```bash
# Run with custom config
python scripts/start_detection.py --config scripts/detection_config.json

# Customize config first (see Configuration section below)
```

### 3. Save Output Video

```bash
# Run and save detection output
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --output detection_output.mp4 \
  --max-frames 1000

# Output video saved to: detection_output.mp4
```

### 4. Disable Display (Server Mode)

```bash
# Run without display window (good for servers/CI)
python scripts/start_detection.py \
  --no-display \
  --max-frames 500
```

---

## 🎯 Running on CCTV Footage

### Step 1: Prepare Video

```bash
# Supported formats: .mp4, .avi, .mov, .mkv, .flv

# Convert video if needed (to MP4)
ffmpeg -i input_video.avi -c:v libx264 -crf 23 output.mp4

# Recommended specs:
# - Resolution: 1920×1080 or 1280×720
# - Frame rate: 30 fps
# - Duration: 5-30 minutes for testing
```

### Step 2: Add Video as Source (Phase 2)

```bash
# Terminal 1: Start video ingestion service
cd backend
python -m app.services.video_ingestion_service

# Terminal 2: Add video source
curl -X POST http://localhost:8000/api/video-ingestion/sources \
  -H "Content-Type: application/json" \
  -d '{
    "type": "FILE",
    "url": "/absolute/path/to/video.mp4",
    "fps": 30,
    "name": "CCTV_Footage"
  }'

# Response: {"status": "created", "source_id": "cctv_1", ...}
```

### Step 3: Configure Detection

Edit `backend/scripts/detection_config.json`:

```json
{
  "yolo_config": {
    "model_size": "s",           // Use 's' for better accuracy
    "confidence_threshold": 0.45, // Lower for more detections
    "use_gpu": true
  },
  "bytetrack_config": {
    "track_buffer": 45,          // Longer buffer for occlusions
    "track_thresh": 0.4
  },
  "zones": [
    {
      "id": "store_section_1",
      "type": "shelf",
      "name": "Section 1",
      "polygon": [[100, 100], [500, 100], [500, 400], [100, 400]],
      "metadata": {"description": "Product shelf"}
    }
  ],
  "publish_all_detections": true,
  "max_concurrent_frames": 5
}
```

### Step 4: Run Detection

```bash
# Terminal 3: Run detection pipeline
cd backend

python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --source cctv_1 \
  --output cctv_detection_output.mp4 \
  --max-frames 2000

# Or without source ID (uses default):
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --output detection_results.mp4
```

**Output**:
- Real-time visualization (if not using --no-display)
- Detection statistics printed to console
- Output video with overlays saved to file

### Step 5: Analyze Results

```bash
# Check metrics via API
curl http://localhost:8000/api/detection/statistics | jq

# Expected response:
{
  "frames_processed": 1200,
  "total_detections": 5431,
  "active_tracks": 23,
  "events_published": 8743,
  "zones_count": 4,
  "active_dwell_sessions": 8
}

# Get active tracks
curl http://localhost:8000/api/detection/tracks | jq

# Get dwell sessions
curl http://localhost:8000/api/detection/dwell-sessions | jq
```

---

## 📊 Running Tests

### Test Individual Components

```bash
cd backend

# Test YOLOv11 detector
python scripts/test_detection.py --detector
# Output: Detection benchmarks, FPS calculations

# Test ByteTrack tracker
python scripts/test_detection.py --tracker
# Output: Tracking accuracy, track ID stability

# Test zone detection
python scripts/test_detection.py --zones
# Output: Zone detection results

# Test full pipeline
python scripts/test_detection.py --benchmark
# Output: End-to-end performance metrics
```

### Performance Benchmark

```bash
# Benchmark with 100 frames
python scripts/start_detection.py --benchmark-fps 30

# Output includes:
# - Average FPS
# - Min/Max frame times
# - GPU/CPU utilization
# - Memory usage
```

---

## 🎬 Different Scenarios

### Scenario 1: High-Speed Processing (Live Camera)

```bash
python scripts/start_detection.py \
  --config <(cat <<'EOF'
{
  "yolo_config": {"model_size": "n", "confidence_threshold": 0.6},
  "bytetrack_config": {"track_buffer": 20},
  "max_concurrent_frames": 1,
  "publish_all_detections": false
}
EOF
)
```

**Settings**:
- Nano model (fastest)
- Lower buffer
- Publish only important events
- Result: 60+ FPS

### Scenario 2: High-Accuracy Analysis

```bash
python scripts/start_detection.py \
  --config <(cat <<'EOF'
{
  "yolo_config": {"model_size": "m", "confidence_threshold": 0.4},
  "bytetrack_config": {"track_buffer": 60, "track_thresh": 0.4},
  "max_concurrent_frames": 5,
  "publish_all_detections": true
}
EOF
)
```

**Settings**:
- Medium model (balanced)
- Higher buffer
- Publish all events
- Result: 20-30 FPS

### Scenario 3: Batch Processing (Archive Video)

```bash
python scripts/start_detection.py \
  --source video_file \
  --output batch_results.mp4 \
  --no-display \
  --max-frames 10000

# No real-time constraints
# Process entire video in background
```

---

## 📈 Configuration Options

### Model Size Selection

```bash
# Nano: Fastest, less accurate
python scripts/start_detection.py --config <(cat <<'EOF'
{"yolo_config": {"model_size": "n"}}
EOF
)

# Small: Balanced
python scripts/start_detection.py --config <(cat <<'EOF'
{"yolo_config": {"model_size": "s"}}
EOF
)

# Medium: Better accuracy
python scripts/start_detection.py --config <(cat <<'EOF'
{"yolo_config": {"model_size": "m"}}
EOF
)
```

### GPU Configuration

```bash
# Enable GPU
python scripts/start_detection.py --config <(cat <<'EOF'
{"yolo_config": {"use_gpu": true, "gpu_device_id": 0}}
EOF
)

# Force CPU (no GPU)
python scripts/start_detection.py --config <(cat <<'EOF'
{"yolo_config": {"use_gpu": false}}
EOF
)

# Multi-GPU (use GPU 1)
python scripts/start_detection.py --config <(cat <<'EOF'
{"yolo_config": {"gpu_device_id": 1}}
EOF
)
```

---

## 🔍 Monitoring & Debugging

### Enable Debug Logging

```bash
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --log-level DEBUG
```

### Real-time Metrics

```bash
# In another terminal, watch metrics
watch -n 1 'curl -s http://localhost:8000/api/detection/statistics | jq'
```

### Performance Profiling

```bash
# Run with profiling
python -m cProfile -s cumtime scripts/start_detection.py \
  --max-frames 100 > profile_results.txt
```

---

## 🚨 Troubleshooting

### Issue: "No module named ultralytics"

```bash
# Solution: Install YOLO
pip install ultralytics opencv-python
```

### Issue: "CUDA out of memory"

```bash
# Solution: Reduce GPU memory usage
# Edit config:
{
  "yolo_config": {"model_size": "n"},  // Use smaller model
  "gpu_memory_fraction": 0.3            // Use 30% of GPU
}
```

### Issue: "No detections found"

```bash
# Lower confidence threshold
{
  "yolo_config": {"confidence_threshold": 0.3}
}

# Or use larger model
{
  "yolo_config": {"model_size": "m"}
}
```

### Issue: "Tracking IDs keep changing"

```bash
# Increase track buffer and threshold
{
  "bytetrack_config": {
    "track_buffer": 60,
    "track_thresh": 0.6
  }
}
```

---

## 📊 Output Interpretation

### Console Output Example

```
[2024-01-15 10:30:45] Frames: 150 | FPS: 28.5 | Detections: 412 | Active tracks: 8 | Detection time: 32.5ms
[2024-01-15 10:30:50] Frames: 300 | FPS: 29.2 | Detections: 856 | Active tracks: 12 | Detection time: 31.2ms

===============================================================================
📊 Detection Pipeline Statistics
===============================================================================
Total frames processed: 300
Total time: 10.3 seconds
Average FPS: 29.1
Total detections: 856
Active tracks: 12
Events published: 1245
Average detection time: 31.8ms
===============================================================================
```

### Interpreting Metrics

| Metric | Good | Acceptable | Poor |
|--------|------|-----------|------|
| FPS | 30+ | 15-30 | <15 |
| Detection time | <50ms | 50-100ms | >100ms |
| Active tracks | Matches expected | ±20% | Way off |
| Events | Consistent | Some variance | Sporadic |

---

## 🔗 Integration with Other Phases

### Input from Phase 2 (Video Ingestion)

```python
# Detection automatically consumes from video ingestion
# No additional setup needed - just run both services

# Terminal 1: Video ingestion
python -m app.services.video_ingestion_service

# Terminal 2: Detection
python scripts/start_detection.py
```

### Output to Phase 4+ (Analytics)

```bash
# Events automatically published to Redis Streams
# Subscribe to detection events:

redis-cli XREAD STREAMS detection:events 0

# Expected output:
# 1) "detection:events"
#    1) 1) "1705317045000-0"
#          1) "event_type"
#          2) "detection"
#          3) "track_id"
#          4) "5"
#          ...
```

---

## 📚 Full Command Examples

### Example 1: Quick Test (30 seconds)

```bash
python scripts/start_detection.py \
  --create-sample \
  --max-frames 900
```

### Example 2: Process CCTV Video (Full)

```bash
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --source cctv_1 \
  --output analysis.mp4 \
  --log-level INFO
```

### Example 3: Server Mode (No Display)

```bash
python scripts/start_detection.py \
  --config scripts/detection_config.json \
  --no-display \
  --max-frames 5000
```

### Example 4: Benchmark Only

```bash
python scripts/start_detection.py --benchmark-fps 30
```

### Example 5: Lightweight Processing

```bash
python scripts/start_detection.py \
  --config <(cat <<'EOF'
{
  "yolo_config": {"model_size": "n", "confidence_threshold": 0.6},
  "max_concurrent_frames": 1
}
EOF
) \
  --no-display
```

---

## ✅ Success Criteria

You'll know it's working when:

- ✅ Console shows frame processing with FPS > 15
- ✅ Detection count increases over time
- ✅ Tracking IDs remain stable for same objects
- ✅ Output video shows bounding boxes and IDs
- ✅ API returns detection statistics
- ✅ Events published to Redis Streams
- ✅ No CUDA out-of-memory errors (if using GPU)

---

## 🎯 Next Steps

1. **Test on sample video** → `max-frames 300`
2. **Tune configuration** → Adjust model/thresholds
3. **Process full video** → Remove `max-frames` limit
4. **Integrate zones** → Add store-specific zones
5. **Connect to Phase 4** → Subscribe to detection events

---

Ready to run! 🚀

For more details, see [PHASE3_DETECTION.md](PHASE3_DETECTION.md)
