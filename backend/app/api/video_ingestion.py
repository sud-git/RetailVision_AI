"""
Video Ingestion API Routes - FastAPI endpoints for video source management

Endpoints:
- POST /api/video-ingestion/sources - Add source
- GET /api/video-ingestion/sources - List sources
- GET /api/video-ingestion/sources/{id} - Get source status
- DELETE /api/video-ingestion/sources/{id} - Remove source
- POST /api/video-ingestion/sources/{id}/pause - Pause source
- POST /api/video-ingestion/sources/{id}/resume - Resume source
- GET /api/video-ingestion/metrics - Get aggregated metrics
- GET /api/video-ingestion/sources/{id}/metrics - Get source metrics
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any
import logging

from app.services.video_ingestion_service import get_video_ingestion_service
from app.video_ingestion import VideoSourceConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video-ingestion", tags=["video-ingestion"])


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def add_video_source(config: VideoSourceConfig) -> Dict[str, Any]:
    """
    Add new video source.
    
    Args:
        config: Video source configuration
        
    Returns:
        Status message
    """
    try:
        service = await get_video_ingestion_service()
        success = await service.add_source(config)
        
        if success:
            return {
                "status": "created",
                "source_id": config.id,
                "message": f"Source '{config.id}' added successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add source '{config.id}'"
            )
    except Exception as e:
        logger.error(f"Error adding source: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/sources")
async def list_video_sources() -> Dict[str, Any]:
    """
    List all video sources.
    
    Returns:
        List of sources with status
    """
    try:
        service = await get_video_ingestion_service()
        sources = await service.get_sources()
        
        return {
            "total": len(sources),
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error listing sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sources/{source_id}")
async def get_video_source_status(source_id: str) -> Dict[str, Any]:
    """
    Get status of specific video source.
    
    Args:
        source_id: Source identifier
        
    Returns:
        Source status
    """
    try:
        service = await get_video_ingestion_service()
        status_data = await service.get_source_status(source_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source '{source_id}' not found"
            )
        
        return status_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/sources/{source_id}", status_code=status.HTTP_200_OK)
async def remove_video_source(source_id: str) -> Dict[str, str]:
    """
    Remove video source.
    
    Args:
        source_id: Source identifier
        
    Returns:
        Status message
    """
    try:
        service = await get_video_ingestion_service()
        success = await service.remove_source(source_id)
        
        if success:
            return {
                "status": "deleted",
                "source_id": source_id,
                "message": f"Source '{source_id}' removed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source '{source_id}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sources/{source_id}/pause")
async def pause_video_source(source_id: str) -> Dict[str, str]:
    """
    Pause video source processing.
    
    Args:
        source_id: Source identifier
        
    Returns:
        Status message
    """
    try:
        service = await get_video_ingestion_service()
        success = await service.pause_source(source_id)
        
        if success:
            return {
                "status": "paused",
                "source_id": source_id,
                "message": f"Source '{source_id}' paused"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source '{source_id}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sources/{source_id}/resume")
async def resume_video_source(source_id: str) -> Dict[str, str]:
    """
    Resume video source processing.
    
    Args:
        source_id: Source identifier
        
    Returns:
        Status message
    """
    try:
        service = await get_video_ingestion_service()
        success = await service.resume_source(source_id)
        
        if success:
            return {
                "status": "resumed",
                "source_id": source_id,
                "message": f"Source '{source_id}' resumed"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source '{source_id}' not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/metrics")
async def get_aggregated_metrics() -> Dict[str, Any]:
    """
    Get aggregated metrics from all sources.
    
    Returns:
        Aggregated metrics
    """
    try:
        service = await get_video_ingestion_service()
        metrics = await service.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sources/{source_id}/metrics")
async def get_source_metrics(source_id: str) -> Dict[str, Any]:
    """
    Get metrics for specific source.
    
    Args:
        source_id: Source identifier
        
    Returns:
        Source metrics
    """
    try:
        service = await get_video_ingestion_service()
        status_data = await service.get_source_status(source_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source '{source_id}' not found"
            )
        
        return {
            "source_id": source_id,
            "metrics": status_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
