from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class PanelBase(BaseModel):
    name: str
    server_ip: str
    url: str
    username: str
    password: str
    panel_type: str = "3x-ui"
    geo_location: Optional[str] = None
    country_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class PanelCreate(PanelBase):
    panel_group_id: Optional[int] = None

class PanelUpdate(BaseModel):
    name: Optional[str] = None
    server_ip: Optional[str] = None
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    panel_type: Optional[str] = None
    geo_location: Optional[str] = None
    country_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    panel_group_id: Optional[int] = None

class PanelResponse(PanelBase):
    id: int
    panel_group_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Panel Domain Schemas - Moved up to resolve forward references
class PanelDomainCreate(BaseModel):
    domain: str
    is_primary: bool = False

class PanelDomainResponse(BaseModel):
    id: int
    panel_id: int
    domain: str
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Panel Stats Schema - Moved up to resolve forward references
class PanelStatsResponse(BaseModel):
    id: int
    name: str
    online_clients: int
    total_clients: int
    current_usage_gb: float
    total_usage_gb: float
    updated_at: Optional[datetime]

class PanelDetailResponse(PanelResponse):
    """Detailed panel response with additional information"""
    domains: Optional[List[PanelDomainResponse]] = None
    stats: Optional[PanelStatsResponse] = None
    
    class Config:
        from_attributes = True

# Panel Migration Schemas
class PanelMigrationCreate(BaseModel):
    new_server_ip: str
    new_url: str
    new_geo_location: Optional[str] = None
    new_country_code: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None

class PanelMigrationComplete(BaseModel):
    affected_clients_count: int = 0
    backup_file: Optional[str] = None
    notes: Optional[str] = None

class PanelMigrationResponse(BaseModel):
    id: int
    panel_id: int
    status: str
    old_server_ip: str
    new_server_ip: str
    old_url: str
    new_url: str
    old_geo_location: Optional[str] = None
    new_geo_location: Optional[str] = None
    old_country_code: Optional[str] = None
    new_country_code: Optional[str] = None
    backup_file: Optional[str] = None
    affected_clients_count: Optional[int] = None
    performed_by: Optional[int] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Health Check Schemas
class HealthCheckRequest(BaseModel):
    """Request to check panel health."""
    panel_id: Optional[int] = None
    
class HealthCheckResponse(BaseModel):
    """Response from panel health check."""
    panel_id: int
    panel_name: str
    health_check: Dict[str, Any] 