"""
Performance testing API endpoints for MoonVPN.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....database.session import get_db
from ....services.performance_testing import PerformanceTestingService
from ....core.security import get_current_user
from ....models.user import User
from ....schemas.performance import (
    TestConfig,
    TestResult,
    PerformanceTest,
    TestStatus,
    TestSummary
)

router = APIRouter()

@router.post("/load", response_model=str)
async def start_load_test(
    config: TestConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a load test."""
    service = PerformanceTestingService(db)
    test_id = await service.start_load_test(config)
    return test_id

@router.post("/stress", response_model=str)
async def start_stress_test(
    config: TestConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a stress test."""
    service = PerformanceTestingService(db)
    test_id = await service.start_stress_test(config)
    return test_id

@router.post("/scalability", response_model=str)
async def start_scalability_test(
    config: TestConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a scalability test."""
    service = PerformanceTestingService(db)
    test_id = await service.start_scalability_test(config)
    return test_id

@router.post("/{test_id}/stop", response_model=bool)
async def stop_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop a running test."""
    service = PerformanceTestingService(db)
    success = await service.stop_test(test_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")
    return success

@router.get("/{test_id}/status", response_model=TestStatus)
async def get_test_status(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the status of a test."""
    service = PerformanceTestingService(db)
    status = await service.get_test_status(test_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")
    return status

@router.get("/{test_id}/summary", response_model=TestSummary)
async def get_test_summary(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a summary of test results."""
    service = PerformanceTestingService(db)
    status = await service.get_test_status(test_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")
        
    # Calculate summary metrics
    results = status["results"]
    if not results:
        raise HTTPException(status_code=400, detail="No results available")
        
    total_users = len(set(r.user_id for r in results if r.user_id is not None))
    total_actions = len(results)
    success_rate = sum(1 for r in results if r.success) / total_actions
    avg_cpu_usage = sum(r.cpu_usage or 0 for r in results) / total_actions
    avg_memory_usage = sum(r.memory_usage or 0 for r in results) / total_actions
    avg_disk_usage = sum(r.disk_usage or 0 for r in results) / total_actions
    avg_duration = sum(r.duration or 0 for r in results) / total_actions
    
    return TestSummary(
        test_id=test_id,
        type=status["type"],
        start_time=status["start_time"],
        end_time=status["end_time"],
        duration=status["duration"],
        status=status["status"],
        total_users=total_users,
        total_actions=total_actions,
        success_rate=success_rate,
        avg_cpu_usage=avg_cpu_usage,
        avg_memory_usage=avg_memory_usage,
        avg_disk_usage=avg_disk_usage,
        avg_duration=avg_duration
    )

@router.get("/", response_model=List[PerformanceTest])
async def list_tests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all performance tests."""
    service = PerformanceTestingService(db)
    return service.db.query(PerformanceTest).all()

@router.get("/{test_id}/results", response_model=List[TestResult])
async def get_test_results(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed results for a test."""
    service = PerformanceTestingService(db)
    status = await service.get_test_status(test_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Test {test_id} not found")
    return status["results"] 