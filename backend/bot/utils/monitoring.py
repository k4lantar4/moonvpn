"""
Monitoring utilities for MoonVPN Telegram Bot.

This module provides utilities for monitoring server status
and system resources periodically.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from models.server import Server
from core.services.panel.api import get_panel_client
from core.services.notification import notification_service

logger = logging.getLogger(__name__)

# Store monitoring tasks
_monitoring_tasks = {}

async def monitor_all_servers() -> Dict[str, Any]:
    """
    Monitor all servers and return results.
    
    Returns:
        Dictionary with monitoring results
    """
    try:
        # Get all servers
        servers = await Server.all()
        
        if not servers:
            logger.warning("No servers found for monitoring")
            return {"status": "error", "message": "No servers found"}
        
        # Monitor each server
        results = []
        for server in servers:
            try:
                panel_client = await get_panel_client(server.id)
                if not panel_client:
                    results.append({
                        "server": server,
                        "status": "error",
                        "error": "Panel not found"
                    })
                    continue
                
                # Monitor server status
                monitoring_result = await panel_client.monitor_server_status()
                results.append({
                    "server": server,
                    "status": monitoring_result.get("status", "unknown"),
                    "data": monitoring_result
                })
            except Exception as e:
                logger.error(f"Error monitoring server {server.id}: {e}")
                results.append({
                    "server": server,
                    "status": "error",
                    "error": str(e)
                })
        
        # Compile summary
        online_count = sum(1 for r in results if r.get("status") == "online")
        offline_count = sum(1 for r in results if r.get("status") in ["offline", "error"])
        issues_count = sum(len(r.get("data", {}).get("issues", [])) for r in results if r.get("status") == "online")
        
        critical_issues = []
        for result in results:
            if result.get("status") == "online":
                issues = result.get("data", {}).get("issues", [])
                server = result["server"]
                
                for issue in issues:
                    if issue.get("severity") == "critical":
                        critical_issues.append({
                            "server": server,
                            "issue": issue
                        })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "servers_count": len(servers),
            "online_count": online_count,
            "offline_count": offline_count,
            "issues_count": issues_count,
            "critical_issues_count": len(critical_issues),
            "critical_issues": critical_issues,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in monitor_all_servers: {e}")
        return {"status": "error", "message": str(e)}

async def monitoring_task(interval_seconds: int = 900) -> None:
    """
    Periodic task for monitoring servers.
    
    Args:
        interval_seconds: Interval in seconds between monitoring runs
    """
    while True:
        try:
            # Wait for the notification service to be ready
            if notification_service._bot is None:
                logger.warning("Notification service not ready, waiting...")
                await asyncio.sleep(30)
                continue
            
            logger.info(f"Running server monitoring task")
            
            # Monitor all servers
            results = await monitor_all_servers()
            
            # Check for offline servers
            offline_servers = [r for r in results.get("results", []) if r.get("status") in ["offline", "error"]]
            if offline_servers:
                # Send notification about offline servers
                offline_message = (
                    f"⚠️ <b>سرورهای آفلاین: {len(offline_servers)}</b>\n\n"
                )
                
                for result in offline_servers:
                    server = result["server"]
                    error = result.get("error", "خطای نامشخص")
                    offline_message += f"❌ <b>{server.name}</b> ({server.address})\n"
                    offline_message += f"  خطا: {error}\n\n"
                
                # Create server data for notification
                server_data = {
                    "name": "گزارش مانیتورینگ",
                    "address": "مانیتورینگ خودکار"
                }
                
                await notification_service.send_server_monitoring_alert(
                    server_data=server_data,
                    alert_type="سرورهای آفلاین",
                    details=offline_message
                )
            
            # Check for critical issues
            critical_issues = results.get("critical_issues", [])
            if critical_issues:
                # Group issues by server
                issues_by_server = {}
                for issue_data in critical_issues:
                    server = issue_data["server"]
                    issue = issue_data["issue"]
                    
                    if server.id not in issues_by_server:
                        issues_by_server[server.id] = {
                            "server": server,
                            "issues": []
                        }
                    
                    issues_by_server[server.id]["issues"].append(issue)
                
                # Send notification for each server with critical issues
                for server_data in issues_by_server.values():
                    server = server_data["server"]
                    issues = server_data["issues"]
                    
                    issues_message = f"⚠️ <b>مشکلات حیاتی در سرور {server.name}</b>\n\n"
                    
                    for i, issue in enumerate(issues, 1):
                        if issue["type"] == "high_traffic_usage":
                            issues_message += f"{i}. مصرف بالای ترافیک ({issue['usage_percent']}%) برای {issue['client_email']}\n"
                        elif issue["type"] == "near_expiry":
                            issues_message += f"{i}. انقضای نزدیک ({issue['days_left']} روز) برای {issue['client_email']}\n"
                        elif issue["type"] == "panel_offline":
                            issues_message += f"{i}. پنل آفلاین: {issue.get('details', 'بدون جزئیات')}\n"
                    
                    # Create server data for notification
                    notification_server_data = {
                        "name": server.name,
                        "address": server.address
                    }
                    
                    await notification_service.send_server_monitoring_alert(
                        server_data=notification_server_data,
                        alert_type="مشکلات حیاتی",
                        details=issues_message
                    )
            
            # Sleep until next run
            logger.info(f"Server monitoring completed, sleeping for {interval_seconds} seconds")
            await asyncio.sleep(interval_seconds)
            
        except Exception as e:
            logger.error(f"Error in monitoring_task: {e}")
            await asyncio.sleep(interval_seconds)

def start_monitoring(interval_seconds: int = 900) -> None:
    """
    Start the monitoring background task.
    
    Args:
        interval_seconds: Interval in seconds between monitoring runs
    """
    global _monitoring_tasks
    
    if "server_monitoring" in _monitoring_tasks:
        # Task already running
        return
    
    logger.info(f"Starting server monitoring task with interval {interval_seconds} seconds")
    
    # Create and store the task
    loop = asyncio.get_event_loop()
    task = loop.create_task(monitoring_task(interval_seconds))
    _monitoring_tasks["server_monitoring"] = task

def stop_monitoring() -> None:
    """Stop the monitoring background task."""
    global _monitoring_tasks
    
    if "server_monitoring" in _monitoring_tasks:
        logger.info("Stopping server monitoring task")
        task = _monitoring_tasks["server_monitoring"]
        task.cancel()
        del _monitoring_tasks["server_monitoring"] 