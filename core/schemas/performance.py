"""
Performance testing schemas for MoonVPN.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.performance import TuningType, TuningPhase

class TestConfig(BaseModel):
    """Configuration for performance tests."""
    
    concurrent_users: int = Field(..., description="Number of concurrent users to simulate")
    actions_per_user: int = Field(..., description="Number of actions per user")
    action_delay: float = Field(..., description="Delay between actions in seconds")
    api_latency: float = Field(..., description="Simulated API latency in seconds")
    error_rate: float = Field(0.0, description="Rate of simulated API errors (0-1)")
    max_instances: int = Field(1, description="Maximum number of instances for scalability testing")
    
class TestResultBase(BaseModel):
    """Base schema for test results."""
    
    test_id: str
    user_id: Optional[int] = None
    num_instances: Optional[int] = None
    duration: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    success: bool = True
    timestamp: datetime
    
class TestResultCreate(TestResultBase):
    """Schema for creating test results."""
    
    pass
    
class TestResult(TestResultBase):
    """Schema for test results."""
    
    id: int
    
    class Config:
        orm_mode = True
        
class PerformanceTestBase(BaseModel):
    """Base schema for performance tests."""
    
    id: str
    type: str
    config: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: str
    results: List[TestResult] = []
    
class PerformanceTestCreate(BaseModel):
    """Schema for creating performance tests."""
    
    type: str
    config: TestConfig
    
class PerformanceTest(PerformanceTestBase):
    """Schema for performance tests."""
    
    class Config:
        orm_mode = True
        
class TestStatus(BaseModel):
    """Schema for test status."""
    
    test_id: str
    status: str
    results: List[TestResult] = []
    
class TestSummary(BaseModel):
    """Schema for test summary."""
    
    test_id: str
    type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: str
    total_users: int
    total_actions: int
    success_rate: float
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_disk_usage: float
    avg_duration: float

class TuningConfig(BaseModel):
    """Schema for tuning configuration."""
    
    # Database tuning settings
    max_connections: Optional[int] = Field(None, description="Maximum number of database connections")
    buffer_pool_size: Optional[int] = Field(None, description="Size of database buffer pool in MB")
    query_cache_size: Optional[int] = Field(None, description="Size of query cache in MB")
    
    # Cache tuning settings
    cache_size: Optional[int] = Field(None, description="Size of cache in MB")
    eviction_policy: Optional[str] = Field(None, description="Cache eviction policy")
    ttl: Optional[int] = Field(None, description="Cache TTL in seconds")
    
    # Network tuning settings
    tcp_keepalive: Optional[bool] = Field(None, description="Enable TCP keepalive")
    connection_timeout: Optional[int] = Field(None, description="Connection timeout in seconds")
    max_retries: Optional[int] = Field(None, description="Maximum number of retries")
    
    # Application tuning settings
    thread_pool_size: Optional[int] = Field(None, description="Size of thread pool")
    memory_limit: Optional[int] = Field(None, description="Memory limit in MB")
    gc_interval: Optional[int] = Field(None, description="Garbage collection interval in seconds")

class TuningResultCreate(BaseModel):
    """Schema for creating tuning results."""
    
    tuning_id: str = Field(..., description="ID of the tuning process")
    phase: TuningPhase = Field(..., description="Phase of the tuning process")
    metrics: Dict[str, Any] = Field(..., description="Metrics collected during tuning")
    timestamp: datetime = Field(..., description="Timestamp of the result")

class TuningResultRead(TuningResultCreate):
    """Schema for reading tuning results."""
    
    id: str = Field(..., description="ID of the tuning result")

    class Config:
        orm_mode = True

class TuningCreate(BaseModel):
    """Schema for creating performance tuning."""
    
    type: TuningType = Field(..., description="Type of tuning to perform")
    config: TuningConfig = Field(..., description="Tuning configuration")

class TuningRead(BaseModel):
    """Schema for reading performance tuning."""
    
    id: str = Field(..., description="ID of the tuning process")
    type: TuningType = Field(..., description="Type of tuning performed")
    config: TuningConfig = Field(..., description="Tuning configuration")
    start_time: datetime = Field(..., description="Start time of tuning")
    end_time: Optional[datetime] = Field(None, description="End time of tuning")
    duration: Optional[float] = Field(None, description="Duration of tuning in seconds")
    status: str = Field(..., description="Status of tuning")
    results: List[TuningResultRead] = Field(default_factory=list, description="Tuning results")

    class Config:
        orm_mode = True

class TuningStatus(BaseModel):
    """Schema for tuning status."""
    
    tuning_id: str = Field(..., description="ID of the tuning process")
    status: str = Field(..., description="Status of tuning")
    results: List[TuningResultRead] = Field(default_factory=list, description="Tuning results") 