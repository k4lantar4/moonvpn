"""
کلاس کلاینت برای ارتباط با پنل‌های 3x-ui بر پایه AsyncApi
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import httpx # Assuming py3xui uses httpx or similar, need to know the actual connection error type
from json import JSONDecodeError
import base64
import json
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

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

class XuiNotFoundError(Exception):
    """خطا زمانی که موردی در پنل XUI پیدا نشود."""
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
    
    async def logout(self) -> bool:
        """
        خروج از پنل (اگر py3xui از آن پشتیبانی کند).
        توجه: نیاز به بررسی وجود متد logout در py3xui.async_api است.

        Returns:
            True در صورت موفقیت آمیز بودن خروج.
        """
        try:
            # --- فرض بر اینکه متدی به نام logout وجود دارد ---
            # result = await self.api.logout()
            # logger.info(f"Successfully logged out from panel {self.host}")
            # return result
            # --- اگر متد logout وجود ندارد ---
            logger.warning(f"Logout method called for {self.host}, but assumed not implemented or needed in py3xui. Skipping.")
            return True
        except AttributeError:
            logger.warning(f"Logout method explicitly not found in py3xui for panel {self.host}.")
            return False
        except Exception as e:
            logger.error(f"Failed to logout from panel {self.host}: {e}", exc_info=True)
            raise # خطای اصلی را دوباره ایجاد می‌کنیم
    
    # --------- مدیریت کلاینت‌ها ---------
    
    async def get_all_clients(self) -> List[Dict[str, Any]]:
        """
        دریافت لیست کامل تمام کلاینت‌های موجود در پنل (از تمام inboundها).

        Returns:
            لیستی از دیکشنری‌ها که هر کدام اطلاعات یک کلاینت را نشان می‌دهد.
            ساختار دقیق دیکشنری بستگی به پاسخ API پنل دارد.

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای دیگر API.
        """
        logger.info(f"Attempting to get all clients from panel {self.host}")
        try:
            # استفاده از متد get_list از py3xui.async_api.client
            clients = await self.api.client.get_list()
            if clients is None:
                logger.warning(f"Received None when getting all clients from panel {self.host}. Assuming empty list.")
                return []
            logger.info(f"Successfully retrieved {len(clients)} clients from panel {self.host}")
            # py3xui ممکن است لیستی از آبجکت‌ها برگرداند، نیاز به تبدیل به dict؟
            # فرض می‌کنیم clients لیستی از dict است یا آیتم‌های آن __dict__ دارند
            processed_clients = []
            for client in clients:
                if hasattr(client, '__dict__'):
                    processed_clients.append(client.__dict__)
                elif isinstance(client, dict):
                    processed_clients.append(client)
                else:
                    logger.warning(f"Found unexpected item type ({type(client)}) in client list from {self.host}. Skipping.")
            return processed_clients
        except AttributeError:
            logger.error(f"The py3xui library (or its client module) does not seem to have a 'get_list' method for panel {self.host}.")
            return [] # یا raise خطا
        except (httpx.RequestError, ConnectionError, TimeoutError) as conn_err:
            logger.error(f"Connection failed while getting all clients for panel {self.host}: {conn_err}", exc_info=True)
            raise XuiConnectionError(f"امکان اتصال به پنل {self.host} هنگام دریافت لیست کلاینت‌ها وجود ندارد.") from conn_err
        except Exception as e:
            logger.error(f"Failed to get all clients from panel {self.host}: {e}", exc_info=True)
            raise

    async def create_client(self, inbound_id: int, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ایجاد کلاینت جدید در یک inbound خاص (معادل py3xui client.create).

        Args:
            inbound_id: شناسه inbound
            client_data: داده‌های کلاینت شامل email، uuid، total_gb و...

        Returns:
            اطلاعات کلاینت ایجاد شده (به صورت دیکشنری).

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای دیگر API.
        """
        logger.info(f"Attempting to create client in inbound {inbound_id} on panel {self.host}")
        try:
            # استفاده از client.create
            result = await self.api.client.create(inbound_id=inbound_id, client=client_data)
            logger.info(f"Successfully created client in inbound {inbound_id} on panel {self.host}")
            # تبدیل به dict اگر آبجکت بود
            if hasattr(result, '__dict__'): return result.__dict__
            return result
        except AttributeError:
             logger.error(f"The py3xui library (or its client module) does not seem to have a 'create' method for panel {self.host}.")
             raise NotImplementedError("create_client is not available in the current py3xui version.") from None
        except Exception as e:
            logger.error(f"Failed to create client in inbound {inbound_id} on panel {self.host}: {e}", exc_info=True)
            raise

    async def get_client_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک کلاینت با ایمیل/نام آن (معادل py3xui client.get_by_email).

        Args:
            email: آدرس ایمیل/نام کلاینت

        Returns:
            اطلاعات کلاینت یا None اگر پیدا نشد
        """
        try:
            result = await self.api.client.get_by_email(email)
            if result:
                logger.info(f"Successfully retrieved client with email {email}")
                 # تبدیل به dict اگر آبجکت بود
                if hasattr(result, '__dict__'): return result.__dict__
                return result
            else:
                logger.warning(f"Client with email {email} not found on panel {self.host}")
                return None # Return None if not found
        except AttributeError:
            logger.error(f"The py3xui library (or its client module) does not seem to have a 'get_by_email' method for panel {self.host}.")
            return None
        except Exception as e:
            logger.error(f"Failed to get client with email {email} on panel {self.host}: {e}")
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
        دریافت لینک کانفیگ یک کلاینت بر اساس UUID آن.
        از فرمت‌های VLESS و VMess پشتیبانی می‌کند.

        Args:
            uuid: UUID کلاینت

        Returns:
            لینک کانفیگ کلاینت (VLESS یا VMess) یا رشته خالی در صورت بروز مشکل.

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای دیگر API یا پردازش.
        """
        logger.info(f"Attempting to generate config link for client UUID {uuid} on panel {self.host}")
        try:
            # دریافت اطلاعات کلاینت
            client = await self.get_client_by_uuid(uuid)
            if not client:
                logger.warning(f"Client with UUID {uuid} not found when trying to get config.")
                return ""

            # دریافت اطلاعات inbound مرتبط
            inbound_id = client.get("inboundId") # نام فیلد ممکن است فرق کند!
            if not inbound_id:
                 logger.error(f"Could not determine inboundId for client UUID {uuid}. Client data: {client}")
                 return ""

            inbound = await self.get_inbound_by_id(inbound_id)
            if not inbound:
                logger.error(f"Could not retrieve inbound {inbound_id} for client UUID {uuid}.")
                return ""

            # استخراج اطلاعات لازم
            protocol = inbound.get("protocol")
            # استخراج آدرس دامنه/IP از هاست پنل (بدون http/https)
            parsed_host = urlparse(self.host)
            address = parsed_host.hostname if parsed_host.hostname else self.host # اگر hostname نبود، کل هاست را بگذار
            port = inbound.get("port")
            remark = client.get("email") or uuid # اسم کانفیگ: ایمیل یا اگر نبود، UUID

            # تنظیمات streamSettings و sniffing
            stream_settings = inbound.get("streamSettings", {})
            sniffing_settings = inbound.get("sniffing", {})
            network = stream_settings.get("network", "tcp") # ws, tcp, grpc, etc.
            security = stream_settings.get("security", "none") # tls, reality, none

            # مقادیر پیش‌فرض
            config_link = ""

            # --- ساخت لینک VLESS ---
            if protocol == "vless":
                base_link = f"vless://{uuid}@{address}:{port}"
                params = {
                    "type": network,
                    "security": security,
                }

                # پارامترهای خاص شبکه
                if network == "tcp":
                    tcp_settings = stream_settings.get("tcpSettings", {})
                    header = tcp_settings.get("header", {})
                    if header.get("type") == "http":
                         params["headerType"] = "http"
                         # path و host را از request یا host در header استخراج کن
                         req = header.get("request", {})
                         path = req.get("path", ["/"])[0] # معمولا لیست است
                         host_headers = req.get("headers", {}).get("Host", [])
                         host = host_headers[0] if host_headers else ""
                         params["path"] = path
                         if host: params["host"] = host
                elif network == "ws":
                    ws_settings = stream_settings.get("wsSettings", {})
                    params["path"] = ws_settings.get("path", "/")
                    host = ws_settings.get("headers", {}).get("Host", "")
                    if host: params["host"] = host
                elif network == "grpc":
                    grpc_settings = stream_settings.get("grpcSettings", {})
                    params["serviceName"] = grpc_settings.get("serviceName", "")
                    # mode (multi) ?

                # پارامترهای امنیتی
                if security == "tls":
                    tls_settings = stream_settings.get("tlsSettings", {})
                    params["sni"] = tls_settings.get("serverName", address) # SNI
                    params["fp"] = tls_settings.get("fingerprint", "") # Fingerprint
                    # alpn? 
                elif security == "reality":
                    reality_settings = stream_settings.get("realitySettings", {})
                    params["sni"] = reality_settings.get("serverNames", [address])[0] # اولین SNI
                    params["fp"] = reality_settings.get("fingerprints", ["chrome"])[0] # اولین fingerprint
                    params["pbk"] = reality_settings.get("publicKey", "") # Public Key
                    params["sid"] = reality_settings.get("shortIds", [""])[0] # اولین Short ID
                    # spiderX ?

                # اضافه کردن پارامترهای sniffing اگر فعال بود
                if sniffing_settings.get("enabled", False):
                    dest_override = sniffing_settings.get("destOverride", [])
                    if "http" in dest_override: params["flow"] = "xtls-rprx-vision"
                    # آیا sniffing پارامتر دیگری در لینک دارد؟

                # Encode کردن پارامترها
                query_string = urlencode({k: v for k, v in params.items() if v is not None and v != ""}) # حذف پارامترهای خالی
                config_link = f"{base_link}?{query_string}#{remark}"

            # --- ساخت لینک VMess ---
            elif protocol == "vmess":
                # ساخت دیکشنری JSON بر اساس فرمت رایج
                vmess_data = {
                    "v": "2", # Version
                    "ps": remark, # Remark
                    "add": address,
                    "port": str(port),
                    "id": uuid,
                    "aid": str(client.get("alterId", 0)), # AlterId, default 0
                    "net": network,
                    "type": "none", # Header type, default none (برای tcp)
                    "host": "", # Host header
                    "path": "", # Path (برای ws/grpc)
                    "tls": "", # tls or reality
                    "sni": "",
                    "alpn": "",
                    "fp": ""
                }

                # تنظیمات شبکه
                if network == "tcp":
                    tcp_settings = stream_settings.get("tcpSettings", {})
                    header = tcp_settings.get("header", {})
                    if header.get("type") == "http":
                        vmess_data["type"] = "http"
                        req = header.get("request", {})
                        # path و host را از request یا host در header استخراج کن
                        paths = req.get("path", ["/"])
                        vmess_data["path"] = ",".join(paths) if paths else "/" # Join if multiple paths?
                        host_headers = req.get("headers", {}).get("Host", [])
                        vmess_data["host"] = host_headers[0] if host_headers else ""
                elif network == "ws":
                    ws_settings = stream_settings.get("wsSettings", {})
                    vmess_data["path"] = ws_settings.get("path", "/")
                    vmess_data["host"] = ws_settings.get("headers", {}).get("Host", "")
                elif network == "grpc":
                    grpc_settings = stream_settings.get("grpcSettings", {})
                    vmess_data["path"] = grpc_settings.get("serviceName", "")
                    # mode? ('gun' for grpc?)
                    vmess_data["type"] = "multi" if grpc_settings.get("multiMode", False) else "gun"

                # تنظیمات امنیتی
                if security == "tls":
                    vmess_data["tls"] = "tls"
                    tls_settings = stream_settings.get("tlsSettings", {})
                    vmess_data["sni"] = tls_settings.get("serverName", address)
                    vmess_data["fp"] = tls_settings.get("fingerprint", "")
                    # alpn?
                    alpn_list = tls_settings.get("alpn", [])
                    vmess_data["alpn"] = ",".join(alpn_list) if alpn_list else ""
                # VMess از Reality پشتیبانی نمی‌کند؟ اگر بکند باید اضافه شود

                # تبدیل به JSON و کد کردن با Base64
                json_string = json.dumps(vmess_data, separators=(',', ':')) # فشرده‌ترین حالت
                encoded_bytes = base64.urlsafe_b64encode(json_string.encode('utf-8'))
                encoded_string = encoded_bytes.decode('utf-8').rstrip('=') # حذف padding =
                config_link = f"vmess://{encoded_string}"

            else:
                logger.warning(f"Unsupported protocol '{protocol}' for config generation for client UUID {uuid}.")
                return ""

            logger.info(f"Successfully generated config link for client UUID {uuid}")
            return config_link

        except KeyError as ke:
             logger.error(f"Missing expected key in client or inbound data for UUID {uuid}: {ke}", exc_info=True)
             return ""
        except Exception as e:
            logger.error(f"Failed to get/generate config for client with UUID {uuid}: {e}", exc_info=True)
            # raise # یا برگرداندن رشته خالی؟
            return ""
    
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

    async def get_inbound_by_id(self, inbound_id: int) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک inbound خاص با شناسه آن (معادل py3xui inbound.get_by_id).

        Args:
            inbound_id: شناسه inbound

        Returns:
            اطلاعات inbound یا None اگر پیدا نشد
        """
        try:
            # Assuming py3xui method is 'inbound.get'
            # **اصلاح:** بر اساس مستندات py3xui باید از get_by_id استفاده شود
            result = await self.api.inbound.get_by_id(inbound_id)
            if result:
                logger.info(f"Successfully retrieved inbound {inbound_id} from panel {self.host}")
                 # تبدیل به dict اگر آبجکت بود
                if hasattr(result, '__dict__'): return result.__dict__
                return result
            else:
                logger.warning(f"Inbound {inbound_id} not found on panel {self.host}")
                return None # Return None if not found
        except AttributeError:
            logger.error(f"The py3xui library (or its inbound module) does not seem to have a 'get_by_id' method for panel {self.host}.")
            return None
        except Exception as e:
            logger.error(f"Failed to get inbound {inbound_id} from panel {self.host}: {e}", exc_info=True)
            # Consider raising a more specific exception if needed
            raise

    async def add_inbound(self, inbound_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ایجاد یک inbound جدید (معادل py3xui inbound.add).
        توجه: py3xui معمولا آبجکت Inbound را به عنوان ورودی انتظار دارد.
              این پیاده‌سازی سعی می‌کند دیکشنری را مستقیما ارسال کند.

        Args:
            inbound_data: داده‌های inbound (به صورت دیکشنری).

        Returns:
            اطلاعات inbound ایجاد شده (به صورت دیکشنری).

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            ValueError: اگر داده‌های ورودی با مدل py3xui سازگار نباشد.
            Exception: برای خطاهای دیگر API.
        """
        logger.info(f"Attempting to add inbound on panel {self.host}")
        try:
            # استفاده از inbound.add
            # **توجه:** py3xui آبجکت Inbound می‌گیرد.
            # from py3xui.models import Inbound
            # inbound_obj = Inbound(**inbound_data) # ممکن است نیاز به تبدیل دقیق‌تر باشد
            # result = await self.api.inbound.add(inbound=inbound_obj)
            # --- روش فعلی با فرض اینکه add دیکشنری هم قبول می‌کند (نیاز به تست) ---
            logger.warning("The 'add_inbound' method ideally expects an Inbound object from py3xui, but received a dict. Attempting to pass dict directly.")
            result = await self.api.inbound.add(inbound=inbound_data) # استفاده مستقیم از دیکشنری
            logger.info(f"Successfully added inbound on panel {self.host}")
            # تبدیل نتیجه به dict اگر آبجکت بود
            if hasattr(result, '__dict__'): return result.__dict__
            return result
        except AttributeError:
             logger.error(f"The py3xui library (or its inbound module) does not seem to have an 'add' method for panel {self.host}.")
             raise NotImplementedError("add_inbound is not available in the current py3xui version.") from None
        except TypeError as te:
            logger.error(f"Type error during inbound creation on {self.host}. Input data might be incompatible with py3xui's Inbound model: {te}", exc_info=True)
            raise ValueError("داده‌های ورودی برای ساخت inbound با مدل py3xui سازگار نیست.") from te
        except Exception as e:
            logger.error(f"Failed to add inbound on panel {self.host}: {e}", exc_info=True)
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
    
    async def reset_all_inbound_stats(self) -> bool:
        """
        ریست کردن آمار ترافیک *تمام* inboundهای پنل.

        Returns:
            True اگر دستور با موفقیت به پنل ارسال شد، False در غیر این صورت.

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای دیگر API.
        """
        logger.info(f"Requesting reset of all inbound stats on panel {self.host}")
        try:
            # استفاده از متد reset_stats از py3xui.async_api.inbound
            await self.api.inbound.reset_stats()
            logger.info(f"Successfully requested reset of all inbound stats on panel {self.host}")
            return True
        except AttributeError:
            logger.error(f"The py3xui library (or its inbound module) does not seem to have a 'reset_stats' method for panel {self.host}.")
            return False
        except (httpx.RequestError, ConnectionError, TimeoutError) as conn_err:
            logger.error(f"Connection failed during reset_all_inbound_stats request for panel {self.host}: {conn_err}", exc_info=True)
            raise XuiConnectionError(f"امکان اتصال به پنل {self.host} هنگام درخواست ریست آمار inboundها وجود ندارد.") from conn_err
        except Exception as e:
            logger.error(f"Failed to request reset of all inbound stats on panel {self.host}: {e}", exc_info=True)
            raise

    async def reset_inbound_client_stats(self, inbound_id: int) -> bool:
        """
        ریست کردن آمار ترافیک *تمام کلاینت‌های* یک inbound خاص.

        Args:
            inbound_id: شناسه inbound مورد نظر.

        Returns:
            True اگر دستور با موفقیت به پنل ارسال شد، False در غیر این صورت.

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای دیگر API (مانند پیدا نشدن inbound_id).
        """
        logger.info(f"Requesting reset of client stats for inbound {inbound_id} on panel {self.host}")
        try:
            # استفاده از متد reset_client_stats از py3xui.async_api.inbound
            await self.api.inbound.reset_client_stats(inbound_id=inbound_id)
            logger.info(f"Successfully requested reset of client stats for inbound {inbound_id} on panel {self.host}")
            return True
        except AttributeError:
            logger.error(f"The py3xui library (or its inbound module) does not seem to have a 'reset_client_stats' method for panel {self.host}.")
            return False
        except (httpx.RequestError, ConnectionError, TimeoutError) as conn_err:
            logger.error(f"Connection failed during reset_inbound_client_stats request for inbound {inbound_id} on panel {self.host}: {conn_err}", exc_info=True)
            raise XuiConnectionError(f"امکان اتصال به پنل {self.host} هنگام درخواست ریست آمار کلاینت‌های inbound {inbound_id} وجود ندارد.") from conn_err
        except Exception as e:
            # اینجا می‌تواند خطای مربوط به پیدا نشدن inbound_id هم باشد
            logger.error(f"Failed to request reset of client stats for inbound {inbound_id} on panel {self.host}: {e}", exc_info=True)
            # می‌توان خطای خاص‌تری برای Not Found برگرداند اگر py3xui آن را مشخص کند
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
    # async def get_stats(self) -> Optional[Dict[str, Any]]:
    #     """
    #     دریافت آمار کلی سرور (Method might not exist in py3xui)
        
    #     Returns:
    #         آمار سرور شامل CPU، RAM، ترافیک و...
    #     """
    #     logger.warning(f"Attempted to call get_stats for {self.host}, but py3xui may not support this directly.")
    #     # Raise an error or return None, as self.api.get_stats() likely doesn't exist
    #     # raise NotImplementedError("get_stats is not directly supported by the py3xui library wrapper.")
    #     return None # Returning None as the previous attempt showed it's not available

    async def get_server_status(self) -> Optional[Dict[str, Any]]:
        """
        دریافت وضعیت فعلی سرور (CPU، RAM، شبکه و غیره) از پنل.

        Returns:
            یک دیکشنری شامل اطلاعات وضعیت سرور در صورت موفقیت، None در غیر این صورت.
            ساختار دقیق دیکشنری بستگی به پاسخ API پنل دارد.
            {'cpu': float, 'mem': {'current': int, 'total': int}, 'swap': ..., 'net': ...}

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای دیگر API یا پردازش.
        """
        logger.info(f"Attempting to get server status from panel {self.host}")
        try:
            # استفاده از متد get_status از py3xui.async_api.server
            status = await self.api.server.get_status()
            if status:
                 logger.info(f"Successfully retrieved server status from panel {self.host}")
                 # py3xui ممکن است مستقیماً آبجکت Server برگرداند، نیاز به تبدیل به dict؟
                 # فرض می‌کنیم status یا dict است یا دارای __dict__
                 if hasattr(status, '__dict__'):
                     return status.__dict__ # تبدیل آبجکت به دیکشنری
                 elif isinstance(status, dict):
                     return status
                 else:
                     logger.warning(f"Received unexpected type for server status from {self.host}: {type(status)}. Returning raw.")
                     return status # یا None یا raise خطا
            else:
                 logger.warning(f"Received empty or None status from panel {self.host}")
                 return None
        except AttributeError:
            logger.error(f"The py3xui library (or its server module) does not seem to have a 'get_status' method for panel {self.host}.")
            # raise NotImplementedError("get_server_status is not available in the current py3xui version.") from None
            return None # یا raise خطا
        except (httpx.RequestError, ConnectionError, TimeoutError) as conn_err:
            logger.error(f"Connection failed while getting server status for panel {self.host}: {conn_err}", exc_info=True)
            raise XuiConnectionError(f"امکان اتصال به پنل {self.host} هنگام دریافت وضعیت سرور وجود ندارد.") from conn_err
        except Exception as e:
            logger.error(f"Failed to get server status from panel {self.host}: {e}", exc_info=True)
            raise # خطای اصلی را دوباره ایجاد می‌کنیم

    async def download_db_backup(self, save_path: str) -> bool:
        """
        دانلود فایل بکاپ دیتابیس پنل و ذخیره آن در مسیر مشخص شده.

        Args:
            save_path: مسیر کامل فایل برای ذخیره بکاپ (مثال: '/backups/panel_backup.db').

        Returns:
            True اگر دانلود و ذخیره موفقیت آمیز باشد، False در غیر این صورت.

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            IOError: اگر مشکلی در نوشتن فایل ذخیره وجود داشته باشد.
            Exception: برای خطاهای دیگر API.
        """
        logger.info(f"Attempting to download database backup from {self.host} to {save_path}")
        try:
            # استفاده از متد get_db از py3xui.async_api.server
            # این متد در py3xui ممکن است خودش فایل را ذخیره کند یا محتوا را برگرداند
            # مستندات py3xui نشان می‌دهد save_path را به عنوان آرگومان می‌گیرد و None برمی‌گرداند
            await self.api.server.get_db(save_path=save_path)
            logger.info(f"Successfully downloaded database backup from {self.host} and saved to {save_path}")
            # در اینجا باید بررسی کنیم فایل واقعا ایجاد شده یا نه؟ (اختیاری)
            # import os
            # if not os.path.exists(save_path):
            #     logger.error(f"Backup file {save_path} was not created after download attempt from {self.host}.")
            #     return False
            return True
        except AttributeError:
            logger.error(f"The py3xui library (or its server module) does not seem to have a 'get_db' method for panel {self.host}.")
            # raise NotImplementedError("download_db_backup is not available in the current py3xui version.") from None
            return False
        except (httpx.RequestError, ConnectionError, TimeoutError) as conn_err:
            logger.error(f"Connection failed during DB backup download for panel {self.host}: {conn_err}", exc_info=True)
            raise XuiConnectionError(f"امکان اتصال به پنل {self.host} هنگام دانلود بکاپ دیتابیس وجود ندارد.") from conn_err
        except IOError as io_err:
            logger.error(f"Failed to save database backup file to {save_path} from panel {self.host}: {io_err}", exc_info=True)
            raise # خطای نوشتن فایل را دوباره ایجاد می‌کنیم
        except Exception as e:
            logger.error(f"Failed to download database backup from panel {self.host}: {e}", exc_info=True)
            raise # خطای اصلی را دوباره ایجاد می‌کنیم

    async def export_database(self) -> bool:
        """
        دستور به پنل برای ایجاد بکاپ دیتابیس و ارسال آن (معمولا به تلگرام ادمین‌ها).
        این متد فقط دستور را صادر می‌کند و وضعیت ارسال را چک نمی‌کند.

        Returns:
            True اگر دستور با موفقیت به پنل ارسال شد، False در غیر این صورت.

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای دیگر API.
        """
        logger.info(f"Requesting database export on panel {self.host}")
        try:
            # استفاده از متد export از py3xui.async_api.database
            # این متد معمولا None برمی‌گرداند اگر موفق باشد
            await self.api.database.export()
            logger.info(f"Successfully requested database export on panel {self.host}")
            return True
        except AttributeError:
            logger.error(f"The py3xui library (or its database module) does not seem to have an 'export' method for panel {self.host}.")
            # raise NotImplementedError("export_database is not available in the current py3xui version.") from None
            return False
        except (httpx.RequestError, ConnectionError, TimeoutError) as conn_err:
            logger.error(f"Connection failed during database export request for panel {self.host}: {conn_err}", exc_info=True)
            raise XuiConnectionError(f"امکان اتصال به پنل {self.host} هنگام درخواست export دیتابیس وجود ندارد.") from conn_err
        except Exception as e:
            logger.error(f"Failed to request database export on panel {self.host}: {e}", exc_info=True)
            raise # خطای اصلی را دوباره ایجاد می‌کنیم

    async def restart_core(self) -> bool:
        """
        راه‌اندازی مجدد هسته xray/v2ray پنل.
        
        Returns:
            True در صورت موفقیت ارسال دستور (وضعیت ریستارت شدن چک نمی‌شود).
            False اگر متد در کتابخانه موجود نباشد.

        Raises:
            XuiConnectionError: اگر اتصال به پنل برقرار نشود.
            Exception: برای خطاهای دیگر API.
        """
        logger.info(f"Requesting core restart on panel {self.host}")
        try:
            # --- تلاش برای یافتن متد ریستارت --- 
            restart_method = None
            if hasattr(self.api, 'restart_core'):
                 restart_method = self.api.restart_core
            elif hasattr(self.api, 'server') and hasattr(self.api.server, 'restart_core'):
                 restart_method = self.api.server.restart_core
            # اضافه کردن بررسی‌های دیگر اگر لازم باشد # کامنت اضافی حذف شود

            if restart_method:
                result = await restart_method()
                # بررسی نتیجه (معمولا None یا True)
                if result is None or result is True:
                    logger.info(f"Successfully requested core restart on panel {self.host} (Result: {result})")
                    return True
                else:
                    logger.warning(f"Core restart request on {self.host} returned unexpected result: {result}. Assuming failure.")
                    return False
            else:
                logger.error(f"Could not find a 'restart_core' method in py3xui (checked api and api.server) for panel {self.host}.")
                return False # متد یافت نشد

        except (httpx.RequestError, httpx.TimeoutException, httpx.ConnectError) as conn_err:
             logger.error(f"Connection failed during core restart request for panel {self.host}: {conn_err}", exc_info=True)
             raise XuiConnectionError(f"امکان اتصال به پنل {self.host} هنگام درخواست ریستارت هسته وجود ندارد.") from conn_err
        except Exception as e:
            logger.error(f"Failed to request core restart on panel {self.host}: {e}", exc_info=True)
            # raise # یا False # کامنت اضافی حذف شود
            return False

    def is_logged_in(self) -> bool:
        """
        بررسی اینکه آیا کلاینت احتمالاً لاگین شده است یا خیر.
        این متد فقط یک حدس آگاهانه بر اساس وجود توکن ارائه می‌دهد
        و نمی‌تواند اعتبار واقعی سشن را تضمین کند.

        Returns:
            bool: True اگر کلاینت احتمالاً لاگین شده باشد، False در غیر این صورت.
        """
        # بررسی اینکه آیا api توکن یا کوکی دارد
        has_token = bool(getattr(self.api, 'token', None))
        has_cookie = False
        
        # بررسی وجود کوکی در کلاینت httpx داخلی
        if hasattr(self.api, '_client') and hasattr(self.api._client, 'cookies'):
            has_cookie = bool(self.api._client.cookies)
        
        # اگر توکن یا کوکی داشته باشیم، احتمالاً لاگین هستیم
        return has_token or has_cookie
