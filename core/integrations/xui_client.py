"""
کلاس کلاینت برای ارتباط با پنل‌های 3x-ui بر پایه AsyncApi
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import httpx # Assuming py3xui uses httpx or similar, need to know the actual connection error type
from json import JSONDecodeError

# استفاده از کلاس AsyncApi از کتابخانه py3xui
from py3xui import AsyncApi

logger = logging.getLogger(__name__)

# Add specific exceptions
class XuiAuthenticationError(Exception):
    """Raised when login fails due to authentication issues."""
    pass

class XuiConnectionError(Exception):
    """Raised when connection to the panel fails."""
    pass

class XuiClient:
    """
    کلاس کلاینت برای ارتباط با پنل‌های 3x-ui با استفاده از AsyncApi
    این کلاس یک wrapper سبک روی AsyncApi است
    """
    
    def __init__(self, host: str, username: str, password: str, token: str = ""):
        """
        راه‌اندازی کلاینت با آدرس و اطلاعات ورود پنل
        
        Args:
            host: آدرس پنل (همراه با http/https)
            username: نام کاربری پنل
            password: رمز عبور پنل
            token: توکن احراز هویت (اختیاری)
        """
        # حذف اسلش انتهایی اگر وجود داشته باشد
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.token = token
        
        # ایجاد نمونه AsyncApi
        self.api = AsyncApi(self.host, self.username, self.password, self.token)
        logger.info(f"XuiClient initialized for panel at {self.host}")
    
    async def login(self) -> bool:
        """
        احراز هویت و ورود به پنل
        
        Returns:
            True در صورت موفقیت

        Raises:
            XuiAuthenticationError: اگر نام کاربری/رمز عبور اشتباه باشد یا پاسخ API نشان‌دهنده شکست احراز هویت باشد.
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای غیرمنتظره دیگر (مانند JSONDecodeError).
        """
        try:
            # --- Log entry ---
            logger.debug(f"Attempting login to panel at {self.host}...")
            result = await self.api.login()

            # --- Explicit result check including dict with success: True ---
            if result is True or (isinstance(result, dict) and result.get("success") is True):
                # Consider both boolean True and dict {'success': True, ...} as success
                logger.info(f"Successfully logged in to panel at {self.host} (Result: {result})")
                return True
            elif result is False:
                # Specific case where login returns False directly
                err_msg = "نام کاربری یا رمز عبور پنل اشتباه است. (login returned False)"
                logger.warning(f"Authentication failed for panel at {self.host}: {err_msg}")
                raise XuiAuthenticationError(err_msg)
            elif isinstance(result, dict) and result.get("success") is False:
                # Case where login returns a dict indicating failure
                api_msg = result.get("msg", "API response indicated failure without specific message.")
                err_msg = f"نام کاربری یا رمز عبور پنل اشتباه است. (API response: {api_msg})"
                logger.warning(f"Authentication failed for panel at {self.host}: {err_msg}")
                raise XuiAuthenticationError(err_msg)
            # --- Treat None as an ambiguous success, but log warning ---
            elif result is None:
                logger.warning(f"Login to {self.host} returned None. Assuming success based on likely HTTP 200 OK, but py3xui behavior is ambiguous. Connection needs verification.")
                return True # Return True, but verification is needed later
            else:
                # Handle other unexpected success cases or types if necessary
                logger.warning(f"Login to {self.host} returned an unexpected result: {result} (Type: {type(result)}). Treating as failure.")
                err_msg = f"پاسخ غیرمنتظره ({type(result).__name__}) از API هنگام لاگین دریافت شد."
                raise XuiConnectionError(err_msg) # Map unexpected types to connection/API error

        except (httpx.RequestError, TimeoutError, ConnectionError) as conn_err:
             # Generic connection/network errors
             error_type = type(conn_err).__name__
             logger.error(f"Login failed to panel at {self.host}: Type={error_type}, Message={conn_err}", exc_info=True)
             # Provide more user-friendly messages based on common scenarios
             if isinstance(conn_err, httpx.TimeoutException):
                 user_msg = f"اتصال به پنل {self.host} به دلیل Timeout برقرار نشد. لطفاً از در دسترس بودن پنل و عدم وجود مشکل شبکه مطمئن شوید."
             elif "connection refused" in str(conn_err).lower():
                  user_msg = f"اتصال به پنل {self.host} رد شد. ممکن است پنل خاموش باشد، پورت اشتباه باشد یا فایروال مانع اتصال شده باشد."
             elif "ssl" in str(conn_err).lower() or "certificate" in str(conn_err).lower():
                 user_msg = f"مشکل SSL در اتصال به پنل {self.host}. مطمئن شوید از http/https درست استفاده می‌کنید و گواهی معتبر است."
             elif "dns" in str(conn_err).lower() or "name or service not known" in str(conn_err).lower():
                  user_msg = f"آدرس پنل {self.host} نامعتبر است (خطای DNS). لطفاً آدرس را بررسی کنید."
             else:
                  user_msg = f"امکان اتصال به پنل {self.host} وجود ندارد ({error_type}). لطفاً آدرس، پورت و وضعیت شبکه را بررسی کنید."
             raise XuiConnectionError(user_msg) from conn_err

        except JSONDecodeError as json_err:
             # Error decoding the response from the panel
             logger.error(f"Login failed to panel at {self.host}: Type=JSONDecodeError, Message={json_err}", exc_info=True)
             user_msg = f"پاسخ نامعتبر (JSON) از پنل {self.host} دریافت شد. ممکن است آدرس اشتباه باشد، پنل 3x-ui نباشد یا پنل مشکل داشته باشد."
             raise XuiConnectionError(user_msg) from json_err

        except XuiAuthenticationError: # Re-raise specific auth errors caught above
             raise
        except Exception as e:
             # Catch-all for any other unexpected errors during login
             logger.error(f"Login failed to panel at {self.host}: Type={type(e).__name__}, Message={e}", exc_info=True)
             user_msg = f"خطای پیش‌بینی نشده ({type(e).__name__}) هنگام تلاش برای ورود به پنل {self.host} رخ داد."
             # Generally map unknown errors to connection problems unless specifically identified
             raise XuiConnectionError(user_msg) from e
    
    async def get_status(self) -> bool:
        """
        بررسی وضعیت اتصال و احراز هویت پنل با تلاش برای لاگین

        Returns:
            True اگر اتصال و احراز هویت موفقیت‌آمیز باشد.

        Raises:
            XuiAuthenticationError: اگر نام کاربری/رمز عبور اشتباه باشد.
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای دیگر.
        """
        logger.debug(f"Checking status for panel {self.host} by attempting login.")
        # Re-uses the login logic including exception handling
        return await self.login()
    
    # --------- مدیریت کلاینت‌ها ---------
    
    async def add_client_to_inbound(self, inbound_id: int, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ایجاد کلاینت جدید در یک inbound خاص
        
        Args:
            inbound_id: شناسه inbound
            client_data: داده‌های کلاینت شامل email، uuid، total_gb و...
            
        Returns:
            اطلاعات کلاینت ایجاد شده
        """
        try:
            # Assuming py3xui API method for adding client is 'client.create'
            result = await self.api.client.create(inbound_id, client_data)
            logger.info(f"Successfully added client to inbound {inbound_id} on panel {self.host}")
            return result
        except Exception as e:
            logger.error(f"Failed to add client to inbound {inbound_id} on panel {self.host}: {e}", exc_info=True)
            # Consider raising a more specific exception if needed
            raise
    
    async def get_client(self, email: str) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک کلاینت با ایمیل/نام آن
        
        Args:
            email: آدرس ایمیل/نام کلاینت
            
        Returns:
            اطلاعات کلاینت
        """
        try:
            result = await self.api.client.get_by_email(email)
            if result:
                logger.info(f"Successfully retrieved client with email {email}")
            else:
                logger.warning(f"Client with email {email} not found")
                return None # Return None if not found
            return result
        except Exception as e:
            logger.error(f"Failed to get client with email {email}: {e}")
            raise
    
    async def get_client_by_uuid(self, uuid: str) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک کلاینت با UUID آن
        
        Args:
            uuid: UUID کلاینت
            
        Returns:
            اطلاعات کلاینت
        """
        try:
            result = await self.api.client.get(uuid)
            if result:
                logger.info(f"Successfully retrieved client with UUID {uuid}")
            else:
                logger.warning(f"Client with UUID {uuid} not found")
                return None # Return None if not found
            return result
        except Exception as e:
            logger.error(f"Failed to get client with UUID {uuid}: {e}")
            raise
    
    async def delete_client(self, uuid: str) -> bool:
        """
        حذف یک کلاینت با UUID آن
        
        Args:
            uuid: UUID کلاینت
            
        Returns:
            True در صورت موفقیت
        """
        try:
            result = await self.api.client.delete(uuid)
            logger.info(f"Successfully deleted client with UUID {uuid}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete client with UUID {uuid}: {e}")
            raise
    
    async def update_client(self, uuid: str, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        به‌روزرسانی اطلاعات یک کلاینت
        
        Args:
            uuid: UUID کلاینت
            client_data: داده‌های جدید کلاینت
            
        Returns:
            اطلاعات به‌روز شده کلاینت
        """
        try:
            result = await self.api.client.update(uuid, client_data)
            logger.info(f"Successfully updated client with UUID {uuid}")
            return result
        except Exception as e:
            logger.error(f"Failed to update client with UUID {uuid}: {e}")
            raise
    
    async def reset_client_traffic(self, uuid: str) -> bool:
        """
        ریست کردن ترافیک یک کلاینت
        
        Args:
            uuid: UUID کلاینت
            
        Returns:
            True در صورت موفقیت
        """
        try:
            result = await self.api.client.reset_traffic(uuid)
            logger.info(f"Successfully reset traffic for client with UUID {uuid}")
            return result
        except Exception as e:
            logger.error(f"Failed to reset traffic for client with UUID {uuid}: {e}")
            raise
    
    async def get_client_traffic(self, uuid: str) -> Dict[str, Any]:
        """
        دریافت اطلاعات ترافیک یک کلاینت
        
        Args:
            uuid: UUID کلاینت
            
        Returns:
            اطلاعات ترافیک کلاینت
        """
        try:
            result = await self.api.client.get_traffic(uuid)
            logger.info(f"Successfully retrieved traffic info for client with UUID {uuid}")
            return result
        except Exception as e:
            logger.error(f"Failed to get traffic info for client with UUID {uuid}: {e}")
            raise
    
    async def get_config(self, uuid: str) -> str:
        """
        دریافت لینک کانفیگ یک کلاینت
        
        Args:
            uuid: UUID کلاینت
            
        Returns:
            لینک کانفیگ کلاینت (vmess/vless)
        """
        try:
            # دریافت اطلاعات کلاینت
            client = await self.get_client_by_uuid(uuid)
            if not client:
                logger.warning(f"Client with UUID {uuid} not found when trying to get config.")
                return "" # Return empty string or raise error?

            # دریافت اطلاعات inbound مرتبط
            inbound_id = client.get("inbound_id") # Assuming 'inbound_id' is available in client data
            if not inbound_id:
                 logger.error(f"Could not determine inbound_id for client UUID {uuid}.")
                 return "" # Or raise appropriate error

            inbound = await self.get_inbound(inbound_id)
            if not inbound:
                logger.error(f"Could not retrieve inbound {inbound_id} for client UUID {uuid}.")
                return "" # Or raise error

            # تولید لینک کانفیگ بر اساس نوع inbound و اطلاعات کلاینت
            # این بخش نیاز به پیاده‌سازی دقیق بر اساس فرمت لینک‌های xui دارد
            # Example (needs actual implementation based on py3xui or panel structure):
            protocol = inbound.get("protocol")
            address = self.host.replace("http://", "").replace("https://", "") # Simplistic address extraction
            port = inbound.get("port")
            settings = client.get("settings", {}) # Assuming settings are within client data directly

            if protocol == "vmess":
                # Construct VMess link (requires specific format knowledge)
                # Example structure - requires real implementation
                # link = f"vmess://..."
                link = f"vmess://{{'add':'{address}','port':'{port}','id':'{uuid}', ...}}" # Placeholder
                logger.warning("VMess link generation is a placeholder.")
                return link # Placeholder return
            elif protocol == "vless":
                # Construct VLESS link (requires specific format knowledge)
                # Example structure - requires real implementation
                # link = f"vless://{uuid}@{address}:{port}?..."
                link = f"vless://{uuid}@{address}:{port}?type=tcp&security=none#Placeholder" # Placeholder
                logger.warning("VLESS link generation is a placeholder.")
                return link # Placeholder return
            else:
                logger.warning(f"Unsupported protocol {protocol} for config generation for client UUID {uuid}.")
                return ""

        except Exception as e:
            logger.error(f"Failed to get config for client with UUID {uuid}: {e}", exc_info=True)
            raise
    
    # --------- مدیریت Inbound‌ها ---------
    
    async def get_inbounds(self) -> List[Dict[str, Any]]:
        """
        دریافت لیست تمام inbound‌های پنل
        
        Returns:
            لیست inbound‌ها
        """
        try:
            result = await self.api.inbound.get_list()
            logger.info(f"Successfully retrieved inbounds from panel {self.host}")
            return result
        except Exception as e:
            logger.error(f"Failed to get inbounds from panel {self.host}: {e}", exc_info=True)
            # Consider raising a more specific exception if needed
            raise
    
    async def sync_inbounds(self) -> List[Dict[str, Any]]:
        """
        همگام‌سازی (دریافت) لیست کامل inboundها از پنل.
        این متد در حال حاضر فقط لیست را دریافت می‌کند و برمی‌گرداند.
        منطق همگام‌سازی با دیتابیس باید در لایه سرویس پیاده‌سازی شود.

        Returns:
            لیست inboundهای موجود در پنل.

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای دیگر API.
        """
        logger.info(f"Syncing inbounds from panel {self.host}")
        try:
            inbounds = await self.api.inbound.get_list() # Use correct py3xui method
            if inbounds is None: # Check if API returns None on failure/empty
                 logger.warning(f"Received None when syncing inbounds from panel {self.host}. Assuming empty list.")
                 return []
            logger.info(f"Successfully synced {len(inbounds)} inbounds from panel {self.host}")
            return inbounds
        except (httpx.RequestError, ConnectionError, TimeoutError) as conn_err:
             logger.error(f"Connection failed during inbound sync for panel {self.host}: {conn_err}", exc_info=True)
             raise XuiConnectionError(f"امکان اتصال به پنل {self.host} هنگام همگام‌سازی inboundها وجود ندارد.") from conn_err
        except Exception as e:
            logger.error(f"Failed to sync inbounds from panel {self.host}: {e}", exc_info=True)
            # Consider raising a more specific exception if needed
            raise

    async def get_inbound(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک inbound خاص با شناسه آن
        
        Args:
            inbound_id: شناسه inbound
            
        Returns:
            اطلاعات inbound
        """
        try:
            # Assuming py3xui method is 'inbound.get'
            result = await self.api.inbound.get(inbound_id)
            if result:
                logger.info(f"Successfully retrieved inbound {inbound_id} from panel {self.host}")
            else:
                logger.warning(f"Inbound {inbound_id} not found on panel {self.host}")
                return None # Return None if not found
            return result
        except Exception as e:
            logger.error(f"Failed to get inbound {inbound_id} from panel {self.host}: {e}", exc_info=True)
            # Consider raising a more specific exception if needed
            raise
    
    async def create_inbound(self, inbound_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ایجاد یک inbound جدید
        
        Args:
            inbound_data: داده‌های inbound
            
        Returns:
            اطلاعات inbound ایجاد شده
        """
        try:
            # Assuming py3xui method is 'inbound.create'
            result = await self.api.inbound.create(inbound_data)
            logger.info(f"Successfully created inbound on panel {self.host}")
            return result
        except Exception as e:
            logger.error(f"Failed to create inbound on panel {self.host}: {e}", exc_info=True)
            # Consider raising a more specific exception if needed
            raise
    
    async def update_inbound(self, inbound_id: int, inbound_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        به‌روزرسانی یک inbound
        
        Args:
            inbound_id: شناسه inbound
            inbound_data: داده‌های جدید inbound
            
        Returns:
            اطلاعات به‌روز شده inbound
        """
        try:
            # Assuming py3xui method is 'inbound.update'
            result = await self.api.inbound.update(inbound_id, inbound_data)
            logger.info(f"Successfully updated inbound {inbound_id} on panel {self.host}")
            return result
        except Exception as e:
            logger.error(f"Failed to update inbound {inbound_id} on panel {self.host}: {e}", exc_info=True)
            # Consider raising a more specific exception if needed
            raise
    
    async def delete_inbound(self, inbound_id: int) -> bool:
        """
        حذف یک inbound
        
        Args:
            inbound_id: شناسه inbound
            
        Returns:
            True در صورت موفقیت
        """
        try:
            # Assuming py3xui method is 'inbound.delete'
            result = await self.api.inbound.delete(inbound_id)
            logger.info(f"Successfully deleted inbound {inbound_id} from panel {self.host}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete inbound {inbound_id} from panel {self.host}: {e}", exc_info=True)
            # Consider raising a more specific exception if needed
            raise
    
    # --------- مدیریت سرور ---------
    
    async def verify_connection(self) -> bool:
        """
        Verifies the connection by attempting to fetch inbounds.
        This should fail if the login wasn't truly successful.

        Returns:
            True if fetching inbounds works, False otherwise.
        """
        try:
            logger.debug(f"Verifying connection to {self.host} by fetching inbounds...")
            inbounds = await self.api.inbound.get_list()
            # If get_list returns None on auth failure or error, treat as verification failure
            if inbounds is None:
                 logger.warning(f"Connection verification failed for {self.host}: get_list() returned None.")
                 return False
            logger.info(f"Connection verification successful for {self.host}. Found {len(inbounds)} inbounds.")
            return True
        except (XuiAuthenticationError, XuiConnectionError) as e:
            # Catch errors that might occur if the session/cookie is invalid
            logger.warning(f"Connection verification failed for {self.host}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection verification ({self.host}): {e}", exc_info=True)
            return False # Treat unexpected errors as verification failure

    # Keep get_stats but fix the underlying call if possible or remove if unused
    # For now, let's assume get_stats is not directly available via py3xui
    async def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        دریافت آمار کلی سرور (Method might not exist in py3xui)
        
        Returns:
            آمار سرور شامل CPU، RAM، ترافیک و...
        """
        logger.warning(f"Attempted to call get_stats for {self.host}, but py3xui may not support this directly.")
        # Raise an error or return None, as self.api.get_stats() likely doesn't exist
        # raise NotImplementedError("get_stats is not directly supported by the py3xui library wrapper.")
        return None # Returning None as the previous attempt showed it's not available

    async def restart_core(self) -> bool:
        """
        راه‌اندازی مجدد هسته xray/v2ray
        
        Returns:
            True در صورت موفقیت
        """
        try:
            result = await self.api.restart_core() # Assuming py3xui has a direct method
            logger.info(f"Successfully requested core restart on panel {self.host}")
            return result
        except (httpx.RequestError, ConnectionError, TimeoutError) as conn_err:
             logger.error(f"Connection failed during restart_core for panel {self.host}: {conn_err}", exc_info=True)
             raise XuiConnectionError(f"امکان اتصال به پنل {self.host} هنگام درخواست ریستارت وجود ندارد.") from conn_err
        except Exception as e:
            logger.error(f"Failed to restart core on panel {self.host}: {e}", exc_info=True)
            # Consider raising a more specific exception if needed
            raise
