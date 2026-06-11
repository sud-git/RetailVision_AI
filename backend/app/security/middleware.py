"""Security middleware and authentication."""
import logging
import hashlib
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, Header, Depends
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class APIKey:
    """API key validator."""
    
    # In production, load these from a database or secure config
    VALID_KEYS = {
        "demo-key-12345": {
            "name": "Demo API Key",
            "active": True,
            "rate_limit": 1000,
            "scope": ["read", "write"]
        },
        "test-key-67890": {
            "name": "Test API Key",
            "active": True,
            "rate_limit": 100,
            "scope": ["read"]
        }
    }
    
    @staticmethod
    def validate(api_key: str) -> Optional[dict]:
        """Validate API key."""
        key_info = APIKey.VALID_KEYS.get(api_key)
        if key_info and key_info.get("active"):
            return key_info
        return None


class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.requests = defaultdict(list)  # client_id -> [timestamps]
        self.cleanup_task = None
    
    def is_rate_limited(self, client_id: str, max_requests: int, 
                       window_seconds: int = 60) -> bool:
        """Check if client is rate limited."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        self.requests[client_id] = [
            t for t in self.requests[client_id] 
            if t > cutoff
        ]
        
        if len(self.requests[client_id]) >= max_requests:
            return True
        
        self.requests[client_id].append(now)
        return False
    
    def get_remaining(self, client_id: str, max_requests: int) -> int:
        """Get remaining requests."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=60)
        
        recent = [t for t in self.requests[client_id] if t > cutoff]
        return max(0, max_requests - len(recent))


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for authentication and rate limiting."""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        """Initialize middleware."""
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.excluded_paths = [
            "/health",
            "/ready",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request."""
        # Skip auth for health checks and docs
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Extract API key
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error_code": "MISSING_API_KEY",
                    "error_message": "X-API-Key header is required",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Validate API key
        key_info = APIKey.validate(api_key)
        if not key_info:
            logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
            return JSONResponse(
                status_code=403,
                content={
                    "error_code": "INVALID_API_KEY",
                    "error_message": "Invalid or inactive API key",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Rate limiting
        client_id = api_key
        if self.rate_limiter.is_rate_limited(
            client_id,
            key_info["rate_limit"]
        ):
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "error_message": "Too many requests",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Add request metadata
        request.state.api_key = api_key
        request.state.api_key_info = key_info
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response


class InputValidator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_uuid(value: str) -> bool:
        """Validate UUID format."""
        import uuid
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize string input."""
        # Remove potentially dangerous characters
        value = value.strip()
        if len(value) > max_length:
            value = value[:max_length]
        return value
    
    @staticmethod
    def validate_json(data: dict, schema: dict) -> bool:
        """Validate JSON against schema (basic)."""
        for key, expected_type in schema.items():
            if key in data:
                if not isinstance(data[key], expected_type):
                    return False
        return True


class ExceptionHandler:
    """Global exception handler utilities."""
    
    @staticmethod
    def format_error(error_code: str, message: str, 
                    details: Optional[dict] = None) -> dict:
        """Format error response."""
        return {
            "error_code": error_code,
            "error_message": message,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def handle_validation_error(errors: list) -> dict:
        """Handle Pydantic validation errors."""
        return {
            "error_code": "VALIDATION_ERROR",
            "error_message": "Input validation failed",
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }


# Dependency for API key
async def verify_api_key(x_api_key: str = Header(None)) -> str:
    """Dependency to verify API key."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    
    if not APIKey.validate(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return x_api_key


# Global rate limiter
rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    return rate_limiter
