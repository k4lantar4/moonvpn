# طرح داده‌ای برای اکانت‌ها

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClientAccountBase(BaseModel):
    user_id: int
    panel_id: int
    inbound_id: int
    remote_uuid: str
    client_name: str
    email_name: Optional[str] = None
    plan_id: int
    expires_at: datetime
    expiry_time: int
    traffic_limit: int
    data_limit: int
    traffic_used: int
    data_used: int
    status: str
    enable: bool
    config_url: Optional[str] = None
    qr_code_path: Optional[str] = None  # مسیر فایل QR Code تصویری (QR code image file path)
    inbound_ids: Optional[list] = None
    ip_limit: Optional[int] = None
    sub_updated_at: Optional[datetime] = None
    sub_last_user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class ClientAccountCreate(ClientAccountBase):
    pass

class ClientAccountUpdate(BaseModel):
    expires_at: Optional[datetime] = None
    expiry_time: Optional[int] = None
    traffic_limit: Optional[int] = None
    data_limit: Optional[int] = None
    traffic_used: Optional[int] = None
    data_used: Optional[int] = None
    status: Optional[str] = None
    enable: Optional[bool] = None
    config_url: Optional[str] = None
    qr_code_path: Optional[str] = None
    inbound_ids: Optional[list] = None
    ip_limit: Optional[int] = None
    sub_updated_at: Optional[datetime] = None
    sub_last_user_agent: Optional[str] = None

    class Config:
        orm_mode = True

class ClientAccountSchema(ClientAccountBase):
    id: int
