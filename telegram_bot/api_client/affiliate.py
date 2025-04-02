from typing import Dict, Any, Optional, List

from httpx import AsyncClient, HTTPStatusError, RequestError

from .base import BaseAPIClient, APIError
from app.core.config import settings

class AffiliateAPIClient(BaseAPIClient):
    """API Client for affiliate related operations."""
    
    async def get_user_referral_info(self, user_id: int) -> Dict[str, Any]:
        """
        Gets referral information for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            Dictionary containing referral code, link, count of referrals, earnings, etc.
            
        Raises:
            APIError: If the API request fails.
        """
        endpoint = f"/affiliates/user/{user_id}"
        try:
            response = await self.get(endpoint)
            response.raise_for_status()
            return response.json()
        except HTTPStatusError as e:
            error_detail = self._parse_error_response(e.response)
            raise APIError(f"Failed to get user referral info: {error_detail}", status_code=e.response.status_code)
        except RequestError as e:
            raise APIError(f"Network error getting user referral info: {e}")
        except Exception as e:
            # Catch unexpected errors
            raise APIError(f"An unexpected error occurred getting user referral info: {e}")
    
    async def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Gets detailed referral statistics for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            Dictionary containing detailed stats about referrals, conversions, commissions, etc.
            
        Raises:
            APIError: If the API request fails.
        """
        endpoint = f"/affiliates/stats/{user_id}"
        try:
            response = await self.get(endpoint)
            response.raise_for_status()
            return response.json()
        except HTTPStatusError as e:
            error_detail = self._parse_error_response(e.response)
            raise APIError(f"Failed to get referral stats: {error_detail}", status_code=e.response.status_code)
        except RequestError as e:
            raise APIError(f"Network error getting referral stats: {e}")
        except Exception as e:
            # Catch unexpected errors
            raise APIError(f"An unexpected error occurred getting referral stats: {e}")
    
    async def get_referral_transactions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Gets a list of referral transactions (commissions earned) for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            List of transaction dictionaries containing amount, date, referred user, etc.
            
        Raises:
            APIError: If the API request fails.
        """
        endpoint = f"/affiliates/transactions/{user_id}"
        try:
            response = await self.get(endpoint)
            response.raise_for_status()
            return response.json()
        except HTTPStatusError as e:
            error_detail = self._parse_error_response(e.response)
            raise APIError(f"Failed to get referral transactions: {error_detail}", status_code=e.response.status_code)
        except RequestError as e:
            raise APIError(f"Network error getting referral transactions: {e}")
        except Exception as e:
            # Catch unexpected errors
            raise APIError(f"An unexpected error occurred getting referral transactions: {e}")
    
    async def generate_referral_link(self, user_id: int) -> Dict[str, Any]:
        """
        Generates or retrieves a referral link/code for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            Dictionary containing the referral code and full link.
            
        Raises:
            APIError: If the API request fails.
        """
        endpoint = f"/affiliates/generate-link/{user_id}"
        try:
            response = await self.get(endpoint)
            response.raise_for_status()
            return response.json()
        except HTTPStatusError as e:
            error_detail = self._parse_error_response(e.response)
            raise APIError(f"Failed to generate referral link: {error_detail}", status_code=e.response.status_code)
        except RequestError as e:
            raise APIError(f"Network error generating referral link: {e}")
        except Exception as e:
            # Catch unexpected errors
            raise APIError(f"An unexpected error occurred generating referral link: {e}")
    
    async def withdraw_commission(self, user_id: int, amount: float) -> Dict[str, Any]:
        """
        Requests a withdrawal of commission to the user's wallet.
        
        Args:
            user_id: The ID of the user.
            amount: The amount to withdraw.
            
        Returns:
            Dictionary containing the result of the withdrawal request.
            
        Raises:
            APIError: If the API request fails.
        """
        endpoint = f"/affiliates/withdraw"
        payload = {
            "user_id": user_id,
            "amount": amount
        }
        try:
            response = await self.post(endpoint, json_data=payload)
            response.raise_for_status()
            return response.json()
        except HTTPStatusError as e:
            error_detail = self._parse_error_response(e.response)
            raise APIError(f"Failed to withdraw commission: {error_detail}", status_code=e.response.status_code)
        except RequestError as e:
            raise APIError(f"Network error withdrawing commission: {e}")
        except Exception as e:
            # Catch unexpected errors
            raise APIError(f"An unexpected error occurred withdrawing commission: {e}")

# Instantiate the client
affiliate_client = AffiliateAPIClient(base_url=settings.CORE_API_BASE_URL + "/api/v1") 