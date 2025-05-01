"""
سرویس مدیریت پنل‌ها و تنظیمات inbound
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from urllib.parse import urlparse # Added for default name generation

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
            logger.warning(f"Failed to call .dict() on object {type(obj)}: {e}. Falling back to vars(). (فراخوانی dict. ناموفق بود)")
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
             logger.error(f"Object of type {type(obj)} could not be serialized to JSON even with vars(). Returning empty dict. (امکان سریال‌سازی با vars وجود ندارد)", exc_info=True)
             return {} # Cannot serialize
        except Exception as e:
            logger.error(f"Error converting object {type(obj)} using vars(): {e}. Returning empty dict. (خطا در تبدیل با vars)", exc_info=True)
            return {}

    # If it's not None, not dict, has no .dict() or vars(), or vars() fails serialization
    logger.warning(f"Object of type {type(obj)} is not directly JSON serializable and couldn't be converted to dict. Storing as empty JSON. (امکان تبدیل به دیکشنری وجود ندارد)")
    return {} # Default to empty dict if conversion fails

class PanelService:
    """سرویس جامع برای مدیریت پنل‌های XUI شامل عملیات CRUD،
    تست اتصال، همگام‌سازی inboundها و مدیریت وضعیت.
    """

    def __init__(self, session: AsyncSession):
        """
        ایجاد نمونه سرویس PanelService.

        Args:
            session: نشست پایگاه داده (AsyncSession).
        """
        self.session = session
        self.panel_repo = PanelRepository(session)
        self.notification_service = NotificationService(session)
        self._xui_clients: Dict[int, XuiClient] = {}  # Cache for XuiClient instances

    async def _test_panel_connection_details(self, url: str, username: str, password: str) -> bool:
        """
        [Helper خصوصی] تست اتصال و لاگین به پنل با اطلاعات داده شده.
        این متد شامل تأیید اتصال از طریق فراخوانی `verify_connection` در کلاینت است.

        Args:
            url: آدرس پنل.
            username: نام کاربری.
            password: رمز عبور.

        Returns:
            True اگر لاگین و تأیید موفقیت‌آمیز باشد.

        Raises:
            PanelConnectionError: اگر لاگین یا تأیید ناموفق باشد یا خطای دیگری رخ دهد.
        """
        logger.debug(f"شروع تست اتصال داخلی برای: {url} (Starting internal connection test for: {url})")
        temp_client = XuiClient(host=url, username=username, password=password)
        try:
            # Login first
            await temp_client.login()
            logger.debug(f"Login successful for {url} during internal test.")
            # verify_connection handles login internally if needed, but logging in explicitly ensures it happens
            verified = await temp_client.verify_connection()
            if verified:
                 logger.info(f"✅ تست و تأیید اتصال داخلی موفق بود برای {url}. (Internal connection test and verification successful for {url}.)")
                 return True
            else:
                 # Should ideally not happen if verify_connection raises exceptions
                 logger.warning(f"🔥 تست اتصال داخلی برای {url} ناموفق بود (تأیید شکست خورد). (Internal connection test failed for {url} (verification failed).)")
                 raise PanelConnectionError("تأیید اتصال پس از لاگین ناموفق بود. (Connection verification failed after login.)")

        except (XuiAuthenticationError, XuiConnectionError) as e:
            logger.warning(f"🔥 تست اتصال داخلی ناموفق بود برای {url}: {e} (Internal connection test failed for {url}: {e})")
            # Wrap XUI exceptions in our service-level exception
            raise PanelConnectionError(f"تست اتصال ناموفق: {e} (Connection test failed: {e})") from e
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده حین تست اتصال داخلی برای {url}: {e} (Unexpected error during internal connection test for {url}: {e})", exc_info=True)
            raise PanelConnectionError(f"خطای پیش‌بینی نشده در تست اتصال به پنل: {e} (Unexpected error during panel connection test: {e})") from e

    async def test_panel_connection(self, panel_id: int) -> tuple[bool, str | None]:
        """
        تست اتصال و لاگین به یک پنل ثبت شده با استفاده از ID آن.
        این متد از `_test_panel_connection_details` که شامل تأیید با `get_inbounds` است، استفاده نمی‌کند
        و فقط لاگین اولیه را چک می‌کند و سپس با `verify_connection` تأیید می‌کند.

        Args:
            panel_id: شناسه پنل.

        Returns:
            tuple[bool, str | None]: (موفقیت اتصال و تأیید, پیام خطا در صورت عدم موفقیت).
        """
        logger.info(f"شروع تست اتصال برای پنل ID: {panel_id}... (Starting connection test for panel ID: {panel_id}...)")
        panel = await self.panel_repo.get_panel_by_id(panel_id) # Use repo directly
        if not panel:
            logger.warning(f"تست اتصال ناموفق: پنل با ID {panel_id} یافت نشد. (Connection test failed: Panel with ID {panel_id} not found.)")
            return False, f"پنل مورد نظر (ID: {panel_id}) یافت نشد."

        if not panel.url or not panel.username or not panel.password:
            logger.warning(f"تست اتصال ناموفق برای پنل {panel_id}: اطلاعات اتصال ناقص است. (Connection test failed for panel {panel_id}: Incomplete connection details.)")
            return False, "اطلاعات اتصال (URL, نام کاربری، رمز عبور) پنل کامل نیست."

        # Use the cached client if available, otherwise create a temporary one
        client = await self._get_xui_client(panel) # Use helper to get/create client

        try:
            # Explicitly login first
            await client.login()
            logger.debug(f"Login successful for panel {panel_id} during connection test.")
            # verify_connection might handle login internally, but explicit login ensures it.
            verified = await client.verify_connection()
            if verified:
                logger.info(f"✅ تست اتصال و تأیید برای پنل {panel_id} موفق بود. (Connection test and verification successful for panel {panel_id}.)")
                # Update panel status to ACTIVE if it was in ERROR state? Maybe.
                # if panel.status == PanelStatus.ERROR:
                #     await self.update_panel_status(panel_id, PanelStatus.ACTIVE)
                #     logger.info(f"وضعیت پنل {panel_id} از ERROR به ACTIVE تغییر یافت پس از تست موفق. (Panel {panel_id} status changed from ERROR to ACTIVE after successful test.)")
                return True, None
            else:
                # This case might be less likely if verify_connection raises exceptions on failure
                logger.warning(f"🔥 تست اتصال برای پنل {panel_id} ناموفق بود (تأیید اتصال شکست خورد). (Connection test failed for panel {panel_id} (verification failed).)")
                return False, "اتصال به پنل برقار شد اما تأیید نشد (احتمالا خطای دریافت inboundها)."

        except (XuiAuthenticationError, XuiConnectionError) as e:
            logger.warning(f"🔥 تست اتصال برای پنل {panel_id} ناموفق بود: {e} (Connection test failed for panel {panel_id}: {e})")
            # Update panel status to ERROR?
            # if panel.status == PanelStatus.ACTIVE:
            #     await self.update_panel_status(panel_id, PanelStatus.ERROR)
            #     logger.warning(f"وضعیت پنل {panel_id} به ERROR تغییر یافت به دلیل خطای اتصال/احراز هویت. (Panel {panel_id} status changed to ERROR due to connection/auth error.)")
            return False, f"خطای اتصال یا احراز هویت: {e} (Connection or Authentication Error: {e})"
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده حین تست اتصال برای پنل {panel_id}: {e} (Unexpected error testing connection for panel {panel_id}: {e})", exc_info=True)
            # Update panel status to ERROR?
            # if panel.status == PanelStatus.ACTIVE:
            #    await self.update_panel_status(panel_id, PanelStatus.ERROR)
            #    logger.warning(f"وضعیت پنل {panel_id} به ERROR تغییر یافت به دلیل خطای پیش‌بینی نشده. (Panel {panel_id} status changed to ERROR due to unexpected error.)")
            return False, f"خطای پیش‌بینی نشده: {e} (Unexpected Error: {e})"

    async def add_panel(self, name: str, location: str, flag_emoji: str,
                     url: str, username: str, password: str) -> Panel:
        """
        افزودن پنل جدید به سیستم پس از تست اتصال اولیه.

        Args:
            name: نام پنل.
            location: موقعیت جغرافیایی پنل (مثلاً Tehran).
            flag_emoji: ایموجی پرچم کشور مربوطه.
            url: آدرس کامل پنل XUI (همراه با http/https و پورت).
            username: نام کاربری پنل.
            password: رمز عبور پنل.

        Returns:
            شیء Panel ایجاد شده در دیتابیس.

        Raises:
            PanelConnectionError: در صورت عدم موفقیت در تست اتصال اولیه.
            ValueError: در صورت بروز خطا هنگام ذخیره در دیتابیس یا خطای غیرمنتظره دیگر.
            SQLAlchemyError: در صورت بروز خطای پایگاه داده.
        """
        logger.info(f"در حال تلاش برای افزودن پنل جدید: {name} در {location} ({url}) (Attempting to add new panel: {name} at {location} ({url}))")

        # 1. تست اتصال به پنل قبل از ایجاد
        try:
            await self._test_panel_connection_details(url=url, username=username, password=password)
            logger.info(f"تست اتصال اولیه موفق بود: {url} (Initial connection test successful for: {url})")
        except PanelConnectionError as e:
            logger.error(f"افزودن پنل {name} در {url} ناموفق بود. تست اتصال شکست خورد: {e} (Failed to add panel {name} at {url}. Connection test failed: {e})")
            raise e # Re-raise the specific connection error for the bot layer
        except Exception as e:
             logger.error(f"خطای پیش‌بینی نشده حین تست اتصال برای پنل {name} در {url}: {e} (Unexpected error during connection test for panel {name} at {url}: {e})", exc_info=True)
             # Raise a generic connection error for other unexpected issues
             raise PanelConnectionError(f"خطای پیش‌بینی نشده در زمان تست اتصال: {e} (Unexpected error during connection test: {e})") from e

        # 2. ایجاد پنل در دیتابیس
        panel_data = {
            "name": name,
            "location_name": location,
            "flag_emoji": flag_emoji,
            "url": url,
            "username": username,
            "password": password,
            "status": PanelStatus.ACTIVE, # پنل به صورت پیش‌فرض فعال است
            "type": PanelType.XUI      # نوع پنل فعلاً فقط XUI است
        }

        panel: Optional[Panel] = None # Initialize panel as None
        try:
            panel = await self.panel_repo.create_panel(panel_data)
            logger.info(f"✅ پنل '{panel.name}' (ID: {panel.id}) با موفقیت در دیتابیس ایجاد شد. (Panel '{panel.name}' (ID: {panel.id}) created successfully in DB.)")

            # 3. همگام‌سازی اولیه inbound‌ها
            logger.info(f"شروع همگام‌سازی اولیه inboundها برای پنل {panel.id}... (Starting initial inbound sync for panel {panel.id}...)")
            await self.sync_panel_inbounds(panel.id)
            logger.info(f"✅ همگام‌سازی اولیه inboundها برای پنل {panel.id} با موفقیت انجام شد. (Initial inbound sync completed for panel {panel.id}.)")

        except SQLAlchemyError as db_err:
            logger.error(f"خطای دیتابیس هنگام افزودن پنل {name} یا همگام‌سازی اولیه: {db_err} (Database error while adding panel {name} or initial syncing: {db_err})", exc_info=True)
            await self.session.rollback()
            raise ValueError(f"خطا در ذخیره اطلاعات پنل در دیتابیس: {db_err} (Error saving panel data to database: {db_err})") from db_err
        except PanelSyncError as sync_err:
             logger.error(f"🔥 پنل {panel.id} ({panel.name}) در دیتابیس ایجاد شد، اما همگام‌سازی اولیه inboundها ناموفق بود: {sync_err} (Panel {panel.id} ({panel.name}) created in DB, but initial inbound sync failed: {sync_err})", exc_info=True)
             # Panel exists in DB, but sync failed. Set status to ERROR.
             if panel: # Ensure panel object exists
                 panel.status = PanelStatus.ERROR
                 try:
                     # Commit status change directly via repository
                     await self.panel_repo.update_panel(panel.id, {"status": PanelStatus.ERROR})
                     logger.info(f"وضعیت پنل {panel.id} به ERROR تغییر یافت به دلیل خطای همگام‌سازی. (Set status of panel {panel.id} to ERROR due to sync failure.)")
                     await self.notification_service.notify_admins(
                         f"⚠️ پنل {panel.name} (ID: {panel.id}) ثبت شد، اما همگام‌سازی اولیه ناموفق بود: `{sync_err}` وضعیت به ERROR تغییر یافت."
                     )
                 except SQLAlchemyError as db_commit_err:
                     logger.error(f"خطا در ذخیره وضعیت ERROR برای پنل {panel.id} پس از خطای همگام‌سازی: {db_commit_err} (Failed to commit ERROR status for panel {panel.id} after sync failure: {db_commit_err})", exc_info=True)
                     await self.session.rollback() # Rollback if status update fails
             # Return the panel (with potentially ERROR status) so the caller knows it was created but failed sync
             return panel
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده پس از تست اتصال حین افزودن/همگام‌سازی پنل {panel.id if panel else 'N/A'}: {e} (Unexpected error after connection test during panel add/sync for panel {panel.id if panel else 'N/A'}: {e})", exc_info=True)
            await self.session.rollback()
            # If panel object exists and has an ID, try setting status to ERROR
            if panel and panel.id:
                try:
                    panel.status = PanelStatus.ERROR
                    await self.panel_repo.update_panel(panel.id, {"status": PanelStatus.ERROR})
                    logger.warning(f"وضعیت پنل {panel.id} به ERROR تغییر یافت به دلیل خطای غیرمنتظره. (Set status of panel {panel.id} to ERROR due to unexpected error.)")
                except Exception as commit_err:
                    logger.error(f"خطا در تنظیم وضعیت ERROR برای پنل {panel.id} پس از خطای غیرمنتظره: {commit_err} (Failed to set panel {panel.id} status to ERROR after unexpected error: {commit_err})")
                    await self.session.rollback() # Rollback if status update fails
            raise ValueError(f"خطای پیش‌بینی نشده در زمان ثبت پنل یا همگام‌سازی: {e} (Unexpected error during panel registration or sync: {e})") from e

        return panel

    async def get_panel_by_id(self, panel_id: int) -> Optional[Panel]:
        """
        دریافت اطلاعات یک پنل خاص با استفاده از شناسه آن.

        Args:
            panel_id: شناسه پنل.

        Returns:
            شیء Panel یا None اگر یافت نشد.
        """
        # logger.debug(f"دریافت پنل با ID: {panel_id} (Fetching panel with ID: {panel_id})")
        return await self.panel_repo.get_panel_by_id(panel_id)

    async def get_active_panels(self) -> List[Panel]:
        """دریافت تمام پنل‌های فعال از ریپازیتوری"""
        try:
            # Get panels using repository's enhanced get_active_panels method
            panels = await self.panel_repo.get_active_panels()
            
            # Ensure all returned panels have correct status
            for panel in panels:
                if isinstance(panel.status, str):
                    panel.status = PanelStatus.ACTIVE
            
            logger.info(f"دریافت {len(panels)} پنل فعال. (Retrieved {len(panels)} active panels.)")
            return panels
        except Exception as e:
            logger.error(f"خطا در دریافت پنل‌های فعال: {e}", exc_info=True)
            return []

    async def get_all_panels(self) -> List[Panel]:
        """
        دریافت لیست تمام پنل‌های ثبت شده در سیستم (صرف نظر از وضعیت).

        Returns:
            لیستی از تمام اشیاء Panel.
        """
        # logger.debug("دریافت تمام پنل‌ها... (Fetching all panels...)")
        return await self.panel_repo.get_all_panels()

    async def get_panel_by_location(self, location: str) -> Optional[Panel]:
        """
        دریافت پنل بر اساس نام موقعیت جغرافیایی آن (location_name).
        فقط اولین پنل منطبق را برمی‌گرداند.

        Args:
            location: نام موقعیت (مثلاً Tehran).

        Returns:
            شیء Panel یا None اگر یافت نشد.
        """
        # logger.debug(f"جستجوی پنل بر اساس موقعیت: {location} (Searching panel by location: {location})")
        return await self.panel_repo.get_panel_by_location(location)

    async def get_panel_by_address(self, address: str) -> Optional[Panel]:
        """
        دریافت پنل بر اساس آدرس URL آن.
        فقط اولین پنل منطبق را برمی‌گرداند.

        Args:
            address: آدرس URL پنل.

        Returns:
            شیء Panel یا None اگر یافت نشد.
        """
        # logger.debug(f"جستجوی پنل بر اساس آدرس: {address} (Searching panel by address: {address})")
        return await self.panel_repo.get_panel_by_address(address)

    async def get_suitable_panel_for_location(self, location_name: str) -> Optional[Panel]:
        """
        یافتن پنل مناسب برای یک لوکیشن خاص.
        
        Args:
            location_name: نام لوکیشن.
            
        Returns:
            شیء Panel مناسب یا None در صورت عدم وجود.
        """
        logger.debug(f"جستجوی پنل مناسب برای لوکیشن: {location_name}")
        panels = await self.panel_repo.filter_by(location_name=location_name, status=PanelStatus.ACTIVE)
        
        if not panels:
            logger.warning(f"هیچ پنل فعالی برای لوکیشن {location_name} یافت نشد.")
            return None
            
        # فعلاً اولین پنل فعال را انتخاب می‌کنیم
        # در آینده می‌توان الگوریتم‌های پیچیده‌تری برای توزیع بار اضافه کرد
        return panels[0]

    async def get_inbounds_by_panel_id(self, panel_id: int, status: Optional[InboundStatus] = None) -> List[Inbound]:
        """
        دریافت لیست inboundهای مرتبط با یک پنل خاص از دیتابیس.

        Args:
            panel_id: شناسه پنل.
            status (Optional[InboundStatus]): فیلتر بر اساس وضعیت inbound (اختیاری).

        Returns:
            لیستی از اشیاء Inbound.
        """
        # استفاده از inbound_repo به‌جای panel_repo برای عملیات inbound
        from db.repositories.inbound_repo import InboundRepository
        inbound_repo = InboundRepository(self.session)
        return await inbound_repo.get_by_panel_id(panel_id, status=status)

    async def _get_xui_client(self, panel: Panel) -> XuiClient:
        """
        [Helper خصوصی] دریافت یا ایجاد نمونه XuiClient برای یک پنل.
        از کش داخلی برای جلوگیری از ایجاد مکرر کلاینت استفاده می‌کند.
        همچنین وضعیت لاگین کلاینت کش شده را بررسی و در صورت نیاز لاگین مجدد انجام می‌دهد.

        Args:
            panel: شیء Panel که اطلاعات اتصال را دارد.

        Returns:
            نمونه XuiClient آماده به کار.

        Raises:
            ValueError: اگر اطلاعات اتصال پنل (url, username, password) ناقص باشد.
            PanelConnectionError: اگر لاگین مجدد ناموفق باشد.
        """
        if not panel.url or not panel.username or not panel.password:
            logger.error(f"امکان دریافت XUI client برای پنل ID {panel.id} وجود ندارد: اطلاعات اتصال ناقص است. (Cannot get XUI client for panel ID {panel.id}: Incomplete connection details.)")
            raise ValueError(f"اطلاعات اتصال پنل (ID: {panel.id}) ناقص است.")

        panel_id = panel.id
        client: Optional[XuiClient] = self._xui_clients.get(panel_id)

        if client:
            logger.debug(f"استفاده از XUI client موجود در کش برای پنل ID: {panel_id}. (Using cached XUI client for panel ID: {panel_id}.)")
            # بررسی وضعیت لاگین کلاینت کش شده
            if not client.is_logged_in():
                logger.info(f"کلاینت XUI کش شده برای پنل {panel_id} لاگین نیست یا سشن معتبر نیست، تلاش برای لاگین مجدد... (Cached XUI client for panel {panel_id} is not logged in or session invalid, attempting re-login...)")
                try:
                    await client.login()
                    logger.info(f"✅ لاگین مجدد برای کلاینت XUI کش شده پنل {panel_id} موفق بود. (Re-login successful for cached XUI client of panel {panel_id}.)")
                except (XuiAuthenticationError, XuiConnectionError) as e:
                    logger.warning(f"🔥 لاگین مجدد برای کلاینت XUI کش شده پنل {panel_id} ناموفق بود: {e}. (Re-login failed for cached XUI client of panel {panel_id}: {e}.)")
                    # حذف از کش برای ایجاد مجدد بعدی
                    if panel_id in self._xui_clients:
                        del self._xui_clients[panel_id] # حذف کلاینت مشکل‌دار از کش
                    raise PanelConnectionError(f"لاگین مجدد کلاینت کش شده برای پنل {panel_id} ناموفق بود: {e}") from e
                except Exception as e:
                    logger.error(f"خطای پیش‌بینی نشده هنگام لاگین مجدد کلاینت کش شده پنل {panel_id}: {e}. (Unexpected error during re-login for cached client of panel {panel_id}: {e}).", exc_info=True)
                    if panel_id in self._xui_clients:
                        del self._xui_clients[panel_id] # حذف کلاینت احتمالاً خراب
                    raise PanelConnectionError(f"خطای پیش‌بینی نشده در لاگین مجدد کلاینت پنل {panel_id}: {e}") from e
            else:
                logger.debug(f"کلاینت XUI کش شده برای پنل {panel_id} لاگین است و سشن معتبر فرض می‌شود. (Cached XUI client for panel {panel_id} is logged in and session assumed valid.)")
            return client
        else:
            logger.debug(f"ایجاد XUI client جدید برای پنل ID: {panel_id} در {panel.url}. (Creating new XUI client for panel ID: {panel_id} at {panel.url}.)")
            client = XuiClient(host=panel.url, username=panel.username, password=panel.password)
            # تلاش برای لاگین اولیه هنگام ایجاد قبل از ذخیره در کش
            try:
                logger.info(f"تلاش برای لاگین اولیه هنگام ایجاد کلاینت برای پنل {panel_id}... (Attempting initial login upon client creation for panel {panel_id}...) ")
                await client.login()
                logger.info(f"✅ لاگین اولیه برای کلاینت جدید پنل {panel_id} موفق بود. (Initial login successful for new client of panel {panel_id}.)")
                self._xui_clients[panel_id] = client # ذخیره در کش فقط پس از لاگین موفق
                return client
            except (XuiAuthenticationError, XuiConnectionError) as e:
                logger.error(f"🔥 لاگین اولیه هنگام ایجاد کلاینت برای پنل {panel_id} ناموفق بود: {e}. کلاینت کش نخواهد شد. (Initial login failed upon client creation for panel {panel_id}: {e}. Client will not be cached.)")
                # اگر لاگین اولیه ناموفق باشد کلاینت را کش نمی‌کنیم
                raise PanelConnectionError(f"ایجاد کلاینت برای پنل {panel_id} ناموفق بود (خطای لاگین اولیه): {e}") from e
            except Exception as e:
                logger.error(f"خطای پیش‌بینی نشده هنگام لاگین اولیه کلاینت جدید پنل {panel_id}: {e}. (Unexpected error during initial login for new client of panel {panel_id}: {e}).", exc_info=True)
                raise PanelConnectionError(f"ایجاد کلاینت برای پنل {panel_id} ناموفق بود (خطای پیش‌بینی نشده در لاگین): {e}") from e

    async def sync_panel_inbounds(self, panel_id: int) -> None:
        """
        همگام‌سازی inboundهای یک پنل خاص بین XUI و دیتابیس.
        Inboundهای جدید را اضافه، موجود را به‌روزرسانی و آنهایی که در XUI نیستند را غیرفعال می‌کند.

        Args:
            panel_id: شناسه پنل برای همگام‌سازی.

        Raises:
            PanelSyncError: در صورت بروز خطا حین دریافت اطلاعات از XUI یا ذخیره در دیتابیس.
            ValueError: اگر پنل یافت نشود.
        """
        logger.info(f"شروع همگام‌سازی inboundها برای پنل ID: {panel_id}... (Starting inbound sync for panel ID: {panel_id}...)")
        
        # دریافت اطلاعات پنل
        panel = await self.panel_repo.get_panel_by_id(panel_id)
        if not panel:
            logger.error(f"همگام‌سازی ناموفق: پنل با ID {panel_id} یافت نشد. (Sync failed: Panel with ID {panel_id} not found.)")
            raise ValueError(f"Panel with ID {panel_id} not found.")

        if panel.status != PanelStatus.ACTIVE:
             logger.warning(f"همگام‌سازی برای پنل {panel_id} انجام نشد زیرا وضعیت آن {panel.status.value} است. (Skipping sync for panel {panel_id} because its status is {panel.status.value}.)")
             return # پنل‌های غیرفعال یا دارای خطا همگام‌سازی نمی‌شوند

        try:
            # دریافت کلاینت XUI و اطمینان از لاگین بودن
            client = await self._get_xui_client(panel)
            
            # دریافت inboundها از پنل XUI
            logger.debug(f"در حال دریافت inboundها از پنل {panel_id}...")
            xui_inbounds_raw = await client.get_inbounds()
            
            if xui_inbounds_raw is None:
                 logger.warning(f"دریافت inboundها از XUI برای پنل {panel_id} نتیجه‌ای نداشت (None). همگام‌سازی متوقف شد. (Received None when fetching inbounds from XUI for panel {panel_id}. Stopping sync.)")
                 raise PanelSyncError("دریافت لیست inboundها از پنل XUI ناموفق بود (نتیجه None). (Failed to get inbound list from XUI panel (result was None).)")

            # تبدیل inboundهای دریافتی به دیکشنری
            xui_inbounds_list = [_to_dict_safe(ib) for ib in xui_inbounds_raw if ib is not None]
            logger.info(f"تعداد {len(xui_inbounds_list)} اینباند از پنل XUI {panel_id} دریافت شد. (Fetched {len(xui_inbounds_list)} inbounds from XUI panel {panel_id}.)")

            # دریافت inboundهای موجود در دیتابیس برای این پنل
            db_inbounds = await self.panel_repo.get_inbounds_by_panel_id(panel_id)
            db_inbounds_map = {ib.remote_id: ib for ib in db_inbounds}

            # آماده‌سازی داده‌ها برای عملیات ریپازیتوری
            inbounds_to_add = []
            inbounds_to_update = []
            active_xui_inbound_ids = set()

            for xui_ib_data in xui_inbounds_list:
                inbound_id = xui_ib_data.get('id')
                if not inbound_id:
                    logger.warning(f"رد شدن از inbound دریافتی از XUI برای پنل {panel_id} به دلیل نداشتن ID: {xui_ib_data} (Skipping inbound from XUI for panel {panel_id} due to missing ID: {xui_ib_data})")
                    continue

                active_xui_inbound_ids.add(inbound_id)
                remark = xui_ib_data.get('remark', f'Inbound {inbound_id}')
                
                # استخراج تنظیمات به صورت ایمن - مدیریت None یا JSON رشته‌ای
                settings_str = xui_ib_data.get('settings')
                settings_dict = {}
                if isinstance(settings_str, str):
                    try:
                        settings_dict = json.loads(settings_str)
                    except json.JSONDecodeError:
                        logger.warning(f"Parsing settings JSON failed for inbound {inbound_id} (Panel {panel_id}): {settings_str}. Storing raw string.", exc_info=True)
                        settings_dict = {"raw_settings": settings_str}
                elif isinstance(settings_str, dict):
                     settings_dict = settings_str

                # آماده‌سازی دیکشنری داده متناسب با مدل دیتابیس
                ib_data_for_db = {
                    'remote_id': inbound_id,
                    'panel_id': panel_id,
                    'tag': xui_ib_data.get('tag'),
                    'protocol': xui_ib_data.get('protocol'),
                    'port': xui_ib_data.get('port'),
                    'listen': xui_ib_data.get('listen'),
                    'settings_json': settings_dict,
                    'stream_settings': json.loads(xui_ib_data['streamSettings']) if isinstance(xui_ib_data.get('streamSettings'), str) else xui_ib_data.get('streamSettings', {}),
                    'sniffing': json.loads(xui_ib_data['sniffing']) if isinstance(xui_ib_data.get('sniffing'), str) else xui_ib_data.get('sniffing', {}),
                    'remark': remark,
                    'status': InboundStatus.ACTIVE if xui_ib_data.get('enable', False) else InboundStatus.DISABLED,
                    'last_synced': datetime.utcnow()
                }

                existing_db_inbound = db_inbounds_map.get(inbound_id)

                if existing_db_inbound:
                    # آماده‌سازی payload داده از XUI
                    update_payload = ib_data_for_db
                    # افزودن کلید اصلی دیتابیس مورد نیاز bulk_update_inbounds
                    update_payload['id'] = existing_db_inbound.id
                    inbounds_to_update.append(update_payload)
                else:
                    # نیازی به تکرار remote_id نیست چون قبلاً به دیکشنری اضافه شده
                    inbounds_to_add.append(ib_data_for_db)

            # شناسایی inboundهایی که باید غیرفعال شوند (در دیتابیس هستند اما در لیست XUI فعال نیستند)
            inbounds_to_deactivate_ids = []
            for db_inbound_id, db_inbound in db_inbounds_map.items():
                if db_inbound_id not in active_xui_inbound_ids and db_inbound.status != InboundStatus.INACTIVE:
                    inbounds_to_deactivate_ids.append(db_inbound_id)

            # انجام عملیات‌های دیتابیس از طریق ریپازیتوری
            from db.repositories.inbound_repo import InboundRepository
            inbound_repo = InboundRepository(self.session)
            
            # افزودن inboundهای جدید
            if inbounds_to_add:
                added_count = await inbound_repo.bulk_add_inbounds(inbounds_to_add)
                logger.info(f"{added_count} اینباند جدید برای پنل {panel_id} اضافه شد. (Added {added_count} new inbounds for panel {panel_id}.)")

            # به‌روزرسانی inboundهای موجود
            if inbounds_to_update:
                updated_count = await inbound_repo.bulk_update_inbounds(inbounds_to_update)
                logger.info(f"{updated_count} اینباند برای پنل {panel_id} به‌روز شد. (Updated {updated_count} inbounds for panel {panel_id}.)")

            # غیرفعال کردن inboundهایی که در XUI یافت نشدند
            if inbounds_to_deactivate_ids:
                deactivated_count = 0
                for remote_id_to_deactivate in inbounds_to_deactivate_ids:
                     success = await inbound_repo.update_inbound_status(remote_id_to_deactivate, panel_id, InboundStatus.INACTIVE)
                     if success:
                         deactivated_count += 1

                logger.info(f"{deactivated_count} اینباند که در XUI یافت نشدند، برای پنل {panel_id} غیرفعال شدند. (Deactivated {deactivated_count} inbounds not found in XUI for panel {panel_id}.)")

            # نیاز به commit نیست، commit در لایه بالاتر انجام می‌شود
            await self.session.flush()  # فقط برای اطمینان از اعمال تغییرات در session
            logger.info(f"✅ همگام‌سازی inboundها برای پنل {panel_id} با موفقیت تکمیل شد. (Inbound sync completed successfully for panel {panel_id}.)")

        except (XuiAuthenticationError, XuiConnectionError) as conn_err:
            logger.error(f"خطای اتصال یا احراز هویت حین همگام‌سازی پنل {panel_id}: {conn_err} (Connection or Authentication error during sync for panel {panel_id}: {conn_err})", exc_info=True)
            raise PanelSyncError(f"خطای اتصال/احراز هویت در زمان همگام‌سازی: {conn_err} (Connection/Authentication error during sync: {conn_err})") from conn_err
        except SQLAlchemyError as db_err:
            logger.error(f"خطای دیتابیس حین همگام‌سازی پنل {panel_id}: {db_err} (Database error during sync for panel {panel_id}: {db_err})", exc_info=True)
            await self.session.rollback()
            raise PanelSyncError(f"خطای دیتابیس در زمان همگام‌سازی: {db_err} (Database error during sync: {db_err})") from db_err
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده حین همگام‌سازی پنل {panel_id}: {e} (Unexpected error during sync for panel {panel_id}: {e})", exc_info=True)
            await self.session.rollback()
            raise PanelSyncError(f"خطای پیش‌بینی نشده در زمان همگام‌سازی: {e} (Unexpected error during sync: {e})") from e

    async def sync_all_panels_inbounds(self) -> Dict[int, List[str]]:
        """
        همگام‌سازی inboundها برای تمام پنل‌های فعال (ACTIVE) در سیستم.

        Returns:
            Dict[int, List[str]]: دیکشنری شامل نتایج همگام‌سازی برای هر پنل.
                                  کلید: ID پنل.
                                  مقدار: لیستی از پیام‌های وضعیت یا خطا.
                                  مثال: { 1: ["Sync successful"], 2: ["Sync failed: Connection error"] }
        """
        logger.info("شروع همگام‌سازی inboundها برای تمام پنل‌های فعال... (Starting inbound sync for all active panels...)")
        active_panels = await self.get_active_panels()
        results: Dict[int, List[str]] = {}

        if not active_panels:
            logger.info("هیچ پنل فعالی برای همگام‌سازی یافت نشد. (No active panels found to sync.)")
            return results

        for panel in active_panels:
            panel_id = panel.id
            panel_name = panel.name
            logger.info(f"شروع همگام‌سازی برای پنل: {panel_name} (ID: {panel_id})... (Starting sync for panel: {panel_name} (ID: {panel_id})...)")
            try:
                # اطمینان از دریافت کلاینت XUI و لاگین بودن آن
                try:
                    client = await self._get_xui_client(panel)
                    # بررسی وضعیت لاگین
                    if not client.is_logged_in():
                        logger.info(f"لاگین به پنل {panel_name} (ID: {panel_id}) قبل از همگام‌سازی...")
                        await client.login()
                        logger.info(f"لاگین به پنل {panel_name} (ID: {panel_id}) موفق بود.")
                    else:
                        logger.debug(f"کلاینت برای پنل {panel_name} (ID: {panel_id}) قبلاً لاگین است.")
                except (XuiAuthenticationError, XuiConnectionError) as login_err:
                    logger.error(f"خطای لاگین به پنل {panel_name} (ID: {panel_id}) قبل از همگام‌سازی: {login_err}")
                    results[panel_id] = [f"🔥 همگام‌سازی ناموفق: خطای لاگین: {login_err} (Sync failed: Login error: {login_err})"]
                    continue

                # انجام همگام‌سازی
                await self.sync_panel_inbounds(panel_id)
                results[panel_id] = ["✅ همگام‌سازی موفق بود. (Sync successful.)"]
                logger.info(f"✅ همگام‌سازی برای پنل {panel_name} (ID: {panel_id}) موفق بود. (Sync successful for panel {panel_name} (ID: {panel_id}).)")
            except (PanelSyncError, ValueError) as e:
                # لاگ قبلاً در sync_panel_inbounds یا get_panel_by_id ثبت شده است
                logger.error(f"🔥 همگام‌سازی برای پنل {panel_name} (ID: {panel_id}) ناموفق بود: {e} (Sync failed for panel {panel_name} (ID: {panel_id}): {e})")
                results[panel_id] = [f"🔥 همگام‌سازی ناموفق: {e} (Sync failed: {e})"]
            except Exception as e:
                 logger.error(f"🔥 خطای پیش‌بینی نشده حین همگام‌سازی پنل {panel_name} (ID: {panel_id}): {e} (Unexpected error syncing panel {panel_name} (ID: {panel_id}): {e})", exc_info=True)
                 results[panel_id] = [f"🔥 خطای پیش‌بینی نشده: {e} (Unexpected error: {e})"]

        # نیازی به commit نیست زیرا در سطح بالاتر انجام می‌شود
        await self.session.flush()
        logger.info("همگام‌سازی تمام پنل‌های فعال به پایان رسید. (Finished syncing all active panels.)")
        return results

    async def update_panel_status(self, panel_id: int, status: PanelStatus) -> bool:
        """
        به‌روزرسانی وضعیت یک پنل خاص.

        Args:
            panel_id: شناسه پنل.
            status: وضعیت جدید (از نوع PanelStatus).

        Returns:
            True اگر وضعیت با موفقیت به‌روز شد، False اگر پنل یافت نشد.

        Raises:
            SQLAlchemyError: در صورت بروز خطای دیتابیس.
        """
        logger.info(f"در حال تلاش برای به‌روزرسانی وضعیت پنل ID: {panel_id} به {status.value} (Attempting to update status for panel ID: {panel_id} to {status.value})")
        try:
            updated_panel = await self.panel_repo.update_panel(panel_id, {"status": status})
            if updated_panel:
                logger.info(f"✅ وضعیت پنل {panel_id} با موفقیت به {status.value} تغییر یافت. (Panel {panel_id} status updated successfully to {status.value}.)")
                # Invalidate cache if panel becomes inactive
                if status == PanelStatus.INACTIVE and panel_id in self._xui_clients:
                     del self._xui_clients[panel_id]
                     logger.info(f"کلاینت XUI کش شده برای پنل غیرفعال {panel_id} حذف شد. (Removed cached XUI client for inactive panel {panel_id}.)")
                return True
            else:
                logger.warning(f"به‌روزرسانی وضعیت ناموفق: پنل با ID {panel_id} یافت نشد. (Status update failed: Panel with ID {panel_id} not found.)")
                return False
        except SQLAlchemyError as e:
            logger.error(f"خطای دیتابیس حین به‌روزرسانی وضعیت پنل {panel_id}: {e} (Database error updating panel {panel_id} status: {e})", exc_info=True)
            await self.session.rollback()
            raise e
