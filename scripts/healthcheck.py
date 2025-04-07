#!/usr/bin/env python3
"""
Health Check Script for MoonVPN

This script checks the health of all MoonVPN services and external resources.
It can be run independently or as part of a monitoring system.
"""

import os
import sys
import time
import json
import logging
import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

import httpx
import redis.asyncio as redis
import pymysql

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('healthcheck')

# Health check statuses
STATUS_HEALTHY = "healthy"
STATUS_WARNING = "warning"
STATUS_ERROR = "error"


async def check_api_health(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Check the health of the API service.
    
    Args:
        url: API URL to check
        timeout: Request timeout
        
    Returns:
        Dict: Health check result
    """
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url}/ping")
            
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = {
                "status": STATUS_HEALTHY,
                "response_time_ms": int(elapsed * 1000),
                "details": {"version": response.headers.get("X-API-Version", "unknown")}
            }
        else:
            result = {
                "status": STATUS_WARNING,
                "response_time_ms": int(elapsed * 1000),
                "details": {"error": f"Unexpected status code: {response.status_code}"}
            }
    except httpx.TimeoutException:
        elapsed = time.time() - start_time
        result = {
            "status": STATUS_ERROR,
            "response_time_ms": int(elapsed * 1000),
            "details": {"error": "Request timed out"}
        }
    except Exception as e:
        elapsed = time.time() - start_time
        result = {
            "status": STATUS_ERROR,
            "response_time_ms": int(elapsed * 1000),
            "details": {"error": f"Unexpected error: {str(e)}"}
        }
    
    return result


async def check_bot_health(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Check the health of the Telegram bot service.
    
    Args:
        url: Bot health URL to check
        timeout: Request timeout
        
    Returns:
        Dict: Health check result
    """
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url}/health")
            
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            result = {
                "status": STATUS_HEALTHY,
                "response_time_ms": int(elapsed * 1000),
                "details": {
                    "version": data.get("version", "unknown"),
                    "uptime": data.get("uptime", 0),
                    "bot_username": data.get("bot_username", "unknown")
                }
            }
        else:
            result = {
                "status": STATUS_WARNING,
                "response_time_ms": int(elapsed * 1000),
                "details": {"error": f"Unexpected status code: {response.status_code}"}
            }
    except httpx.TimeoutException:
        elapsed = time.time() - start_time
        result = {
            "status": STATUS_ERROR,
            "response_time_ms": int(elapsed * 1000),
            "details": {"error": "Request timed out"}
        }
    except Exception as e:
        elapsed = time.time() - start_time
        result = {
            "status": STATUS_ERROR,
            "response_time_ms": int(elapsed * 1000),
            "details": {"error": f"Unexpected error: {str(e)}"}
        }
    
    return result


async def check_mysql_health(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str
) -> Dict[str, Any]:
    """
    Check the health of the MySQL database.
    
    Args:
        host: MySQL host
        port: MySQL port
        user: MySQL user
        password: MySQL password
        database: MySQL database name
        
    Returns:
        Dict: Health check result
    """
    start_time = time.time()
    try:
        # MySQL doesn't have async driver, so use sync connection
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=5
        )
        
        with connection.cursor() as cursor:
            # Check if we can execute queries
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            # Check connection stats
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            threads_connected = cursor.fetchone()[1]
            
            # Get database size
            cursor.execute(f"SELECT SUM(data_length + index_length) FROM information_schema.TABLES WHERE table_schema = '{database}'")
            db_size = cursor.fetchone()[0]
        
        connection.close()
        
        elapsed = time.time() - start_time
        result = {
            "status": STATUS_HEALTHY,
            "response_time_ms": int(elapsed * 1000),
            "details": {
                "version": version,
                "connections": threads_connected,
                "database_size_bytes": db_size
            }
        }
    except Exception as e:
        elapsed = time.time() - start_time
        result = {
            "status": STATUS_ERROR,
            "response_time_ms": int(elapsed * 1000),
            "details": {"error": f"Failed to connect to MySQL: {str(e)}"}
        }
    
    return result


async def check_redis_health(
    host: str,
    port: int,
    db: int = 0,
    password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check the health of the Redis cache.
    
    Args:
        host: Redis host
        port: Redis port
        db: Redis database
        password: Redis password
        
    Returns:
        Dict: Health check result
    """
    start_time = time.time()
    try:
        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            socket_timeout=5.0,
            decode_responses=True
        )
        
        # Check if Redis is responsive
        info = await client.info()
        
        # Write and read a test key
        test_key = "healthcheck:test"
        test_value = f"test_{int(time.time())}"
        
        await client.set(test_key, test_value, ex=60)
        read_value = await client.get(test_key)
        
        if read_value != test_value:
            raise Exception("Redis read/write test failed")
        
        # Get some useful stats
        memory_used = info.get("used_memory_human", "unknown")
        connected_clients = info.get("connected_clients", "unknown")
        uptime = info.get("uptime_in_seconds", 0)
        
        await client.close()
        
        elapsed = time.time() - start_time
        result = {
            "status": STATUS_HEALTHY,
            "response_time_ms": int(elapsed * 1000),
            "details": {
                "version": info.get("redis_version", "unknown"),
                "memory_used": memory_used,
                "connected_clients": connected_clients,
                "uptime_seconds": uptime
            }
        }
    except Exception as e:
        elapsed = time.time() - start_time
        result = {
            "status": STATUS_ERROR,
            "response_time_ms": int(elapsed * 1000),
            "details": {"error": f"Redis health check failed: {str(e)}"}
        }
    
    return result


async def check_panel_connection(
    url: str,
    username: str,
    password: str,
    timeout: float = 10.0
) -> Dict[str, Any]:
    """
    Check the health of a 3x-ui panel.
    
    Args:
        url: Panel URL
        username: Panel username
        password: Panel password
        timeout: Request timeout
        
    Returns:
        Dict: Health check result
    """
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Try to login
            login_data = {"username": username, "password": password}
            login_response = await client.post(f"{url}/login", json=login_data)
            
            if login_response.status_code != 200:
                raise Exception(f"Login failed: HTTP {login_response.status_code}")
            
            login_result = login_response.json()
            if not login_result.get("success", False):
                raise Exception(f"Login failed: {login_result.get('msg', 'Unknown error')}")
            
            # Get cookies from login
            cookies = login_response.cookies
            
            # Try to get inbounds
            inbounds_response = await client.get(
                f"{url}/panel/api/inbounds/list",
                cookies=cookies
            )
            
            if inbounds_response.status_code != 200:
                raise Exception(f"Failed to get inbounds: HTTP {inbounds_response.status_code}")
            
            inbounds_result = inbounds_response.json()
            if not inbounds_result.get("success", False):
                raise Exception(f"Failed to get inbounds: {inbounds_result.get('msg', 'Unknown error')}")
            
            inbounds = inbounds_result.get("obj", [])
            
            # Try to get online users
            online_response = await client.post(
                f"{url}/panel/api/inbounds/onlines",
                cookies=cookies
            )
            
            online_users = []
            if online_response.status_code == 200:
                online_result = online_response.json()
                if online_result.get("success", False):
                    online_users = online_result.get("obj", [])
        
        elapsed = time.time() - start_time
        result = {
            "status": STATUS_HEALTHY,
            "response_time_ms": int(elapsed * 1000),
            "details": {
                "inbounds_count": len(inbounds),
                "online_users_count": len(online_users)
            }
        }
    except Exception as e:
        elapsed = time.time() - start_time
        result = {
            "status": STATUS_ERROR,
            "response_time_ms": int(elapsed * 1000),
            "details": {"error": f"Panel health check failed: {str(e)}"}
        }
    
    return result


async def run_health_checks() -> Dict[str, Any]:
    """
    Run all health checks and return results.
    
    Returns:
        Dict: Health check results for all services
    """
    # Load environment variables from .env file
    try:
        dotenv_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        with open(dotenv_file, 'r') as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except Exception as e:
        logger.warning(f"Failed to load .env file: {str(e)}")
    
    # Get configuration from environment variables
    api_url = os.environ.get("API_URL", "http://localhost:8000")
    bot_url = os.environ.get("BOT_HEALTH_URL", "http://localhost:8001")
    
    mysql_host = os.environ.get("MYSQL_HOST", "localhost")
    mysql_port = int(os.environ.get("MYSQL_PORT", "3306"))
    mysql_user = os.environ.get("MYSQL_USER", "root")
    mysql_password = os.environ.get("MYSQL_PASSWORD", "")
    mysql_database = os.environ.get("MYSQL_DATABASE", "moonvpn")
    
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    redis_db = int(os.environ.get("REDIS_DB", "0"))
    redis_password = os.environ.get("REDIS_PASSWORD", "")
    
    # Get panel configuration
    panel_url = os.environ.get("PANEL1_URL", "")
    panel_username = os.environ.get("PANEL1_USERNAME", "")
    panel_password = os.environ.get("PANEL1_PASSWORD", "")
    
    # Run health checks concurrently
    tasks = [
        check_api_health(api_url),
        check_bot_health(bot_url),
        check_mysql_health(mysql_host, mysql_port, mysql_user, mysql_password, mysql_database),
        check_redis_health(redis_host, redis_port, redis_db, redis_password),
    ]
    
    # Add panel health check if credentials are available
    if panel_url and panel_username and panel_password:
        tasks.append(check_panel_connection(panel_url, panel_username, panel_password))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    health_checks = {
        "api": results[0] if not isinstance(results[0], Exception) else {"status": STATUS_ERROR, "details": {"error": str(results[0])}},
        "bot": results[1] if not isinstance(results[1], Exception) else {"status": STATUS_ERROR, "details": {"error": str(results[1])}},
        "database": results[2] if not isinstance(results[2], Exception) else {"status": STATUS_ERROR, "details": {"error": str(results[2])}},
        "redis": results[3] if not isinstance(results[3], Exception) else {"status": STATUS_ERROR, "details": {"error": str(results[3])}},
    }
    
    # Add panel check if available
    if panel_url:
        health_checks["panel"] = results[4] if len(results) > 4 and not isinstance(results[4], Exception) else {"status": STATUS_ERROR, "details": {"error": str(results[4]) if len(results) > 4 else "Not checked"}}
    
    # Determine overall status
    statuses = [check["status"] for check in health_checks.values()]
    
    if STATUS_ERROR in statuses:
        overall_status = STATUS_ERROR
    elif STATUS_WARNING in statuses:
        overall_status = STATUS_WARNING
    else:
        overall_status = STATUS_HEALTHY
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": health_checks
    }


def print_color(text: str, status: str) -> None:
    """
    Print text with color based on status.
    
    Args:
        text: Text to print
        status: Status (healthy, warning, error)
    """
    if status == STATUS_HEALTHY:
        print(f"\033[32m{text}\033[0m")  # Green
    elif status == STATUS_WARNING:
        print(f"\033[33m{text}\033[0m")  # Yellow
    else:
        print(f"\033[31m{text}\033[0m")  # Red


def print_report(report: Dict[str, Any], detailed: bool = False) -> None:
    """
    Print health check report in a human-readable format.
    
    Args:
        report: Health check report
        detailed: Whether to print detailed information
    """
    print("\n=== MoonVPN Health Check Report ===")
    print(f"Timestamp: {report['timestamp']}")
    
    status_emoji = "✅" if report["status"] == STATUS_HEALTHY else "⚠️" if report["status"] == STATUS_WARNING else "❌"
    print_color(f"Overall Status: {status_emoji} {report['status'].upper()}", report["status"])
    print("\nServices:")
    
    for service_name, service_report in report["services"].items():
        status = service_report["status"]
        status_emoji = "✅" if status == STATUS_HEALTHY else "⚠️" if status == STATUS_WARNING else "❌"
        
        response_time = service_report.get("response_time_ms", 0)
        print_color(f"  {service_name.upper()}: {status_emoji} {status.upper()} ({response_time}ms)", status)
        
        if detailed and "details" in service_report:
            for key, value in service_report["details"].items():
                if key == "error" and value:
                    print_color(f"    - {key}: {value}", STATUS_ERROR)
                else:
                    print(f"    - {key}: {value}")
    
    print("\n==============================")


def main():
    parser = argparse.ArgumentParser(description="MoonVPN Health Check")
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--detailed', action='store_true', help='Show detailed information')
    args = parser.parse_args()
    
    try:
        result = asyncio.run(run_health_checks())
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_report(result, args.detailed)
        
        # Exit with appropriate code
        sys.exit(0 if result["status"] == STATUS_HEALTHY else 1)
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        if args.json:
            print(json.dumps({
                "status": STATUS_ERROR,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }, indent=2))
        else:
            print_color(f"Health check failed: {str(e)}", STATUS_ERROR)
        sys.exit(1)


if __name__ == "__main__":
    main()
