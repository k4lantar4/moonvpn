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
            result = await self.api.login()

            # --- Refined Success/Auth Failure Check ---
            login_successful = False
            auth_error_message = ""

            if isinstance(result, bool):
                if result:
                    login_successful = True
                else:
                    # Explicit False means auth failure according to py3xui (assumption)
                    auth_error_message = "متد لاگین False برگرداند"
            elif isinstance(result, dict):
                # Check if the result is a dictionary like {"success": bool, "msg": str, ...}
                if result.get('success', False):
                    login_successful = True
                else:
                    # Dictionary indicates failure
                    auth_error_message = result.get('msg', "پاسخ API نشان‌دهنده شکست بود")
                    if "invalid username or password" in auth_error_message.lower():
                        auth_error_message = "نام کاربری یا رمز عبور اشتباه است"
                    else:
                         auth_error_message = f"پیام خطا از پنل: {auth_error_message}"
            else:
                # If it's not bool or dict, but didn't raise exception, assume success?
                # This might need adjustment based on py3xui's actual non-error return types.
                logger.warning(f"Login to {self.host} returned unexpected type: {type(result)}. Assuming success as no exception was raised.")
                login_successful = True

            if login_successful:
                 logger.info(f"Successfully logged in to panel at {self.host} (Result type: {type(result)})")
                 return True
            else:
                 # Raise Authentication Error if login_successful is False
                 logger.warning(f"Authentication failed for panel at {self.host}. Reason: {auth_error_message}")
                 raise XuiAuthenticationError(f"نام کاربری یا رمز عبور پنل {self.host} اشتباه است. ({auth_error_message})")

        # --- Exception Handling (mostly unchanged) ---
        # A: Catch potential py3xui-specific authentication errors FIRST if they exist
        # except Py3xuiAuthError as auth_err: # Replace with actual py3xui auth exception
        #     logger.warning(f"Authentication failed for panel {self.host} via py3xui exception: {auth_err}", exc_info=True)
        #     raise XuiAuthenticationError(f"نام کاربری یا رمز عبور پنل {self.host} اشتباه است (py3xui exception).") from auth_err

        # B: Catch specific connection-related errors (more comprehensive)
        except httpx.TimeoutException as timeout_err: # Specific timeout
             logger.warning(f"Connection timeout for panel {self.host}: {timeout_err}", exc_info=True)
             raise XuiConnectionError(f"اتصال به پنل {self.host} با خطای Timeout مواجه شد.") from timeout_err
        except (httpx.RequestError, ConnectionError) as conn_err: # General HTTP/connection errors (covers DNS, Refused, etc.)
            # Log the specific type of error
            logger.warning(f"Connection failed for panel {self.host}: {type(conn_err).__name__} - {conn_err}", exc_info=True)
            error_msg = f"امکان اتصال به پنل {self.host} وجود ندارد. "
            if "ssl" in str(conn_err).lower() or "certificate" in str(conn_err).lower():
                error_msg += "مشکل SSL وجود دارد (ممکن است نیاز به https داشته باشید یا گواهی نامعتبر باشد)."
            elif "connection refused" in str(conn_err).lower():
                 error_msg += "اتصال رد شد (ممکن است پنل خاموش باشد یا پورت اشتباه باشد)."
            elif "dns" in str(conn_err).lower() or "name or service not known" in str(conn_err).lower():
                 error_msg += "آدرس پنل نامعتبر است (خطای DNS)."
            else:
                 error_msg += "آدرس، پورت یا وضعیت شبکه را بررسی کنید."
            raise XuiConnectionError(error_msg) from conn_err
        
        # C: Catch potential JSON decoding errors if the panel returns invalid response
        except JSONDecodeError as json_err:
            logger.error(f"Failed to decode JSON response from panel {self.host} during login: {json_err}", exc_info=True)
            raise XuiConnectionError(f"پاسخ نامعتبر (JSON) از پنل {self.host} دریافت شد. ممکن است آدرس اشتباه باشد یا پنل مشکل داشته باشد.") from json_err

        # D: Catch *other* potential py3xui-specific errors (e.g., base path issues) if known
        # except Py3xuiSomeOtherError as other_err:
        #     logger.error(f"Specific py3xui error for panel {self.host}: {other_err}", exc_info=True)
        #     # Map to XuiConnectionError or XuiAuthenticationError or a new specific error
        #     raise XuiConnectionError(f"خطای خاصی از کتابخانه py3xui هنگام اتصال به {self.host}: {other_err}") from other_err

        # E: Catch any remaining unexpected errors
        except Exception as e:
            logger.error(f"An unexpected error occurred during login to panel at {self.host}: {type(e).__name__} - {e}", exc_info=True)
            # Avoid guessing, raise a generic connection error or re-raise
            raise XuiConnectionError(f"خطای پیش‌بینی نشده ({type(e).__name__}) هنگام تلاش برای لاگین به پنل {self.host}.") from e
    
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
    
    async def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        دریافت آمار کلی سرور
        
        Returns:
            آمار سرور شامل CPU، RAM، ترافیک و...
        """
        try:
            result = await self.api.get_stats() # Assuming py3xui has a direct method
            if result:
                logger.info(f"Successfully retrieved stats from panel {self.host}")
            else:
                 logger.warning(f"Received no stats data from panel {self.host}")
                 return None
            return result
        except (httpx.RequestError, ConnectionError, TimeoutError) as conn_err:
             logger.error(f"Connection failed during get_stats for panel {self.host}: {conn_err}", exc_info=True)
             raise XuiConnectionError(f"امکان اتصال به پنل {self.host} هنگام دریافت آمار وجود ندارد.") from conn_err
        except Exception as e:
            logger.error(f"Failed to get stats from panel {self.host}: {e}", exc_info=True)
            # Consider raising a more specific exception if needed
            raise
    
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
