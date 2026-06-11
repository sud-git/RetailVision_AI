# PHASE 8 ARCHITECTURE

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           React/Next.js Dashboard                        │  │
│  │  ┌──────────────────┐  ┌──────────────────┐             │  │
│  │  │ Alert Dashboard  │  │ Analytics        │             │  │
│  │  │ - Live feed      │  │ - Risk trends    │             │  │
│  │  │ - Filtering      │  │ - Zone heatmaps  │             │  │
│  │  │ - Management     │  │ - Reports        │             │  │
│  │  └──────────────────┘  └──────────────────┘             │  │
│  └──────────────────────────────────────────────────────────┘  │
│             ↓ HTTP/WebSocket ↓                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ REST API + WebSocket
                           │
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ REST Endpoints (20+)                                    │  │
│  │ ├─ /anomalies/...        (Anomaly management)           │  │
│  │ ├─ /alerts/...           (Alert management)             │  │
│  │ ├─ /risk-scores/...      (Risk assessment)              │  │
│  │ ├─ /statistics/...       (Reporting)                    │  │
│  │ └─ /zones/...            (Zone configuration)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ WebSocket Server                                        │  │
│  │ ├─ alert:new      → Alert created                       │  │
│  │ ├─ alert:ack      → Alert acknowledged                  │  │
│  │ ├─ anomaly:det    → Anomaly detected                    │  │
│  │ └─ risk:updated   → Risk score changed                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│             ↓ Business Logic ↓                                   │
└─────────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────────┐
│               SERVICE LAYER (Business Logic)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ AnomalyDetectionService                                │  │
│  │ ├─ Initialize zone profiles                            │  │
│  │ ├─ Run all detectors                                   │  │
│  │ ├─ Persist to database                                 │  │
│  │ └─ Update active anomalies                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ AlertService                                            │  │
│  │ ├─ Create alerts from anomalies                        │  │
│  │ ├─ Manage alert lifecycle                              │  │
│  │ ├─ Route to channels                                   │  │
│  │ └─ Handle acknowledgment/resolution                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ RiskManagementService                                  │  │
│  │ ├─ Calculate customer risk                             │  │
│  │ ├─ Calculate zone risk                                 │  │
│  │ ├─ Generate statistics                                 │  │
│  │ └─ Track trends                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│             ↓ Detection & Scoring ↓                              │
└─────────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────────┐
│           ANOMALY DETECTION & RISK SCORING LAYER                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Anomaly Detection Engine                                │  │
│  │ ├─ LoiteringDetector                                    │  │
│  │ │  └─ Dwell-time analysis per zone                     │  │
│  │ ├─ CrowdDetector                                        │  │
│  │ │  └─ Occupancy threshold monitoring                   │  │
│  │ ├─ SuspiciousBehaviorDetector                           │  │
│  │ │  ├─ Excessive interactions                           │  │
│  │ │  ├─ Rapid zone switching                             │  │
│  │ │  └─ Restricted area access                           │  │
│  │ └─ AbandonedObjectDetector                              │  │
│  │    └─ Stationarity tracking                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Risk Scoring Engine                                     │  │
│  │ ├─ CustomerRiskCalculator                               │  │
│  │ │  ├─ Anomaly factor (40%)                             │  │
│  │ │  ├─ History factor (30%)                             │  │
│  │ │  ├─ Frequency factor (20%)                           │  │
│  │ │  └─ Time factor (10%)                                │  │
│  │ ├─ ZoneRiskCalculator                                   │  │
│  │ │  ├─ Occupancy factor (35%)                           │  │
│  │ │  ├─ Anomaly density (35%)                            │  │
│  │ │  ├─ Interaction rate (20%)                           │  │
│  │ │  └─ Trend analysis (10%)                             │  │
│  │ └─ AlertPriorityEngine                                  │  │
│  │    └─ Multi-factor priority calculation (1-100)        │  │
│  └──────────────────────────────────────────────────────────┘  │
│             ↓ Data Persistence ↓                                 │
└─────────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────────┐
│              DATA PERSISTENCE LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ PostgreSQL Database                                     │  │
│  │ ├─ anomaly              (Detected anomalies)            │  │
│  │ ├─ alert                (Generated alerts)              │  │
│  │ ├─ zone_risk_profile    (Zone configuration)            │  │
│  │ ├─ alert_acknowledgment (User actions)                  │  │
│  │ ├─ anomaly_history      (Audit trail)                   │  │
│  │ ├─ risk_score_history   (Trend tracking)                │  │
│  │ └─ alert_statistics     (Aggregated stats)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Redis Cache                                             │  │
│  │ ├─ Active anomalies (fast lookup)                       │  │
│  │ ├─ Active alerts    (fast lookup)                       │  │
│  │ ├─ Zone profiles    (frequently accessed)               │  │
│  │ └─ Risk scores      (cached calculations)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│             ↑ Input Data ↑                                       │
└─────────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                                 │
│  ├─ Video Ingestion Pipeline                                   │
│  │  └─ Frame-by-frame analysis                               │
│  ├─ Customer Detection & Tracking                              │
│  │  └─ Real-time customer positions                           │
│  ├─ Zone Interaction Events                                    │
│  │  └─ Shelf interactions, zone entry/exit                    │
│  └─ Object Detection                                           │
│     └─ Items, packages, abandoned objects                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Anomaly Detection Flow

```
Input Data (from Video Pipeline)
    ↓
Customer Tracking Data
├─ customer_id, zone_id, position
├─ dwell_time, interaction_count
└─ zones_visited, speed, direction
    ↓
Zone Occupancy Data
├─ zone_id, current_occupancy
└─ occupancy_history
    ↓
Object Tracking Data
├─ object_id, position
├─ timestamp, zone_id
└─ movement_history
    ↓
═══════════════════════════════════════════
ANOMALY DETECTION ENGINE
═══════════════════════════════════════════
    ↓
Loitering Detection
├─ Dwell time > threshold?
├─ Calculate severity
└─ Generate anomaly
    ↓
Crowd Detection
├─ Occupancy > max?
├─ Calculate severity
└─ Generate anomaly
    ↓
Suspicious Behavior
├─ Interaction count > threshold?
├─ Rapid zone switches?
└─ Restricted zone access?
    ↓
Abandoned Object
├─ Object stationary > threshold?
├─ Distance < tolerance?
└─ Generate anomaly
    ↓
═══════════════════════════════════════════
DETECTED ANOMALIES
═══════════════════════════════════════════
    ↓
Store in Database
├─ anomaly table
├─ anomaly_history table
└─ Create event
    ↓
Risk Scoring
├─ Customer risk calculation
├─ Zone risk calculation
├─ Confidence scoring
└─ Severity classification
    ↓
═══════════════════════════════════════════
ALERT GENERATION
═══════════════════════════════════════════
    ↓
Create Alert
├─ alert table record
├─ Set channels
└─ Calculate priority
    ↓
Multi-Channel Distribution
├─ Dashboard (all alerts)
├─ WebSocket (real-time)
├─ Email (critical)
└─ SMS (critical)
    ↓
User Acknowledgment/Resolution
└─ Update alert status
```

---

## Component Interaction

```
Frontend Dashboard
    ↓ HTTP/REST ↓
    ↓ WebSocket ↓
API Layer (FastAPI)
    ├─ Request Validation
    ├─ Authentication (API Key)
    ├─ Rate Limiting
    └─ Response Formatting
    ↓
Service Layer
    ├─ AnomalyDetectionService
    ├─ AlertService
    └─ RiskManagementService
    ↓
Detection Engine
    ├─ Run all detectors
    ├─ Aggregate results
    └─ Persist data
    ↓
Risk Scoring
    ├─ Calculate scores
    ├─ Determine severity
    └─ Generate alerts
    ↓
Database Layer
    ├─ PostgreSQL (persistent)
    └─ Redis (cache)
```

---

## Detector Interaction

```
Incoming Data Stream
    ↓
AnomalyDetectionEngine.detect_all()
    ├─ LoiteringDetector.detect()
    │  └─ Returns: [Loitering Anomalies]
    ├─ CrowdDetector.detect()
    │  └─ Returns: [Crowd Anomalies]
    ├─ SuspiciousBehaviorDetector.detect()
    │  └─ Returns: [Behavioral Anomalies]
    └─ AbandonedObjectDetector.detect()
       └─ Returns: [Abandoned Object Anomalies]
    ↓
Merge All Results
    ├─ Combine detected anomalies
    ├─ Deduplicate
    └─ Sort by priority
    ↓
Update Master Store
    ├─ all_anomalies dict
    ├─ active_anomalies list
    └─ Update statuses
    ↓
Return to Service Layer
    └─ [All Detected Anomalies]
```

---

## Risk Scoring Flow

```
Anomaly Detected
    ↓
Risk Scoring Engine
    ├─ Get Customer Data
    │  ├─ Current anomalies
    │  ├─ History
    │  └─ Recent incidents
    │
    ├─ Calculate Customer Risk
    │  ├─ Anomaly Factor (40%)
    │  ├─ History Factor (30%)
    │  ├─ Frequency Factor (20%)
    │  └─ Time Factor (10%)
    │
    └─ Get Zone Data
       ├─ Current occupancy
       ├─ Anomaly density
       └─ Interaction rate
       
    ├─ Calculate Zone Risk
    │  ├─ Occupancy Factor (35%)
    │  ├─ Anomaly Density (35%)
    │  ├─ Interaction Rate (20%)
    │  └─ Trend Factor (10%)
    │
    └─ Generate Risk Scores
       ├─ Risk Level (LOW/MED/HIGH/CRITICAL)
       ├─ Alert Severity (INFO/WARN/HIGH/CRIT)
       ├─ Confidence (0.0-1.0)
       └─ Priority (1-100)
    ↓
Risk Score -> Database
    ├─ Store in risk_score_history
    └─ Update dashboard cache
    ↓
Determine Alert Action
    ├─ Create alert
    ├─ Set channels based on severity
    └─ Calculate priority
```

---

## Alert Lifecycle

```
DETECTED
├─ Anomaly detected by engine
├─ Risk scored
└─ Alert created
    │
    ↓
TRIGGERED
├─ Database record created
├─ Initial status: "active"
└─ Event published
    │
    ├─→ Dashboard Update (WebSocket)
    ├─→ Email Notification (if CRITICAL)
    ├─→ SMS Notification (if CRITICAL)
    └─→ Webhook Dispatch
    │
    ↓
ACKNOWLEDGED
├─ User reviews alert
├─ Clicks "Acknowledge"
├─ Status changes to "acknowledged"
└─ Timestamp recorded
    │
    ↓
RESOLVED
├─ Issue addressed (customer moved, etc.)
├─ User clicks "Resolve"
├─ Status changes to "resolved"
├─ Resolution timestamp recorded
└─ Alert removed from active list
    │
    ↓
ARCHIVED
└─ Alert moved to history
   ├─ Retained for analytics
   └─ Accessible in reports
```

---

## Configuration Hierarchy

```
System Level (environment variables)
    ├─ DEFAULT_LOITERING_THRESHOLD_SEC
    ├─ DEFAULT_CROWD_MULTIPLIER
    └─ DEFAULT_INTERACTION_THRESHOLD
    ↓
Zone Profile Level (database)
    ├─ max_occupancy
    ├─ loitering_threshold
    ├─ interaction_threshold
    └─ risk_weights
    ↓
Runtime Level (service initialization)
    ├─ Register zone profiles
    ├─ Set restricted zones
    └─ Configure detectors
    ↓
Request Level (API calls)
    └─ Per-request overrides
```

---

## Error Handling

```
Request → API Layer
    ├─ Validation Error
    │  └─ 400 Bad Request + details
    ├─ Authentication Error
    │  └─ 401 Unauthorized
    ├─ Rate Limit Error
    │  └─ 429 Too Many Requests
    └─ Service Error
       └─ 500 Internal Server Error
    ↓
Service Layer Error
    ├─ Database Error
    │  └─ Retry with exponential backoff
    ├─ Invalid Data
    │  └─ Log and skip
    └─ System Error
       └─ Alert monitoring system
    ↓
Detector Error
    ├─ Invalid Input
    │  └─ Return empty anomalies
    └─ Calculation Error
       └─ Default to safe values
    ↓
All Errors → Error Log
    └─ Logged for analysis
```

---

## Scaling Considerations

### Current Architecture (Single Instance)
- Processes up to 30 fps video stream
- Handles ~1000 anomalies/minute
- Serves ~100 concurrent dashboard users
- WebSocket: ~500 connections

### Scaling Options
1. **Horizontal Scaling**
   - Multiple FastAPI instances behind load balancer
   - Shared PostgreSQL database
   - Shared Redis cache

2. **Microservices**
   - Detection service (compute-intensive)
   - Alert service (I/O-intensive)
   - Reporting service (analytics)

3. **Caching Strategy**
   - Redis for hot data
   - Database for persistence
   - CDN for static assets

4. **Database Optimization**
   - Partitioning by date
   - Archival of old data
   - Index tuning

---

This architecture enables real-time anomaly detection, intelligent risk scoring, and multi-channel alerting while maintaining a clean, maintainable codebase ready for ML integration.
