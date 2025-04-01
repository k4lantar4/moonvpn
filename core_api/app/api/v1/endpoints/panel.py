from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.api.deps import get_db, get_current_active_superuser, get_current_active_user
from app.models.user import User
from app.schemas.panel import PanelClientCreate, PanelClientResponse, PanelInboundResponse, PanelClientUpdate, PanelClientConfigResponse, PanelClientQRCodeResponse
from app.services.panel_service import (
    PanelService, PanelException, PanelConnectionError, 
    PanelAuthenticationError, PanelClientNotFoundError, PanelInboundNotFoundError
)

router = APIRouter()

# --- Panel Information Endpoints --- #

@router.get("/inbounds", response_model=List[PanelInboundResponse])
def get_inbounds(
    panel_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Get all inbounds from the panel.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            inbounds = panel_service.get_inbounds()
            return inbounds
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.get("/inbounds/{inbound_id}", response_model=PanelInboundResponse)
def get_inbound_detail(
    inbound_id: int = Path(..., description="ID of the inbound to get details for"),
    panel_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Get details for a specific inbound.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            inbound = panel_service.get_inbound_detail(inbound_id=inbound_id)
            return inbound
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound with ID {inbound_id} not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

# --- Client Management Endpoints --- #

@router.post("/clients", response_model=PanelClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    client_data: PanelClientCreate,
    panel_id: Optional[int] = None,
    inbound_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Create a new client on the panel.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            client = panel_service.add_client(
                email=client_data.email,
                total_gb=client_data.total_gb,
                expire_days=client_data.expire_days,
                limit_ip=client_data.limit_ip,
                inbound_id=inbound_id,
                client_uuid=client_data.client_uuid
            )
            return client
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound with ID {inbound_id} not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.get("/clients/{email}", response_model=PanelClientResponse)
def get_client(
    email: str = Path(..., description="Email/remark of the client to get"),
    panel_id: Optional[int] = None,
    inbound_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Get client details from the panel.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            client = panel_service.get_client(
                email=email,
                inbound_id=inbound_id
            )
            return client
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with email {email} not found",
        )
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.put("/clients/{email}", response_model=Dict[str, Any])
def update_client(
    client_data: PanelClientUpdate,
    email: str = Path(..., description="Email/remark of the client to update"),
    panel_id: Optional[int] = None,
    inbound_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Update client settings on the panel.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            success = panel_service.update_client(
                email=email,
                total_gb=client_data.total_gb,
                expire_days=client_data.expire_days,
                limit_ip=client_data.limit_ip,
                inbound_id=inbound_id
            )
            return {"success": success}
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with email {email} not found",
        )
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.delete("/clients/{email}", response_model=Dict[str, bool])
def remove_client(
    email: str = Path(..., description="Email/remark of the client to remove"),
    panel_id: Optional[int] = None,
    inbound_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Remove a client from the panel.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            success = panel_service.remove_client(
                email=email,
                inbound_id=inbound_id
            )
            return {"success": success}
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with email {email} not found",
        )
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.post("/clients/{email}/enable", response_model=Dict[str, bool])
def enable_client(
    email: str = Path(..., description="Email/remark of the client to enable"),
    panel_id: Optional[int] = None,
    inbound_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Enable a client on the panel.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            success = panel_service.enable_client(
                email=email,
                inbound_id=inbound_id
            )
            return {"success": success}
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with email {email} not found",
        )
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.post("/clients/{email}/disable", response_model=Dict[str, bool])
def disable_client(
    email: str = Path(..., description="Email/remark of the client to disable"),
    panel_id: Optional[int] = None,
    inbound_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Disable a client on the panel.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            success = panel_service.disable_client(
                email=email,
                inbound_id=inbound_id
            )
            return {"success": success}
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with email {email} not found",
        )
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.get("/clients/{email}/traffic", response_model=Dict[str, Any])
def get_client_traffic(
    email: str = Path(..., description="Email/remark of the client to get traffic for"),
    panel_id: Optional[int] = None,
    inbound_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Get traffic statistics for a client.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            traffic = panel_service.get_client_traffic(
                email=email,
                inbound_id=inbound_id
            )
            return traffic
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with email {email} not found",
        )
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.post("/sync/client/{client_id}", response_model=Dict[str, Any])
def sync_client_with_panel(
    client_id: int = Path(..., description="Database ID of the client to sync"),
    panel_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Synchronize a client from the database with the panel.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            client_info = panel_service.sync_client_with_db(client_db_id=client_id)
            return {
                "success": True,
                "client": client_info
            }
    except PanelClientNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PanelInboundNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.get("/clients/{email}/config", response_model=PanelClientConfigResponse)
def get_client_config(
    email: str = Path(..., description="Email/remark of the client to get config for"),
    panel_id: Optional[int] = None,
    inbound_id: Optional[int] = None,
    protocol: Optional[str] = Query(None, description="Protocol type to filter by (vmess, vless, trojan)"),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Get client configuration details, including connection link.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            config = panel_service.get_client_config(
                email=email,
                inbound_id=inbound_id,
                protocol=protocol
            )
            return config
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with email {email} not found",
        )
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.get("/clients/{email}/qrcode", response_model=PanelClientQRCodeResponse)
def get_client_qrcode(
    email: str = Path(..., description="Email/remark of the client to get QR code for"),
    panel_id: Optional[int] = None,
    inbound_id: Optional[int] = None,
    protocol: Optional[str] = Query(None, description="Protocol type to filter by (vmess, vless, trojan)"),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Get QR code for client configuration.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            # Get client config first to get protocol and link
            config = panel_service.get_client_config(
                email=email,
                inbound_id=inbound_id,
                protocol=protocol
            )
            
            # Generate QR code
            qrcode_base64 = panel_service.get_client_qrcode(
                email=email,
                inbound_id=inbound_id,
                protocol=protocol
            )
            
            # Create response
            response = {
                "email": email,
                "protocol": config["protocol"],
                "qrcode": qrcode_base64,
                "link": config["link"]
            }
            
            return response
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with email {email} not found",
        )
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        )

@router.get("/clients/{email}/config/image", response_class=JSONResponse)
def get_client_qrcode_image(
    email: str = Path(..., description="Email/remark of the client to get QR code for"),
    panel_id: Optional[int] = None,
    inbound_id: Optional[int] = None,
    protocol: Optional[str] = Query(None, description="Protocol type to filter by (vmess, vless, trojan)"),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Get QR code for client configuration as a base64 image with content type.
    Useful for embedding directly in HTML img tags.
    Requires superuser privileges.
    """
    try:
        with PanelService(panel_id=panel_id) as panel_service:
            # Get client config first to get protocol
            config = panel_service.get_client_config(
                email=email,
                inbound_id=inbound_id,
                protocol=protocol
            )
            
            # Generate QR code
            qrcode_base64 = panel_service.get_client_qrcode(
                email=email,
                inbound_id=inbound_id,
                protocol=protocol
            )
            
            # Create response with HTML-ready image source
            return {
                "image_data_url": f"data:image/png;base64,{qrcode_base64}",
                "protocol": config["protocol"],
                "email": email
            }
    except PanelClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with email {email} not found",
        )
    except PanelInboundNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbound not found",
        )
    except PanelAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Panel authentication failed: {str(e)}",
        )
    except PanelConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to panel: {str(e)}",
        )
    except PanelException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Panel error: {str(e)}",
        ) 