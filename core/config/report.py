"""
Report model for managing system reports and analytics.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class ReportType(str, enum.Enum):
    """Report type enumeration."""
    SYSTEM = "system"
    USER = "user"
    PAYMENT = "payment"
    TRAFFIC = "traffic"
    SECURITY = "security"
    CUSTOM = "custom"

class ReportFormat(str, enum.Enum):
    """Report format enumeration."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"

class Report(BaseModel):
    """
    Report model for managing system reports.
    
    Attributes:
        type: Report type
        format: Report format
        title: Report title
        description: Report description
        content: Report content
        file_path: Report file path
        generated_at: Report generation timestamp
        metadata: Additional report data
    """
    
    # Report identification
    type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(Enum(ReportFormat), nullable=False)
    
    # Report details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the report."""
        return f"<Report(type={self.type}, format={self.format})>" 