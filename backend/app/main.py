"""
FastAPI application factory and lifecycle management.
Main entry point for the RetailVision AI backend service.

PHASE 5: Complete Backend Platform
- REST APIs (analytics, events, system, customers, alerts)
- Redis Streams consumer for event processing
- WebSocket support for live event streaming
- Security middleware (API key auth, rate limiting)
- Database models and services
"""

from contextlib import asynccontextmanager
import logging
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.logger import get_logger, setup_logging
from app.database import init_db, close_db, create_tables, get_session
from app.cache import init_redis, close_redis, cache_manager
from app.security.middleware import SecurityMiddleware, rate_limiter
from app.api.websocket import init_websocket, get_connection_manager, get_event_broadcaster
from app.workers.redis_consumer import init_consumer, get_consumer
from app.api.v1.routes import analytics_router, events_router, system_router, customers_router, alerts_router
from app.api.v1 import analytics as analytics_v1_module
from app.api.v1 import anomalies as anomalies_v1_module
from app.api.v1 import health as health_v1_module

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting RetailVision AI",
        version=settings.service_version,
        environment=settings.environment
    )

    consumer_task = None
    broadcaster_task = None

    try:
        # Initialize database
        await init_db()
        await create_tables()

        # Initialize Redis
        await init_redis()
        
        # Initialize WebSocket components
        init_websocket()
        logger.info("WebSocket components initialized")
        
        # Initialize Redis Stream Consumer
        redis_client = cache_manager.redis_client
        if redis_client:
            consumer = None
            try:
                from sqlalchemy.ext.asyncio import AsyncSession
                from app.database import async_session_maker
                async with async_session_maker() as session:
                    await init_consumer(redis_client, session)
                    consumer = await get_consumer()
                    if consumer:
                        consumer_task = asyncio.create_task(consumer.start())
                        logger.info("Redis Stream Consumer started")
            except Exception as e:
                logger.warning(f"Could not start Redis consumer: {e}")
        
        # Start event broadcaster
        broadcaster = get_event_broadcaster()
        if broadcaster:
            broadcaster_task = asyncio.create_task(broadcaster.broadcast_loop())
            logger.info("Event broadcaster started")

        logger.info("Application startup completed")

    except Exception as e:
        logger.error("Application startup failed", error=str(e), exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down RetailVision AI")

    try:
        # Stop consumer
        if consumer_task:
            consumer = await get_consumer()
            if consumer:
                await consumer.stop()
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
        
        # Stop broadcaster
        if broadcaster_task:
            broadcaster_task.cancel()
            try:
                await broadcaster_task
            except asyncio.CancelledError:
                pass
        
        await close_db()
        await close_redis()
        logger.info("Application shutdown completed")

    except Exception as e:
        logger.error("Application shutdown failed", error=str(e), exc_info=True)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="Real-Time Store Intelligence & Customer Analytics Platform (Phase 5: Complete Backend)",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security Middleware (API key auth & rate limiting)
    app.add_middleware(SecurityMiddleware, rate_limiter=rate_limiter)

    # Register routers
    app.include_router(analytics_router, tags=["analytics"])
    app.include_router(analytics_v1_module.router, tags=["analytics-phase7"])
    app.include_router(anomalies_v1_module.router, tags=["anomalies-phase8"])
    app.include_router(health_v1_module.router, tags=["system-health"])
    app.include_router(events_router, tags=["events"])
    app.include_router(system_router, tags=["system"])
    app.include_router(customers_router, tags=["customers"])
    app.include_router(alerts_router, tags=["alerts"])

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        try:
            # Check Redis
            redis_status = "connected" if cache_manager.redis_client else "disconnected"
        except:
            redis_status = "disconnected"
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": settings.service_name,
                "version": settings.service_version,
                "environment": settings.environment,
                "redis": redis_status,
                "phase": "Phase 5 - Complete Backend Platform"
            }
        )

    # Ready check endpoint
    @app.get("/ready")
    async def readiness_check():
        """Readiness check endpoint."""
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "service": settings.service_name,
                "phase": "Phase 5"
            }
        )

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": settings.service_name,
            "version": settings.service_version,
            "phase": "Phase 5 - Complete Backend Platform",
            "status": "running",
            "endpoints": {
                "analytics": "/api/v1/analytics",
                "events": "/api/v1/events",
                "system": "/api/v1/system",
                "customers": "/api/v1/customers",
                "alerts": "/api/v1/alerts"
            },
            "websocket": "/ws",
            "docs_url": "/docs" if settings.debug else None
        }
    
    # WebSocket endpoint for live event streaming
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for live events."""
        manager = get_connection_manager()
        if not manager:
            await websocket.close(code=1000, reason="WebSocket not initialized")
            return
        
        client_id = f"client_{id(websocket)}"
        await manager.connect(websocket, client_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                
                if data.startswith("subscribe:"):
                    channel = data.replace("subscribe:", "").strip()
                    await manager.subscribe(websocket, channel)
                
                elif data.startswith("unsubscribe:"):
                    channel = data.replace("unsubscribe:", "").strip()
                    await manager.unsubscribe(websocket, channel)
                
                elif data == "ping":
                    await manager.send_personal(
                        websocket,
                        {"type": "pong", "message": "pong"}
                    )
        
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            logger.info(f"WebSocket client {client_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(websocket)

    # Error handler
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "detail": "Internal server error",
                "error": str(exc) if settings.debug else "An error occurred",
                "phase": "Phase 5"
            }
        )

    return app


# Create application instance
app = create_app()
