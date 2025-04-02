# Import necessary components from FastAPI and standard libraries
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks
from typing import List, Any, Optional, Dict
from sqlalchemy.orm import Session

# Import CRUD functions, schemas, models, and dependencies
from app import crud
from app import schemas
from app import models
from app.api import deps
from app.services.panel_service import PanelService, PanelException, PanelConnectionError, PanelAuthenticationError

# Create a new FastAPI router for panel endpoints
router = APIRouter()

# --- Panel API Endpoints ---

@router.post("/", response_model=schemas.Panel, status_code=status.HTTP_201_CREATED)
def create_panel(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_in: schemas.PanelCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Create a new V2Ray panel configuration.
    
    Requires superuser permissions.
    Handles potential duplicate panel names.
    Password is required in the input but excluded from the response.
    """
    # Check if a panel with the same name already exists
    existing_panel = crud.panel.get_by_name(db, name=panel_in.name)
    if existing_panel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A panel with the name '{panel_in.name}' already exists.",
        )
    # Create the panel using the CRUD function
    # Remember that password storage should be secured in production
    panel = crud.panel.create(db=db, obj_in=panel_in)
    # The response_model=schemas.Panel ensures the password is not returned
    return panel

@router.get("/", response_model=List[schemas.Panel])
def read_panels(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    only_active: Optional[bool] = Query(None, description="Filter to return only active panels"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve a list of V2Ray panel configurations.
    
    Includes pagination and optional filtering by active status.
    Password is not included in the response.
    Requires superuser permissions.
    """
    panels = crud.panel.get_multi(db, skip=skip, limit=limit, only_active=only_active or False)
    return panels

@router.get("/{panel_id}", response_model=schemas.Panel)
def read_panel(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_id: int = Path(..., description="The ID of the panel to retrieve"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve a specific panel configuration by its ID.
    
    Handles not found errors. Password is not included.
    Requires superuser permissions.
    """
    panel = crud.panel.get(db, id=panel_id)
    if not panel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")
    return panel

@router.put("/{panel_id}", response_model=schemas.Panel)
def update_panel(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_id: int = Path(..., description="The ID of the panel to update"),
    panel_in: schemas.PanelUpdate, # Request body with update data
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Update an existing panel configuration.
    
    Requires superuser permissions.
    Handles not found errors and potential duplicate names.
    Password can be updated (sent in request) but is not returned.
    """
    panel = crud.panel.get(db, id=panel_id)
    if not panel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")

    # Check for duplicate name if the name is being changed
    if panel_in.name is not None and panel_in.name != panel.name:
        existing_panel = crud.panel.get_by_name(db, name=panel_in.name)
        if existing_panel and existing_panel.id != panel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A panel with the name '{panel_in.name}' already exists.",
            )

    # Perform the update (remember to handle password security if updated)
    updated_panel = crud.panel.update(db=db, db_obj=panel, obj_in=panel_in)
    # Response model ensures password isn't returned
    return updated_panel

@router.delete("/{panel_id}", response_model=schemas.Panel)
def delete_panel(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_id: int = Path(..., description="The ID of the panel to delete"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Delete a panel configuration by ID.
    
    Requires superuser permissions.
    Handles not found errors.
    Returns the deleted panel data (excluding password) as confirmation.
    Checks for any active subscriptions or orders using this panel.
    """
    panel = crud.panel.get(db, id=panel_id)
    if not panel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")
    
    # Check if there are any subscriptions or orders using this panel
    # This helps prevent data integrity issues
    if panel.subscriptions and len(panel.subscriptions) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete panel with active subscriptions. Delete or migrate subscriptions first."
        )
    
    if panel.orders and len(panel.orders) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete panel with associated orders. Delete or migrate orders first."
        )

    # Perform deletion
    deleted_panel = crud.panel.remove(db=db, id=panel_id)
    # Response model ensures password isn't returned
    return deleted_panel

@router.post("/{panel_id}/test-connection", response_model=Dict[str, Any])
def test_panel_connection(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_id: int = Path(..., description="The ID of the panel to test"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Test connection to a V2Ray panel.
    
    Attempts to connect to the panel and authenticate.
    Requires superuser permissions.
    """
    panel = crud.panel.get(db, id=panel_id)
    if not panel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")
    
    try:
        # Use the PanelService to test connection
        with PanelService(panel_id=panel_id) as panel_service:
            # Try to get inbounds to verify connection
            inbounds = panel_service.get_inbounds()
            inbound_count = len(inbounds) if inbounds else 0
            
            return {
                "success": True,
                "message": "Connection successful",
                "panel_id": panel_id,
                "panel_name": panel.name,
                "url": panel.url,
                "inbound_count": inbound_count
            }
    except PanelAuthenticationError:
        return {
            "success": False,
            "message": "Authentication failed. Check username and password.",
            "panel_id": panel_id,
            "panel_name": panel.name,
            "url": panel.url
        }
    except PanelConnectionError:
        return {
            "success": False,
            "message": "Connection failed. Check URL and ensure panel is running.",
            "panel_id": panel_id,
            "panel_name": panel.name,
            "url": panel.url
        }
    except PanelException as e:
        return {
            "success": False,
            "message": f"Panel error: {str(e)}",
            "panel_id": panel_id,
            "panel_name": panel.name,
            "url": panel.url
        }

@router.get("/{panel_id}/status", response_model=Dict[str, Any])
def get_panel_status(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_id: int = Path(..., description="The ID of the panel to check status for"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Get detailed status information for a panel.
    
    Includes connection status, client count, and traffic statistics.
    Requires superuser permissions.
    """
    panel = crud.panel.get(db, id=panel_id)
    if not panel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")
    
    status_data = {
        "panel_id": panel_id,
        "panel_name": panel.name,
        "url": panel.url, 
        "is_active": panel.is_active,
        "connection_status": "unknown",
        "inbounds": [],
        "total_clients": 0,
        "active_clients": 0,
        "total_traffic": 0,
        "up_traffic": 0,
        "down_traffic": 0,
        "error": None
    }
    
    try:
        # Try to connect to panel and get data
        with PanelService(panel_id=panel_id) as panel_service:
            inbounds = panel_service.get_inbounds()
            
            # Calculate statistics from inbounds
            total_clients = 0
            active_clients = 0
            total_traffic = 0
            up_traffic = 0
            down_traffic = 0
            inbound_data = []
            
            for inbound in inbounds:
                inbound_clients = inbound.get("clientStats", [])
                inbound_active_clients = sum(1 for c in inbound_clients if c.get("enable", False))
                
                inbound_info = {
                    "id": inbound.get("id"),
                    "protocol": inbound.get("protocol"),
                    "port": inbound.get("port"),
                    "remark": inbound.get("remark"),
                    "total_clients": len(inbound_clients),
                    "active_clients": inbound_active_clients,
                    "up_traffic": inbound.get("up", 0),
                    "down_traffic": inbound.get("down", 0),
                    "total_traffic": inbound.get("total", 0)
                }
                
                inbound_data.append(inbound_info)
                total_clients += len(inbound_clients)
                active_clients += inbound_active_clients
                up_traffic += inbound.get("up", 0)
                down_traffic += inbound.get("down", 0)
                total_traffic += inbound.get("total", 0)
            
            # Update status data
            status_data.update({
                "connection_status": "connected",
                "inbounds": inbound_data,
                "total_clients": total_clients,
                "active_clients": active_clients,
                "total_traffic": total_traffic,
                "up_traffic": up_traffic,
                "down_traffic": down_traffic
            })
            
    except PanelException as e:
        status_data.update({
            "connection_status": "error",
            "error": str(e)
        })
    
    return status_data

@router.get("/{panel_id}/statistics", response_model=Dict[str, Any])
def get_panel_statistics(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_id: int = Path(..., description="The ID of the panel to retrieve statistics for"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Get detailed statistics for a panel.
    
    Includes client counts, traffic usage, and subscription information.
    Requires superuser permissions.
    """
    panel = crud.panel.get(db, id=panel_id)
    if not panel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")
    
    # Query for subscription count on this panel
    subscription_count = db.query(models.Subscription).filter(
        models.Subscription.panel_id == panel_id,
        models.Subscription.is_active == True
    ).count()
    
    # Query for order count associated with this panel
    order_count = db.query(models.Order).filter(
        models.Order.panel_id == panel_id
    ).count()
    
    # Count frozen subscriptions
    frozen_subscription_count = db.query(models.Subscription).filter(
        models.Subscription.panel_id == panel_id,
        models.Subscription.is_frozen == True
    ).count()
    
    # Basic statistics from database
    db_stats = {
        "subscription_count": subscription_count,
        "frozen_subscription_count": frozen_subscription_count,
        "order_count": order_count,
    }
    
    # Try to get panel-level statistics
    panel_stats = {
        "connection_status": "unknown",
        "inbound_count": 0,
        "client_count": 0,
        "active_client_count": 0,
        "total_traffic_bytes": 0
    }
    
    try:
        # Connect to panel to get real-time statistics
        with PanelService(panel_id=panel_id) as panel_service:
            inbounds = panel_service.get_inbounds()
            
            total_clients = 0
            active_clients = 0
            total_traffic = 0
            
            for inbound in inbounds:
                inbound_clients = inbound.get("clientStats", [])
                total_clients += len(inbound_clients)
                active_clients += sum(1 for c in inbound_clients if c.get("enable", False))
                total_traffic += inbound.get("total", 0)
            
            panel_stats.update({
                "connection_status": "connected",
                "inbound_count": len(inbounds),
                "client_count": total_clients,
                "active_client_count": active_clients,
                "total_traffic_bytes": total_traffic
            })
            
    except PanelException as e:
        panel_stats.update({
            "connection_status": "error",
            "error": str(e)
        })
    
    # Combine all statistics
    result = {
        "panel_id": panel_id,
        "panel_name": panel.name,
        "database_statistics": db_stats,
        "panel_statistics": panel_stats
    }
    
    return result

@router.post("/{panel_id}/sync", response_model=Dict[str, Any])
def sync_panel_data(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_id: int = Path(..., description="The ID of the panel to sync"),
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Synchronize data between the database and panel.
    
    This can be a long-running operation, so it runs in the background.
    Requires superuser permissions.
    """
    panel = crud.panel.get(db, id=panel_id)
    if not panel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")
    
    # Define the background task
    def sync_panel_background(panel_id: int):
        """Background task to synchronize panel data"""
        try:
            # Create a new DB session for the background task
            sync_db = next(deps.get_db())
            
            # Get all subscriptions for this panel
            subscriptions = sync_db.query(models.Subscription).filter(
                models.Subscription.panel_id == panel_id,
                models.Subscription.is_active == True
            ).all()
            
            # Use PanelService to sync each subscription with the panel
            with PanelService(panel_id=panel_id) as panel_service:
                for subscription in subscriptions:
                    try:
                        # Attempt to sync this subscription
                        if subscription.client_email:
                            # Check if client exists on panel
                            try:
                                client = panel_service.get_client(email=subscription.client_email)
                                # Update subscription with latest panel data
                                subscription.is_enabled = client.get("enable", False)
                                # Add any other fields to update here
                            except Exception as client_err:
                                # Log error but continue with other subscriptions
                                print(f"Error syncing client {subscription.client_email}: {str(client_err)}")
                    except Exception as sub_err:
                        # Log error but continue with other subscriptions
                        print(f"Error processing subscription {subscription.id}: {str(sub_err)}")
            
            # Commit changes
            sync_db.commit()
        except Exception as e:
            # Log the error
            print(f"Error in background sync task: {str(e)}")
        finally:
            # Always close the DB session
            sync_db.close()
    
    # Schedule the background task
    background_tasks.add_task(sync_panel_background, panel_id)
    
    return {
        "message": "Panel synchronization started in background",
        "panel_id": panel_id,
        "panel_name": panel.name
    } 