# Architecture Documentation

## System Overview

RetailVision AI is a production-grade, distributed system for real-time store intelligence and customer analytics. The system processes CCTV video streams, detects and tracks customers, analyzes interactions with products, and generates real-time analytics through a modern web dashboard.

## Component Architecture

### Backend (FastAPI)

**Purpose**: Core business logic, video processing, analytics, and API serving

**Key Modules**:
- `app/main.py` - FastAPI application factory
- `app/config.py` - Configuration management
- `app/database.py` - PostgreSQL/SQLAlchemy setup
- `app/cache.py` - Redis connection and operations
- `app/ml/` - Computer vision and tracking models
- `app/services/` - Business logic layer
- `app/workers/` - Background job processing
- `app/api/v1/` - REST and WebSocket endpoints

**Technology Stack**:
- Python 3.11+
- FastAPI 0.104+
- SQLAlchemy 2.0+
- PostgreSQL 16
- Redis 7+

### Frontend (Next.js)

**Purpose**: Real-time dashboard and analytics visualization

**Key Components**:
- `/app` - Next.js app router pages
- `/components` - Reusable React components
- `/lib` - Utility functions and API clients
- `/hooks` - Custom React hooks
- `/styles` - Tailwind CSS styling

**Technology Stack**:
- Next.js 14+
- React 18+
- TypeScript
- Tailwind CSS
- Recharts for visualization

### Computer Vision Pipeline

**Purpose**: Detect customers, track movements, analyze shelf interactions

**Models**:
- **YOLOv11**: Human detection and classification
- **ByteTrack**: Multi-object tracking
- **Custom zones**: Shelf interaction detection

**Processing Flow**:
```
Video Stream → Frame Extraction → Object Detection → Tracking → 
Zone Analysis → Analytics → Redis Streams → Frontend
```

### Event Streaming (Redis Streams)

**Purpose**: Real-time event pipeline for decoupled processing

**Stream Keys**:
- `retailvision:events` - Main event stream
- `retailvision:detections` - Detection events
- `retailvision:interactions` - Shelf interactions
- `retailvision:analytics` - Computed analytics

**Consumer Groups**:
- `analytics-workers` - Analytics aggregation
- `alert-workers` - Anomaly detection
- `cache-workers` - Cache updates

## Data Flow

### Real-Time Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ 1. VIDEO INGESTION                                          │
│    • RTSP/Webcam/File sources                              │
│    • Frame buffering & FPS control                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. OBJECT DETECTION (YOLOv11)                              │
│    • Customer detection with confidence threshold          │
│    • GPU acceleration with CPU fallback                    │
│    • Bounding box & confidence scores                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. MULTI-OBJECT TRACKING (ByteTrack)                       │
│    • Persistent customer IDs across frames                 │
│    • Trajectory history                                    │
│    • Velocity & acceleration metrics                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. ZONE INTERACTION ANALYSIS                               │
│    • Detect zone entry/exit events                         │
│    • Measure dwell time                                    │
│    • Detect pickup/putback interactions                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. EVENT STREAMING (Redis Streams)                         │
│    • Event serialization                                   │
│    • Stream publishing                                     │
│    • Consumer group management                             │
└────────────────┬────────────────────────────────────────────┘
                 │
     ┌───────────┼────────────────┐
     │           │                │
     ▼           ▼                ▼
┌─────────┐ ┌─────────┐      ┌──────────┐
│Analytics│ │Database │      │Cache     │
│Workers  │ │Storage  │      │Updates   │
└─────────┘ └─────────┘      └──────────┘
     │           │                │
     └───────────┼────────────────┘
                 │
                 ▼
         ┌──────────────┐
         │Frontend      │
         │WebSocket API │
         └──────────────┘
```

## Database Schema (High-Level)

### Core Tables

- **customers**: Customer tracking records
- **detections**: Frame-by-frame detections
- **interactions**: Shelf zone interactions
- **analytics**: Aggregated metrics
- **heatmaps**: Heatmap data points
- **anomalies**: Flagged suspicious behavior

## API Endpoints (v1)

### Detection APIs
- `POST /api/v1/detect/frame` - Process frame
- `GET /api/v1/customers` - List tracked customers
- `GET /api/v1/customers/{id}` - Customer details

### Analytics APIs
- `GET /api/v1/analytics/summary` - Summary metrics
- `GET /api/v1/analytics/dwell-time` - Dwell time analysis
- `GET /api/v1/analytics/heatmap` - Heatmap data
- `GET /api/v1/analytics/trends` - Trend analysis

### Event APIs
- `GET /api/v1/events` - Event stream
- `WebSocket /ws/events` - Live event stream

### Configuration APIs
- `GET /api/v1/config/zones` - Shelf zones
- `PUT /api/v1/config/zones` - Update zones

## Deployment Architecture

### Development (Docker Compose)

```
┌─────────────────────────────────────────┐
│         Docker Compose Dev              │
├─────────────────────────────────────────┤
│ ┌─────────────┐  ┌─────────────┐      │
│ │ Backend     │  │ Frontend    │      │
│ │ (Reload)    │  │ (Hot module)│      │
│ ├─────────────┤  ├─────────────┤      │
│ │ PostgreSQL  │  │ Redis       │      │
│ └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────┘
```

### Production (Docker Compose)

```
┌──────────────────────────────────────────┐
│         Docker Compose Prod              │
├──────────────────────────────────────────┤
│ ┌──────────┐  ┌──────────┐  ┌────────┐ │
│ │ Backend  │  │ Frontend │  │ Nginx  │ │
│ │ (Multi)  │  │ (Multi)  │  │ Proxy  │ │
│ ├──────────┤  ├──────────┤  ├────────┤ │
│ │ PostgreSQL  │  Redis    │         │ │
│ └──────────────────────────┘         │ │
└──────────────────────────────────────┘
```

## Scalability Considerations

### Horizontal Scaling

- **Backend**: Multiple replicas with load balancer
- **Frontend**: Static CDN with edge caching
- **Video Processing**: Distributed frame queue
- **Analytics**: Parallel stream consumer groups

### Vertical Scaling

- **GPU Acceleration**: CUDA support for YOLOv11
- **Database**: Connection pooling, index optimization
- **Cache**: Redis memory optimization
- **Memory**: Frame buffer size tuning

### Performance Optimization

- **Lazy Loading**: Models loaded on demand
- **Batch Processing**: Process frames in batches
- **Caching**: Aggressive caching of predictions
- **Compression**: Stream compression for WebSocket
- **Async/Await**: Non-blocking I/O throughout

## Monitoring & Observability

### Metrics

- Video FPS
- Detection latency
- Database query time
- Redis operations/sec
- API response time
- Memory usage
- GPU utilization

### Logging

- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized log aggregation ready
- Request/response logging

### Health Checks

- `/health` - Basic health status
- `/ready` - Readiness probe
- Database connectivity
- Redis connectivity
- Model availability

## Security Architecture

- **Authentication**: JWT-based (extensible)
- **Authorization**: Role-based access control
- **Encryption**: HTTPS/TLS for all communication
- **CORS**: Configurable origin restrictions
- **API Rate Limiting**: Ready for implementation
- **Input Validation**: Pydantic-based schema validation
- **Environment Secrets**: Secure credential management

## Next Phases

- **Phase 2**: Video ingestion pipeline implementation
- **Phase 3**: Customer detection and tracking
- **Phase 4**: Shelf interaction detection
- **Phase 5**: Redis Streams architecture
- **Phase 6**: Backend APIs
- **Phase 7**: PostgreSQL integration
- **Phase 8**: WebSocket system
- **Phase 9**: Frontend dashboard
- **Phase 10**: Heatmaps and analytics
- **Phase 11**: Anomaly detection
- **Phase 12**: Production deployment
