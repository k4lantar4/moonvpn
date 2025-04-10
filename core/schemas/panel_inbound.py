import datetime
from typing import Any, Optional, Dict, Union

from pydantic import BaseModel, Field, field_validator, ConfigDict


class PanelInboundBaseSchema(BaseModel):
    """Base schema for PanelInbound, shared properties."""
    panel_inbound_id: int = Field(..., description="ID of the inbound on the panel (maps to panel's 'id')")
    tag: str = Field(..., max_length=255, description="Tag name of the inbound")
    protocol: str = Field(..., max_length=50, description="Protocol (e.g., vless, trojan)")
    port: int = Field(..., description="Listening port")
    listen_ip: Optional[str] = Field(None, description="Listening IP address (maps to panel's 'listen')")
    remark: Optional[str] = Field(None, max_length=255, description="Panel's remark for the inbound")
    settings: Optional[Dict[str, Any]] = Field(None, description="Inbound specific settings (JSON format)")
    stream_settings: Optional[Dict[str, Any]] = Field(None, description="Stream settings (JSON format)")
    total_gb: Optional[float] = Field(None, ge=0, description="Data limit in Gigabytes (converted from bytes)")
    expiry_time: Optional[Union[int, datetime.datetime]] = Field(None, description="Expiry time (timestamp in ms or datetime object)")
    panel_enabled: bool = Field(True, description="Whether the inbound is enabled on the panel")
    is_active: bool = Field(True, description="Whether the inbound is active for use in the system (our flag)")
    max_clients: Optional[int] = Field(None, description="Maximum number of clients allowed for this inbound")

    @field_validator('expiry_time', mode='before')
    @classmethod
    def convert_timestamp_ms_to_datetime(cls, v: Any) -> Optional[datetime.datetime]:
        if isinstance(v, (int, float)) and v > 0:
            try:
                return datetime.datetime.fromtimestamp(v / 1000, tz=datetime.timezone.utc)
            except (ValueError, TypeError):
                return None
        elif isinstance(v, datetime.datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=datetime.timezone.utc)
            return v.astimezone(datetime.timezone.utc)
        return None

    class Config:
        orm_mode = True
        populate_by_name = True


class PanelInboundCreateSchema(PanelInboundBaseSchema):
    """Schema used for creating new PanelInbound records in the database."""
    # No additional fields needed for creation compared to base for now
    pass


class PanelInboundSchema(PanelInboundBaseSchema):
    """Schema for representing PanelInbound data read from the database."""
    id: int = Field(..., description="Internal database ID")
    panel_id: int = Field(..., description="Foreign key referencing the panel")
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True


class PanelInboundUpdate(PanelInboundBaseSchema):
    # Fields for update
    tag: str | None = None
    # ...

class PanelInboundInDBBase(PanelInboundBaseSchema):
    id: int
    panel_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # ...

    class Config:
        orm_mode = True
        # from_attributes = True

class PanelInbound(PanelInboundInDBBase):
    pass 