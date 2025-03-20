"""
MoonVPN Telegram Bot - Subscription Plan Model

This module provides the SubscriptionPlan model for managing VPN subscription plans.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class SubscriptionPlan:
    """Subscription Plan model for managing VPN packages."""
    
    def __init__(self, plan_data: Dict[str, Any]):
        """
        Initialize a subscription plan object.
        
        Args:
            plan_data (Dict[str, Any]): Plan data from database
        """
        self.id = plan_data.get('id')
        self.name = plan_data.get('name')
        self.description = plan_data.get('description')
        self.duration_days = plan_data.get('duration_days')
        self.traffic_gb = plan_data.get('traffic_gb')
        self.price = float(plan_data.get('price', 0))
        self.server_id = plan_data.get('server_id')
        self.is_active = plan_data.get('is_active', True)
        self.created_at = plan_data.get('created_at')
        self.updated_at = plan_data.get('updated_at')
        
        # Additional data that might be included in joins
        self.server_name = plan_data.get('server_name')
        self.server_location = plan_data.get('server_location')
        
    @staticmethod
    def get_by_id(plan_id: int) -> Optional['SubscriptionPlan']:
        """
        Get a subscription plan by ID.
        
        Args:
            plan_id (int): Subscription plan ID
            
        Returns:
            Optional[SubscriptionPlan]: Subscription plan object or None if not found
        """
        # Try to get from cache first
        cached_plan = cache_get(f"plan:id:{plan_id}")
        if cached_plan:
            return SubscriptionPlan(cached_plan)
        
        # Get from database with server info
        query = """
            SELECT p.*, s.name as server_name, s.location as server_location
            FROM vpn_packages p
            LEFT JOIN servers s ON p.server_id = s.id
            WHERE p.id = %s
        """
        result = execute_query(query, (plan_id,), fetch="one")
        
        if result:
            # Cache plan data
            cache_set(f"plan:id:{plan_id}", dict(result), 300)  # Cache for 5 minutes
            return SubscriptionPlan(result)
            
        return None
        
    @staticmethod
    def get_all() -> List['SubscriptionPlan']:
        """
        Get all subscription plans.
        
        Returns:
            List[SubscriptionPlan]: List of subscription plan objects
        """
        query = """
            SELECT p.*, s.name as server_name, s.location as server_location
            FROM vpn_packages p
            LEFT JOIN servers s ON p.server_id = s.id
            ORDER BY p.price, p.duration_days
        """
        results = execute_query(query)
        
        return [SubscriptionPlan(result) for result in results]
        
    @staticmethod
    def get_active() -> List['SubscriptionPlan']:
        """
        Get all active subscription plans.
        
        Returns:
            List[SubscriptionPlan]: List of active subscription plan objects
        """
        try:
            query = """
                SELECT p.*, s.name as server_name, s.location as server_location
                FROM vpn_packages p
                LEFT JOIN servers s ON p.server_id = s.id
                WHERE p.is_active = TRUE
                ORDER BY p.price, p.duration_days
            """
            results = execute_query(query)
            
            return [SubscriptionPlan(result) for result in results]
        except Exception as e:
            logger.error(f"Error getting active subscription plans: {e}")
            # Return default plans if table doesn't exist
            return []
        
    @staticmethod
    def get_by_duration(duration_days: int) -> List['SubscriptionPlan']:
        """
        Get subscription plans by duration.
        
        Args:
            duration_days (int): Duration in days
            
        Returns:
            List[SubscriptionPlan]: List of subscription plan objects
        """
        query = """
            SELECT p.*, s.name as server_name, s.location as server_location
            FROM vpn_packages p
            LEFT JOIN servers s ON p.server_id = s.id
            WHERE p.duration_days = %s AND p.is_active = TRUE
            ORDER BY p.price
        """
        results = execute_query(query, (duration_days,))
        
        return [SubscriptionPlan(result) for result in results]
        
    @staticmethod
    def get_by_server(server_id: int) -> List['SubscriptionPlan']:
        """
        Get subscription plans by server.
        
        Args:
            server_id (int): Server ID
            
        Returns:
            List[SubscriptionPlan]: List of subscription plan objects
        """
        query = """
            SELECT p.*, s.name as server_name, s.location as server_location
            FROM vpn_packages p
            LEFT JOIN servers s ON p.server_id = s.id
            WHERE p.server_id = %s AND p.is_active = TRUE
            ORDER BY p.price, p.duration_days
        """
        results = execute_query(query, (server_id,))
        
        return [SubscriptionPlan(result) for result in results]
        
    @staticmethod
    def create(name: str, description: str, duration_days: int, traffic_gb: float,
             price: float, server_id: Optional[int] = None,
             is_active: bool = True) -> Optional['SubscriptionPlan']:
        """
        Create a new subscription plan.
        
        Args:
            name (str): Plan name
            description (str): Plan description
            duration_days (int): Duration in days
            traffic_gb (float): Traffic limit in GB
            price (float): Price in the default currency
            server_id (int, optional): Server ID if the plan is tied to a specific server
            is_active (bool, optional): Plan active status
            
        Returns:
            Optional[SubscriptionPlan]: Subscription plan object or None if creation failed
        """
        # Insert into database
        query = """
            INSERT INTO vpn_packages (
                name, description, duration_days, traffic_gb, price,
                server_id, is_active
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        plan_id = execute_insert(query, (
            name, description, duration_days, traffic_gb, price,
            server_id, is_active
        ))
        
        if plan_id:
            # Return the created plan
            return SubscriptionPlan.get_by_id(plan_id)
            
        return None
        
    def save(self) -> bool:
        """
        Save subscription plan changes to the database.
        
        Returns:
            bool: True if changes were saved, False otherwise
        """
        if not self.id:
            return False
            
        query = """
            UPDATE vpn_packages SET
                name = %s,
                description = %s,
                duration_days = %s,
                traffic_gb = %s,
                price = %s,
                server_id = %s,
                is_active = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        success = execute_update(query, (
            self.name,
            self.description,
            self.duration_days,
            self.traffic_gb,
            self.price,
            self.server_id,
            self.is_active,
            self.id
        ))
        
        if success:
            # Clear cache
            cache_delete(f"plan:id:{self.id}")
            
        return success
        
    def delete(self) -> bool:
        """
        Delete subscription plan from database.
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self.id:
            return False
            
        # Check if plan has accounts
        query = "SELECT COUNT(*) as count FROM vpn_accounts WHERE package_id = %s"
        result = execute_query(query, (self.id,), fetch="one")
        
        if result and result.get('count', 0) > 0:
            logger.error(f"Cannot delete plan {self.id} as it has active VPN accounts")
            return False
            
        # Delete from database
        query = "DELETE FROM vpn_packages WHERE id = %s"
        success = execute_delete(query, (self.id,))
        
        if success:
            # Clear cache
            cache_delete(f"plan:id:{self.id}")
            
        return success
        
    def activate(self) -> bool:
        """
        Activate subscription plan.
        
        Returns:
            bool: True if activation was successful, False otherwise
        """
        self.is_active = True
        return self.save()
        
    def deactivate(self) -> bool:
        """
        Deactivate subscription plan.
        
        Returns:
            bool: True if deactivation was successful, False otherwise
        """
        self.is_active = False
        return self.save()
        
    def update_price(self, price: float) -> bool:
        """
        Update subscription plan price.
        
        Args:
            price (float): New price
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        self.price = price
        return self.save()
        
    def get_monthly_price(self) -> float:
        """
        Get monthly price (converted from the actual plan duration).
        
        Returns:
            float: Monthly price
        """
        if not self.duration_days or self.duration_days == 0:
            return 0
            
        return self.price * 30 / self.duration_days
        
    def get_daily_price(self) -> float:
        """
        Get daily price (converted from the actual plan duration).
        
        Returns:
            float: Daily price
        """
        if not self.duration_days or self.duration_days == 0:
            return 0
            
        return self.price / self.duration_days
        
    def get_gb_price(self) -> float:
        """
        Get price per GB.
        
        Returns:
            float: Price per GB
        """
        if not self.traffic_gb or self.traffic_gb == 0:
            return 0
            
        return self.price / self.traffic_gb
        
    def get_total_bytes(self) -> int:
        """
        Get total traffic in bytes.
        
        Returns:
            int: Total traffic in bytes
        """
        return int(self.traffic_gb * 1024 * 1024 * 1024)
        
    def get_server(self) -> Optional[Any]:
        """
        Get the server for this plan.
        
        Returns:
            Optional[Server]: Server object or None if not found
        """
        if not self.server_id:
            return None
            
        from models.server import Server
        return Server.get_by_id(self.server_id)
        
    @staticmethod
    def get_cheapest() -> Optional['SubscriptionPlan']:
        """
        Get the cheapest active plan.
        
        Returns:
            Optional[SubscriptionPlan]: Cheapest plan or None if no plans available
        """
        query = """
            SELECT p.*, s.name as server_name, s.location as server_location
            FROM vpn_packages p
            LEFT JOIN servers s ON p.server_id = s.id
            WHERE p.is_active = TRUE
            ORDER BY p.price
            LIMIT 1
        """
        result = execute_query(query, fetch="one")
        
        if result:
            return SubscriptionPlan(result)
            
        return None
        
    @staticmethod
    def get_most_popular() -> Optional['SubscriptionPlan']:
        """
        Get the most popular plan (the one with the most accounts).
        
        Returns:
            Optional[SubscriptionPlan]: Most popular plan or None if no plans available
        """
        query = """
            SELECT p.*, s.name as server_name, s.location as server_location,
                  COUNT(va.id) as account_count
            FROM vpn_packages p
            LEFT JOIN servers s ON p.server_id = s.id
            LEFT JOIN vpn_accounts va ON p.id = va.package_id
            WHERE p.is_active = TRUE
            GROUP BY p.id, s.name, s.location
            ORDER BY account_count DESC
            LIMIT 1
        """
        result = execute_query(query, fetch="one")
        
        if result:
            return SubscriptionPlan(result)
            
        return None
        
    @staticmethod
    def get_plan_categories() -> List[Dict[str, Any]]:
        """
        Get plan categories (durations).
        
        Returns:
            List[Dict[str, Any]]: List of plan categories with duration_days and plan_count
        """
        query = """
            SELECT duration_days, COUNT(*) as plan_count
            FROM vpn_packages
            WHERE is_active = TRUE
            GROUP BY duration_days
            ORDER BY duration_days
        """
        return execute_query(query)
        
    @staticmethod
    def count_plans() -> int:
        """
        Count all plans.
        
        Returns:
            int: Number of plans
        """
        query = "SELECT COUNT(*) as count FROM vpn_packages"
        result = execute_query(query, fetch="one")
        
        return result.get('count', 0) if result else 0
        
    @staticmethod
    def count_active_plans() -> int:
        """
        Count active plans.
        
        Returns:
            int: Number of active plans
        """
        query = "SELECT COUNT(*) as count FROM vpn_packages WHERE is_active = TRUE"
        result = execute_query(query, fetch="one")
        
        return result.get('count', 0) if result else 0
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert subscription plan to dictionary.
        
        Returns:
            Dict[str, Any]: Subscription plan data as dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'duration_days': self.duration_days,
            'traffic_gb': self.traffic_gb,
            'price': self.price,
            'server_id': self.server_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'server_name': self.server_name,
            'server_location': self.server_location,
            'monthly_price': self.get_monthly_price(),
            'daily_price': self.get_daily_price(),
            'gb_price': self.get_gb_price(),
            'total_bytes': self.get_total_bytes()
        } 