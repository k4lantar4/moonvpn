from typing import Dict, Any, Optional, List

from httpx import AsyncClient, HTTPStatusError, RequestError

from .base import BaseAPIClient, APIError
from app.core.config import settings

class SellerAPIClient(BaseAPIClient):
    """API Client for seller related operations."""
    
    async def get_seller_requirements(self) -> Dict[str, Any]:
        """
        Gets the requirements to become a seller from the /users/me/seller-requirements endpoint.
        
        Returns:
            Dictionary containing requirements like threshold, wallet_balance, etc.
            
        Raises:
            APIError: If the API request fails.
        """
        endpoint = "/users/me/seller-requirements"
        try:
            response = await self.get(endpoint)
            response.raise_for_status()
            data = response.json()
            
            # Format the response to match expected structure
            return {
                "minimum_topup_amount": data.get("threshold", 1000000),
                "wallet_balance": data.get("wallet_balance", 0),
                "benefits": [
                    "دسترسی به قیمت‌های ویژه محصولات",
                    "امکان فروش محصولات به مشتریان",
                    "کسب درآمد از فروش هر سرویس",
                    "پنل مدیریت اختصاصی برای نظارت بر فروش"
                ],
                "is_seller": data.get("is_seller", False),
                "can_become_seller": data.get("can_become_seller", False),
                "balance_needed": data.get("balance_needed", 0)
            }
        except HTTPStatusError as e:
            error_detail = self._parse_error_response(e.response)
            raise APIError(f"Failed to get seller requirements: {error_detail}", status_code=e.response.status_code)
        except RequestError as e:
            raise APIError(f"Network error getting seller requirements: {e}")
        except Exception as e:
            # Catch unexpected errors
            raise APIError(f"An unexpected error occurred getting seller requirements: {e}")
    
    async def check_seller_eligibility(self, user_id: int) -> Dict[str, Any]:
        """
        Checks if a user is eligible to become a seller using /users/me/seller-requirements.
        
        Args:
            user_id: The ID of the user (not used in new API).
            
        Returns:
            Dictionary containing eligibility info like is_eligible, missing_requirements, etc.
            
        Raises:
            APIError: If the API request fails.
        """
        try:
            # Use the seller requirements endpoint to get eligibility info
            requirements = await self.get_seller_requirements()
            
            is_eligible = requirements.get("can_become_seller", False)
            balance_needed = requirements.get("balance_needed", 0)
            
            missing_requirements = []
            if balance_needed > 0:
                missing_requirements.append(
                    f"نیاز به شارژ {balance_needed:,} تومان دیگر به کیف پول خود دارید"
                )
            
            return {
                "is_eligible": is_eligible,
                "missing_requirements": missing_requirements,
                "wallet_balance": requirements.get("wallet_balance", 0),
                "minimum_amount": requirements.get("minimum_topup_amount", 1000000)
            }
        except Exception as e:
            # Pass through any underlying API errors
            if isinstance(e, APIError):
                raise
            # Wrap other errors
            raise APIError(f"Failed to check seller eligibility: {e}")
    
    async def become_seller(self, user_id: int) -> Dict[str, Any]:
        """
        Upgrades a user to seller role using the /users/me/become-seller endpoint.
        
        Args:
            user_id: The ID of the user (not used in new API).
            
        Returns:
            Dictionary containing the updated user info.
            
        Raises:
            APIError: If the API request fails.
        """
        endpoint = "/users/me/become-seller"
        try:
            response = await self.post(endpoint)
            response.raise_for_status()
            user_data = response.json()
            
            # Format response to match expected structure
            return {
                "success": True,
                "user": user_data,
                "message": "Successfully upgraded to seller role"
            }
        except HTTPStatusError as e:
            error_detail = self._parse_error_response(e.response)
            return {
                "success": False,
                "error": error_detail,
                "message": f"Failed to upgrade: {error_detail}"
            }
        except RequestError as e:
            raise APIError(f"Network error upgrading user to seller: {e}")
        except Exception as e:
            # Catch unexpected errors
            raise APIError(f"An unexpected error occurred upgrading user to seller: {e}")
    
    async def get_seller_plans(self) -> List[Dict[str, Any]]:
        """
        Gets the list of plans with seller pricing.
        
        Returns:
            List of plans with regular and seller pricing.
            
        Raises:
            APIError: If the API request fails.
        """
        endpoint = "/plans"
        try:
            response = await self.get(endpoint)
            response.raise_for_status()
            plans = response.json()
            
            # Filter plans that have seller_price defined
            seller_plans = [
                plan for plan in plans 
                if plan.get("seller_price") is not None
            ]
            
            return seller_plans
        except HTTPStatusError as e:
            error_detail = self._parse_error_response(e.response)
            raise APIError(f"Failed to get seller plans: {error_detail}", status_code=e.response.status_code)
        except RequestError as e:
            raise APIError(f"Network error getting seller plans: {e}")
        except Exception as e:
            # Catch unexpected errors
            raise APIError(f"An unexpected error occurred getting seller plans: {e}")

    async def get_seller_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Gets statistics for a seller, such as sales, commission, etc.
        
        Args:
            user_id: The ID of the seller.
            
        Returns:
            Dictionary containing seller statistics.
            
        Raises:
            APIError: If the API request fails.
        """
        # This is a placeholder until we implement seller statistics in the API
        return {
            "total_sales": 0,
            "total_commission": 0,
            "sales_this_month": 0,
            "commission_this_month": 0,
            "active_customers": 0,
            "most_popular_plan": "N/A"
        }

# Instantiate the client
seller_client = SellerAPIClient(base_url=settings.CORE_API_BASE_URL + "/api/v1") 