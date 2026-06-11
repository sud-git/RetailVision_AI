# 🎬 Running the Video Ingestion Pipeline

Complete guide to running RetailVision AI's video ingestion system with different video sources and configurations.

---

## 📋 Quick Start

### Easiest: With Sample Webcam

```bash
cd backend

# Terminal 1: Start FastAPI backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start video ingestion (with webcam)
python scripts/start_video_ingestion.py --create-sample --log-level INFO
```

Visit: `http://localhost:8000/api/video-ingestion/sources`

---

## 🎯 Different Source Types

### 1. **Webcam Source** (USB/Built-in Camera)

**Simple (Auto-detect):**
```bash
python scripts/start_video_ingestion.py --source-webcam
```

**Advanced (Specific device):**
```bash
# List available webcams
python -c "import cv2; [print(f'Device {i}') for i in range(10) if cv2.VideoCapture(i).isOpened()]"

# Start with specific device
python scripts/start_video_ingestion.py --source-webcam --device 1
```

**Configuration:**
```json
{
  "id": "webcam_main",
  "type": "WEBCAM",
  "device_id": 0,
  "fps": 15,
  "resolution": [1280, 720]
}
```

---

### 2. **RTSP Stream** (IP Cameras)

**From Command Line:**
```bash
python scripts/start_video_ingestion.py \
  --source-rtsp "rtsp://admin:password@192.168.1.100:554/stream"
```

**From Configuration File:**
```json
{
  "id": "front_entrance",
  "type": "RTSP",
  "url": "rtsp://camera.local:554/stream",
  "username": "admin",
  "password": "camera_password",
  "fps": 30,
  "resolution": [1920, 1080],
  "reconnect_attempts": 5,
  "reconnect_delay_ms": 2000
}
```

**Common RTSP URLs by Camera Manufacturer:**

| Manufacturer | Default URL | Port |
|---|---|---|
| Hikvision | `rtsp://admin:password@ip:554/stream` | 554 |
| Dahua | `rtsp://admin:password@ip:554/stream` | 554 |
| Axis | `rtsp://admin:password@ip:554/axis-media/media.amp` | 554 |
| Reolink | `rtsp://admin:password@ip:554/h264Preview_01_main` | 554 |
| Uniview | `rtsp://admin:password@ip:554/media/video1` | 554 |
| ONVIF Generic | `rtsp://admin:password@ip:554/onvif-media/media.amp` | 554 |

**Test RTSP Connection:**
```bash
# Using ffprobe
ffprobe -v quiet -print_format json -show_format -show_streams \
  "rtsp://admin:password@camera.local:554/stream"

# Using OpenCV (Python)
python -c "
import cv2
cap = cv2.VideoCapture('rtsp://admin:password@camera.local:554/stream')
ret, frame = cap.read()
print('Connected!' if ret else 'Failed!')
cap.release()
"
```

**Troubleshooting RTSP:**

| Issue | Solution |
|---|---|
| Connection timeout | Check firewall, verify IP/port, ping camera |
| 401 Unauthorized | Wrong credentials, check username/password |
| Media not supported | Try different stream path on camera |
| Network lag | Reduce FPS or resolution in config |
| Buffer issues | Set CAP_PROP_BUFFERSIZE to 1 (already done) |

---

### 3. **Local Video File**

**From Command Line:**
```bash
python scripts/start_video_ingestion.py \
  --source-file "/path/to/video.mp4" --log-level INFO
```

**From Configuration File:**
```json
{
  "id": "archive_video",
  "type": "LOCAL_FILE",
  "url": "/data/videos/store_footage.mp4",
  "fps": 30,
  "loop": true
}
```

**Supported Formats:**
- `.mp4` (H.264, H.265)
- `.avi` (MPEG-4, MJPEG)
- `.mov` (QuickTime)
- `.mkv` (Matroska)
- `.flv` (Flash)
- `.webm` (VP8/VP9)

**Generate Test Video:**
```bash
# Create 5-minute test video (30 FPS, 1080p)
ffmpeg -f lavfi -i color=c=blue:s=1920x1080:d=300 \
       -f lavfi -i sine=f=440:d=300 \
       -pix_fmt yuv420p -c:v libx264 -preset fast -y test_video.mp4

# Or use OpenCV
python -c "
import cv2
import numpy as np

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('test_video.mp4', fourcc, 30.0, (1280, 720))

for i in range(300 * 30):  # 5 minutes at 30 FPS
    frame = np.ones((720, 1280, 3), dtype=np.uint8) * (i % 255)
    out.write(frame)

out.release()
"
```

---

## ⚙️ Configuration Files

### Full Configuration Example

```json
{
  "sources": [
    {
      "id": "store_front",
      "name": "Store Front",
      "type": "RTSP",
      "url": "rtsp://camera1.local:554/stream",
      "username": "admin",
      "password": "password123",
      "fps": 30,
      "resolution": [1920, 1080],
      "format": "BGR",
      "buffer_capacity": 1000,
      "reconnect_attempts": 5,
      "reconnect_delay_ms": 2000,
      "reconnect_backoff_factor": 1.5,
      "enable_frame_dedup": true,
      "enable_keyframe_priority": true,
      "health_check_interval_seconds": 30
    }
  ],
  "gpu_acceleration": true,
  "gpu_device_id": 0,
  "gpu_memory_fraction": 0.5,
  "max_concurrent_sources": 10,
  "health_check_interval_seconds": 30,
  "metrics_publish_interval_seconds": 10,
  "log_level": "INFO"
}
```

### Load Configuration:

```bash
python scripts/start_video_ingestion.py --config ./scripts/video_sources_config.json
```

---

## 🧪 Testing & Validation

### Unit Tests

```bash
# Test async queue
python scripts/test_video_ingestion.py --queue

# Test GPU detection
python scripts/test_video_ingestion.py --gpu

# Benchmark frame extraction
python scripts/test_video_ingestion.py --benchmark
```

### Integration Tests

**Test Webcam (10 seconds):**
```bash
python scripts/test_video_ingestion.py --source webcam --duration 10
```

**Test Local File:**
```bash
python scripts/test_video_ingestion.py \
  --source local-file \
  --video /path/to/video.mp4 \
  --duration 30
```

**Test All Components:**
```bash
python scripts/test_video_ingestion.py --all
```

### Performance Metrics

After starting ingestion, monitor metrics:

```bash
# Get all sources
curl http://localhost:8000/api/video-ingestion/sources

# Get aggregated metrics
curl http://localhost:8000/api/video-ingestion/metrics

# Get specific source metrics
curl http://localhost:8000/api/video-ingestion/sources/{source_id}/metrics
```

**Example Metrics Response:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "total_sources": 3,
  "running_sources": 3,
  "total_frames_processed": 45892,
  "total_frames_dropped": 12,
  "total_errors": 0,
  "sources": [
    {
      "source_id": "store_front",
      "status": "RUNNING",
      "frames_processed": 15230,
      "current_fps": 29.8,
      "buffer_occupancy": 45
    }
  ]
}
```

---

## 📊 API Endpoints

### Add Source (Dynamic)

```bash
curl -X POST http://localhost:8000/api/video-ingestion/sources \
  -H "Content-Type: application/json" \
  -d '{
    "id": "new_camera",
    "type": "RTSP",
    "url": "rtsp://camera.local/stream",
    "fps": 30
  }'
```

### List All Sources

```bash
curl http://localhost:8000/api/video-ingestion/sources
```

### Get Source Status

```bash
curl http://localhost:8000/api/video-ingestion/sources/{source_id}
```

### Pause/Resume Source

```bash
# Pause
curl -X POST http://localhost:8000/api/video-ingestion/sources/{source_id}/pause

# Resume
curl -X POST http://localhost:8000/api/video-ingestion/sources/{source_id}/resume
```

### Remove Source

```bash
curl -X DELETE http://localhost:8000/api/video-ingestion/sources/{source_id}
```

### Get Metrics

```bash
curl http://localhost:8000/api/video-ingestion/metrics
```

---

## 🔍 Monitoring & Troubleshooting

### Check Service Health

```bash
# FastAPI health check
curl http://localhost:8000/health

# Ready check
curl http://localhost:8000/ready
```

### View Logs

```bash
# Backend logs
docker-compose logs -f backend

# Or if running locally
# Logs are in ./logs/retailvision_ai.log
tail -f logs/retailvision_ai.log
```

### Common Issues & Solutions

#### **Issue: "Failed to open stream"**

**Causes:**
- Camera URL is incorrect
- Network connectivity problem
- Camera offline

**Solutions:**
```bash
# Test connectivity
ping camera.local

# Test RTSP port
telnet camera.local 554

# Try different stream paths
# Hikvision: rtsp://admin:password@camera/stream
# Dahua: rtsp://admin:password@camera/livestream
```

#### **Issue: High CPU Usage**

**Causes:**
- Too many concurrent sources
- FPS set too high
- GPU not available

**Solutions:**
- Reduce FPS in config (set to 15 instead of 30)
- Reduce resolution
- Limit concurrent sources (max_concurrent_sources)
- Enable GPU acceleration

#### **Issue: Frames Dropping**

**Causes:**
- Buffer full
- Processing too slow
- Network congestion

**Solutions:**
- Increase buffer_capacity
- Reduce FPS
- Lower resolution
- Enable frame deduplication

#### **Issue: GPU Memory Error**

**Cause:**
- GPU memory exhausted

**Solution:**
```bash
# Reduce GPU memory allocation in config
"gpu_memory_fraction": 0.3  # Instead of 0.5
```

---

## 🚀 Production Deployment

### Docker Compose (Complete Stack)

```bash
# Development with hot-reload
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

### Kubernetes (Production-Ready)

See `docs/DEPLOYMENT.md` for Kubernetes setup.

---

## 📈 Performance Optimization

### FPS Configuration by Use Case

| Use Case | Recommended FPS | Reason |
|---|---|---|
| Customer Tracking | 30 | High precision movement |
| Entrance Monitoring | 15 | Sufficient for detection |
| Shelf Monitoring | 10 | Low motion area |
| Archive Recording | 5 | Offline analysis |

### Memory Optimization

```json
{
  "buffer_capacity": 500,
  "enable_frame_dedup": true,
  "enable_keyframe_priority": true,
  "resolution": [1280, 720]
}
```

**Expected Memory Usage:**
- Per source at 1280x720: ~100-200 MB
- 10 sources: ~1-2 GB total

### GPU Optimization

```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU memory
python -c "import torch; print(torch.cuda.mem_get_info())"

# Reduce memory usage if needed
"gpu_memory_fraction": 0.3
```

---

## 📝 Example Workflows

### Scenario 1: Multi-Camera Store Monitoring

**Config:**
```json
{
  "sources": [
    {"id": "entrance", "type": "RTSP", "url": "rtsp://cam1.local/stream", "fps": 30},
    {"id": "aisle1", "type": "RTSP", "url": "rtsp://cam2.local/stream", "fps": 20},
    {"id": "checkout", "type": "RTSP", "url": "rtsp://cam3.local/stream", "fps": 30},
    {"id": "warehouse", "type": "RTSP", "url": "rtsp://cam4.local/stream", "fps": 10}
  ]
}
```

**Start:**
```bash
python scripts/start_video_ingestion.py --config multi_camera_config.json
```

### Scenario 2: Webcam Testing

**Without config:**
```bash
python scripts/start_video_ingestion.py --source-webcam
```

### Scenario 3: Archive Processing

**Config:**
```json
{
  "sources": [
    {
      "id": "daily_archive",
      "type": "LOCAL_FILE",
      "url": "/data/archive/2024-01-15.mp4",
      "fps": 1,
      "loop": false
    }
  ]
}
```

---

## 🔗 Integration with Analytics

After video ingestion, frames are available for:

1. **YOLOv11 Detection** (Phase 3)
2. **ByteTrack Tracking** (Phase 3)
3. **Shelf Analysis** (Phase 4)
4. **Heatmap Generation** (Phase 4)

Get frame for processing:

```python
# Python client
import asyncio
from app.services.video_ingestion_service import get_video_ingestion_service

async def get_latest_frame():
    service = await get_video_ingestion_service()
    result = await service.get_frame("store_front", timeout_seconds=5.0)
    if result:
        frame_data, metadata = result
        # Process frame...
```

---

## 📚 References

- [OpenCV VideoCapture](https://docs.opencv.org/4.8.0/d8/dfe/classcv_1_1VideoCapture.html)
- [RTSP RFC 2326](https://tools.ietf.org/html/rfc2326)
- [FFmpeg Protocols](https://ffmpeg.org/ffmpeg-protocols.html)
- [CUDA Video Decoding](https://developer.nvidia.com/video-codec-sdk)

---

**Status**: ✅ Production Ready  
**Last Updated**: 2024  
**Phase**: 2
