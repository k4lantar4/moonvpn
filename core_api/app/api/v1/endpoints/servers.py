from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks
from typing import List, Any, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from app import crud
from app import schemas
from app import models
from app.api import deps
from app.services.server_service import ServerService, ServerException, ServerConnectionError, ServerAuthenticationError, ServerCommandError

router = APIRouter()

@router.post("/", response_model=schemas.Server, status_code=status.HTTP_201_CREATED)
def create_server(
    *,
    db: Session = Depends(deps.get_db),
    server_in: schemas.ServerCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Create a new server configuration.
    
    Requires superuser permissions.
    """
    # Check if server with same IP already exists
    existing_server = crud.server.get_by_ip_address(db, ip_address=str(server_in.ip_address))
    if existing_server:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A server with IP '{server_in.ip_address}' already exists.",
        )
    
    # If hostname is provided, check if it's unique
    if server_in.hostname:
        hostname_server = crud.server.get_by_hostname(db, hostname=server_in.hostname)
        if hostname_server:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A server with hostname '{server_in.hostname}' already exists.",
            )
    
    server = crud.server.create(db=db, obj_in=server_in)
    return server

@router.get("/", response_model=List[schemas.Server])
def read_servers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    only_active: Optional[bool] = Query(None, description="Filter to return only active servers"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve a list of servers.
    
    Includes pagination and optional filtering by active status.
    Requires superuser permissions.
    """
    servers = crud.server.get_multi(db, skip=skip, limit=limit, only_active=only_active or False)
    return servers

@router.get("/{server_id}", response_model=schemas.Server)
def read_server(
    *,
    db: Session = Depends(deps.get_db),
    server_id: int = Path(..., description="The ID of the server to retrieve"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve a specific server by ID.
    
    Requires superuser permissions.
    """
    server = crud.server.get(db, id=server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return server

@router.put("/{server_id}", response_model=schemas.Server)
def update_server(
    *,
    db: Session = Depends(deps.get_db),
    server_id: int = Path(..., description="The ID of the server to update"),
    server_in: schemas.ServerUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Update a server configuration.
    
    Requires superuser permissions.
    """
    server = crud.server.get(db, id=server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    # Check for IP uniqueness if it's being changed
    if server_in.ip_address is not None and str(server_in.ip_address) != str(server.ip_address):
        existing_server = crud.server.get_by_ip_address(db, ip_address=str(server_in.ip_address))
        if existing_server and existing_server.id != server_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A server with IP '{server_in.ip_address}' already exists.",
            )
    
    # Check for hostname uniqueness if it's being changed
    if server_in.hostname is not None and server_in.hostname != server.hostname:
        hostname_server = crud.server.get_by_hostname(db, hostname=server_in.hostname)
        if hostname_server and hostname_server.id != server_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A server with hostname '{server_in.hostname}' already exists.",
            )
    
    server = crud.server.update(db=db, db_obj=server, obj_in=server_in)
    return server

@router.delete("/{server_id}", response_model=schemas.Server)
def delete_server(
    *,
    db: Session = Depends(deps.get_db),
    server_id: int = Path(..., description="The ID of the server to delete"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Delete a server configuration.
    
    Requires superuser permissions.
    Checks for associated panels before deletion.
    """
    server = crud.server.get(db, id=server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    # Check if the server has any associated panels
    if server.panels and len(server.panels) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete server with associated panels. Remove or reassign panels first.",
        )
    
    server = crud.server.remove(db=db, id=server_id)
    return server

@router.get("/{server_id}/panels", response_model=List[schemas.Panel])
def read_server_panels(
    *,
    db: Session = Depends(deps.get_db),
    server_id: int = Path(..., description="The ID of the server to get panels for"),
    skip: int = 0,
    limit: int = 100,
    only_active: Optional[bool] = Query(None, description="Filter to return only active panels"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve all panels associated with a specific server.
    
    Includes pagination and optional filtering by active status.
    Requires superuser permissions.
    """
    server = crud.server.get(db, id=server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    # Query panels belonging to this server with optional filtering
    query = db.query(models.Panel).filter(models.Panel.server_id == server_id)
    if only_active:
        query = query.filter(models.Panel.is_active == True)
    
    panels = query.offset(skip).limit(limit).all()
    return panels

@router.get("/{server_id}/status", response_model=Dict[str, Any])
def check_server_status(
    *,
    db: Session = Depends(deps.get_db),
    server_id: int = Path(..., description="The ID of the server to check status for"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Check the status of a server by pinging it.
    
    Requires superuser permissions.
    """
    server = crud.server.get(db, id=server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    try:
        with ServerService(server_id=server_id) as server_service:
            status_info = server_service.check_status()
            return status_info
    except ServerException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{server_id}/system-info", response_model=Dict[str, Any])
def get_server_system_info(
    *,
    db: Session = Depends(deps.get_db),
    server_id: int = Path(..., description="The ID of the server to get system info for"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Get detailed system information from the server.
    
    Requires superuser permissions.
    Uses SSH to gather CPU, memory, disk, and OS information.
    """
    server = crud.server.get(db, id=server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    try:
        with ServerService(server_id=server_id) as server_service:
            system_info = server_service.get_system_info()
            return system_info
    except ServerConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Could not connect to server: {str(e)}"
        )
    except ServerAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Authentication failed: {str(e)}"
        )
    except ServerCommandError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Command execution failed: {str(e)}"
        )
    except ServerException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.get("/{server_id}/metrics", response_model=Dict[str, Any])
def get_server_metrics(
    *,
    db: Session = Depends(deps.get_db),
    server_id: int = Path(..., description="The ID of the server to get metrics for"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Get real-time performance metrics from the server.
    
    Requires superuser permissions.
    Uses SSH to gather CPU usage, memory usage, and connection count.
    """
    server = crud.server.get(db, id=server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    try:
        with ServerService(server_id=server_id) as server_service:
            metrics = server_service.get_server_metrics()
            return metrics
    except ServerConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Could not connect to server: {str(e)}"
        )
    except ServerAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Authentication failed: {str(e)}"
        )
    except ServerCommandError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Command execution failed: {str(e)}"
        )
    except ServerException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.post("/{server_id}/restart-xray", response_model=Dict[str, Any])
def restart_xray_service(
    *,
    db: Session = Depends(deps.get_db),
    server_id: int = Path(..., description="The ID of the server to restart Xray on"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Restart the Xray service on the server.
    
    Requires superuser permissions.
    Uses SSH to execute the restart command.
    """
    server = crud.server.get(db, id=server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    try:
        with ServerService(server_id=server_id) as server_service:
            result = server_service.restart_xray()
            
            if not result["success"]:
                return {
                    "success": False,
                    "message": "Failed to restart Xray service",
                    "details": result
                }
            
            return {
                "success": True,
                "message": "Xray service restarted successfully",
                "details": result
            }
    except ServerConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Could not connect to server: {str(e)}"
        )
    except ServerAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Authentication failed: {str(e)}"
        )
    except ServerCommandError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Command execution failed: {str(e)}"
        )
    except ServerException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.post("/{server_id}/reboot", response_model=Dict[str, Any])
def reboot_server(
    *,
    db: Session = Depends(deps.get_db),
    server_id: int = Path(..., description="The ID of the server to reboot"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Reboot the server.
    
    Requires superuser permissions.
    Uses SSH to execute the reboot command.
    """
    server = crud.server.get(db, id=server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    try:
        with ServerService(server_id=server_id) as server_service:
            result = server_service.reboot_server()
            
            # Note: With a reboot, we might not get success=True since the connection
            # may be terminated before we get a response
            return {
                "success": True,
                "message": "Reboot command sent to server",
                "details": result
            }
    except ServerConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Could not connect to server: {str(e)}"
        )
    except ServerAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Authentication failed: {str(e)}"
        )
    except ServerCommandError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Command execution failed: {str(e)}"
        )
    except ServerException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.post("/{server_id}/execute", response_model=Dict[str, Any])
def execute_command(
    *,
    db: Session = Depends(deps.get_db),
    server_id: int = Path(..., description="The ID of the server to execute command on"),
    command_data: schemas.ServerCommandExecute,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Execute a custom command on the server.
    
    Requires superuser permissions.
    Uses SSH to execute the provided command.
    SECURITY WARNING: Be extremely careful with this endpoint as it allows execution of arbitrary commands!
    """
    server = crud.server.get(db, id=server_id)
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    
    # Limit allowed commands for security
    allowed_commands = [
        "systemctl status xray",
        "systemctl status nginx",
        "df -h",
        "free -m",
        "uptime",
        "cat /proc/loadavg",
        "netstat -tulpn",
        "ps aux | grep xray",
        "ls -la /etc/xray"
    ]
    
    command = command_data.command
    
    # Check if command is in allowed list or starts with an allowed command
    if not any(command == allowed or command.startswith(f"{allowed} ") for allowed in allowed_commands):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Command not allowed for security reasons. Use only pre-approved commands."
        )
    
    try:
        with ServerService(server_id=server_id) as server_service:
            result = server_service.execute_command(command)
            return result
    except ServerConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Could not connect to server: {str(e)}"
        )
    except ServerAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Authentication failed: {str(e)}"
        )
    except ServerCommandError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Command execution failed: {str(e)}"
        )
    except ServerException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.get("/batch-status", response_model=List[Dict[str, Any]])
def batch_check_server_status(
    db: Session = Depends(deps.get_db),
    server_ids: Optional[List[int]] = Query(None, description="Specific server IDs to check"),
    only_active: Optional[bool] = Query(True, description="Check only active servers"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Check status of multiple servers in one request.
    
    Requires superuser permissions.
    Optionally filter by server IDs or active status.
    """
    # Determine which servers to check
    if server_ids:
        servers = [srv for srv in db.query(models.Server).filter(models.Server.id.in_(server_ids)).all()]
    else:
        query = db.query(models.Server)
        if only_active:
            query = query.filter(models.Server.is_active == True)
        servers = query.all()
    
    if not servers:
        return []
    
    results = []
    for server in servers:
        try:
            with ServerService(server_id=server.id) as server_service:
                status_info = server_service.check_status()
                results.append(status_info)
        except Exception as e:
            # Include error info but don't break the batch operation
            results.append({
                "server_id": server.id,
                "server_name": server.name,
                "ip_address": str(server.ip_address),
                "is_up": False,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            })
    
    return results 