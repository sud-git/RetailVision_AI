"""
Structured logging configuration.
Provides JSON and text logging with rotation and level management.
"""

import logging
import logging.config
import json
import sys
from pathlib import Path
from typing import Optional

import structlog
from pythonjsonlogger import jsonlogger

from app.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = self.formatTime(record)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['service'] = settings.service_name
        log_record['version'] = settings.service_version
        log_record['environment'] = settings.environment


def setup_logging():
    """Configure structured logging."""

    # Create logs directory if it doesn't exist
    Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)

    # Configure standard logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': CustomJsonFormatter,
                'format': '%(message)s'
            },
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': settings.log_level,
                'formatter': settings.log_format,
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': settings.log_level,
                'formatter': settings.log_format,
                'filename': settings.log_file,
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            'app': {
                'level': settings.log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'uvicorn': {
                'level': settings.log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'sqlalchemy': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'redis': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level': settings.log_level,
            'handlers': ['console', 'file']
        }
    }

    logging.config.dictConfig(logging_config)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# Initialize logging on module import
setup_logging()
