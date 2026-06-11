"""
Application configuration and settings management.
Uses Pydantic Settings for environment variable validation.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Supports .env file for local development.
    """

    # Service Configuration
    service_name: str = Field(default="RetailVision AI", env="SERVICE_NAME")
    service_version: str = Field(default="1.0.0", env="SERVICE_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # API Configuration
    api_title: str = Field(default="RetailVision AI API", env="API_TITLE")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    backend_host: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    backend_port: int = Field(default=8000, env="BACKEND_PORT")
    backend_workers: int = Field(default=4, env="BACKEND_WORKERS")

    # Database Configuration
    database_url: str = Field(
        default="postgresql://user:password@localhost/retailvision_db",
        env="DATABASE_URL"
    )
    sqlalchemy_echo: bool = Field(default=False, env="SQLALCHEMY_ECHO")

    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")

    # Video Ingestion Configuration
    video_source_type: str = Field(default="rtsp", env="VIDEO_SOURCE_TYPE")
    video_rtsp_url: str = Field(default="rtsp://localhost:554/stream", env="VIDEO_RTSP_URL")
    video_webcam_id: int = Field(default=0, env="VIDEO_WEBCAM_ID")
    video_file_path: str = Field(default="/data/video.mp4", env="VIDEO_FILE_PATH")
    video_fps_limit: int = Field(default=15, env="VIDEO_FPS_LIMIT")
    frame_buffer_size: int = Field(default=30, env="FRAME_BUFFER_SIZE")

    # Model Inference Configuration
    use_gpu: bool = Field(default=True, env="USE_GPU")
    gpu_device_id: int = Field(default=0, env="GPU_DEVICE_ID")
    yolo_confidence_threshold: float = Field(default=0.5, env="YOLO_CONFIDENCE_THRESHOLD")
    yolo_iou_threshold: float = Field(default=0.45, env="YOLO_IOU_THRESHOLD")
    tracking_confidence_threshold: float = Field(default=0.3, env="TRACKING_CONFIDENCE_THRESHOLD")

    # Shelf Zones Configuration
    shelf_zones: str = Field(
        default='[]',
        env="SHELF_ZONES"
    )

    # Redis Streams Configuration
    events_stream_key: str = Field(default="retailvision:events", env="EVENTS_STREAM_KEY")
    events_consumer_group: str = Field(default="analytics-workers", env="EVENTS_CONSUMER_GROUP")
    event_batch_size: int = Field(default=100, env="EVENT_BATCH_SIZE")

    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: str = Field(default="/logs/backend.log", env="LOG_FILE")

    # CORS Configuration
    cors_origins: str = Field(
        default='["http://localhost:3000","http://localhost:8000"]',
        env="CORS_ORIGINS"
    )

    # JWT Configuration
    jwt_secret_key: str = Field(default="change-me-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")

    # Frontend URLs
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    frontend_host: str = Field(default="0.0.0.0", env="FRONTEND_HOST")
    frontend_port: int = Field(default=3000, env="FRONTEND_PORT")

    # Next.js Configuration
    next_public_api_url: str = Field(default="http://localhost:8000", env="NEXT_PUBLIC_API_URL")
    next_public_ws_url: str = Field(default="ws://localhost:8000", env="NEXT_PUBLIC_WS_URL")

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    prometheus_metrics_enabled: bool = Field(default=True, env="PROMETHEUS_METRICS_ENABLED")

    # Storage Paths
    data_dir: str = Field(default="/data", env="DATA_DIR")
    models_dir: str = Field(default="/models", env="MODELS_DIR")
    logs_dir: str = Field(default="/logs", env="LOGS_DIR")

    # Timeouts (seconds)
    video_read_timeout: int = Field(default=30, env="VIDEO_READ_TIMEOUT")
    inference_timeout: int = Field(default=10, env="INFERENCE_TIMEOUT")
    db_query_timeout: int = Field(default=30, env="DB_QUERY_TIMEOUT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse CORS origins from JSON string."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    @validator("shelf_zones", pre=True)
    def parse_shelf_zones(cls, v: str) -> List[Dict[str, Any]]:
        """Parse shelf zones from JSON string."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    @property
    def redis_connection_string(self) -> str:
        """Build Redis connection string."""
        if self.redis_url:
            return self.redis_url
        
        password = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{password}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
