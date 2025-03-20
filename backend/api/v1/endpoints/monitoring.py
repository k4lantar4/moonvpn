"""Monitoring endpoints."""
from fastapi import APIRouter, Depends
from prometheus_client import generate_latest
from starlette.responses import Response
from core.services.monitoring_service import monitoring_service

router = APIRouter()

@router.get("/metrics")
async def get_metrics() -> Response:
    """Get Prometheus metrics."""
    return Response(generate_latest(), media_type="text/plain")

@router.get("/health")
async def health_check():
    """Get system health status."""
    return monitoring_service.check_health()

@router.get("/metrics/system")
async def get_system_metrics():
    """Get detailed system metrics."""
    return monitoring_service.get_system_metrics() 