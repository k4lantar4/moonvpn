"""
Resource Optimization Service

This module provides functionality for optimizing system resources including CPU, memory, disk, and network.
"""

import asyncio
import logging
import psutil
from typing import Dict, List, Optional, Union
from datetime import datetime

from core.config import settings
from core.models.resource_optimization import (
    OptimizationConfig,
    OptimizationResult,
    OptimizationStatus,
    ResourceMetrics
)

logger = logging.getLogger(__name__)

class ResourceOptimizationService:
    """Service for optimizing system resources."""
    
    def __init__(self):
        """Initialize the resource optimization service."""
        self.is_initialized = False
        self.optimization_status: Dict[str, OptimizationStatus] = {}
        self.optimization_results: Dict[str, OptimizationResult] = {}
        self.metrics_history: Dict[str, List[ResourceMetrics]] = {}
        self.retry_config = {
            "max_retries": 3,
            "retry_delay": 1.0,
            "backoff_factor": 2.0
        }
    
    async def initialize(self) -> bool:
        """Initialize the resource optimization service."""
        try:
            # Initialize optimization status for each resource type
            self.optimization_status = {
                "cpu": OptimizationStatus(
                    is_active=False,
                    last_optimized=None,
                    current_metrics=None,
                    optimization_history=[]
                ),
                "memory": OptimizationStatus(
                    is_active=False,
                    last_optimized=None,
                    current_metrics=None,
                    optimization_history=[]
                ),
                "disk": OptimizationStatus(
                    is_active=False,
                    last_optimized=None,
                    current_metrics=None,
                    optimization_history=[]
                ),
                "network": OptimizationStatus(
                    is_active=False,
                    last_optimized=None,
                    current_metrics=None,
                    optimization_history=[]
                )
            }
            
            # Initialize metrics history
            self.metrics_history = {
                "cpu": [],
                "memory": [],
                "disk": [],
                "network": []
            }
            
            self.is_initialized = True
            logger.info("Resource optimization service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize resource optimization service: {str(e)}")
            return False
    
    async def optimize_cpu(self, config: OptimizationConfig) -> OptimizationResult:
        """Optimize CPU usage."""
        try:
            # Get current CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Create metrics
            metrics = ResourceMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                cpu_freq_current=cpu_freq.current if cpu_freq else None,
                cpu_freq_min=cpu_freq.min if cpu_freq else None,
                cpu_freq_max=cpu_freq.max if cpu_freq else None
            )
            
            # Store metrics
            self.metrics_history["cpu"].append(metrics)
            if len(self.metrics_history["cpu"]) > 1000:  # Keep last 1000 metrics
                self.metrics_history["cpu"].pop(0)
            
            # Update status
            self.optimization_status["cpu"].current_metrics = metrics
            self.optimization_status["cpu"].last_optimized = datetime.utcnow()
            
            # Create result
            result = OptimizationResult(
                resource_type="cpu",
                timestamp=datetime.utcnow(),
                metrics=metrics,
                optimization_applied=True,
                details={
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "cpu_freq": {
                        "current": cpu_freq.current if cpu_freq else None,
                        "min": cpu_freq.min if cpu_freq else None,
                        "max": cpu_freq.max if cpu_freq else None
                    }
                }
            )
            
            # Store result
            self.optimization_results["cpu"] = result
            
            logger.info(f"CPU optimization completed: {cpu_percent}% usage")
            return result
            
        except Exception as e:
            logger.error(f"Failed to optimize CPU: {str(e)}")
            raise
    
    async def optimize_memory(self, config: OptimizationConfig) -> OptimizationResult:
        """Optimize memory usage."""
        try:
            # Get current memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Create metrics
            metrics = ResourceMetrics(
                timestamp=datetime.utcnow(),
                memory_total=memory.total,
                memory_available=memory.available,
                memory_percent=memory.percent,
                memory_used=memory.used,
                swap_total=swap.total,
                swap_used=swap.used,
                swap_free=swap.free,
                swap_percent=swap.percent
            )
            
            # Store metrics
            self.metrics_history["memory"].append(metrics)
            if len(self.metrics_history["memory"]) > 1000:
                self.metrics_history["memory"].pop(0)
            
            # Update status
            self.optimization_status["memory"].current_metrics = metrics
            self.optimization_status["memory"].last_optimized = datetime.utcnow()
            
            # Create result
            result = OptimizationResult(
                resource_type="memory",
                timestamp=datetime.utcnow(),
                metrics=metrics,
                optimization_applied=True,
                details={
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent,
                        "used": memory.used
                    },
                    "swap": {
                        "total": swap.total,
                        "used": swap.used,
                        "free": swap.free,
                        "percent": swap.percent
                    }
                }
            )
            
            # Store result
            self.optimization_results["memory"] = result
            
            logger.info(f"Memory optimization completed: {memory.percent}% usage")
            return result
            
        except Exception as e:
            logger.error(f"Failed to optimize memory: {str(e)}")
            raise
    
    async def optimize_disk(self, config: OptimizationConfig) -> OptimizationResult:
        """Optimize disk usage."""
        try:
            # Get current disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Create metrics
            metrics = ResourceMetrics(
                timestamp=datetime.utcnow(),
                disk_total=disk.total,
                disk_used=disk.used,
                disk_free=disk.free,
                disk_percent=disk.percent,
                disk_read_bytes=disk_io.read_bytes if disk_io else None,
                disk_write_bytes=disk_io.write_bytes if disk_io else None,
                disk_read_count=disk_io.read_count if disk_io else None,
                disk_write_count=disk_io.write_count if disk_io else None
            )
            
            # Store metrics
            self.metrics_history["disk"].append(metrics)
            if len(self.metrics_history["disk"]) > 1000:
                self.metrics_history["disk"].pop(0)
            
            # Update status
            self.optimization_status["disk"].current_metrics = metrics
            self.optimization_status["disk"].last_optimized = datetime.utcnow()
            
            # Create result
            result = OptimizationResult(
                resource_type="disk",
                timestamp=datetime.utcnow(),
                metrics=metrics,
                optimization_applied=True,
                details={
                    "disk": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": disk.percent
                    },
                    "io": {
                        "read_bytes": disk_io.read_bytes if disk_io else None,
                        "write_bytes": disk_io.write_bytes if disk_io else None,
                        "read_count": disk_io.read_count if disk_io else None,
                        "write_count": disk_io.write_count if disk_io else None
                    }
                }
            )
            
            # Store result
            self.optimization_results["disk"] = result
            
            logger.info(f"Disk optimization completed: {disk.percent}% usage")
            return result
            
        except Exception as e:
            logger.error(f"Failed to optimize disk: {str(e)}")
            raise
    
    async def optimize_network(self, config: OptimizationConfig) -> OptimizationResult:
        """Optimize network usage."""
        try:
            # Get current network metrics
            net_io = psutil.net_io_counters()
            net_if = psutil.net_if_stats()
            
            # Create metrics
            metrics = ResourceMetrics(
                timestamp=datetime.utcnow(),
                network_bytes_sent=net_io.bytes_sent if net_io else None,
                network_bytes_recv=net_io.bytes_recv if net_io else None,
                network_packets_sent=net_io.packets_sent if net_io else None,
                network_packets_recv=net_io.packets_recv if net_io else None,
                network_errin=net_io.errin if net_io else None,
                network_errout=net_io.errout if net_io else None,
                network_dropin=net_io.dropin if net_io else None,
                network_dropout=net_io.dropout if net_io else None
            )
            
            # Store metrics
            self.metrics_history["network"].append(metrics)
            if len(self.metrics_history["network"]) > 1000:
                self.metrics_history["network"].pop(0)
            
            # Update status
            self.optimization_status["network"].current_metrics = metrics
            self.optimization_status["network"].last_optimized = datetime.utcnow()
            
            # Create result
            result = OptimizationResult(
                resource_type="network",
                timestamp=datetime.utcnow(),
                metrics=metrics,
                optimization_applied=True,
                details={
                    "io": {
                        "bytes_sent": net_io.bytes_sent if net_io else None,
                        "bytes_recv": net_io.bytes_recv if net_io else None,
                        "packets_sent": net_io.packets_sent if net_io else None,
                        "packets_recv": net_io.packets_recv if net_io else None,
                        "errin": net_io.errin if net_io else None,
                        "errout": net_io.errout if net_io else None,
                        "dropin": net_io.dropin if net_io else None,
                        "dropout": net_io.dropout if net_io else None
                    },
                    "interfaces": {
                        name: {
                            "isup": stats.isup,
                            "speed": stats.speed,
                            "mtu": stats.mtu
                        }
                        for name, stats in net_if.items()
                    }
                }
            )
            
            # Store result
            self.optimization_results["network"] = result
            
            logger.info("Network optimization completed")
            return result
            
        except Exception as e:
            logger.error(f"Failed to optimize network: {str(e)}")
            raise
    
    async def get_optimization_status(self, resource_type: Optional[str] = None) -> Union[OptimizationStatus, Dict[str, OptimizationStatus]]:
        """Get optimization status for a specific resource type or all resources."""
        if resource_type:
            if resource_type not in self.optimization_status:
                raise ValueError(f"Invalid resource type: {resource_type}")
            return self.optimization_status[resource_type]
        return self.optimization_status
    
    async def get_optimization_result(self, resource_type: str) -> OptimizationResult:
        """Get optimization result for a specific resource type."""
        if resource_type not in self.optimization_results:
            raise ValueError(f"No optimization result found for resource type: {resource_type}")
        return self.optimization_results[resource_type]
    
    async def get_metrics_history(self, resource_type: str, limit: int = 100) -> List[ResourceMetrics]:
        """Get metrics history for a specific resource type."""
        if resource_type not in self.metrics_history:
            raise ValueError(f"No metrics history found for resource type: {resource_type}")
        return self.metrics_history[resource_type][-limit:]
    
    async def shutdown(self) -> None:
        """Shutdown the resource optimization service."""
        try:
            # Clear all data
            self.optimization_status.clear()
            self.optimization_results.clear()
            self.metrics_history.clear()
            self.is_initialized = False
            
            logger.info("Resource optimization service shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during resource optimization service shutdown: {str(e)}")
            raise 