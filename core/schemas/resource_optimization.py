"""
Resource Optimization Schemas

This module contains the Pydantic schemas for resource optimization API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class OptimizationRequest(BaseModel):
    """Request model for starting resource optimization."""
    resource_type: str = Field(..., description="Type of resource to optimize (cpu, memory, disk, network)")
    target_usage: float = Field(..., description="Target usage percentage (0-100)")
    max_iterations: Optional[int] = Field(default=3, description="Maximum number of optimization iterations")
    interval: Optional[float] = Field(default=1.0, description="Interval between optimization attempts in seconds")
    threshold: Optional[float] = Field(default=0.1, description="Threshold for considering optimization complete")
    parameters: Optional[Dict[str, any]] = Field(default_factory=dict, description="Additional optimization parameters")

class OptimizationResponse(BaseModel):
    """Response model for optimization operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, any]] = Field(None, description="Additional response data")

class OptimizationStatusResponse(BaseModel):
    """Response model for optimization status."""
    is_active: bool = Field(..., description="Whether optimization is currently active")
    resource_type: str = Field(..., description="Type of resource being optimized")
    last_optimized: Optional[datetime] = Field(None, description="Timestamp of last optimization")
    current_metrics: Optional[Dict[str, any]] = Field(None, description="Current resource metrics")
    optimization_history: List[Dict[str, any]] = Field(default_factory=list, description="History of optimization results")

class OptimizationHistoryResponse(BaseModel):
    """Response model for optimization history."""
    total_optimizations: int = Field(..., description="Total number of optimization operations")
    successful_optimizations: int = Field(..., description="Number of successful optimizations")
    failed_optimizations: int = Field(..., description="Number of failed optimizations")
    history: List[Dict[str, any]] = Field(..., description="Detailed optimization history")

class ResourceMetricsResponse(BaseModel):
    """Response model for resource metrics."""
    timestamp: datetime = Field(..., description="Timestamp of the metrics")
    metrics: Dict[str, any] = Field(..., description="Current resource metrics")
    optimization_status: Optional[Dict[str, any]] = Field(None, description="Current optimization status")

class OptimizationSummaryResponse(BaseModel):
    """Response model for optimization summary."""
    total_optimizations: int = Field(..., description="Total number of optimization operations")
    successful_optimizations: int = Field(..., description="Number of successful optimizations")
    failed_optimizations: int = Field(..., description="Number of failed optimizations")
    average_improvement: float = Field(..., description="Average improvement in resource usage")
    best_optimization: Optional[Dict[str, any]] = Field(None, description="Details of best optimization")
    worst_optimization: Optional[Dict[str, any]] = Field(None, description="Details of worst optimization")
    resource_types: Dict[str, int] = Field(..., description="Number of optimizations per resource type") 