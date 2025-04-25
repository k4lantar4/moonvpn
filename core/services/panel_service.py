"""
سرویس مدیریت پنل‌ها و تنظیمات inbound
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from db.models.panel import Panel, PanelStatus, PanelType
from db.models.inbound import Inbound, InboundStatus
from core.integrations.xui_client import XuiClient, XuiAuthenticationError, XuiConnectionError
from core.services.notification_service import NotificationService
from db.repositories.panel_repo import PanelRepository
from db import get_async_db

logger = logging.getLogger(__name__)

# Define service-level exceptions
class PanelConnectionError(Exception):
    """Raised when connection testing fails."""
    pass

class PanelSyncError(Exception):
    """Raised when syncing inbounds fails."""
    pass

# Helper function to convert potential py3xui objects to dict
def _to_dict_safe(obj: Any) -> Dict | Any:
    if obj is None:
        return {} # Return empty dict for None to store as JSON '{}'
    if isinstance(obj, dict):
        return obj # Already a dict
    if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
        try:
            return obj.dict() # Try calling .dict() method
        except Exception as e:
            logger.warning(f"Failed to call .dict() on object {type(obj)}: {e}. Falling back to vars().")
            # Fallback or handle error appropriately
    if hasattr(obj, '__dict__'):
        try:
            # Fallback using vars() if .dict() fails or doesn't exist
            # Be cautious as vars() might expose private attributes
            d = vars(obj)
            # Attempt to serialize the dict to catch issues early
            json.dumps(d) 
            return d
        except TypeError:
             logger.error(f"Object of type {type(obj)} could not be serialized to JSON even with vars(). Returning empty dict.", exc_info=True)
             return {} # Cannot serialize
        except Exception as e:
            logger.error(f"Error converting object {type(obj)} using vars(): {e}. Returning empty dict.", exc_info=True)
            return {}
            
    # If it's not None, not dict, has no .dict() or vars(), or vars() fails serialization
    logger.warning(f"Object of type {type(obj)} is not directly JSON serializable and couldn't be converted to dict. Storing as empty JSON.")
    return {} # Default to empty dict if conversion fails

class PanelService:
    """سرویس مدیریت پنل‌ها و تنظیمات inbound"""

    def __init__(self, session: AsyncSession):
        """
        ایجاد نمونه سرویس
        Args:
            session: نشست پایگاه داده
        """
        self.session = session
        self.panel_repo = PanelRepository(session)
        self.notification_service = NotificationService(session)
        self._xui_clients: Dict[int, XuiClient] = {}  # Cache for XuiClient instances

    async def _test_panel_connection_details(self, url: str, username: str, password: str) -> bool:
        """
        Private helper: Tests connection and login to potential panel details,
        including verification via get_inbounds.

        Returns:
            True if login and verification succeed.
        Raises:
            PanelConnectionError: If login or verification fails.
        """
        temp_client = XuiClient(host=url, username=username, password=password)
        try:
            login_successful = await temp_client.login() # Attempt login (may return True for None)
            if not login_successful:
                 logger.warning(f"Initial login failed during connection test for {url}.")
                 raise PanelConnectionError("احراز هویت اولیه ناموفق بود.") # More specific than str(e)
            
            # Verify connection
            logger.info(f"Initial login reported success for {url}. Verifying...")
            verified = await temp_client.verify_connection()
            if verified:
                 logger.info(f"Connection test and verification successful for {url}.")
                 return True
            else:
                 logger.warning(f"Connection verification failed during connection test for {url}.")
                 raise PanelConnectionError("تأیید اتصال پس از لاگین ناموفق بود.")

        except (XuiAuthenticationError, XuiConnectionError) as e:
            # Catch errors from login() or verify_connection()
            logger.warning(f"Panel connection test failed for {url}: {e}")
            raise PanelConnectionError(f"تست اتصال ناموفق: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during panel connection test for {url}: {e}", exc_info=True)
            raise PanelConnectionError(f"خطای پیش‌بینی نشده در تست اتصال به پنل: {e}") from e
            
    async def test_panel_connection(self, panel_id: int) -> tuple[bool, str | None]:
        """
        تست اتصال و لاگین به یک پنل ثبت شده با استفاده از ID.

        Args:
            panel_id: شناسه پنل

        Returns:
            tuple[bool, str | None]: (موفقیت, پیام خطا در صورت عدم موفقیت)
        """
        panel = await self.get_panel_by_id(panel_id)
        if not panel:
            return False, "پنل مورد نظر یافت نشد."
            
        if not panel.url or not panel.username or not panel.password:
            return False, "اطلاعات اتصال (URL, نام کاربری، رمز عبور) پنل کامل نیست."

        temp_client = XuiClient(host=panel.url, username=panel.username, password=panel.password)
        try:
            login_result = await temp_client.login() # May return True even if ambiguous
            if login_result:
                 logger.info(f"Initial login reported success for panel {panel_id} test. Verifying...")
                 # Verify connection with get_inbounds
                 verified = await temp_client.verify_connection()
                 if verified:
                     logger.info(f"Connection verified successfully for panel {panel_id} test.")
                     return True, None  # Connection successful and verified
                 else:
                     logger.warning(f"Connection verification failed for panel {panel_id} test (get_inbounds failed)." )
                     return False, "اتصال به پنل برقرار شد اما تأیید نشد (خطای دریافت لیست inboundها)."
            else:
                 # Should not happen if login() only returns True or raises Exception
                 logger.error(f"temp_client.login() returned False unexpectedly during test for panel {panel_id}.")
                 return False, "خطای داخلی: لاگین ناموفق بود."
            
        except XuiAuthenticationError as e:
            logger.warning(f"Panel {panel_id} authentication failed during login or verification: {e}")
            return False, f"خطای احراز هویت: {e}"
        except XuiConnectionError as e:
            # This will catch connection errors during login() or verify_connection()
            logger.warning(f"Panel {panel_id} connection failed during login or verification: {e}")
            return False, f"خطای اتصال/تأیید: {e}"
        except Exception as e:
            logger.error(f"Unexpected error testing connection for panel {panel_id}: {e}", exc_info=True)
            return False, f"خطای پیش‌بینی نشده: {e}"

    async def add_panel(self, name: str, location: str, flag_emoji: str,
                     url: str, username: str, password: str) -> Panel:
        """
        افزودن پنل جدید
        Args:
            name: نام پنل
            location: موقعیت پنل
            flag_emoji: ایموجی پرچم
            url: آدرس پنل
            username: نام کاربری
            password: رمز عبور
        Returns:
            Panel: پنل ایجاد شده
        """
        # 1. تست اتصال به پنل قبل از ایجاد
        try:
            await self._test_panel_connection_details(url=url, username=username, password=password)
            logger.info(f"Panel connection test successful for {url}")
        except PanelConnectionError as e:
            logger.error(f"Failed to add panel {name} at {url}. Connection test failed: {e}")
            # Raise the specific connection error for the bot layer
            raise e
        except Exception as e:
             logger.error(f"Unexpected error during connection test for panel {name} at {url}: {e}", exc_info=True)
             # Raise a generic error for other unexpected issues
             raise PanelConnectionError(f"خطای پیش‌بینی نشده در زمان تست اتصال: {e}") from e

        # 2. ایجاد پنل در دیتابیس
        panel_data = {
            "name": name,
            "location_name": location, # Changed key from location to location_name
            "flag_emoji": flag_emoji,
            "url": url,
            "username": username,
            "password": password,
            "status": PanelStatus.ACTIVE,
            "type": PanelType.XUI # Assuming XUI is the default/only type for now
        }
        
        panel: Optional[Panel] = None # Initialize panel as None
        try:
            # Use the repository method to create the panel
            panel = await self.panel_repo.create_panel(panel_data)
            # No need to flush here, create_panel should handle it.
            # await self.session.flush() # Flush to get the panel ID
            logger.info(f"Panel {name} (ID: {panel.id}) created successfully in DB.")

            # 3. همگام‌سازی اولیه inbound‌ها
            await self.sync_panel_inbounds(panel.id)
            logger.info(f"Initial inbound sync completed for panel {panel.id}.")

        except SQLAlchemyError as db_err:
            logger.error(f"Database error while adding panel {name} or syncing: {db_err}", exc_info=True)
            await self.session.rollback()
            # Consider deleting the panel if DB add failed but test passed?
            raise ValueError(f"خطا در ذخیره اطلاعات پنل در دیتابیس: {db_err}")
        except PanelSyncError as sync_err: # Catch specific sync error from sync_panel_inbounds
             logger.error(f"Panel {panel.id} ({panel.name}) created in DB, but initial inbound sync failed: {sync_err}", exc_info=True)
             # Panel exists in DB, but sync failed. Set status to ERROR.
             if panel: # Ensure panel object exists before trying to update
                 panel.status = PanelStatus.ERROR
                 try:
                     await self.session.commit() # Commit status change
                     logger.info(f"Set status of panel {panel.id} to ERROR due to sync failure.")
                 except SQLAlchemyError as db_commit_err:
                     logger.error(f"Failed to commit ERROR status for panel {panel.id} after sync failure: {db_commit_err}", exc_info=True)
                     # Rollback might be needed if commit fails
                     await self.session.rollback()
                 # Send notification even if commit failed, as the issue happened
                 await self.notification_service.notify_admins(
                     f"⚠️ پنل {panel.name} (ID: {panel.id}) در دیتابیس ثبت شد، اما همگام‌سازی اولیه inboundها با خطا مواجه شد:\n`{sync_err}`\nوضعیت پنل به ERROR تغییر یافت."
                 )
             # Don't raise here, return the panel with error status so the callback can inform the user
        except Exception as e:
            logger.error(f"Unexpected error after connection test during panel add/sync {panel.id}: {e}", exc_info=True)
            await self.session.rollback()
            # If panel object exists and has an ID, maybe try setting status to ERROR
            if panel and panel.id:
                try:
                    panel.status = PanelStatus.ERROR
                    await self.session.commit()
                except Exception as commit_err:
                    logger.error(f"Failed to set panel {panel.id} status to ERROR after failed sync: {commit_err}")
            raise ValueError(f"خطای پیش‌بینی نشده در زمان ثبت پنل یا همگام‌سازی: {e}")

        return panel

    async def get_panel_by_id(self, panel_id: int) -> Optional[Panel]:
        """
        دریافت پنل با شناسه
        Args:
            panel_id: شناسه پنل
        Returns:
            Panel: پنل یافت شده یا None
        """
        return await self.panel_repo.get_panel_by_id(panel_id)

    async def get_active_panels(self) -> List[Panel]:
        """
        دریافت لیست پنل‌های فعال
        Returns:
            List[Panel]: لیست پنل‌های فعال
        """
        return await self.panel_repo.get_active_panels()

    async def get_all_panels(self) -> List[Panel]:
        """
        دریافت لیست تمامی پنل‌ها
        Returns:
            List[Panel]: لیست تمامی پنل‌ها
        """
        return await self.panel_repo.get_all_panels()

    async def _get_xui_client(self, panel: Panel) -> XuiClient:
        """
        Get or create a verified XuiClient instance for a panel.
        Always verifies the connection upon creation or retrieval if not recently verified.
        """
        # Check cache first
        if panel.id in self._xui_clients:
            client = self._xui_clients[panel.id]
            # Ensure host matches in case panel URL was updated
            if client.host == panel.url.rstrip("/"):
                 # Optional: Add a check here to avoid re-verifying too frequently if needed
                 # For now, let's re-verify to be safe, as the underlying login is ambiguous
                 logger.debug(f"Re-verifying cached client for panel {panel.id}")
                 try:
                     if await client.verify_connection():
                         logger.info(f"Cached client verification successful for panel {panel.id}")
                         return client
                     else:
                         logger.warning(f"Cached client verification failed for panel {panel.id}. Re-initializing.")
                 except Exception as verify_err:
                      logger.error(f"Error verifying cached client for panel {panel.id}: {verify_err}. Re-initializing.", exc_info=True)
            else:
                logger.info(f"Panel URL changed for panel {panel.id} or client invalid. Re-initializing XuiClient.")
        
        # Initialize or re-initialize if not cached, host mismatch, or verification failed
        logger.info(f"Initializing XuiClient for panel {panel.id} at {panel.url}")
        if not panel.url or not panel.username or not panel.password:
            raise PanelConnectionError(f"اطلاعات اتصال پنل {panel.id} (URL, نام کاربری، رمز عبور) ناقص است.")

        client = XuiClient(host=panel.url, username=panel.username, password=panel.password)
        try:
            login_successful = await client.login() # Attempt login (may return True for None)
            if not login_successful:
                 # Should not happen based on current login logic, but handle defensively
                 logger.error(f"client.login() returned False unexpectedly for panel {panel.id}.")
                 raise PanelConnectionError(f"احراز هویت اولیه برای پنل {panel.id} ناموفق بود.")
            
            # Always verify after login due to ambiguous None return
            logger.info(f"Initial login reported success for panel {panel.id}. Verifying connection...")
            verified = await client.verify_connection()
            if verified:
                logger.info(f"Connection verified successfully for panel {panel.id} after initialization.")
                self._xui_clients[panel.id] = client # Cache the verified client
                return client
            else:
                logger.error(f"Connection verification failed for panel {panel.id} after initialization.")
                raise PanelConnectionError(f"تأیید اتصال به پنل {panel.id} پس از لاگین ناموفق بود.")

        except (XuiAuthenticationError, XuiConnectionError) as e:
            # Catch errors from login() or verify_connection()
            logger.error(f"Failed to initialize or verify client for panel {panel.id}: {e}", exc_info=True)
            raise PanelConnectionError(f"خطا در اتصال یا تأیید پنل {panel.id}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error initializing/verifying client for panel {panel.id}: {e}", exc_info=True)
            raise PanelConnectionError(f"خطای پیش‌بینی نشده هنگام مقداردهی کلاینت برای پنل {panel.id}: {e}") from e
            
    async def sync_panel_inbounds(self, panel_id: int) -> None:
        """
        همگام‌سازی inbound‌های پنل با پایگاه داده
        Args:
            panel_id: شناسه پنل
        """
        # دریافت پنل
        panel = await self.panel_repo.get_panel_by_id(panel_id)
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")

        # دریافت inbound‌های فعلی
        await self.session.refresh(panel, attribute_names=['inbounds']) # Explicitly load/refresh inbounds
        current_inbounds = {inb.remote_id: inb for inb in panel.inbounds 
                          if inb.status != InboundStatus.DELETED}

        client: Optional[XuiClient] = None # Initialize client to None
        try:
            # دریافت کلاینت (شامل تست اتصال/لاگین)
            client = await self._get_xui_client(panel)
        except PanelConnectionError as client_err:
            logger.error(f"Failed to get XUI client for panel {panel_id} during sync: {client_err}", exc_info=True)
            panel.status = PanelStatus.ERROR # Mark panel as error if client cannot be initialized
            await self.session.commit()
            raise PanelSyncError(f"امکان اتصال یا احراز هویت به پنل {panel.name} برای همگام‌سازی وجود ندارد.") from client_err

        try:
            # دریافت inbound‌ها از پنل با کلاینت تایید شده
            panel_inbounds = await client.get_inbounds()

            if panel_inbounds is None: # Handle case where get_inbounds might return None
                logger.warning(f"Received None for inbounds from panel {panel.id} during sync. Assuming empty list.")
                panel_inbounds = []
            
            # Set of remote inbound IDs from the panel - using attribute access
            remote_ids = {inb_data.id for inb_data in panel_inbounds}

            # به‌روزرسانی یا ایجاد inbound‌ها - using attribute access and converting objects to dict
            for inb_data in panel_inbounds:
                remote_id = inb_data.id # Use attribute access
                
                settings_obj = getattr(inb_data, 'settings', None)
                sniffing_obj = getattr(inb_data, 'sniffing', None)

                # Convert settings and sniffing objects to dictionaries
                settings_dict = _to_dict_safe(settings_obj)
                sniffing_dict = _to_dict_safe(sniffing_obj)
                
                if remote_id in current_inbounds:
                    # به‌روزرسانی inbound موجود
                    inbound = current_inbounds[remote_id]
                    inbound.protocol = getattr(inb_data, 'protocol', None) # Use getattr for safety
                    inbound.tag = getattr(inb_data, 'remark', "") # Use remark as tag?
                    inbound.port = getattr(inb_data, 'port', None)
                    inbound.settings_json = settings_dict # Assign converted dict
                    inbound.sniffing = sniffing_dict # Assign converted dict
                    inbound.status = (InboundStatus.ACTIVE 
                                    if getattr(inb_data, 'enable', True) 
                                    else InboundStatus.DISABLED)
                    inbound.last_synced = datetime.utcnow()
                else:
                    # ایجاد inbound جدید
                    new_inbound = Inbound(
                        panel_id=panel.id,
                        remote_id=remote_id,
                        protocol=getattr(inb_data, 'protocol', None),
                        tag=getattr(inb_data, 'remark', ""), # Use remark as tag?
                        port=getattr(inb_data, 'port', None),
                        settings_json=settings_dict, # Assign converted dict
                        sniffing=sniffing_dict, # Assign converted dict
                        status=(InboundStatus.ACTIVE 
                                if getattr(inb_data, 'enable', True) 
                                else InboundStatus.DISABLED),
                        last_synced=datetime.utcnow()
                        # Assign other potential fields if they exist in the py3xui object
                        # Example: Check if attributes exist before assigning to DB model fields
                        # listen = getattr(inb_data, 'listen', None),
                        # receive_original_dest = getattr(inb_data, 'receive_original_dest', False),
                        # allow_transparent = getattr(inb_data, 'allow_transparent', False),
                    )
                    self.session.add(new_inbound)
                    logger.info(f"Added new inbound {remote_id} ('{new_inbound.tag}') for panel {panel.id}")

            # شناسایی و حذف inbound‌هایی که در پنل نیستند
            inbounds_to_delete = []
            for remote_id, inbound in current_inbounds.items():
                if remote_id not in remote_ids:
                    inbound.status = InboundStatus.DELETED
                    inbound.last_synced = datetime.utcnow()
                    inbounds_to_delete.append(inbound)
                    logger.info(f"Marking inbound {remote_id} ('{inbound.tag}') for panel {panel.id} as DELETED.")

            await self.session.commit()
            logger.info(f"Successfully synced inbounds for panel {panel.id}.")

            # Update panel status to ACTIVE if it was previously in ERROR
            if panel.status == PanelStatus.ERROR:
                logger.info(f"Panel {panel.id} was in ERROR status, setting back to ACTIVE after successful sync.")
                panel.status = PanelStatus.ACTIVE
                await self.session.commit()

        except (XuiAuthenticationError, XuiConnectionError) as panel_api_err:
            # Errors specifically from client.get_inbounds()
            logger.error(f"XUI API error during inbound sync for panel {panel_id}: {panel_api_err}", exc_info=True)
            panel.status = PanelStatus.ERROR # Mark panel as error on sync failure
            await self.session.commit()
            raise PanelSyncError(f"خطا در ارتباط با API پنل {panel.name} هنگام همگام‌سازی: {panel_api_err}") from panel_api_err
        except SQLAlchemyError as db_err:
            logger.error(f"Database error during inbound sync commit for panel {panel_id}: {db_err}", exc_info=True)
            await self.session.rollback()
            # Don't change panel status here, the connection might be fine, DB is the issue
            raise PanelSyncError(f"خطا در ذخیره اطلاعات inboundها برای پنل {panel.id}: {db_err}") from db_err
        except Exception as e:
            # Catch potential TypeErrors during attribute access or conversion
            logger.error(f"Unexpected error during inbound sync processing for panel {panel_id}: {e}", exc_info=True)
            await self.session.rollback() # Rollback any partial changes
            # Consider setting panel status to ERROR for unexpected issues?
            panel.status = PanelStatus.ERROR
            await self.session.commit()
            raise PanelSyncError(f"خطای پیش‌بینی نشده در همگام‌سازی inboundها برای پنل {panel.id}: {e}") from e

    async def sync_all_panels_inbounds(self) -> Dict[int, List[Inbound]]:
        """
        همگام‌سازی inbound‌های تمام پنل‌های فعال با دیتابیس
        
        Returns:
            دیکشنری از شناسه پنل به لیست inbound‌های همگام‌سازی شده
        """
        panels = await self.get_active_panels()
        results = {}
        
        for panel in panels:
            try:
                await self.sync_panel_inbounds(panel.id)
                results[panel.id] = panel.inbounds
                logger.info(f"Successfully synced {len(panel.inbounds)} inbounds for panel {panel.name}")
            except Exception as e:
                logger.error(f"Failed to sync inbounds for panel {panel.name} (ID: {panel.id}): {str(e)}")
                # ارسال نوتیفیکیشن به ادمین‌ها
                await self.notification_service.notify_admins(
                    f"⚠️ خطا در همگام‌سازی inbound‌های پنل {panel.name}:\n{str(e)}"
                )
                # ادامه دادن با پنل بعدی بدون توقف پروسه
                results[panel.id] = []
        
        return results

    async def get_panel_by_location(self, location: str) -> Optional[Panel]:
        """
        دریافت پنل با لوکیشن مشخص
        
        Args:
            location: نام لوکیشن
            
        Returns:
            پنل یافت شده یا None
        """
        return await self.panel_repo.get_by_location(location)

    async def get_panel_by_address(self, address: str) -> Optional[Panel]:
        """
        دریافت پنل با آدرس مشخص
        
        Args:
            address: آدرس پنل
            
        Returns:
            پنل یافت شده یا None
        """
        return await self.panel_repo.get_by_address(address)

    # اضافه کردن متد برای دریافت لیست اینباندها به صورت real-time
    async def get_inbounds_by_panel_id(self, panel_id: int) -> List[Dict[str, Any]]:
        """
        دریافت لیست inbound‌های یک پنل خاص
        Args:
            panel_id: شناسه پنل
        Returns:
            لیست inbound‌ها
        """
        panel = await self.panel_repo.get_by_id(panel_id, [selectinload(Panel.inbounds)])
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")

        # Filter out deleted inbounds
        active_inbounds = [
            {
                "id": inb.remote_id,
                "protocol": inb.protocol,
                "remark": inb.tag,
                "port": inb.port,
                "enable": inb.status == InboundStatus.ACTIVE
            }
            for inb in panel.inbounds if inb.status != InboundStatus.DELETED
        ]
        return active_inbounds

    async def get_clients_by_inbound(self, panel_id: int, inbound_id: int) -> List[Dict[str, Any]]:
        """
        دریافت لیست کلاینت‌های یک inbound خاص از پنل
        Args:
            panel_id: شناسه پنل
            inbound_id: شناسه inbound در پنل
        Returns:
            لیست دیکشنری شامل اطلاعات کلاینت‌ها
        """
        panel = await self.panel_repo.get_by_id(panel_id)
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")

        client = await self._get_xui_client(panel)
        inbound_data = await client.get_inbound(inbound_id)

        if not inbound_data:
            return [] # Inbound not found or no data

        # Determine if clientStats is enabled and available
        use_client_stats = inbound_data.get("clientStats", False) and "clientStats" in inbound_data

        clients_list = []
        if use_client_stats and isinstance(inbound_data.get("clientStats"), list):
             # Use clientStats if enabled and available
             for client_stat in inbound_data["clientStats"]:
                clients_list.append({
                    "uuid": client_stat.get("id"), # Use id for UUID
                    "email": client_stat.get("email"),
                    "enable": client_stat.get("enable", False),
                    "totalGB": client_stat.get("totalGB", 0),
                    "up": client_stat.get("up", 0),
                    "down": client_stat.get("down", 0),
                    "expiryTime": client_stat.get("expiryTime", 0),
                    # Add other relevant fields from clientStats if needed
                })
        elif isinstance(inbound_data.get("settings", {}).get("clients"), list):
            # Otherwise, use clients from settings
            for client_setting in inbound_data["settings"]["clients"]:
                clients_list.append({
                    "uuid": client_setting.get("id"), # Use id for UUID
                    "email": client_setting.get("email"),
                    "enable": client_setting.get("enable", False), # Assuming enable is in settings
                    "totalGB": client_setting.get("totalGB", 0), # Assuming totalGB is in settings
                    "up": client_setting.get("up", 0), # Assuming these are not in settings and will be 0 if clientStats is off
                    "down": client_setting.get("down", 0),
                    "expiryTime": client_setting.get("expiryTime", 0), # Assuming expiryTime is in settings
                    # Add other relevant fields from settings if needed
                })
        else:
            # No client data found
            return []


        return clients_list

    async def get_client_config(self, panel_id: int, inbound_id: int, uuid: str) -> str:
        """
        دریافت لینک کانفیگ یک کلاینت
        """
        panel = await self.get_panel_by_id(panel_id)
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")
        client = await self._get_xui_client(panel)
        try:
            config_url = await client.get_config(uuid)
            logger.info(f"Generated config URL for client {uuid} on panel {panel_id}")
            return config_url
        except Exception as e:
            logger.error(f"Error getting config for client {uuid} on panel {panel_id}: {str(e)}", exc_info=True)
            raise

    async def reset_client_traffic(self, panel_id: int, uuid: str) -> bool:
        """
        ریست کردن ترافیک یک کلاینت
        """
        panel = await self.get_panel_by_id(panel_id)
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")
        client = await self._get_xui_client(panel)
        try:
            result = await client.reset_client_traffic(uuid)
            logger.info(f"Successfully reset traffic for client {uuid} on panel {panel_id}")
            return result
        except Exception as e:
            logger.error(f"Error resetting traffic for client {uuid} on panel {panel_id}: {str(e)}", exc_info=True)
            raise

    async def delete_client(self, panel_id: int, inbound_id: int, uuid: str) -> bool:
        """
        حذف یک کلاینت از inbound و دیتابیس
        """
        panel = await self.get_panel_by_id(panel_id)
        if not panel:
            raise ValueError(f"پنل با شناسه {panel_id} یافت نشد")
        client = await self._get_xui_client(panel)
        try:
            result = await client.delete_client(uuid)
            if result:
                from db.models.client_account import ClientAccount
                # حذف رکورد از دیتابیس
                stmt = select(ClientAccount).where(
                    ClientAccount.panel_id == panel_id,
                    ClientAccount.inbound_id == inbound_id,
                    ClientAccount.remote_uuid == uuid
                )
                res = await self.session.execute(stmt)
                account = res.scalar_one_or_none()
                if account:
                    await self.session.delete(account)
                    await self.session.commit()
                logger.info(f"Deleted client {uuid} from panel {panel_id} and DB")
            return result
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting client {uuid} on panel {panel_id}: {str(e)}", exc_info=True)
            raise

    async def register_panel(self, url: str, username: str, password: str, location_name: str) -> Panel:
        """Register a new panel after testing connection."""
        logger.info(f"Attempting to register panel: {url}, Location: {location_name}")

        # Check if panel with this URL already exists
        existing_panel = await self.panel_repo.get_panel_by_url(url)
        if existing_panel:
            logger.warning(f"Panel registration failed: Panel with URL {url} already exists (ID: {existing_panel.id})")
            raise ValueError(f"پنلی با آدرس {url} قبلاً ثبت شده است.")

        # Temporary panel object for connection testing
        temp_panel_data = {
            "url": url, 
            "username": username, 
            "password": password,
            "location_name": location_name # Need a name for logging/error context
        }
        
        # Use a temporary Panel object structure for testing
        client = XuiClient(
            host=url,
            username=username,
            password=password
        )

        try:
            logger.info(f"Attempting to login to panel at {url} for connection test...")
            # Use login() method to test connection and credentials
            is_connected = await client.login() 
            if not is_connected:
                logger.error(f"Login failed for panel at {url} during registration test.")
                # Optionally raise a more specific error if login returns False but doesn't raise exception
                raise ConnectionError("ورود به پنل ناموفق بود. لطفاً اطلاعات را بررسی کنید.")
            logger.info(f"Connection test (via login) successful for panel at {url}")

            # Extract flag emoji if possible
            flag_emoji = self._extract_flag_emoji(location_name)

            # Create panel data
            panel_data = {
                "url": url,
                "username": username,
                "password": password,  # Consider encrypting password later
                "location_name": location_name.strip(),
                "flag_emoji": flag_emoji,
                "status": PanelStatus.ACTIVE, # Set to active after successful test
                "type": "xui" # Assuming x-ui panel type for now
            }
            
            # Create panel using repository
            logger.info(f"Creating panel record in database for {url}...")
            panel = await self.panel_repo.create_panel(panel_data)
            
            # Log success after flush/refresh in repo confirms persistence tentatively
            logger.info(f"✅ Panel persisted to DB: ID={panel.id}, Location={panel.location_name}, URL={panel.url}")

            # Perform initial inbound sync after creation
            try:
                logger.info(f"Performing initial inbound sync for panel {panel.id}...")
                await self.sync_panel_inbounds(panel.id)
                logger.info(f"Initial inbound sync completed for panel {panel.id}")
            except Exception as sync_error:
                logger.error(f"Error during initial inbound sync for panel {panel.id}: {sync_error}", exc_info=True)
                # Decide if this error should prevent panel registration or just be logged
                # For now, log it and continue, panel is registered but sync failed.
                # Consider adding a notification here.


            return panel

        except ConnectionError as ce:
             logger.error(f"ConnectionError during panel registration for {url}: {ce}")
             raise # Re-raise connection errors to be handled by the caller
        except ValueError as ve:
            logger.error(f"ValueError during panel registration for {url}: {ve}")
            raise # Re-raise value errors (like duplicate URL)
        except Exception as e:
            logger.error(f"Unexpected error registering panel {url}: {str(e)}", exc_info=True)
            raise RuntimeError(f"خطای غیرمنتظره در زمان ثبت پنل: {str(e)}") # Raise a generic runtime error

    async def update_panel_status(self, panel_id: int, status: PanelStatus) -> bool:
        """
        Updates the status of a specific panel.
        Args:
            panel_id: ID of the panel to update.
            status: The new PanelStatus enum value.
        Returns:
            True if update was successful, False otherwise.
        """
        try:
            panel = await self.panel_repo.get_panel_by_id(panel_id)
            if not panel:
                logger.error(f"Cannot update status: Panel with ID {panel_id} not found.")
                return False
            
            if panel.status == status:
                logger.info(f"Panel {panel_id} status is already {status}. No update needed.")
                return True # No change needed
                
            panel.status = status
            await self.session.commit()
            logger.info(f"Successfully updated status for panel {panel_id} to {status}.")
            
            # Notify admins if status changed to ERROR
            if status == PanelStatus.ERROR:
                 await self.notification_service.notify_admins(
                     f"⚠️ وضعیت پنل {panel.name} (ID: {panel.id}) به ERROR تغییر یافت."
                 )
            # Notify if changed back to ACTIVE from ERROR
            elif status == PanelStatus.ACTIVE and panel.status == PanelStatus.ERROR:
                await self.notification_service.notify_admins(
                     f"✅ وضعیت پنل {panel.name} (ID: {panel.id}) به ACTIVE بازگردانده شد."
                 )
                 
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error updating status for panel {panel_id}: {e}", exc_info=True)
            return False
        except Exception as e:
            await self.session.rollback() # Rollback on any other error
            logger.error(f"Unexpected error updating status for panel {panel_id}: {e}", exc_info=True)
            return False
