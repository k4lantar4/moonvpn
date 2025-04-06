"""
Panel Management API Routes

This module defines API routes for panel management operations.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Dict, Any, Optional, List
import logging
from core.config import get_settings
from integrations.panels.client import test_panel_connection, test_default_panel_connection

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# --- Request and Response Models ---

class PanelConnectionTestRequest(BaseModel):
    """Request model for testing connection to a panel."""
    url: HttpUrl = Field(..., description="Panel URL (including http/https and port)")
    username: str = Field(..., description="Admin username")
    password: str = Field(..., description="Admin password")
    login_path: Optional[str] = Field("/login", description="Login endpoint path")
    
    @validator('url')
    def convert_url_to_string(cls, v):
        """Convert Pydantic HttpUrl to string."""
        if isinstance(v, HttpUrl):
            return str(v)
        return v

class PanelConnectionTestResponse(BaseModel):
    """Response model for panel connection test results."""
    success: bool = Field(..., description="Whether the connection test was successful")
    url: str = Field(..., description="Panel URL that was tested")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    status: str = Field(..., description="Status of the connection (healthy, auth_failed, etc.)")
    error: Optional[str] = Field(None, description="Error message if the test failed")
    panel_info: Optional[Dict[str, Any]] = Field(None, description="Panel information if available")
    timestamp: str = Field(..., description="Timestamp of the test (ISO format)")

# --- Routes ---

@router.post(
    "/test",
    response_model=PanelConnectionTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Test connection to a 3x-ui panel",
    tags=["Panels"],
)
async def test_panel_endpoint(request: PanelConnectionTestRequest):
    """Test connection to a 3x-ui panel.
    
    This endpoint tests connectivity to a 3x-ui panel, including authentication
    and API functionality. It returns detailed status information including
    response time and any errors encountered.
    
    - **url**: Panel URL (including http/https and port)
    - **username**: Admin username
    - **password**: Admin password
    - **login_path**: Login endpoint path (optional, default: "/login")
    """
    try:
        logger.info(f"Testing panel connection to: {request.url}")
        result = await test_panel_connection(
            url=request.url,
            username=request.username,
            password=request.password,
            login_path=request.login_path
        )
        
        # Log appropriate information based on result
        if result["success"]:
            logger.info(f"Panel connection test successful: {request.url}")
        else:
            logger.warning(f"Panel connection test failed: {request.url}, Status: {result['status']}, Error: {result.get('error')}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error testing panel connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing panel connection: {str(e)}"
        )

@router.get(
    "/test/default",
    response_model=PanelConnectionTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Test connection to the default panel",
    tags=["Panels"],
)
async def test_default_panel_endpoint():
    """Test connection to the default panel configured in environment variables.
    
    This endpoint tests connectivity to the default panel configured with 
    PANEL1_* environment variables. It performs the same tests as the /test
    endpoint but doesn't require providing credentials in the request.
    """
    try:
        logger.info("Testing connection to default panel")
        result = await test_default_panel_connection()
        
        # Check if configuration is missing
        if result.get("status") == "config_error":
            logger.error(f"Default panel configuration error: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', "Panel configuration is incomplete")
            )
        
        # Log appropriate information based on result
        if result["success"]:
            logger.info(f"Default panel connection test successful: {result['url']}")
        else:
            logger.warning(f"Default panel connection test failed: {result['url']}, Status: {result['status']}, Error: {result.get('error')}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error testing default panel connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing default panel connection: {str(e)}"
        ) 