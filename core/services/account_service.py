"""
سرویس مدیریت اکانت‌های VPN (ClientAccount) در دیتابیس و پنل‌ها.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from core.services.client_service import ClientService
from core.services.panel_service import PanelService
from db.repositories.account_repo import AccountRepository
from db.models.client_account import AccountStatus, ClientAccount
from db.models import Panel, Inbound, Plan, User

logger = logging.getLogger(__name__)


class AccountService:
    """
    سرویس مدیریت اکانت‌های VPN کاربران در دیتابیس و هماهنگی با پنل‌ها از طریق سرویس‌های دیگر.
    """
    
    def __init__(self, session: AsyncSession, client_service: ClientService, panel_service: PanelService):
        """
        مقداردهی اولیه سرویس با دسترسی به دیتابیس و سرویس‌های وابسته.

        Args:
            session: نشست دیتابیس AsyncSession.
            client_service: سرویس مدیریت کلاینت‌ها (برای تعامل با پنل).
            panel_service: سرویس مدیریت پنل‌ها (برای دریافت اطلاعات پنل و کلاینت XUI).
        """
        self.session = session
        self.client_service = client_service
        self.panel_service = panel_service
        self.account_repo = AccountRepository(session)
    
    def _generate_transfer_id(self, user_id: int) -> str:
        """
        ایجاد شناسه انتقال (transfer_id) برای اکانت‌های کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            شناسه منحصر به فرد انتقال.
        """
        return f"moonvpn-{user_id:03d}"
    
    def _create_label(self, panel_flag_emoji: str, panel_default_label: str, user_id: int) -> str:
        """
        ایجاد برچسب (label/remark) اکانت با فرمت استاندارد.

        Args:
            panel_flag_emoji: اموجی پرچم پنل.
            panel_default_label: برچسب پیش‌فرض پنل.
            user_id: شناسه کاربر.

        Returns:
            برچسب اکانت.
        """
        # Ensure parts exist before joining
        parts = [part for part in [panel_flag_emoji, panel_default_label, f"{user_id:03d}"] if part]
        return "-".join(parts)
    
    async def provision_account(
        self,
        user_id: int,
        plan: Plan,
        inbound: Inbound,
        panel: Panel,
        order_id: Optional[int] = None
    ) -> Optional[ClientAccount]:
        """
        ایجاد اکانت VPN جدید برای کاربر در دیتابیس و پنل XUI.

        این متد ابتدا کلاینت را در پنل XUI از طریق ClientService ایجاد می‌کند،
        سپس اطلاعات آن را به همراه URL کانفیگ دریافت کرده و در نهایت
        رکورد ClientAccount را در دیتابیس ایجاد می‌کند.

        Args:
            user_id: شناسه کاربر.
            plan: شیء پلن انتخابی.
            inbound: شیء Inbound انتخابی.
            panel: شیء پنل مرتبط با Inbound.
            order_id: شناسه سفارش (اختیاری).

        Returns:
            شیء ClientAccount ایجاد شده یا None در صورت خطا.

        Raises:
            ValueError: اگر داده‌های ورودی نامعتبر باشند.
            ClientCreationFailedError: اگر ایجاد کلاینت در پنل یا دیتابیس با خطا مواجه شود.
            SQLAlchemyError: در صورت بروز خطای پایگاه داده.
        """
        log_prefix = f"[User ID: {user_id}, Plan ID: {plan.id}, Inbound ID: {inbound.id}]"
        logger.info(f"{log_prefix} Starting account provisioning. | شروع فرآیند ایجاد اکانت.")

        created_client_uuid_on_panel: Optional[str] = None # برای rollback احتمالی پنل

        try:
            # 1. محاسبه تاریخ انقضا و حجم ترافیک
            expires_at = datetime.utcnow() + timedelta(days=plan.duration_days)
            traffic_total_bytes = plan.traffic_gb * (1024**3) # تبدیل GB به بایت
            logger.debug(f"{log_prefix} Calculated expiry: {expires_at}, traffic: {plan.traffic_gb} GB. | محاسبه تاریخ انقضا و ترافیک.")

            # 2. تولید مشخصات کلاینت (UUID, label, email, transfer_id)
            client_uuid = str(uuid.uuid4())
            label = self._create_label(panel.flag_emoji, panel.default_label, user_id)
            email = f"{label}@{panel.name}" # Example email format
            transfer_id = self._generate_transfer_id(user_id)

            logger.debug(f"{log_prefix} Generated client details: UUID={client_uuid}, Label={label}, Email={email}. | تولید مشخصات کلاینت.")

            # 3. آماده‌سازی داده‌های کلاینت برای پنل
            expire_timestamp_ms = int(datetime.timestamp(expires_at)) * 1000
            client_data_for_panel = {
                "id": client_uuid,
                "email": email, # Use generated email
                "remark": label, # Use label as remark
                "enable": True,
                "total_gb": plan.traffic_gb, # XUI client likely expects GB directly here, confirm ClientService logic
                "expiry_time": expire_timestamp_ms,
                "flow": plan.flow or "",
                "limit_ip": plan.ip_limit or 1,
                "sub_id": transfer_id
            }
            logger.debug(f"{log_prefix} Prepared client data for panel API: {client_data_for_panel}. | آماده‌سازی داده برای API پنل.")

            # 4. دریافت کلاینت XUI از PanelService
            # این کار حالا داخل ClientService انجام می‌شود.
            # panel_xui_client = await self.panel_service._get_xui_client(panel) # Private method call not ideal

            # 5. ایجاد کلاینت در پنل از طریق ClientService
            logger.info(f"{log_prefix} Calling ClientService to create client on panel {panel.id}. | فراخوانی ClientService برای ایجاد کلاینت در پنل.")
            
            panel_response = await self.client_service._create_client_on_panel(
                panel=panel,
                inbound_id=inbound.remote_id,
                client_data=client_data_for_panel
            )
            created_client_uuid_on_panel = client_uuid # Set for potential rollback
            logger.info(f"{log_prefix} Client successfully created on panel via ClientService. Response: {panel_response}. | کلاینت با موفقیت در پنل ایجاد شد.")

            # 6. دریافت URL کانفیگ از طریق ClientService
            logger.info(f"{log_prefix} Calling ClientService to get config URL for UUID {client_uuid}. | فراخوانی ClientService برای دریافت URL کانفیگ.")
            
            config_url = await self.client_service._generate_config_url(
                panel=panel, 
                inbound=inbound, 
                client_uuid=client_uuid, 
                client_email=email
            )
            logger.info(f"{log_prefix} Config URL received: {config_url}. | URL کانفیگ دریافت شد.")

            # 7. ایجاد رکورد ClientAccount در دیتابیس
            account_data = {
                "user_id": user_id,
                "order_id": order_id,
                "panel_id": panel.id,
                "inbound_id": inbound.id, # Our DB inbound ID
                "plan_id": plan.id,
                "remote_uuid": client_uuid,
                "client_name": label,
                "email_name": email,
                "expires_at": expires_at,
                "expiry_time": expire_timestamp_ms,
                "traffic_limit": plan.traffic_gb,
                "data_limit": traffic_total_bytes,
                "traffic_used": 0,
                "data_used": 0,
                "status": AccountStatus.ACTIVE,
                "enable": True,
                "config_url": config_url,
                "ip_limit": plan.ip_limit or 1, # Use the value from plan
                "created_at": datetime.utcnow() # Ensure UTC time
            }
            logger.debug(f"{log_prefix} Prepared ClientAccount data for DB: {account_data}. | آماده‌سازی داده ClientAccount برای دیتابیس.")

            client_account = await self.account_repo.create(account_data)
            if not client_account: # Should not happen if create doesn't raise error
                 logger.error(f"{log_prefix} Failed to create ClientAccount in DB after panel creation. Rolling back panel. | عدم موفقیت در ایجاد رکورد دیتابیس پس از ایجاد در پنل.")
                 raise ValueError("ایجاد رکورد اکانت در دیتابیس ناموفق بود.") # Generic error

            # 8. Flush کردن تغییرات دیتابیس (بدون commit)
            await self.session.flush([client_account]) # Flush only this object
            logger.info(f"{log_prefix} ClientAccount flushed to DB. Account ID: {client_account.id}. | رکورد ClientAccount در دیتابیس Flush شد.")

            # Refresh to get potentially updated state (like ID)
            await self.session.refresh(client_account)

            logger.info(f"{log_prefix} Account provisioning successful. Account ID: {client_account.id}. | ایجاد اکانت با موفقیت انجام شد.")
            return client_account

        except (SQLAlchemyError, ValueError) as db_err:
            logger.error(f"{log_prefix} Database or Value error during account provisioning: {db_err}. Rolling back session. | خطای دیتابیس یا مقدار ورودی در ایجاد اکانت.", exc_info=True)
            await self.session.rollback()
            logger.info(f"{log_prefix} Session rolled back due to DB/Value error. | نشست به دلیل خطا بازگردانی شد.")
            # اگر کلاینت روی پنل ایجاد شده بود، آن را حذف کن
            if created_client_uuid_on_panel:
                logger.warning(f"{log_prefix} Attempting to roll back panel client creation for UUID {created_client_uuid_on_panel}. | تلاش برای بازگردانی ایجاد کلاینت در پنل.")
                await self.client_service._rollback_panel_creation(panel, created_client_uuid_on_panel, log_prefix)
            raise # Re-raise the caught exception

        except Exception as e: # Catch potential errors from ClientService calls or others
            logger.error(f"{log_prefix} Unexpected error during account provisioning: {e}. Rolling back session. | خطای پیش‌بینی نشده در ایجاد اکانت.", exc_info=True)
            await self.session.rollback()
            logger.info(f"{log_prefix} Session rolled back due to unexpected error. | نشست به دلیل خطای پیش‌بینی نشده بازگردانی شد.")
            # اگر کلاینت روی پنل ایجاد شده بود، آن را حذف کن
            if created_client_uuid_on_panel:
                logger.warning(f"{log_prefix} Attempting to roll back panel client creation for UUID {created_client_uuid_on_panel}. | تلاش برای بازگردانی ایجاد کلاینت در پنل.")
                await self.client_service._rollback_panel_creation(panel, created_client_uuid_on_panel, log_prefix)
            # Wrap unexpected errors for clarity
            raise ValueError(f"خطای پیش‌بینی نشده در ایجاد اکانت: {e}") from e

    async def get_account_by_id(self, account_id: int) -> Optional[ClientAccount]:
        """
        دریافت اطلاعات یک اکانت خاص با شناسه آن.

        Args:
            account_id: شناسه اکانت.

        Returns:
            شیء ClientAccount یا None اگر یافت نشد.
        """
        logger.info(f"Fetching account by ID: {account_id}. | دریافت اکانت با شناسه.")
        try:
            account = await self.account_repo.get_by_id(account_id)
            if account:
                logger.debug(f"Account found: ID={account_id}, UUID={account.uuid}. | اکانت یافت شد.")
            else:
                logger.warning(f"Account with ID {account_id} not found. | اکانت یافت نشد.")
            return account
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching account ID {account_id}: {e}. | خطای دیتابیس در دریافت اکانت.", exc_info=True)
            return None # Or re-raise depending on desired behavior

    async def get_account_by_uuid(self, client_uuid: str) -> Optional[ClientAccount]:
        """
        دریافت اطلاعات یک اکانت خاص با UUID کلاینت پنل آن.

        Args:
            client_uuid: شناسه UUID کلاینت در پنل.

        Returns:
            شیء ClientAccount یا None اگر یافت نشد.
        """
        logger.info(f"Fetching account by UUID: {client_uuid}. | دریافت اکانت با UUID.")
        try:
            account = await self.account_repo.get_by_uuid(client_uuid)
            if account:
                 logger.debug(f"Account found for UUID {client_uuid}: ID={account.id}. | اکانت برای UUID یافت شد.")
            else:
                logger.warning(f"Account with UUID {client_uuid} not found. | اکانت یافت نشد.")
            return account
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching account UUID {client_uuid}: {e}. | خطای دیتابیس در دریافت اکانت.", exc_info=True)
            return None # Or re-raise

    async def get_active_accounts_by_user(self, user_id: int) -> List[ClientAccount]:
        """
        دریافت لیست تمام اکانت‌های فعال یک کاربر.

        Args:
            user_id: شناسه کاربر.

        Returns:
            لیستی از اشیاء ClientAccount فعال.
        """
        logger.info(f"Fetching active accounts for user ID: {user_id}. | دریافت اکانت‌های فعال کاربر.")
        try:
            accounts = await self.account_repo.get_active_by_user_id(user_id)
            logger.debug(f"Found {len(accounts)} active accounts for user {user_id}. | {len(accounts)} اکانت فعال یافت شد.")
            return accounts
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching active accounts for user {user_id}: {e}. | خطای دیتابیس در دریافت اکانت‌های فعال.", exc_info=True)
            return [] # Return empty list on error

    async def renew_account(self, account_id: int, plan: Plan) -> Optional[ClientAccount]:
        """
        تمدید یک اکانت موجود بر اساس پلن جدید.

        این متد ابتدا کلاینت را در پنل از طریق ClientService آپدیت می‌کند (تاریخ انقضا، ترافیک و غیره)
        و سپس رکورد ClientAccount را در دیتابیس با اطلاعات جدید به‌روزرسانی می‌کند.

        Args:
            account_id: شناسه اکانت برای تمدید.
            plan: شیء پلن جدید برای تمدید.

        Returns:
            شیء ClientAccount به‌روز شده یا None در صورت خطا.

        Raises:
            ValueError: اگر اکانت یافت نشد یا خطای دیگری رخ دهد.
            ClientUpdateFailedError: اگر آپدیت کلاینت در پنل یا دیتابیس با خطا مواجه شود.
            SQLAlchemyError: در صورت بروز خطای پایگاه داده.
        """
        log_prefix = f"[Account ID: {account_id}, New Plan ID: {plan.id}]"
        logger.info(f"{log_prefix} Starting account renewal process. | شروع فرآیند تمدید اکانت.")

        account = await self.get_account_by_id(account_id)
        if not account:
            logger.warning(f"{log_prefix} Account not found for renewal. | اکانت برای تمدید یافت نشد.")
            raise ValueError(f"اکانت با شناسه {account_id} یافت نشد.")

        try:
            # 1. محاسبه مقادیر جدید (تاریخ انقضا، ترافیک)
            # تمدید: اضافه کردن مدت زمان پلن به تاریخ انقضای *فعلی* یا از *حالا* اگر منقضی شده
            current_expiry = account.expires_at or datetime.utcnow() # Use current time if no expiry set
            base_expiry = max(current_expiry, datetime.utcnow()) # Start from now if already expired
            new_expires_at = base_expiry + timedelta(days=plan.duration_days)
            # تمدید: اضافه کردن ترافیک پلن به ترافیک *باقی‌مانده* (اگر منطق این باشد) یا جایگزینی کامل
            # فرض: ترافیک جدید به ترافیک *کل* قبلی اضافه می‌شود (نه مصرف شده) - این نیاز به شفاف‌سازی دارد
            # یا شاید پلن جدید ترافیک کل جدیدی تعریف می‌کند؟ فرض می‌کنیم ترافیک کل جدید تنظیم می‌شود.
            new_traffic_total_gb = plan.traffic_gb
            new_traffic_total_bytes = new_traffic_total_gb * (1024**3)

            logger.debug(f"{log_prefix} Calculated new expiry: {new_expires_at}, new total traffic: {new_traffic_total_gb} GB. | محاسبه مقادیر جدید برای تمدید.")

            # 2. آماده‌سازی داده‌های آپدیت برای پنل
            new_expire_timestamp_ms = int(datetime.timestamp(new_expires_at)) * 1000
            client_update_data_for_panel = {
                "id": account.remote_uuid, # UUID不变
                "email": account.email_name,
                "remark": account.client_name,
                "enable": True, # Ensure it's enabled on renewal
                "totalGB": new_traffic_total_gb * (1024**3), # Update total traffic in bytes (Confirm if API expects bytes or GB)
                "expiryTime": new_expire_timestamp_ms, # Update expiry time
                "flow": plan.flow or "", # Update flow if needed
                "limitIP": plan.ip_limit or 1 # Update IP limit if needed
            }
            logger.debug(f"{log_prefix} Prepared client update data for panel API: {client_update_data_for_panel}. | آماده‌سازی داده آپدیت برای API پنل.")

            # 3. آپدیت کلاینت در پنل از طریق ClientService
            # ** فرض: ClientService متد _update_client_on_panel یا مشابه دارد **
            logger.info(f"{log_prefix} Calling ClientService to update client on panel {account.panel_id}. | فراخوانی ClientService برای آپدیت کلاینت در پنل.")
            # === نیازمند متد در ClientService ===
            panel_update_success = await self.client_service._update_client_on_panel(
                panel_id=account.panel_id,
                client_uuid=account.uuid,
                inbound_id=account.inbound.inbound_id, # Need panel's inbound ID
                client_settings=client_update_data_for_panel,
                log_prefix=log_prefix
            )
            if not panel_update_success:
                 # ClientService method should raise error on failure ideally
                 logger.error(f"{log_prefix} ClientService failed to update client on panel. | ClientService در آپدیت کلاینت پنل ناموفق بود.")
                 raise ValueError("به‌روزرسانی کلاینت در پنل ناموفق بود.") # Or specific error from ClientService
            logger.info(f"{log_prefix} Client successfully updated on panel via ClientService. | کلاینت با موفقیت در پنل آپدیت شد.")
            # =====================================

            # 4. آپدیت رکورد ClientAccount در دیتابیس
            update_data = {
                "plan_id": plan.id,
                "expires_at": new_expires_at,
                "expiry_time": new_expire_timestamp_ms,
                "traffic_limit": new_traffic_total_gb,
                "data_limit": new_traffic_total_bytes,
                "status": AccountStatus.ACTIVE, # Ensure status is active after renewal
                "enable": True, # Ensure it's enabled in DB
                "updated_at": datetime.utcnow()
            }
            # Preserve existing fields not included in update_data
            updated_account = await self.account_repo.update(account_id, update_data)

            if not updated_account:
                 # Should not happen if update doesn't raise error and account exists
                 logger.error(f"{log_prefix} Failed to update ClientAccount in DB after panel update. This should not happen. | عدم موفقیت در آپدیت رکورد دیتابیس پس از آپدیت پنل.")
                 # Consider how to handle this inconsistency. Manual intervention might be needed.
                 raise ValueError("آپدیت رکورد اکانت در دیتابیس ناموفق بود.")

            # 5. Flush کردن تغییرات دیتابیس
            await self.session.flush([updated_account])
            logger.info(f"{log_prefix} ClientAccount DB record updated and flushed. | رکورد دیتابیس آپدیت و Flush شد.")

            # Refresh to get updated state
            await self.session.refresh(updated_account)

            logger.info(f"{log_prefix} Account renewal successful. Account ID: {account_id}. | تمدید اکانت با موفقیت انجام شد.")
            return updated_account

        except (SQLAlchemyError, ValueError) as db_err:
            logger.error(f"{log_prefix} Database or Value error during account renewal: {db_err}. Rolling back session. | خطای دیتابیس یا مقدار ورودی در تمدید اکانت.", exc_info=True)
            await self.session.rollback()
            logger.info(f"{log_prefix} Session rolled back due to DB/Value error. | نشست به دلیل خطا بازگردانی شد.")
            # Panel update might have succeeded. This state needs monitoring/reconciliation.
            raise # Re-raise the caught exception

        except Exception as e: # Catch potential errors from ClientService calls or others
            logger.error(f"{log_prefix} Unexpected error during account renewal: {e}. Rolling back session. | خطای پیش‌بینی نشده در تمدید اکانت.", exc_info=True)
            await self.session.rollback()
            logger.info(f"{log_prefix} Session rolled back due to unexpected error. | نشست به دلیل خطای پیش‌بینی نشده بازگردانی شد.")
            # Panel update might have succeeded.
            raise ValueError(f"خطای پیش‌بینی نشده در تمدید اکانت: {e}") from e

    async def deactivate_account(self, account_id: int) -> Optional[ClientAccount]:
        """
        غیرفعال کردن یک اکانت (در پنل و دیتابیس).

        Args:
            account_id: شناسه اکانت برای غیرفعال کردن.

        Returns:
            شیء ClientAccount به‌روز شده یا None در صورت خطا.

        Raises:
            ValueError: اگر اکانت یافت نشد یا خطای دیگری رخ دهد.
            ClientUpdateFailedError: اگر غیرفعال‌سازی کلاینت در پنل یا دیتابیس با خطا مواجه شود.
            SQLAlchemyError: در صورت بروز خطای پایگاه داده.
        """
        log_prefix = f"[Account ID: {account_id}]"
        logger.info(f"{log_prefix} Starting account deactivation process. | شروع فرآیند غیرفعال‌سازی اکانت.")

        account = await self.get_account_by_id(account_id)
        if not account:
            logger.warning(f"{log_prefix} Account not found for deactivation. | اکانت برای غیرفعال‌سازی یافت نشد.")
            raise ValueError(f"اکانت با شناسه {account_id} یافت نشد.")

        if account.status == AccountStatus.INACTIVE:
             logger.info(f"{log_prefix} Account is already inactive. No action needed. | اکانت از قبل غیرفعال است.")
             return account

        try:
            # 1. غیرفعال کردن کلاینت در پنل از طریق ClientService
            # ** فرض: ClientService متد _disable_client_on_panel یا مشابه دارد **
            logger.info(f"{log_prefix} Calling ClientService to disable client on panel {account.panel_id}. | فراخوانی ClientService برای غیرفعال کردن کلاینت در پنل.")
            # === نیازمند متد در ClientService ===
            panel_disable_success = await self.client_service._disable_client_on_panel(
                panel_id=account.panel_id,
                client_uuid=account.uuid,
                inbound_id=account.inbound.inbound_id, # Need panel's inbound ID
                log_prefix=log_prefix
            )
            if not panel_disable_success:
                logger.error(f"{log_prefix} ClientService failed to disable client on panel. | ClientService در غیرفعال کردن کلاینت پنل ناموفق بود.")
                raise ValueError("غیرفعال کردن کلاینت در پنل ناموفق بود.") # Or specific error
            logger.info(f"{log_prefix} Client successfully disabled on panel via ClientService. | کلاینت با موفقیت در پنل غیرفعال شد.")
            # =====================================

            # 2. آپدیت وضعیت اکانت در دیتابیس
            update_data = {
                "status": AccountStatus.INACTIVE,
                "enable": False,
                "updated_at": datetime.utcnow()
            }
            # Preserve existing fields not included in update_data
            updated_account = await self.account_repo.update(account_id, update_data)
            if not updated_account:
                 # Should not happen if update doesn't raise error and account exists
                 logger.error(f"{log_prefix} Failed to update ClientAccount status in DB. This should not happen. | عدم موفقیت در آپدیت وضعیت اکانت در دیتابیس.")
                 raise ValueError("آپدیت وضعیت اکانت در دیتابیس ناموفق بود.")

            # 3. Flush کردن تغییرات دیتابیس
            await self.session.flush([updated_account])
            logger.info(f"{log_prefix} ClientAccount status updated and flushed. | وضعیت اکانت آپدیت و Flush شد.")

            # Refresh to get updated state
            await self.session.refresh(updated_account)

            logger.info(f"{log_prefix} Account deactivation successful. Account ID: {account_id}. | غیرفعال‌سازی اکانت با موفقیت انجام شد.")
            return updated_account

        except (SQLAlchemyError, ValueError) as db_err:
            logger.error(f"{log_prefix} Database or Value error during account deactivation: {db_err}. Rolling back session. | خطای دیتابیس یا مقدار ورودی در غیرفعال‌سازی اکانت.", exc_info=True)
            await self.session.rollback()
            logger.info(f"{log_prefix} Session rolled back due to DB/Value error. | نشست به دلیل خطا بازگردانی شد.")
            # Panel update might have succeeded.
            raise # Re-raise the caught exception

        except Exception as e: # Catch potential errors from ClientService calls or others
            logger.error(f"{log_prefix} Unexpected error during account deactivation: {e}. Rolling back session. | خطای پیش‌بینی نشده در غیرفعال‌سازی اکانت.", exc_info=True)
            await self.session.rollback()
            logger.info(f"{log_prefix} Session rolled back due to unexpected error. | نشست به دلیل خطای پیش‌بینی نشده بازگردانی شد.")
            # Panel update might have succeeded.
            raise ValueError(f"خطای پیش‌بینی نشده در غیرفعال‌سازی اکانت: {e}") from e

    async def delete_account(self, account_id: int) -> bool:
        """
        حذف کامل اکانت VPN (از پنل و دیتابیس).

        ابتدا سعی در حذف کلاینت از پنل از طریق ClientService می‌کند (best-effort).
        سپس رکورد ClientAccount را از دیتابیس حذف می‌کند.

        Args:
            account_id: شناسه اکانت برای حذف.

        Returns:
            True اگر حذف از دیتابیس موفق بود، False در غیر این صورت.
            (موفقیت حذف از پنل تضمین نمی‌شود).

        Raises:
            SQLAlchemyError: در صورت بروز خطای پایگاه داده حین حذف.
        """
        log_prefix = f"[Account ID: {account_id}]"
        logger.info(f"{log_prefix} Starting account deletion process. | شروع فرآیند حذف اکانت.")

        # 1. دریافت اطلاعات اکانت (شامل panel_id و uuid)
        account = await self.account_repo.get_by_id(account_id) # Fetch before delete
        if not account:
            logger.warning(f"{log_prefix} Account not found for deletion. | اکانت برای حذف یافت نشد.")
            return False # Account doesn't exist, deletion considered "successful" in a way

        panel_id_for_delete = account.panel_id
        client_uuid_for_delete = account.uuid
        inbound_id_for_delete = account.inbound.inbound_id if account.inbound else None # Handle case where inbound might be missing

        # 2. تلاش برای حذف کلاینت از پنل از طریق ClientService (Best-effort)
        panel_delete_success = False
        if panel_id_for_delete and client_uuid_for_delete:
            try:
                logger.info(f"{log_prefix} Calling ClientService to delete client UUID {client_uuid_for_delete} from panel {panel_id_for_delete}. | فراخوانی ClientService برای حذف کلاینت از پنل.")
                
                # Get panel object
                panel = await self.panel_service.get_panel_by_id(panel_id_for_delete)
                if panel:
                    panel_delete_success = await self.client_service._delete_client_on_panel(
                        panel=panel,
                        client_uuid=client_uuid_for_delete
                    )
                    if panel_delete_success:
                        logger.info(f"{log_prefix} Client successfully deleted from panel via ClientService. | کلاینت با موفقیت از پنل حذف شد.")
                    else:
                        logger.warning(f"{log_prefix} ClientService reported client UUID {client_uuid_for_delete} not found or deletion failed on panel {panel_id_for_delete}. Proceeding with DB deletion. | حذف کلاینت از پنل ناموفق بود یا کلاینت یافت نشد.")
                else:
                    logger.warning(f"{log_prefix} Panel {panel_id_for_delete} not found, skipping panel deletion.")

            except Exception as panel_err:
                logger.error(f"{log_prefix} Error calling ClientService to delete client from panel {panel_id_for_delete}: {panel_err}. Proceeding with DB deletion. | خطا در حذف کلاینت از پنل.", exc_info=True)
        else:
            logger.warning(f"{log_prefix} Missing panel_id or client_uuid for account. Skipping panel deletion. | اطلاعات لازم برای حذف از پنل موجود نیست.")

        # 3. حذف رکورد ClientAccount از دیتابیس
        try:
            delete_result = await self.account_repo.delete(account_id)
            if delete_result:
                # Flush کردن تغییرات دیتابیس
                await self.session.flush() # Flush the delete operation
                logger.info(f"{log_prefix} ClientAccount record deleted from DB and flushed. Panel deletion status: {panel_delete_success}. | رکورد از دیتابیس حذف و Flush شد.")
                return True
            else:
                # اکانت در مرحله اول پیدا شد ولی delete آن را پیدا نکرد؟ عجیب است.
                logger.warning(f"{log_prefix} ClientAccount record was not found by delete operation, though fetched earlier. Panel deletion status: {panel_delete_success}. | رکورد در عملیات حذف یافت نشد (عجیب).")
                # شاید همزمان حذف شده؟ در این حالت هم حذف موفق است.
                return False # Or True depending on interpretation

        except SQLAlchemyError as db_err:
            logger.error(f"{log_prefix} Database error during account deletion: {db_err}. Rolling back session. | خطای دیتابیس در حذف اکانت.", exc_info=True)
            await self.session.rollback()
            logger.info(f"{log_prefix} Session rolled back due to DB error during deletion. | نشست به دلیل خطا بازگردانی شد.")
            raise # Re-raise the DB error
