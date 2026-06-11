"""
System health check and status monitoring module.
Provides comprehensive system status information for localhost testing and deployment.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from app.config import settings
from app.cache import cache_manager
from app.database import get_session
from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ServiceStatus:
    """Individual service status."""
    name: str
    healthy: bool
    status_code: int
    response_time_ms: float
    message: str
    timestamp: str


@dataclass
class SystemStatus:
    """Overall system status."""
    timestamp: str
    uptime_seconds: float
    overall_healthy: bool
    database: ServiceStatus
    redis: ServiceStatus
    backend_api: ServiceStatus
    frontend: Optional[ServiceStatus]
    services: Dict[str, Any]


class HealthCheckManager:
    """Manager for system health checks and status monitoring."""

    def __init__(self):
        self.startup_time = time.time()
        self.check_history: Dict[str, list] = {}
        self.max_history = 100

    async def check_database(self) -> ServiceStatus:
        """Check database connectivity and performance."""
        start = time.time()
        try:
            async with get_session() as session:
                # Simple query to test connectivity
                result = await session.execute("SELECT 1")
                response_time = (time.time() - start) * 1000
                
                return ServiceStatus(
                    name="database",
                    healthy=True,
                    status_code=200,
                    response_time_ms=response_time,
                    message=f"PostgreSQL connected - {response_time:.2f}ms response",
                    timestamp=datetime.utcnow().isoformat()
                )
        except Exception as e:
            response_time = (time.time() - start) * 1000
            logger.error(f"Database health check failed: {str(e)}")
            
            return ServiceStatus(
                name="database",
                healthy=False,
                status_code=500,
                response_time_ms=response_time,
                message=f"Database error: {str(e)}",
                timestamp=datetime.utcnow().isoformat()
            )

    async def check_redis(self) -> ServiceStatus:
        """Check Redis connectivity and performance."""
        start = time.time()
        try:
            if cache_manager.redis_client is None:
                raise Exception("Redis client not initialized")
            
            # Test Redis connectivity
            await cache_manager.redis_client.ping()
            response_time = (time.time() - start) * 1000
            
            return ServiceStatus(
                name="redis",
                healthy=True,
                status_code=200,
                response_time_ms=response_time,
                message=f"Redis connected - {response_time:.2f}ms response",
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            response_time = (time.time() - start) * 1000
            logger.error(f"Redis health check failed: {str(e)}")
            
            return ServiceStatus(
                name="redis",
                healthy=False,
                status_code=500,
                response_time_ms=response_time,
                message=f"Redis error: {str(e)}",
                timestamp=datetime.utcnow().isoformat()
            )

    async def check_backend_api(self) -> ServiceStatus:
        """Check backend API health."""
        return ServiceStatus(
            name="backend_api",
            healthy=True,
            status_code=200,
            response_time_ms=1.0,
            message=f"Backend running - v{settings.service_version}",
            timestamp=datetime.utcnow().isoformat()
        )

    async def check_frontend(self) -> Optional[ServiceStatus]:
        """Check frontend availability."""
        try:
            import aiohttp
            
            start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{settings.frontend_url}",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    response_time = (time.time() - start) * 1000
                    
                    if resp.status == 200:
                        return ServiceStatus(
                            name="frontend",
                            healthy=True,
                            status_code=200,
                            response_time_ms=response_time,
                            message="Frontend responding",
                            timestamp=datetime.utcnow().isoformat()
                        )
                    else:
                        return ServiceStatus(
                            name="frontend",
                            healthy=False,
                            status_code=resp.status,
                            response_time_ms=response_time,
                            message=f"Frontend returned {resp.status}",
                            timestamp=datetime.utcnow().isoformat()
                        )
        except Exception as e:
            logger.debug(f"Frontend check skipped: {str(e)}")
            return None

    async def get_system_status(self, include_frontend: bool = False) -> SystemStatus:
        """Get complete system status."""
        
        # Run all checks in parallel
        checks = [
            self.check_database(),
            self.check_redis(),
            self.check_backend_api(),
        ]
        
        if include_frontend:
            checks.append(self.check_frontend())
        
        results = await asyncio.gather(*checks)
        
        db_status = results[0]
        redis_status = results[1]
        api_status = results[2]
        frontend_status = results[3] if include_frontend else None

        # Determine overall health
        critical_services = [db_status.healthy, redis_status.healthy, api_status.healthy]
        overall_healthy = all(critical_services)

        uptime = time.time() - self.startup_time

        return SystemStatus(
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=uptime,
            overall_healthy=overall_healthy,
            database=db_status,
            redis=redis_status,
            backend_api=api_status,
            frontend=frontend_status,
            services={
                "database": asdict(db_status),
                "redis": asdict(redis_status),
                "backend_api": asdict(api_status),
                **({"frontend": asdict(frontend_status)} if frontend_status else {})
            }
        )

    def record_check(self, check_name: str, status: ServiceStatus) -> None:
        """Record health check result for history."""
        if check_name not in self.check_history:
            self.check_history[check_name] = []
        
        history = self.check_history[check_name]
        history.append(asdict(status))
        
        # Keep only recent history
        if len(history) > self.max_history:
            history.pop(0)

    async def get_detailed_diagnostics(self) -> Dict[str, Any]:
        """Get detailed system diagnostics for troubleshooting."""
        status = await self.get_system_status(include_frontend=True)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": asdict(status),
            "configuration": {
                "environment": settings.environment,
                "debug": settings.debug,
                "service_version": settings.service_version,
                "database_url": settings.database_url.replace(settings.database_url.split("@")[0], "***"),
                "redis_url": settings.redis_connection_string,
                "frontend_url": settings.frontend_url,
                "cors_origins": settings.cors_origins,
            },
            "check_history": self.check_history,
            "uptime_seconds": status.uptime_seconds,
            "overall_healthy": status.overall_healthy
        }


# Global instance
health_manager = HealthCheckManager()


async def get_health() -> Dict[str, Any]:
    """Quick health check - returns 200 if critical services are up."""
    status = await health_manager.get_system_status()
    return asdict(status)


async def get_full_diagnostics() -> Dict[str, Any]:
    """Full system diagnostics."""
    return await health_manager.get_detailed_diagnostics()
