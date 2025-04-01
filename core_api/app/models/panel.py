# Import necessary components from SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Import the Base class from the database configuration
from app.db.base import Base

# Define the Panel model class, inheriting from Base
class Panel(Base):
    """
    Represents a V2Ray panel instance (e.g., 3x-ui) used to manage user accounts.
    Stores connection details and metadata for interacting with the panel API.
    """
    # Define the table name explicitly
    __tablename__ = "panels"

    # Primary key column: 'id'
    id = Column(Integer, primary_key=True, index=True)

    # Panel name column: 'name'
    # - A friendly name to identify the panel (e.g., "Germany Server 1", "Main Panel")
    # - Should be unique
    name = Column(String(100), unique=True, index=True, nullable=False)

    # Panel URL or IP column: 'url'
    # - The base URL for the panel's API (e.g., "http://1.2.3.4:54321")
    # - Cannot be null
    url = Column(String(255), nullable=False)

    # Panel API Username column: 'admin_username'
    # - Username for authenticating with the panel's API
    # - Cannot be null
    # TODO: Implement secure storage (e.g., encryption)
    admin_username = Column(String(100), nullable=False)

    # Panel API Password column: 'admin_password'
    # - Password for authenticating with the panel's API
    # - Cannot be null
    # TODO: Implement secure storage (e.g., encryption)
    admin_password = Column(String(255), nullable=False) # Store securely!

    # Panel type column: 'panel_type'
    # - For supporting different panel types in future
    panel_type = Column(String(50), nullable=False, default="3x-ui")

    # Panel API path column: 'api_path'
    # - Optional - specific API path if different from URL
    api_path = Column(String(255), nullable=True)

    # Panel status column: 'is_active'
    # - Indicates if the panel is currently operational and should be used
    # - Defaults to True
    is_active = Column(Boolean, default=True)

    # Optional description column: 'description'
    description = Column(Text, nullable=True)

    # Maximum users column: 'max_users'
    # - null = unlimited
    max_users = Column(Integer, nullable=True)

    # Optional link to a server record: 'server_id'
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=True)

    # Creation timestamp column: 'created_at'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Update timestamp column: 'updated_at'
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to Server
    server = relationship("Server", back_populates="panels")

    # Relationship to Accounts to be added later
    # accounts = relationship("Account", back_populates="panel")

    # Representation method for easy debugging
    def __repr__(self) -> str:
        """
        Provides a string representation of the Panel instance.
        """
        return f"<Panel(id={self.id}, name='{self.name}', url='{self.url}', type='{self.panel_type}')>" 