"""
FastAPI endpoint for exposing Prometheus metrics.
"""
from fastapi import APIRouter, Response
from prometheus_client import generate_latest
from app.core.metrics import get_metrics

router = APIRouter()

@router.get("/metrics")
async def metrics():
    """Expose Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")

@router.get("/metrics/json")
async def metrics_json():
    """Get metrics in JSON format."""
    return get_metrics() 