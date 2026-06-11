# 🎬 PHASE 2: Video Ingestion Pipeline

**Building Production-Ready Real-Time CCTV Stream Processing**

---

## 📋 Overview

Phase 2 implements a robust, scalable video ingestion pipeline that handles multiple concurrent video sources with async processing, intelligent buffering, and GPU-accelerated frame extraction.

### Key Objectives

✅ **Multi-Source Support**: RTSP streams, webcams, local video files  
✅ **Async Processing**: Non-blocking frame extraction with queue management  
✅ **Intelligent Buffering**: Frame deduplication, capacity management, backpressure handling  
✅ **Reliable Streaming**: Auto-reconnect, retry logic, health monitoring  
✅ **GPU Optimization**: Hardware acceleration with graceful CPU fallback  
✅ **Production Ready**: Structured logging, error handling, monitoring  

---

## 🏗️ Architecture

### System Design

```
┌────────────────────────────────────────────────────────────┐
│                    VIDEO SOURCES                            │
│  RTSP Stream    Webcam (USB)    Local File                │
└────────────┬────────────────────────┬─────────────────────┘
             │                        │
             ▼                        ▼
┌────────────────────────────────────────────────────────────┐
│            VIDEO SOURCE REGISTRY                            │
│  • Catalog all sources                                      │
│  • Manage lifecycle                                         │
│  • Route to extractors                                      │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│         ASYNC FRAME EXTRACTOR (per source)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ OpenCV VideoCapture │ FPS Control │ Decode Frame    │  │
│  │ GPU Optimization    │ Error Retry  │ Metadata        │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│        INTELLIGENT FRAME BUFFER (AsyncQueue)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • Capacity Management  (1000 frames max per source)  │  │
│  │ • Deduplication        (Skip identical frames)       │  │
│  │ • Priority Handling    (Keyframes prioritized)       │  │
│  │ • Backpressure         (Drop old frames if full)     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│         STREAM MANAGER                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • Monitor health                                     │  │
│  │ • Detect failures                                    │  │
│  │ • Auto-reconnect with exponential backoff           │  │
│  │ • Publish metrics to Redis                          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│    HEALTH MONITORING & METRICS                             │
│  • Stream status (RUNNING/DISCONNECTED/ERROR)             │
│  • Frames/sec, latency, buffer occupancy                  │
│  • Error rates, reconnection attempts                      │
│  • GPU utilization, CPU usage                              │
└────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│       REDIS STREAMS (Event Pipeline)                       │
│  frames:source:rtsp1    │  frames:source:webcam           │
│  stream_events:rtsp1    │  stream_events:webcam           │
│  stream_metrics:rtsp1   │  stream_metrics:webcam          │
└────────────────────────────────────────────────────────────┘
```

---

## 📂 Folder Structure

```
backend/
├── app/
│   ├── main.py                          [Existing - FastAPI app]
│   ├── config.py                        [Existing - Configuration]
│   ├── logger.py                        [Existing - Logging]
│   ├── database.py                      [Existing - DB]
│   ├── cache.py                         [Existing - Redis]
│   │
│   ├── video_ingestion/                 [NEW - Phase 2]
│   │   ├── __init__.py
│   │   ├── models.py                    [Video source data models]
│   │   ├── source_registry.py           [Video source management]
│   │   ├── frame_extractor.py           [Async frame extraction]
│   │   ├── stream_manager.py            [Stream lifecycle & health]
│   │   ├── async_queue.py               [Intelligent frame buffer]
│   │   ├── gpu_optimizer.py             [GPU/CPU optimization]
│   │   ├── health_monitor.py            [Stream health tracking]
│   │   └── exceptions.py                [Custom exceptions]
│   │
│   ├── api/                             [Existing - API routes]
│   │   ├── health.py                    [Existing]
│   │   └── video_ingestion.py           [NEW - Video ingestion endpoints]
│   │
│   └── services/                        [NEW - Service layer]
│       ├── __init__.py
│       └── video_ingestion_service.py   [Orchestrate pipeline]
│
├── requirements.txt                     [Updated with new deps]
│
└── scripts/                             [NEW - Utilities]
    ├── start_video_ingestion.py         [Start pipeline]
    ├── test_video_ingestion.py          [Testing script]
    ├── sample_rtsp_config.json          [RTSP stream config]
    └── test_video.mp4                   [Sample video for testing]
```

---

## 🔧 Core Components

### 1. **Video Source Models** (`models.py`)

**Defines**:
- `VideoSourceType` (RTSP, WEBCAM, LOCAL_FILE)
- `VideoSourceConfig` (connection parameters)
- `FrameMetadata` (frame info, timestamp, source)
- `StreamHealth` (status, metrics)
- `StreamEvent` (event logging)

**Key Features**:
- Type validation with Pydantic
- Default values for connection timeouts
- Automatic metadata generation

### 2. **Stream Manager** (`stream_manager.py`)

**Responsibilities**:
- Manage stream lifecycle (connect → processing → disconnect)
- Detect connection failures
- Auto-reconnect with exponential backoff
- Publish events and metrics

**Architecture**:
```python
class StreamManager:
    async def connect(source_config)      # Establish connection
    async def process_stream()             # Main processing loop
    async def health_check()               # Periodic health verification
    async def disconnect()                 # Graceful shutdown
    async def auto_reconnect()             # Retry with backoff
```

### 3. **Frame Extractor** (`frame_extractor.py`)

**Handles**:
- Opening video sources (RTSP, webcam, file)
- Extracting frames at target FPS
- GPU optimization (CUDA if available)
- Error recovery

**Features**:
- Async operation using `asyncio`
- FPS throttling (configurable frame rate)
- GPU-accelerated decode when possible
- Fallback to CPU decode
- Retry on temporary failures

### 4. **Async Queue** (`async_queue.py`)

**Intelligent Frame Buffer**:
- Capacity management (max 1000 frames)
- Duplicate frame detection
- Keyframe prioritization
- Backpressure handling (drops old frames when full)

**Operations**:
```python
async def put(frame)        # Add frame to queue
async def get() -> frame    # Retrieve next frame
async def size() -> int     # Current queue size
```

### 5. **Video Source Registry** (`source_registry.py`)

**Manages**:
- Catalog of all video sources
- Source lifecycle (add, remove, pause, resume)
- Thread-safe operations
- Metrics aggregation

**API**:
```python
registry.add_source(config)          # Register source
registry.remove_source(source_id)    # Unregister source
registry.get_source(source_id)       # Retrieve source
registry.get_all_sources()           # List all sources
registry.get_metrics()               # Aggregate metrics
```

### 6. **Health Monitor** (`health_monitor.py`)

**Tracks**:
- Stream status (RUNNING/DISCONNECTED/ERROR)
- Frames per second
- Buffer occupancy
- Latency (frame age)
- Error rates and reconnection attempts

**Publishes to Redis**:
```
stream_metrics:{source_id}
{
  "status": "RUNNING",
  "fps": 30.0,
  "frames_processed": 15432,
  "buffer_size": 45,
  "latency_ms": 150,
  "errors": 2,
  "reconnection_attempts": 0,
  "uptime_seconds": 3600
}
```

### 7. **GPU Optimizer** (`gpu_optimizer.py`)

**Features**:
- Detect GPU availability (CUDA, ROCm)
- GPU memory management
- Automatic CPU fallback
- Performance metrics

**Optimizations**:
- GPU frame decoding (if available)
- Async GPU operations
- Memory pooling for frames
- CPU fallback for compatibility

---

## 📊 Data Flow

### Single Frame Journey

```
1. FRAME EXTRACTION
   VideoCapture.read() 
   → Frame (numpy array: H×W×3, uint8)
   → Metadata (timestamp, index, source_id)

2. FRAME ENHANCEMENT (if GPU available)
   Raw Frame 
   → GPU Transfer
   → Async Processing
   → Result back to CPU

3. QUEUE INSERTION
   Frame + Metadata
   → Deduplication check
   → Keyframe detection
   → Priority determination
   → Add to AsyncQueue

4. QUEUE MANAGEMENT
   AsyncQueue (max 1000 frames)
   → Size check
   → If full: Drop oldest non-keyframe
   → Publish metrics

5. CONSUMER RETRIEVAL
   Next frame from queue
   → Hand to analytics pipeline
   → Analytics processes (detection, tracking)
   → Results to Redis Streams

6. METRICS PUBLICATION
   Metrics aggregation
   → Frame count, FPS, latency
   → Publish to stream_metrics:{source_id}
```

### Multi-Source Orchestration

```
┌─────────────────────────────────────────────┐
│ VideoIngestionService (Main Orchestrator)   │
└────────────┬────────────────────────────────┘
             │
    ┌────────┴────────┬───────────┬──────────┐
    │                 │           │          │
    ▼                 ▼           ▼          ▼
 StreamManager    StreamManager  ...  StreamManager
    │                 │           │          │
    ▼                 ▼           ▼          ▼
 RTSP Source 1   Webcam 0    Local File   RTSP Source 2
```

Each source runs independently in async tasks, all coordinated by `VideoIngestionService`.

---

## 🎯 Configuration

### Example: `video_sources_config.json`

```json
{
  "sources": [
    {
      "id": "rtsp_store_front",
      "type": "RTSP",
      "url": "rtsp://camera1.local:554/stream",
      "username": "admin",
      "password": "***",
      "fps": 30,
      "resolution": [1920, 1080],
      "buffer_capacity": 1000,
      "reconnect_attempts": 5,
      "reconnect_delay_ms": 2000
    },
    {
      "id": "webcam_checkout",
      "type": "WEBCAM",
      "device_id": 0,
      "fps": 15,
      "resolution": [1280, 720],
      "buffer_capacity": 500
    },
    {
      "id": "archive_video_1",
      "type": "LOCAL_FILE",
      "path": "/data/videos/store_footage_2024.mp4",
      "fps": 30,
      "loop": true
    }
  ],
  "gpu_acceleration": true,
  "gpu_device_id": 0,
  "max_concurrent_sources": 10,
  "health_check_interval_seconds": 30
}
```

---

## 🚀 Usage

### 1. Start Pipeline

```bash
cd backend
python app/video_ingestion/start.py --config /path/to/config.json
```

### 2. Add Source Dynamically

```bash
curl -X POST http://localhost:8000/api/video-ingestion/sources \
  -H "Content-Type: application/json" \
  -d '{
    "id": "new_camera",
    "type": "RTSP",
    "url": "rtsp://camera2.local:554/stream",
    "fps": 30
  }'
```

### 3. Get Stream Status

```bash
curl http://localhost:8000/api/video-ingestion/sources
```

### 4. Get Stream Metrics

```bash
curl http://localhost:8000/api/video-ingestion/sources/rtsp_store_front/metrics
```

---

## 📈 Optimization Strategies

### Frame Rate Optimization

**Smart FPS Control**:
- Configurable target FPS (5 - 60 fps)
- Automatic frame skipping if processing lags
- Adaptive FPS based on buffer occupancy

### Memory Management

**Efficient Buffering**:
- Pre-allocated frame buffers (numpy arrays)
- Frame pooling to reduce allocations
- Automatic cleanup of old frames
- Max buffer size caps memory usage

### GPU Acceleration

**Hardware-Accelerated Decoding**:
- CUDA for NVIDIA GPUs
- ROCm for AMD GPUs
- Automatic fallback to CPU
- GPU memory pooling

### CPU Efficiency

**Async Operations**:
- Non-blocking I/O with `asyncio`
- Concurrent streams with task management
- Minimal GIL contention
- Efficient numpy operations

### Network Optimization

**RTSP Stream Tuning**:
- Connection pooling
- Keepalive heartbeats
- Adaptive bitrate (if camera supports)
- Intelligent retry with backoff

---

## 🧪 Testing Strategy

### Unit Tests

```bash
pytest tests/unit/test_frame_extractor.py
pytest tests/unit/test_async_queue.py
pytest tests/unit/test_health_monitor.py
```

### Integration Tests

```bash
# Test with webcam
python scripts/test_video_ingestion.py --source webcam --duration 60

# Test with RTSP (mocked)
python scripts/test_video_ingestion.py --source rtsp --mock-stream

# Test with local video
python scripts/test_video_ingestion.py --source local-file --video /path/to/video.mp4
```

### Performance Tests

```bash
# Benchmark frame extraction
python scripts/benchmark_frame_extraction.py

# Stress test with 10 concurrent sources
python scripts/stress_test.py --sources 10 --duration 300
```

---

## 📊 Metrics & Monitoring

### Published Metrics (Redis Streams)

```
stream_metrics:{source_id}
├── status             (RUNNING|DISCONNECTED|ERROR)
├── fps                (frames per second)
├── frames_processed   (total count)
├── buffer_occupancy   (current queue size)
├── latency_ms         (frame age)
├── errors_count       (total errors)
├── reconnect_attempts (total reconnects)
└── uptime_seconds     (total running time)
```

### Dashboard Integration

Frontend dashboard displays:
- Real-time stream status
- Per-source FPS
- Buffer occupancy graphs
- Error/reconnection trends
- GPU/CPU utilization

---

## 🔐 Security Considerations

**Credential Management**:
- RTSP credentials stored in environment variables
- Never log credentials
- Rotate credentials regularly

**Network Security**:
- TLS/SSL for RTSP (RTSPS)
- VPN for remote cameras
- Network segmentation

**Resource Limits**:
- Max concurrent sources (configurable)
- Max buffer size per source
- Connection timeouts
- Resource monitoring

---

## 🛠️ Troubleshooting

### Common Issues

**RTSP Connection Fails**
- Check network connectivity
- Verify camera URL format
- Confirm credentials
- Check firewall rules

**High Memory Usage**
- Reduce buffer capacity
- Lower FPS
- Check for memory leaks in loop
- Monitor GPU memory

**Frames Dropping**
- Increase buffer capacity
- Lower FPS
- Reduce video resolution
- Check CPU/GPU utilization

**GPU Not Detected**
- Verify CUDA/ROCm installation
- Check device compatibility
- Falls back to CPU (no error)

---

## 📚 Next Steps (Phase 2 → Phase 3)

✅ Phase 2: Video Ingestion (This)
→ Phase 3: Detection & Tracking Pipeline
  - YOLOv11 integration
  - ByteTrack implementation
  - Real-time inference
  - Result publishing

---

## 📖 References

- **OpenCV Documentation**: https://docs.opencv.org
- **FFmpeg Protocols**: https://ffmpeg.org/ffmpeg-protocols.html
- **RTSP RFC**: https://tools.ietf.org/html/rfc2326
- **CUDA Video Decoding**: https://developer.nvidia.com/nvidia-video-codec-sdk
- **asyncio Best Practices**: https://docs.python.org/3/library/asyncio.html

---

**Status**: 🔨 In Development  
**Last Updated**: 2024  
**Phase**: 2 of 4
