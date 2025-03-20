"""
Resource Optimization Models

This module contains the data models for resource optimization functionality.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class OptimizationConfig(BaseModel):
    """Configuration for resource optimization."""
    resource_type: str = Field(..., description="Type of resource to optimize")
    target_usage: float = Field(..., description="Target usage percentage")
    max_iterations: int = Field(default=3, description="Maximum number of optimization iterations")
    interval: float = Field(default=1.0, description="Interval between optimization attempts")
    threshold: float = Field(default=0.1, description="Threshold for considering optimization complete")
    parameters: Dict[str, any] = Field(default_factory=dict, description="Additional optimization parameters")

class ResourceMetrics(BaseModel):
    """Metrics for system resources."""
    timestamp: datetime = Field(..., description="Timestamp of the metrics")
    
    # CPU metrics
    cpu_percent: Optional[float] = Field(None, description="CPU usage percentage")
    cpu_count: Optional[int] = Field(None, description="Number of CPU cores")
    cpu_freq_current: Optional[float] = Field(None, description="Current CPU frequency")
    cpu_freq_min: Optional[float] = Field(None, description="Minimum CPU frequency")
    cpu_freq_max: Optional[float] = Field(None, description="Maximum CPU frequency")
    
    # Memory metrics
    memory_total: Optional[int] = Field(None, description="Total memory in bytes")
    memory_available: Optional[int] = Field(None, description="Available memory in bytes")
    memory_percent: Optional[float] = Field(None, description="Memory usage percentage")
    memory_used: Optional[int] = Field(None, description="Used memory in bytes")
    swap_total: Optional[int] = Field(None, description="Total swap in bytes")
    swap_used: Optional[int] = Field(None, description="Used swap in bytes")
    swap_free: Optional[int] = Field(None, description="Free swap in bytes")
    swap_percent: Optional[float] = Field(None, description="Swap usage percentage")
    
    # Disk metrics
    disk_total: Optional[int] = Field(None, description="Total disk space in bytes")
    disk_used: Optional[int] = Field(None, description="Used disk space in bytes")
    disk_free: Optional[int] = Field(None, description="Free disk space in bytes")
    disk_percent: Optional[float] = Field(None, description="Disk usage percentage")
    disk_read_bytes: Optional[int] = Field(None, description="Total bytes read from disk")
    disk_write_bytes: Optional[int] = Field(None, description="Total bytes written to disk")
    disk_read_count: Optional[int] = Field(None, description="Number of disk reads")
    disk_write_count: Optional[int] = Field(None, description="Number of disk writes")
    
    # Network metrics
    network_bytes_sent: Optional[int] = Field(None, description="Total bytes sent over network")
    network_bytes_recv: Optional[int] = Field(None, description="Total bytes received over network")
    network_packets_sent: Optional[int] = Field(None, description="Total packets sent over network")
    network_packets_recv: Optional[int] = Field(None, description="Total packets received over network")
    network_errin: Optional[int] = Field(None, description="Total network input errors")
    network_errout: Optional[int] = Field(None, description="Total network output errors")
    network_dropin: Optional[int] = Field(None, description="Total dropped input packets")
    network_dropout: Optional[int] = Field(None, description="Total dropped output packets")

class OptimizationResult(BaseModel):
    """Result of a resource optimization operation."""
    resource_type: str = Field(..., description="Type of resource that was optimized")
    timestamp: datetime = Field(..., description="Timestamp of the optimization")
    metrics: ResourceMetrics = Field(..., description="Current metrics after optimization")
    optimization_applied: bool = Field(..., description="Whether optimization was applied")
    details: Dict[str, any] = Field(..., description="Additional optimization details")

class OptimizationStatus(BaseModel):
    """Status of resource optimization."""
    is_active: bool = Field(..., description="Whether optimization is currently active")
    last_optimized: Optional[datetime] = Field(None, description="Timestamp of last optimization")
    current_metrics: Optional[ResourceMetrics] = Field(None, description="Current resource metrics")
    optimization_history: List[OptimizationResult] = Field(default_factory=list, description="History of optimization results") 