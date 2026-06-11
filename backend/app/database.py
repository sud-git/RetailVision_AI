"""
Database connection and ORM setup.
Provides SQLAlchemy session management and async database access.
"""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# SQLAlchemy ORM Base
Base = declarative_base()

# Database engine (async)
engine = None
AsyncSessionLocal = None

# Database engine (sync) - for migrations
sync_engine = None
SessionLocal = None


async def init_db():
    """Initialize async database connection."""
    global engine, AsyncSessionLocal

    logger.info("Initializing async database connection", url=settings.database_url)

    # Convert PostgreSQL URL to async PostgreSQL URL
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(
        database_url,
        echo=settings.sqlalchemy_echo,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    logger.info("Async database connection initialized")


def init_sync_db():
    """Initialize sync database connection (for migrations)."""
    global sync_engine, SessionLocal

    logger.info("Initializing sync database connection")

    database_url = settings.database_url
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    sync_engine = create_engine(
        database_url,
        echo=settings.sqlalchemy_echo,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    SessionLocal = sessionmaker(
        bind=sync_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    logger.info("Sync database connection initialized")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session.
    Yields async session and handles cleanup.
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e), exc_info=True)
            raise


async def close_db():
    """Close database connection."""
    global engine

    if engine is not None:
        await engine.dispose()
        logger.info("Database connection closed")


async def create_tables():
    """Create all database tables."""
    global engine

    if engine is None:
        raise RuntimeError("Database engine not initialized")

    logger.info("Creating database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def drop_tables():
    """Drop all database tables (use with caution)."""
    global engine

    if engine is None:
        raise RuntimeError("Database engine not initialized")

    logger.warning("Dropping all database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("Database tables dropped")
