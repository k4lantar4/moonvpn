"""
Resource Optimization API Endpoints

This module contains the FastAPI endpoints for resource optimization functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List
from datetime import datetime

from core.schemas.resource_optimization import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationStatusResponse,
    OptimizationHistoryResponse,
    ResourceMetricsResponse,
    OptimizationSummaryResponse
)
from core.services.resource_optimization import ResourceOptimizationService
from core.dependencies import get_current_user

router = APIRouter(prefix="/optimization", tags=["resource_optimization"])

@router.post("/start", response_model=OptimizationResponse)
async def start_optimization(
    request: OptimizationRequest,
    current_user: Dict = Depends(get_current_user),
    optimization_service: ResourceOptimizationService = Depends()
):
    """Start resource optimization process."""
    try:
        result = await optimization_service.start_optimization(
            resource_type=request.resource_type,
            target_usage=request.target_usage,
            max_iterations=request.max_iterations,
            interval=request.interval,
            threshold=request.threshold,
            parameters=request.parameters
        )
        return OptimizationResponse(
            success=True,
            message="Optimization started successfully",
            data={"optimization_id": result}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/stop", response_model=OptimizationResponse)
async def stop_optimization(
    current_user: Dict = Depends(get_current_user),
    optimization_service: ResourceOptimizationService = Depends()
):
    """Stop resource optimization process."""
    try:
        await optimization_service.stop_optimization()
        return OptimizationResponse(
            success=True,
            message="Optimization stopped successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/status", response_model=OptimizationStatusResponse)
async def get_optimization_status(
    current_user: Dict = Depends(get_current_user),
    optimization_service: ResourceOptimizationService = Depends()
):
    """Get current optimization status."""
    try:
        status = await optimization_service.get_status()
        return OptimizationStatusResponse(**status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/history", response_model=OptimizationHistoryResponse)
async def get_optimization_history(
    current_user: Dict = Depends(get_current_user),
    optimization_service: ResourceOptimizationService = Depends()
):
    """Get optimization history."""
    try:
        history = await optimization_service.get_history()
        return OptimizationHistoryResponse(**history)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/metrics", response_model=ResourceMetricsResponse)
async def get_resource_metrics(
    current_user: Dict = Depends(get_current_user),
    optimization_service: ResourceOptimizationService = Depends()
):
    """Get current resource metrics."""
    try:
        metrics = await optimization_service.get_metrics()
        return ResourceMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/summary", response_model=OptimizationSummaryResponse)
async def get_optimization_summary(
    current_user: Dict = Depends(get_current_user),
    optimization_service: ResourceOptimizationService = Depends()
):
    """Get optimization summary."""
    try:
        summary = await optimization_service.get_summary()
        return OptimizationSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 