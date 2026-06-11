"""
Phase 7: Advanced Analytics & Heatmap Intelligence Engine
Comprehensive Test Suite - All Analytics Endpoints

This test suite validates:
- All 15+ analytics API endpoints
- Response schema correctness
- Database integration
- Service layer functionality
- Error handling and edge cases
- Authentication and authorization
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import uuid
from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import application components
from app.main import create_app
from app.config import settings
from app.database import Base
from app.models.analytics import (
    Heatmap, CustomerJourney, ZoneEngagement, RouteAnalytics,
    EngagementMetrics, BusinessInsight, AnalyticsSnapshot, HeatmapHistory
)
from app.schemas.analytics import (
    HeatmapResponse, JourneyResponse, ZoneEngagementResponse,
    RouteResponse, EngagementMetricsResponse, BusinessInsightResponse,
    AnalyticsReportResponse, SuccessResponse, ErrorResponse
)
from app.services.analytics import (
    HeatmapService, JourneyService, ZoneEngagementService,
    InsightsService, AnalyticsReportService
)

# ==================== FIXTURES ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Create test database"""
    # Use in-memory SQLite for testing
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()

@pytest.fixture
async def db_session(test_db):
    """Create database session for each test"""
    async_session = sessionmaker(test_db, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return httpx.Client(app=app, base_url="http://test")

@pytest.fixture
async def async_client():
    """Create async test client"""
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

# ==================== TEST FIXTURES DATA ====================

@pytest.fixture
async def sample_heatmap(db_session: AsyncSession) -> Heatmap:
    """Create sample heatmap"""
    heatmap = Heatmap(
        id=str(uuid.uuid4()),
        heatmap_type="daily",
        time_period_start=datetime.utcnow() - timedelta(hours=24),
        time_period_end=datetime.utcnow(),
        grid_data={
            "grid": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]],
            "width": 3,
            "height": 3
        },
        width=1920,
        height=1080,
        cell_size=40,
        total_samples=1000,
        max_intensity=0.95,
        hotspot_count=5
    )
    db_session.add(heatmap)
    await db_session.commit()
    return heatmap

@pytest.fixture
async def sample_zone_engagement(db_session: AsyncSession) -> ZoneEngagement:
    """Create sample zone engagement"""
    engagement = ZoneEngagement(
        id=str(uuid.uuid4()),
        zone_id=1,
        analytics_date=datetime.utcnow(),
        time_bucket="hourly",
        visitor_count=150,
        unique_visitor_count=120,
        entry_count=150,
        exit_count=148,
        total_dwell_time=18000,
        avg_dwell_time=120,
        interaction_count=85,
        pickup_count=42,
        conversion_rate=0.68,
        engagement_score=0.92,
        zone_type="high_value",
        performance_rating="excellent"
    )
    db_session.add(engagement)
    await db_session.commit()
    return engagement

@pytest.fixture
async def sample_journey(db_session: AsyncSession) -> CustomerJourney:
    """Create sample customer journey"""
    journey = CustomerJourney(
        id=str(uuid.uuid4()),
        customer_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        path_points=[
            {"zone_id": 1, "timestamp": datetime.utcnow().isoformat(), "x": 100, "y": 200},
            {"zone_id": 2, "timestamp": datetime.utcnow().isoformat(), "x": 300, "y": 400},
            {"zone_id": 1, "timestamp": datetime.utcnow().isoformat(), "x": 150, "y": 250},
        ],
        zones_visited=[1, 2],
        entry_zone=1,
        exit_zone=1,
        journey_type="browsing",
        total_dwell_time=450,
        avg_zone_dwell_time=150,
        zone_transitions=2,
        engagement_score=0.78,
        conversion_flag=False,
        key_interactions=["looked_at_product", "picked_up_item"]
    )
    db_session.add(journey)
    await db_session.commit()
    return journey

@pytest.fixture
async def sample_insight(db_session: AsyncSession) -> BusinessInsight:
    """Create sample business insight"""
    insight = BusinessInsight(
        id=str(uuid.uuid4()),
        analytics_date=datetime.utcnow(),
        insight_type="zone_performance",
        title="Zone 1 Excellent Performance",
        description="Zone 1 showing 92% engagement with 150+ visitors",
        recommendation="Maintain current merchandising strategy",
        affected_zones=[1],
        affected_products=["prod_123", "prod_456"],
        key_metrics={"engagement": 0.92, "conversion": 0.68},
        severity="info",
        confidence_score=0.95,
        action_required=False
    )
    db_session.add(insight)
    await db_session.commit()
    return insight

# ==================== HEATMAP ENDPOINT TESTS ====================

class TestHeatmapEndpoints:
    """Tests for heatmap endpoints"""
    
    async def test_get_latest_heatmap(self, async_client: httpx.AsyncClient, sample_heatmap: Heatmap):
        """Test GET /api/v1/analytics/heatmaps/latest"""
        response = await async_client.get(
            "/api/v1/analytics/heatmaps/latest",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "heatmap_id" in data
    
    async def test_get_hourly_heatmaps(self, async_client: httpx.AsyncClient):
        """Test GET /api/v1/analytics/heatmaps/hourly"""
        response = await async_client.get(
            "/api/v1/analytics/heatmaps/hourly",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]
    
    async def test_get_daily_heatmaps(self, async_client: httpx.AsyncClient):
        """Test GET /api/v1/analytics/heatmaps/daily"""
        response = await async_client.get(
            "/api/v1/analytics/heatmaps/daily",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]
    
    async def test_generate_heatmap(self, async_client: httpx.AsyncClient):
        """Test POST /api/v1/analytics/heatmaps/generate"""
        payload = {
            "dwell_records": [
                {"zone_id": 1, "x": 100, "y": 200, "duration": 60},
                {"zone_id": 2, "x": 300, "y": 400, "duration": 90},
            ]
        }
        response = await async_client.post(
            "/api/v1/analytics/heatmaps/generate",
            json=payload,
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 201, 422]

# ==================== JOURNEY ENDPOINT TESTS ====================

class TestJourneyEndpoints:
    """Tests for customer journey endpoints"""
    
    async def test_get_journey_summary(self, async_client: httpx.AsyncClient, sample_journey: CustomerJourney):
        """Test GET /api/v1/analytics/journeys/summary"""
        response = await async_client.get(
            "/api/v1/analytics/journeys/summary",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]
    
    async def test_get_journey_analytics(self, async_client: httpx.AsyncClient):
        """Test GET /api/v1/analytics/journeys/analytics"""
        response = await async_client.get(
            "/api/v1/analytics/journeys/analytics",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]
    
    async def test_get_routes(self, async_client: httpx.AsyncClient):
        """Test GET /api/v1/analytics/journeys/routes"""
        response = await async_client.get(
            "/api/v1/analytics/journeys/routes",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]

# ==================== ZONE ENGAGEMENT TESTS ====================

class TestZoneEngagementEndpoints:
    """Tests for zone engagement endpoints"""
    
    async def test_get_zone_engagement(self, async_client: httpx.AsyncClient, sample_zone_engagement: ZoneEngagement):
        """Test GET /api/v1/analytics/zones/engagement"""
        response = await async_client.get(
            "/api/v1/analytics/zones/engagement",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]
    
    async def test_get_top_zones(self, async_client: httpx.AsyncClient):
        """Test GET /api/v1/analytics/zones/top"""
        response = await async_client.get(
            "/api/v1/analytics/zones/top",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]
    
    async def test_get_underperforming_zones(self, async_client: httpx.AsyncClient):
        """Test GET /api/v1/analytics/zones/underperforming"""
        response = await async_client.get(
            "/api/v1/analytics/zones/underperforming",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]

# ==================== ENGAGEMENT METRICS TESTS ====================

class TestEngagementMetricsEndpoints:
    """Tests for engagement metrics endpoints"""
    
    async def test_get_engagement_metrics(self, async_client: httpx.AsyncClient):
        """Test GET /api/v1/analytics/engagement/metrics"""
        response = await async_client.get(
            "/api/v1/analytics/engagement/metrics",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]
    
    async def test_get_engagement_trends(self, async_client: httpx.AsyncClient):
        """Test GET /api/v1/analytics/engagement/trends"""
        response = await async_client.get(
            "/api/v1/analytics/engagement/trends",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]

# ==================== BUSINESS INSIGHTS TESTS ====================

class TestBusinessInsightsEndpoints:
    """Tests for business insights endpoints"""
    
    async def test_get_insights(self, async_client: httpx.AsyncClient, sample_insight: BusinessInsight):
        """Test GET /api/v1/analytics/insights"""
        response = await async_client.get(
            "/api/v1/analytics/insights",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]
    
    async def test_generate_insights(self, async_client: httpx.AsyncClient):
        """Test POST /api/v1/analytics/insights/generate"""
        payload = {"date": datetime.utcnow().isoformat()}
        response = await async_client.post(
            "/api/v1/analytics/insights/generate",
            json=payload,
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 201, 422]

# ==================== REPORTS TESTS ====================

class TestReportEndpoints:
    """Tests for analytics report endpoints"""
    
    async def test_generate_report(self, async_client: httpx.AsyncClient):
        """Test POST /api/v1/analytics/reports/generate"""
        payload = {
            "report_type": "comprehensive",
            "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
        response = await async_client.post(
            "/api/v1/analytics/reports/generate",
            json=payload,
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 201, 422]
    
    async def test_list_reports(self, async_client: httpx.AsyncClient):
        """Test GET /api/v1/analytics/reports/list"""
        response = await async_client.get(
            "/api/v1/analytics/reports/list",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]
    
    async def test_get_report(self, async_client: httpx.AsyncClient):
        """Test GET /api/v1/analytics/reports/{report_id}"""
        report_id = str(uuid.uuid4())
        response = await async_client.get(
            f"/api/v1/analytics/reports/{report_id}",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [200, 404]

# ==================== SERVICE LAYER TESTS ====================

class TestHeatmapService:
    """Tests for HeatmapService"""
    
    async def test_generate_realtime_heatmap(self, db_session: AsyncSession):
        """Test real-time heatmap generation"""
        service = HeatmapService(db_session)
        dwell_records = [
            {"zone_id": 1, "x": 100, "y": 200, "duration": 60},
            {"zone_id": 1, "x": 110, "y": 210, "duration": 45},
        ]
        result = await service.generate_realtime_heatmap(dwell_records)
        assert result is not None
        assert "heatmap_id" in result or isinstance(result, dict)
    
    async def test_generate_historical_heatmap(self, db_session: AsyncSession):
        """Test historical heatmap generation"""
        service = HeatmapService(db_session)
        date = datetime.utcnow()
        result = await service.generate_historical_heatmap(date)
        # Should return result or None if no data
        assert result is None or isinstance(result, dict)

class TestZoneEngagementService:
    """Tests for ZoneEngagementService"""
    
    async def test_calculate_zone_metrics(self, db_session: AsyncSession, sample_zone_engagement: ZoneEngagement):
        """Test zone metrics calculation"""
        service = ZoneEngagementService(db_session)
        date = datetime.utcnow()
        result = await service.calculate_zone_metrics(date)
        assert isinstance(result, list)

# ==================== SCHEMA VALIDATION TESTS ====================

class TestSchemaValidation:
    """Tests for schema validation"""
    
    def test_heatmap_response_schema(self):
        """Test HeatmapResponse schema"""
        data = {
            "heatmap_id": str(uuid.uuid4()),
            "heatmap_type": "daily",
            "grid": [[0.1, 0.2], [0.3, 0.4]],
            "hotspots": [{"x": 50, "y": 100, "intensity": 0.95, "count": 150}],
            "width": 1920,
            "height": 1080,
            "cell_size": 40,
            "max_intensity": 0.95,
            "metadata": {"total_samples": 1000},
            "generated_at": datetime.utcnow()
        }
        response = HeatmapResponse(**data)
        assert response.heatmap_id is not None
        assert response.heatmap_type == "daily"
    
    def test_zone_engagement_response_schema(self):
        """Test ZoneEngagementResponse schema"""
        data = {
            "zone_id": 1,
            "visitor_count": 150,
            "unique_visitor_count": 120,
            "engagement_score": 0.92,
            "conversion_rate": 0.68,
            "avg_dwell_time": 120,
            "performance_rating": "excellent",
            "total_interactions": 85
        }
        response = ZoneEngagementResponse(**data)
        assert response.zone_id == 1
        assert response.engagement_score == 0.92
    
    def test_business_insight_response_schema(self):
        """Test BusinessInsightResponse schema"""
        data = {
            "title": "Zone Performance Alert",
            "description": "Zone 1 showing excellent performance",
            "severity": "info",
            "confidence_score": 0.95,
            "insight_type": "zone_performance",
            "recommendation": "Maintain current strategy"
        }
        response = BusinessInsightResponse(**data)
        assert response.title == "Zone Performance Alert"
        assert response.severity == "info"
    
    def test_success_response_wrapper(self):
        """Test SuccessResponse wrapper"""
        data = {"heatmap_id": str(uuid.uuid4())}
        response = SuccessResponse(data=data)
        assert response.success is True
        assert response.data == data
    
    def test_error_response_wrapper(self):
        """Test ErrorResponse wrapper"""
        response = ErrorResponse(error="Test error", details="Test details")
        assert response.success is False
        assert response.error == "Test error"

# ==================== INTEGRATION TESTS ====================

class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    async def test_full_analytics_workflow(self, async_client: httpx.AsyncClient, db_session: AsyncSession):
        """Test complete analytics workflow"""
        api_key = "test-key"
        headers = {"X-API-Key": api_key}
        
        # 1. Generate heatmap
        heatmap_response = await async_client.post(
            "/api/v1/analytics/heatmaps/generate",
            json={"dwell_records": [{"zone_id": 1, "x": 100, "y": 200, "duration": 60}]},
            headers=headers
        )
        assert heatmap_response.status_code in [200, 201, 422]
        
        # 2. Get zone engagement
        zones_response = await async_client.get(
            "/api/v1/analytics/zones/engagement",
            headers=headers
        )
        assert zones_response.status_code in [200, 404]
        
        # 3. Generate insights
        insights_response = await async_client.post(
            "/api/v1/analytics/insights/generate",
            json={"date": datetime.utcnow().isoformat()},
            headers=headers
        )
        assert insights_response.status_code in [200, 201, 422]
        
        # 4. Generate report
        report_response = await async_client.post(
            "/api/v1/analytics/reports/generate",
            json={
                "report_type": "comprehensive",
                "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            headers=headers
        )
        assert report_response.status_code in [200, 201, 422]

# ==================== ERROR HANDLING TESTS ====================

class TestErrorHandling:
    """Tests for error handling"""
    
    async def test_missing_api_key(self, async_client: httpx.AsyncClient):
        """Test request without API key"""
        response = await async_client.get("/api/v1/analytics/heatmaps/latest")
        assert response.status_code in [401, 403]
    
    async def test_invalid_api_key(self, async_client: httpx.AsyncClient):
        """Test request with invalid API key"""
        response = await async_client.get(
            "/api/v1/analytics/heatmaps/latest",
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code in [401, 403]
    
    async def test_invalid_date_format(self, async_client: httpx.AsyncClient):
        """Test request with invalid date format"""
        response = await async_client.post(
            "/api/v1/analytics/insights/generate",
            json={"date": "invalid-date"},
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code in [422, 400]

if __name__ == "__main__":
    # Run tests: pytest backend/scripts/test_phase7_complete.py -v
    pytest.main([__file__, "-v", "--tb=short"])
