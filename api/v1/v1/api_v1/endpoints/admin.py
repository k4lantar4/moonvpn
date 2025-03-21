"""
Admin endpoints.

This module provides API endpoints for administrative operations.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.security import get_current_active_superuser
from core.database import get_db
from core.database.models import User, VPNAccount, Server, Transaction

router = APIRouter()


@router.get("/stats", response_model=Dict[str, Any])
def read_stats(
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Get admin statistics.
    
    Retrieve system-wide statistics for the admin dashboard.
    """
    # Count active users
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    
    # Count active VPN accounts
    active_accounts = db.query(func.count(VPNAccount.id)).filter(
        VPNAccount.status == "active"
    ).scalar()
    
    # Count active servers
    active_servers = db.query(func.count(Server.id)).filter(
        Server.is_active == True
    ).scalar()
    
    # Sum of completed transactions
    total_revenue = db.query(func.sum(Transaction.amount)).filter(
        Transaction.status == "completed"
    ).scalar() or 0.0
    
    # Recent transactions
    recent_transactions = db.query(Transaction).order_by(
        Transaction.created_at.desc()
    ).limit(5).all()
    
    # Recent users
    recent_users = db.query(User).order_by(
        User.created_at.desc()
    ).limit(5).all()
    
    return {
        "active_users": active_users,
        "active_accounts": active_accounts,
        "active_servers": active_servers,
        "total_revenue": total_revenue,
        "recent_transactions": [
            {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "amount": transaction.amount,
                "status": transaction.status,
                "created_at": transaction.created_at,
            }
            for transaction in recent_transactions
        ],
        "recent_users": [
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "created_at": user.created_at,
            }
            for user in recent_users
        ],
    }


@router.post("/users/{user_id}/set-superuser", response_model=Dict[str, Any])
def set_superuser(
    user_id: int,
    is_superuser: bool,
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Set user as superuser.
    
    Grant or revoke superuser privileges for a user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.is_superuser = is_superuser
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "user_id": user.id,
        "email": user.email,
        "is_superuser": user.is_superuser,
        "message": f"User superuser status set to {is_superuser}",
    }


@router.post("/servers/check-status", response_model=List[Dict[str, Any]])
def check_server_status(
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_active_superuser),
) -> List[Dict[str, Any]]:
    """
    Check server status.
    
    Check the status of all VPN servers and update their status.
    """
    # Get all active servers
    servers = db.query(Server).filter(Server.is_active == True).all()
    
    results = []
    for server in servers:
        # In a real implementation, you would check server status
        # by connecting to the server API
        
        # For demo purposes, we'll just simulate a check
        try:
            # Here you would call the server API to get status
            # panel_client = PanelClient(
            #     host=server.host,
            #     port=server.api_port,
            #     username=server.api_username,
            #     password=server.api_password,
            # )
            # status = panel_client.get_status()
            
            # Simulate status
            status = {
                "cpu_usage": 25.5,
                "memory_usage": 40.2,
                "disk_usage": 60.8,
                "bandwidth_usage": 15.3,
            }
            
            # Update server with status
            server.cpu_usage = status["cpu_usage"]
            server.memory_usage = status["memory_usage"]
            server.disk_usage = status["disk_usage"]
            server.bandwidth_usage = status["bandwidth_usage"]
            server.status = "active"
            
            db.add(server)
            db.commit()
            db.refresh(server)
            
            results.append({
                "server_id": server.id,
                "name": server.name,
                "host": server.host,
                "status": "active",
                "cpu_usage": server.cpu_usage,
                "memory_usage": server.memory_usage,
                "disk_usage": server.disk_usage,
                "bandwidth_usage": server.bandwidth_usage,
            })
        except Exception as e:
            # If check fails, mark server as inactive
            server.status = "error"
            
            db.add(server)
            db.commit()
            db.refresh(server)
            
            results.append({
                "server_id": server.id,
                "name": server.name,
                "host": server.host,
                "status": "error",
                "error": str(e),
            })
    
    return results 