"""
Client service for managing VPN client accounts
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import uuid
from core.log_config import logger
import os
import qrcode
import base64

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError  # Import standard SQLAlchemy exceptions

# Repositories
from db.repositories.client_repo import ClientRepository
from db.repositories.order_repo import OrderRepository
from db.repositories.panel_repo import PanelRepository
from db.repositories.inbound_repo import InboundRepository
from db.repositories.user_repo import UserRepository
from db.repositories.plan_repo import PlanRepository
from db.repositories.client_renewal_log_repo import ClientRenewalLogRepository

# Models
from db.models import (
    ClientAccount, AccountStatus, Order, OrderStatus,
    Panel, PanelStatus, Inbound, InboundStatus, User, Plan
)
from db.models.client_renewal_log import ClientRenewalLog, OperationType

# Services (For dependency injection, e.g., getting XuiClient)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.services.panel_service import PanelService

# Integrations & Exceptions
from core.integrations.xui_client import XuiClient, XuiConnectionError, XuiAuthenticationError, XuiNotFoundError

# Custom Exceptions (Keep relevant ones or define centrally)
class OrderNotFoundError(Exception):
    """سفارش مورد نظر یافت نشد."""
    pass
class OrderInactiveError(Exception):
    """وضعیت سفارش نامعتبر است."""
    pass
class PanelUnavailableError(Exception):
    """پنل مناسبی برای انجام عملیات یافت نشد."""
    pass
class InboundUnavailableError(Exception):
    """Inbound مناسبی روی پنل یافت نشد."""
    pass
class ClientCreationFailedError(Exception):
    """ایجاد کلاینت با خطا مواجه شد."""
    pass
class ClientUpdateFailedError(Exception):
    """به‌روزرسانی کلاینت با خطا مواجه شد."""
    pass
class ClientDeletionFailedError(Exception):
    """حذف کلاینت با خطا مواجه شد."""
    pass
class ClientNotFoundError(Exception):
    """کلاینت مورد نظر یافت نشد."""
    pass
class PanelOperationFailedError(Exception):
    """عملیات روی پنل با خطا مواجه شد."""
    pass


class ClientService:
    """Service for managing VPN client accounts"""
    
    def __init__(
        self,
        session: AsyncSession,
        client_repo: ClientRepository,
        order_repo: OrderRepository,
        panel_repo: PanelRepository,
        inbound_repo: InboundRepository,
        user_repo: UserRepository,
        plan_repo: PlanRepository,
        renewal_log_repo: ClientRenewalLogRepository,
        panel_service: "PanelService"
    ):
        """
        Constructor for ClientService.

        Args:
            session: AsyncSession for the database.
            client_repo: ClientRepository for client operations.
            order_repo: OrderRepository for order operations.
            panel_repo: PanelRepository for panel operations.
            inbound_repo: InboundRepository for inbound operations.
            user_repo: UserRepository for user operations.
            plan_repo: PlanRepository for plan operations.
            renewal_log_repo: ClientRenewalLogRepository for renewal log operations.
            panel_service: PanelService for getting configured XuiClients.
        """
        self.session = session
        self.client_repo = client_repo
        self.order_repo = order_repo
        self.panel_repo = panel_repo
        self.inbound_repo = inbound_repo
        self.user_repo = user_repo
        self.plan_repo = plan_repo
        self.renewal_log_repo = renewal_log_repo
        self.panel_service = panel_service
    
    async def create_client_account_for_order(
        self,
        panel_id: int,
        inbound_remote_id: int,
        user_id: int,
        plan_id: int
    ) -> ClientAccount:
        """
        ایجاد یک اکانت کلاینت VPN بر اساس یک سفارش و اطلاعات ورودی پنل/اینباند.
        این متد وظیفه هماهنگی بین ایجاد کلاینت در پنل XUI و ثبت رکورد آن در دیتابیس را بر عهده دارد.
        در صورت بروز خطا در هر مرحله، سعی در بازگردانی عملیات (مانند حذف کلاینت از پنل) می‌کند.

        Creates a VPN client account based on provided panel, inbound, user, and plan IDs.
        This method orchestrates the creation of the client on the XUI panel and its corresponding record in the database.
        It attempts to rollback panel operations (e.g., deleting the client) if any subsequent step fails.

        Args:
            panel_id: شناسه پنلی که کلاینت باید روی آن ایجاد شود. / The ID of the panel where the client should be created.
            inbound_remote_id: شناسه ریموت (remote_id) اینباند روی پنل. / The remote ID of the inbound on the panel.
            user_id: شناسه کاربری که اکانت برای او ایجاد می‌شود. / The ID of the user for whom the account is being created.
            plan_id: شناسه پلنی که مشخصات اکانت را تعیین می‌کند. / The ID of the plan defining the account's specifications.

        Returns:
            موجودیت ClientAccount ایجاد شده در دیتابیس (قبل از commit).
            The created ClientAccount entity in the database (before commit).

        Raises:
            UserNotFoundError: اگر کاربر یافت نشود. / If the user is not found.
            PlanNotFoundError: اگر پلن یافت نشود. / If the plan is not found.
            PanelOperationFailedError: اگر عملیات روی پنل (ایجاد کلاینت، دریافت URL) با خطا مواجه شود. / If panel operations (creation, getting URL) fail.
            DatabaseError: اگر خطایی در هنگام flush کردن تغییرات دیتابیس رخ دهد. / If a database error occurs during flush.
            Exception: برای خطاهای پیش‌بینی نشده دیگر. / For other unexpected errors.
        """
        log_prefix = f"[User: {user_id}, Plan: {plan_id}, Panel: {panel_id}, InboundRemote: {inbound_remote_id}]"
        logger.info(f"{log_prefix} Starting client account creation process. | شروع فرآیند ایجاد اکانت کلاینت.")

        created_client_uuid_on_panel: Optional[str] = None # Track if client was created on panel for rollback

        try:
            # --- 1. Fetch required data ---
            logger.debug(f"{log_prefix} Fetching related User and Plan. | دریافت اطلاعات کاربر و پلن.")
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                logger.error(f"{log_prefix} User not found. | کاربر یافت نشد.")
                # Define UserNotFoundError or use a generic one if not defined
                raise ValueError(f"User with ID {user_id} not found.") # Replace with specific exception

            plan = await self.plan_repo.get_by_id(plan_id)
            if not plan:
                logger.error(f"{log_prefix} Plan not found. | پلن یافت نشد.")
                 # Define PlanNotFoundError or use a generic one if not defined
                raise ValueError(f"Plan with ID {plan_id} not found.") # Replace with specific exception

            # --- 2. Prepare Client Data for Panel ---
            logger.debug(f"{log_prefix} Preparing client data for panel. | آماده‌سازی داده‌های کلاینت برای پنل.")
            # Generate unique identifiers and expiry
            client_uuid = str(uuid.uuid4())
            # Using a more descriptive remark, perhaps combining user and plan info
            client_remark = f"user_{user.id}_plan_{plan.id}_{datetime.now().strftime('%Y%m%d')}"
            client_email = f"{client_remark}@moonvpn.cloud" # Example email format
            expiry_datetime = datetime.utcnow() + timedelta(days=plan.expire_duration_days or 30) # Default 30 days

            # Prepare data dict based on plan details with defaults
            client_data_for_panel = {
                "id": client_uuid,
                "email": client_email,
                "flow": plan.flow or "", # Default empty flow if not specified
                "totalGB": (plan.data_limit_gb or 0) * 1024 * 1024 * 1024, # Convert GB to bytes, default 0
                "expiryTime": int(expiry_datetime.timestamp() * 1000), # Convert to milliseconds
                "ipLimit": plan.ip_limit or 0, # Default 0 (no limit) if not specified
                "enable": True,
                # Add other relevant fields if needed by XUI API
                # "subId": "", # Example
                # "tgId": "", # Example
            }
            logger.debug(f"{log_prefix} Prepared client data: {client_data_for_panel} | داده‌های کلاینت آماده شد.")

            # --- 3. Create Client on Panel ---
            logger.info(f"{log_prefix} Attempting to create client on panel. | تلاش برای ایجاد کلاینت روی پنل.")
            created_client_uuid_on_panel = await self._create_client_on_panel(
                panel_id=panel_id,
                inbound_remote_id=inbound_remote_id,
                client_data=client_data_for_panel
            )
            # Note: _create_client_on_panel should return the UUID if successful or raise PanelOperationFailedError
            logger.info(f"{log_prefix} Client successfully created on panel with UUID: {created_client_uuid_on_panel}. | کلاینت با موفقیت روی پنل با UUID ایجاد شد.")

            # --- 4. Get Config URL from Panel ---
            logger.info(f"{log_prefix} Attempting to get config URL from panel. | تلاش برای دریافت لینک کانفیگ از پنل.")
            config_url = await self._get_config_url_from_panel(
                panel_id=panel_id,
                client_uuid=created_client_uuid_on_panel
            )
            # _get_config_url_from_panel should handle its errors and return None or URL
            if config_url:
                 logger.info(f"{log_prefix} Successfully retrieved config URL. | لینک کانفیگ با موفقیت دریافت شد.")
            else:
                 logger.warning(f"{log_prefix} Could not retrieve config URL, proceeding without it. | دریافت لینک کانفیگ ناموفق بود، ادامه بدون لینک.")

            # --- Generate and Save QR Code ---
            qr_code_path = await self._generate_and_save_qr(user_id, created_client_uuid_on_panel, config_url) if config_url else None
            qr_base64 = await self._get_qr_base64(qr_code_path) if qr_code_path else None

            # --- 5. Create ClientAccount in Database ---
            logger.info(f"{log_prefix} Preparing to save ClientAccount to database. | آماده‌سازی برای ذخیره اکانت کلاینت در دیتابیس.")
            client_account = ClientAccount(
                user_id=user.id,
                plan_id=plan.id,
                panel_id=panel_id,
                inbound_remote_id=inbound_remote_id, # Store the inbound remote ID
                client_uuid=created_client_uuid_on_panel,
                remark=client_remark,
                email=client_email,
                data_limit_gb=plan.data_limit_gb, # Store the plan limit
                expire_at=expiry_datetime,
                status=AccountStatus.ACTIVE, # Start as active
                config_url=config_url,
                qr_code_path=qr_code_path,
                # Initial usage stats
                data_usage_bytes=0,
                last_synced_at=datetime.utcnow(), # Set initial sync time
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(client_account)
            logger.info(f"{log_prefix} ClientAccount object created and added to session. | آبجکت ClientAccount ایجاد و به نشست اضافه شد.")
            # افزودن base64 به خروجی برای ارسال نوتیفیکیشن
            client_account.qr_base64 = qr_base64

            # --- 6. Flush Session ---
            logger.info(f"{log_prefix} Flushing session to save ClientAccount. | Flush کردن نشست برای ذخیره ClientAccount.")
            await self.session.flush([client_account]) # Flush only this object if needed, or just flush()
            logger.info(f"{log_prefix} Session flushed successfully. ClientAccount ID pending commit: {client_account.id}. | نشست با موفقیت Flush شد. شناسه ClientAccount در انتظار commit.")

            # --- Success ---
            logger.info(f"{log_prefix} Client account creation process completed successfully (pending commit). | فرآیند ایجاد اکانت کلاینت با موفقیت تکمیل شد (در انتظار commit).")
            return client_account

        except (XuiConnectionError, XuiAuthenticationError, XuiNotFoundError, PanelOperationFailedError) as panel_err:
            logger.error(f"{log_prefix} Panel operation failed: {panel_err}. | عملیات پنل ناموفق بود.")
            # Rollback is implicitly handled if _create_client_on_panel failed.
            # If _get_config_url failed AFTER creation succeeded, we don't necessarily need rollback yet.
            # Rollback only needed if DB operation fails after panel success.
            # Re-raise as a generic panel error for the service layer
            raise PanelOperationFailedError(f"Panel operation failed: {panel_err}") from panel_err

        except SQLAlchemyError as db_err:
            logger.error(f"{log_prefix} Database flush error: {db_err}. | خطای Flush دیتابیس.")
            # Rollback the session to discard the failed ClientAccount add
            await self.session.rollback()
            logger.info(f"{log_prefix} Session rolled back due to database error. | نشست به دلیل خطای دیتابیس بازگردانی شد.")

            # --- 7. Rollback Panel Creation if DB Save Failed ---
            if created_client_uuid_on_panel:
                logger.warning(f"{log_prefix} Database save failed after client creation on panel. Attempting rollback. | ذخیره دیتابیس پس از ایجاد کلاینت روی پنل ناموفق بود. تلاش برای بازگردانی.")
                await self._rollback_panel_creation(
                    panel_id=panel_id,
                    client_uuid=created_client_uuid_on_panel,
                    log_prefix=log_prefix
                )
            else:
                 logger.info(f"{log_prefix} No panel creation rollback needed as client was not confirmed created on panel. | نیازی به بازگردانی پنل نیست زیرا ایجاد کلاینت روی پنل تایید نشده بود.")

            # Define DatabaseError or use a generic one
            raise db_err # Re-raise the original SQLAlchemyError or a custom DB error

        except Exception as e:
            logger.exception(f"{log_prefix} Unexpected error during client creation: {e}. | خطای پیش‌بینی نشده در ایجاد کلاینت.")
            await self.session.rollback() # Rollback potential session changes
            logger.info(f"{log_prefix} Session rolled back due to unexpected error. | نشست به دلیل خطای پیش‌بینی نشده بازگردانی شد.")

            # --- Rollback Panel Creation on Unexpected Error ---
            if created_client_uuid_on_panel:
                logger.warning(f"{log_prefix} Unexpected error occurred after client creation on panel. Attempting rollback. | خطای پیش‌بینی نشده پس از ایجاد کلاینت روی پنل رخ داد. تلاش برای بازگردانی.")
                await self._rollback_panel_creation(
                    panel_id=panel_id,
                    client_uuid=created_client_uuid_on_panel,
                    log_prefix=log_prefix
                )

            raise e # Re-raise the original exception

    async def get_user_active_accounts(self, user_id: int) -> List[ClientAccount]:
        """Get all active VPN accounts for a user"""
        return await self.client_repo.get_active_accounts_by_user_id(user_id)
    
    async def get_account_by_id(self, account_id: int) -> Optional[ClientAccount]:
        """Get a client account by ID"""
        return await self.client_repo.get_by_id(account_id)
    
    async def get_account_by_uuid(self, client_uuid: str) -> Optional[ClientAccount]:
        """Get a specific client account by its remote UUID"""
        return await self.client_repo.get_by_uuid(client_uuid)
    
    async def update_account_status(self, account_id: int, status: AccountStatus) -> Optional[ClientAccount]:
        """Update account status"""
        # Ensure status is a valid AccountStatus enum member
        if isinstance(status, str):
            try:
                status = AccountStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status value: {status}")
        
        account = await self.client_repo.get_by_id(account_id)
        if account:
            account.status = status
            self.session.add(account)
            await self.session.commit()
            await self.session.refresh(account)
        return account
    
    async def delete_account(self, account_id: int, user_id: Optional[int] = None, deleted_by: Optional[int] = None) -> bool:
        """
        Deletes a client account from the database and attempts to delete from the panel.

        Args:
            account_id: شناسه حساب کاربری برای حذف.
            user_id: (اختیاری) شناسه کاربر برای بررسی مالکیت.
            deleted_by: (اختیاری) شناسه کاربری که عمل حذف را انجام می‌دهد (برای لاگ).

        Returns:
            True اگر حذف موفقیت‌آمیز بود (یا حداقل از دیتابیس حذف شد).

        Raises:
            ClientNotFoundError: اگر حساب کاربری یافت نشود.
            ClientDeletionFailedError: اگر حذف از دیتابیس با شکست مواجه شود (خطاهای پنل فقط لاگ می‌شوند).
            SQLAlchemyError: در صورت بروز خطای پایگاه داده.
            PanelUnavailableError: اگر پنل یافت نشود ولی حذف ادامه یابد (فقط لاگ می‌شود).
            XuiConnectionError: در صورت بروز خطای اتصال به پنل XUI (فقط لاگ می‌شود).
            XuiAuthenticationError: در صورت بروز خطای احراز هویت در پنل XUI (فقط لاگ می‌شود).
        """
        log_prefix = f"[Account ID: {account_id}]"
        if user_id:
            log_prefix += f" [User ID Check: {user_id}]"
        if deleted_by:
             log_prefix += f" [Deleted By User: {deleted_by}]"
        logger.info(f"{log_prefix} Attempting to delete account. | شروع فرآیند حذف حساب.")

        # Fetch account, allow inactive for deletion purpose
        account = await self.get_account_by_id(account_id)
        if not account:
            # get_account_by_id logs the reason
            raise ClientNotFoundError(f"حساب کاربری با شناسه {account_id} یافت نشد یا دسترسی مجاز نیست.")

        panel_id = account.panel_id
        client_uuid = account.remote_uuid

        # Attempt to delete from panel first (best effort)
        if panel_id and client_uuid:
            try:
                logger.info(f"{log_prefix} Attempting to delete client from panel {panel_id} (UUID: {client_uuid}). | تلاش برای حذف کلاینت از پنل.")
                await self._delete_client_on_panel(panel_id, client_uuid)
                # Log success/failure is handled within _delete_client_on_panel
            except (PanelUnavailableError, XuiConnectionError, XuiAuthenticationError, PanelOperationFailedError) as panel_err:
                 logger.error(f"{log_prefix} Failed to delete client from panel during account deletion: {panel_err}. Proceeding with DB deletion. | حذف کلاینت از پنل ناموفق بود. ادامه با حذف از دیتابیس.")
            except Exception as e:
                 logger.error(f"{log_prefix} Unexpected error deleting client from panel: {e}. Proceeding with DB deletion. | خطای پیش‌بینی نشده هنگام حذف از پنل.")
        else:
             logger.warning(f"{log_prefix} Skipping panel deletion: Missing panel_id or client_uuid. | رد شدن از حذف پنل: panel_id یا client_uuid موجود نیست.")

        # Delete from database
        try:
            logger.info(f"{log_prefix} Deleting account from database. | حذف اکانت از دیتابیس.")
            # Assuming client_repo.delete handles the actual deletion query
            # Example using session directly if repo doesn't have delete:
            # await self.session.delete(account)
            # await self.session.commit()

            # Using a hypothetical repo method:
            deleted = await self.client_repo.delete_account(account_id) # Assuming this handles commit/flush
            if deleted:
                 logger.info(f"{log_prefix} Account successfully deleted from database. | اکانت با موفقیت از دیتابیس حذف شد.")
                 return True
            else:
                 # This case might happen if the account was deleted between fetch and delete, or repo method failed silently
                 logger.warning(f"{log_prefix} Database deletion reported unsuccessful by repository. | حذف از دیتابیس توسط ریپازیتوری ناموفق گزارش شد.")
                 await self.session.rollback() # Ensure rollback if repo didn't commit/failed
                 return False
        except SQLAlchemyError as db_err:
            logger.error(f"{log_prefix} Database error during account deletion: {db_err}. | خطای دیتابیس حین حذف اکانت.")
            await self.session.rollback()
            return False
        except Exception as e:
            logger.error(f"{log_prefix} Unexpected error during database deletion: {e}. | خطای پیش‌بینی نشده حین حذف از دیتابیس.")
            await self.session.rollback()
            return False

    async def extend_client_account(
        self,
        client_uuid: str,
        executed_by: int, # User ID performing the action
        extra_days: Optional[int] = None,
        extra_gb: Optional[float] = None, # Allow float for GB
        new_plan_id: Optional[int] = None, # Optional: If extending based on a new plan
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extend a client account's expiry time and/or traffic limit.
        Refactored to use injected XuiClient instance and repository.
        """
        log_prefix = f"[Client UUID: {client_uuid}] [Executed By User: {executed_by}]"
        logger.info(f"{log_prefix} Attempting to extend client account. | شروع فرآیند تمدید حساب کاربری.")

        if not extra_days and not extra_gb and not new_plan_id:
            logger.error(f"{log_prefix} Extension failed: No days, GB, or new plan provided. | تمدید ناموفق: هیچ مقدار روز، گیگابایت یا پلن جدیدی ارائه نشده است.")
            raise ValueError("حداقل یکی از مقادیر `extra_days`, `extra_gb`, یا `new_plan_id` باید برای تمدید ارائه شود.")

        # Get account by UUID, allow inactive as we might be reactivating it
        account = await self.get_account_by_uuid(client_uuid)
        if not account:
            # get_account_by_uuid logs the warning
            raise ClientNotFoundError(f"حساب کاربری با UUID {client_uuid} یافت نشد.")

        panel_update_succeeded = False
        try:
            original_expiry = account.expires_at
            original_traffic = account.traffic_limit
            original_plan_id = account.plan_id

            new_expiry_date = account.expires_at
            new_traffic_limit_gb = account.traffic_limit
            days_to_add = 0
            gb_to_add = 0.0
            plan_change_info = ""
            new_plan: Optional[Plan] = None # Store new plan if applicable

            # 1. Determine new expiry and traffic based on input
            if new_plan_id:
                new_plan = await self.plan_repo.get_by_id(new_plan_id)
                if not new_plan:
                    logger.error(f"{log_prefix} Extension failed: New Plan ID {new_plan_id} not found. | تمدید ناموفق: پلن جدید یافت نشد.")
                    raise ValueError(f"پلن با شناسه {new_plan_id} یافت نشد.")
                days_to_add = new_plan.duration_days
                gb_to_add = float(new_plan.traffic_gb) if new_plan.traffic_gb is not None else 0.0
                plan_change_info = f" based on Plan ID {new_plan_id} ({new_plan.name})"
                logger.info(f"{log_prefix} Extending based on plan {new_plan_id}: {days_to_add} days, {gb_to_add} GB. | تمدید بر اساس پلن.")
            else:
                days_to_add = extra_days or 0
                gb_to_add = float(extra_gb) if extra_gb is not None else 0.0
                logger.info(f"{log_prefix} Extending by explicit values: {days_to_add} days, {gb_to_add} GB. | تمدید به میزان مشخص شد.")

            # Calculate new expiry date
            if days_to_add > 0:
                # Extend from now if expired, otherwise from current expiry date
                current_expiry = account.expires_at
                base_date = datetime.utcnow()
                if current_expiry and current_expiry > base_date:
                    base_date = current_expiry
                new_expiry_date = base_date + timedelta(days=days_to_add)

            # Calculate new traffic limit
            if gb_to_add > 0:
                 # Add to existing limit. Handle None (unlimited) correctly.
                 current_limit = account.traffic_limit
                 if current_limit is None:
                     # If current is unlimited, adding finite GB doesn't make sense? Or should it become limited?
                     # Assuming for now: Adding GB to unlimited keeps it unlimited (or log warning).
                     # Let's assume it stays None if current is None.
                     logger.warning(f"{log_prefix} Attempting to add {gb_to_add} GB to an unlimited account. Limit remains unlimited. | تلاش برای افزودن ترافیک به حساب نامحدود.")
                     new_traffic_limit_gb = None
                 else:
                     new_traffic_limit_gb = (current_limit or 0.0) + gb_to_add
            elif new_plan_id and new_plan.traffic_gb is None:
                # If changing to an unlimited plan
                new_traffic_limit_gb = None

            # Convert new limits for XUI
            new_expiry_timestamp = int(new_expiry_date.timestamp() * 1000) if new_expiry_date else 0 # 0 for no expiry in XUI
            # 0 for unlimited traffic in XUI
            new_total_bytes = int(new_traffic_limit_gb * 1024 * 1024 * 1024) if new_traffic_limit_gb is not None else 0

            # 2. Get Panel and XuiClient
            panel = await self.panel_repo.get_by_id(account.panel_id)
            if not panel or panel.status != PanelStatus.ACTIVE:
                logger.error(f"{log_prefix} Panel ID {account.panel_id} not found or inactive. Cannot extend client on panel. | پنل یافت نشد یا غیرفعال است.")
                # Decide if DB update should proceed? For now, fail the whole operation.
                raise PanelUnavailableError(f"پنل مرتبط (ID: {account.panel_id}) یافت نشد یا غیرفعال است.")

            panel_xui_client = await self._get_xui_client(panel.id)

            # 3. Update client on Panel
            update_data = {
                "expiryTime": new_expiry_timestamp,
                "totalGB": new_total_bytes,
                 # Update flow/limitIp if changing plan and new plan has values
                 # Use getattr for safety in case Plan model changes
                 "flow": getattr(new_plan, 'flow', account.flow) if new_plan_id else account.flow,
                 "limitIp": getattr(new_plan, 'limit_ip', account.limit_ip) if new_plan_id else account.limit_ip,
                 # Might need to update other fields like subId if logic requires
            }
            # Filter out None values if modify_client doesn't handle them
            update_data_filtered = {k: v for k, v in update_data.items() if v is not None}

            logger.info(f"{log_prefix} Updating client on panel {panel.id} with data: {update_data_filtered}. | به‌روزرسانی کلاینت در پنل.")
            await panel_xui_client.modify_client(account.remote_uuid, update_data_filtered)
            panel_update_succeeded = True
            logger.info(f"{log_prefix} Client updated successfully on panel. | کلاینت در پنل با موفقیت به‌روز شد.")

            # 4. Update client in Database
            logger.info(f"{log_prefix} Updating account details in database. | به‌روزرسانی جزئیات حساب در دیتابیس.")
            account.expires_at = new_expiry_date
            account.traffic_limit = new_traffic_limit_gb
            account.updated_at = datetime.utcnow()
            # Update status to ACTIVE if it was expired/disabled and has valid expiry
            if account.status in [AccountStatus.EXPIRED, AccountStatus.DISABLED] and (not new_expiry_date or new_expiry_date > datetime.utcnow()):
                 account.status = AccountStatus.ACTIVE
                 logger.info(f"{log_prefix} Account status reactivated to ACTIVE due to extension. | وضعیت اکانت به دلیل تمدید فعال شد.")

            # Update plan_id and potentially flow/limitIp if changed based on new_plan
            if new_plan_id and new_plan_id != account.plan_id:
                account.plan_id = new_plan_id
                account.flow = update_data_filtered.get('flow', account.flow) # Keep DB consistent with panel data sent
                account.limit_ip = update_data_filtered.get('limitIp', account.limit_ip)
                logger.info(f"{log_prefix} Account plan updated to {new_plan_id} in DB. | پلن اکانت به {new_plan_id} در دیتابیس تغییر یافت.")
            elif not new_plan_id: # If extending explicitly, ensure flow/limitIp are not accidentally changed
                 account.flow = account.flow # No change
                 account.limit_ip = account.limit_ip # No change

            self.session.add(account)

            # 5. Log the renewal operation
            renewal_log = ClientRenewalLog(
                client_account_id=account.id,
                user_id=account.user_id,
                executed_by_user_id=executed_by,
                operation_type=OperationType.EXTENSION,
                previous_expiry_date=original_expiry,
                new_expiry_date=new_expiry_date,
                previous_traffic_limit_gb=original_traffic,
                new_traffic_limit_gb=new_traffic_limit_gb,
                days_added=days_to_add,
                traffic_gb_added=gb_to_add,
                previous_plan_id=original_plan_id,
                new_plan_id=account.plan_id,
                note=f"{note or ''}{plan_change_info}".strip(),
                created_at=datetime.utcnow()
            )
            self.session.add(renewal_log)
            logger.info(f"{log_prefix} Renewal log entry created and added to session. | لاگ تمدید ایجاد و به نشست اضافه شد.")

            # 6. Flush changes (Account update + Renewal Log)
            await self.session.flush()
            await self.session.refresh(account)
            await self.session.refresh(renewal_log) # Refresh log as well
            logger.info(f"{log_prefix} Account extended successfully in database. | حساب کاربری در دیتابیس با موفقیت تمدید شد.")

            # --- 6. Create Renewal Log ---
            try:
                await self.renewal_log_repo.create_log({
                    "user_id": account.user_id,
                    "client_account_id": account.id,
                    "data_added_gb": gb_to_add, # Store added GB
                    "days_added": days_to_add, # Store added days
                    "operation_type": OperationType.EXTENSION, # Determine based on context
                    "executed_by_user_id": executed_by, # User performing the action
                    "related_order_id": None, # No direct order involved in manual extension unless new_plan_id implies one
                    "notes": note # Add the optional note
                })
                logger.info(f"{log_prefix} Renewal log created successfully. | لاگ تمدید با موفقیت ایجاد شد.")
            except Exception as log_err:
                # Log the error but don't let it fail the entire operation
                logger.error(f"{log_prefix} Failed to create renewal log: {log_err}", exc_info=True)
                logger.error(f"{log_prefix} خطا در ایجاد لاگ تمدید: {log_err}", exc_info=True)

            return {
                "message_fa": f"حساب کاربری با UUID {client_uuid} با موفقیت تمدید شد.",
                "message_en": f"Client account with UUID {client_uuid} extended successfully.",
                "account_id": account.id,
                "new_expiry_date": new_expiry_date.isoformat() if new_expiry_date else None,
                "new_traffic_limit_gb": new_traffic_limit_gb
            }

        except (XuiConnectionError, XuiAuthenticationError) as xui_err:
            logger.error(f"{log_prefix} Failed to update client on panel during extension: {xui_err}. Database changes were NOT saved. | به‌روزرسانی کلاینت در پنل حین تمدید ناموفق بود. تغییرات دیتابیس ذخیره نشد.")
            await self.session.rollback()
            raise ClientUpdateFailedError(f"خطا در به‌روزرسانی کلاینت در پنل هنگام تمدید: {xui_err}") from xui_err
        except SQLAlchemyError as db_err:
            logger.error(f"{log_prefix} Failed to save extension details in database: {db_err}. | ذخیره جزئیات تمدید در دیتابیس ناموفق بود.")
            await self.session.rollback()
            logger.info(f"{log_prefix} Session rolled back due to SQLAlchemyError. | نشست به دلیل خطای SQLAlchemy بازگردانی شد.")
            # Check for inconsistency
            if panel_update_succeeded:
                 logger.critical(f"{log_prefix} INCONSISTENCY: Panel updated for extension, but DB save failed for account {account.id}. Manual check/fix required. | عدم تطابق: پنل برای تمدید آپدیت شد اما ذخیره دیتابیس ناموفق بود.")
                 # Consider attempting to revert panel changes? Complex.
                 raise ClientUpdateFailedError(f"کلاینت در پنل تمدید شد، اما خطا در ذخیره اطلاعات تمدید در دیتابیس رخ داد: {db_err}") from db_err
            else:
                raise ClientUpdateFailedError(f"خطا در ذخیره اطلاعات تمدید در دیتابیس: {db_err}") from db_err
        except ValueError as ve: # Catch specific value errors like plan not found or missing params
             logger.error(f"{log_prefix} Invalid input for extension: {ve}. | ورودی نامعتبر برای تمدید.")
             await self.session.rollback()
             raise # Re-raise the ValueError
        except PanelUnavailableError as pue:
             # Raised by _get_xui_client_for_panel
             logger.error(f"{log_prefix} Failed to get XUI client for extension: {pue}. | دریافت کلاینت XUI برای تمدید ناموفق بود.")
             await self.session.rollback()
             raise ClientUpdateFailedError(f"عدم امکان دسترسی به پنل برای تمدید حساب: {pue}") from pue
        except Exception as e:
            logger.exception(f"{log_prefix} Unexpected error during account extension: {e}. | خطای پیش‌بینی نشده حین تمدید حساب.")
            await self.session.rollback()
            logger.info(f"{log_prefix} Session rolled back due to unexpected error. | نشست به دلیل خطای پیش‌بینی نشده بازگردانی شد.")
            if panel_update_succeeded:
                  logger.critical(f"{log_prefix} INCONSISTENCY: Panel updated for extension, but unexpected error occurred before/during DB save for account {account.id}. Manual check/fix required.")
            raise ClientUpdateFailedError(f"خطای پیش‌بینی نشده در تمدید حساب: {e}") from e

    # --- Delete Operations ---

    async def delete_account(self, account_id: int, user_id: Optional[int] = None, deleted_by: Optional[int] = None) -> bool:
        """
        Deletes a client account from the database and attempts to delete from the panel.

        Args:
            account_id: ID of the account to delete.
            user_id: Optional user ID for permission checks (Not implemented here).
            deleted_by: Optional ID of the user/admin performing the deletion.

        Returns:
            True if the account was deleted from the database, False otherwise.
            Panel deletion failure is logged but doesn't prevent DB deletion.
        """
        log_prefix = f"[Account ID: {account_id}]"
        logger.info(f"{log_prefix} Attempting to delete client account. | تلاش برای حذف اکانت کلاینت.")

        account = await self.client_repo.get_by_id(account_id)
        if not account:
            logger.warning(f"{log_prefix} Client account not found in database for deletion. | اکانت کلاینت برای حذف در دیتابیس یافت نشد.")
            return False

        panel_id = account.panel_id
        client_uuid = account.remote_uuid

        # Attempt to delete from panel first (best effort)
        if panel_id and client_uuid:
            try:
                logger.info(f"{log_prefix} Attempting to delete client from panel {panel_id} (UUID: {client_uuid}). | تلاش برای حذف کلاینت از پنل.")
                await self._delete_client_on_panel(panel_id, client_uuid)
                # Log success/failure is handled within _delete_client_on_panel
            except (PanelUnavailableError, XuiConnectionError, XuiAuthenticationError, PanelOperationFailedError) as panel_err:
                 logger.error(f"{log_prefix} Failed to delete client from panel during account deletion: {panel_err}. Proceeding with DB deletion. | حذف کلاینت از پنل ناموفق بود. ادامه با حذف از دیتابیس.")
            except Exception as e:
                 logger.error(f"{log_prefix} Unexpected error deleting client from panel: {e}. Proceeding with DB deletion. | خطای پیش‌بینی نشده هنگام حذف از پنل.")
        else:
             logger.warning(f"{log_prefix} Skipping panel deletion: Missing panel_id or client_uuid. | رد شدن از حذف پنل: panel_id یا client_uuid موجود نیست.")

        # Delete from database
        try:
            logger.info(f"{log_prefix} Deleting account from database. | حذف اکانت از دیتابیس.")
            # Assuming client_repo.delete handles the actual deletion query
            # Example using session directly if repo doesn't have delete:
            # await self.session.delete(account)
            # await self.session.commit()

            # Using a hypothetical repo method:
            deleted = await self.client_repo.delete_account(account_id) # Assuming this handles commit/flush
            if deleted:
                 logger.info(f"{log_prefix} Account successfully deleted from database. | اکانت با موفقیت از دیتابیس حذف شد.")
                 return True
            else:
                 # This case might happen if the account was deleted between fetch and delete, or repo method failed silently
                 logger.warning(f"{log_prefix} Database deletion reported unsuccessful by repository. | حذف از دیتابیس توسط ریپازیتوری ناموفق گزارش شد.")
                 await self.session.rollback() # Ensure rollback if repo didn't commit/failed
                 return False
        except SQLAlchemyError as db_err:
            logger.error(f"{log_prefix} Database error during account deletion: {db_err}. | خطای دیتابیس حین حذف اکانت.")
            await self.session.rollback()
            return False
        except Exception as e:
            logger.error(f"{log_prefix} Unexpected error during database deletion: {e}. | خطای پیش‌بینی نشده حین حذف از دیتابیس.")
            await self.session.rollback()
            return False

    # --- Helper Methods ---

    async def _get_validated_order(self, order_id: int, log_prefix: str) -> Order:
        """دریافت و اعتبارسنجی سفارش."""
        logger.debug(f"{log_prefix} Fetching order details. | دریافت جزئیات سفارش.")
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            logger.error(f"{log_prefix} Order not found. | سفارش یافت نشد.")
            raise OrderNotFoundError(f"Order با شناسه {order_id} یافت نشد.")

        if order.status != OrderStatus.PAID:
            logger.warning(f"{log_prefix} Order status is not PAID (current: {order.status}). | وضعیت سفارش پرداخت شده نیست.")
            raise OrderInactiveError(f"سفارش {order_id} پرداخت نشده یا وضعیت نامعتبر ({order.status}) دارد.")
        logger.debug(f"{log_prefix} Order found and validated (Status: {order.status}). | سفارش یافت و اعتبارسنجی شد.")
        return order

    async def _get_related_user(self, user_id: int, log_prefix: str) -> User:
        """دریافت کاربر مرتبط با سفارش."""
        logger.debug(f"{log_prefix} Fetching related user (ID: {user_id}). | دریافت کاربر مرتبط.")
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"{log_prefix} User not found for ID: {user_id}. | کاربر یافت نشد.")
            raise OrderNotFoundError(f"کاربر مرتبط با سفارش (ID: {user_id}) یافت نشد.")
        logger.debug(f"{log_prefix} Related user found. | کاربر مرتبط یافت شد.")
        return user

    async def _get_related_plan(self, plan_id: int, log_prefix: str) -> Plan:
        """دریافت پلن مرتبط با سفارش."""
        logger.debug(f"{log_prefix} Fetching related plan (ID: {plan_id}). | دریافت پلن مرتبط.")
        plan = await self.plan_repo.get_by_id(plan_id)
        if not plan:
            logger.error(f"{log_prefix} Plan not found for ID: {plan_id}. | پلن یافت نشد.")
            raise OrderNotFoundError(f"پلن مرتبط با سفارش (ID: {plan_id}) یافت نشد.")
        logger.debug(f"{log_prefix} Related plan found. | پلن مرتبط یافت شد.")
        return plan

    async def _find_active_panel_and_inbound(self, location_name: str, log_prefix: str) -> Tuple[Panel, Inbound]:
        """پیدا کردن پنل و اینباند فعال بر اساس لوکیشن."""
        logger.debug(f"{log_prefix} Finding active panel for location: '{location_name}'. | جستجوی پنل فعال برای لوکیشن.")
        target_panel = await self.panel_repo.find_active_panel_by_location(location_name)

        if not target_panel:
            logger.error(f"{log_prefix} No active panel found for location: {location_name}. | پنل فعالی برای لوکیشن یافت نشد.")
            raise PanelUnavailableError(f"هیچ پنل فعالی برای لوکیشن '{location_name}' یافت نشد.")
        logger.info(f"{log_prefix} Found active panel ID: {target_panel.id} ({target_panel.name}). | پنل فعال یافت شد.")

        logger.debug(f"{log_prefix} Finding active inbound on panel ID: {target_panel.id}. | جستجوی اینباند فعال روی پنل.")
        active_inbounds = await self.inbound_repo.get_active_inbounds_by_panel_id(target_panel.id)

        if not active_inbounds:
            logger.error(f"{log_prefix} No active inbounds found on panel {target_panel.id}. | اینباند فعالی روی پنل یافت نشد.")
            raise InboundUnavailableError(f"هیچ inbound فعالی روی پنل {target_panel.name} (ID: {target_panel.id}) یافت نشد.")

        # TODO: Implement smarter inbound selection if needed
        # Current strategy: Pick the first active inbound.
        target_inbound = active_inbounds[0]
        logger.info(f"{log_prefix} Selected active inbound ID: {target_inbound.id} (Tag: {target_inbound.tag}, Protocol: {target_inbound.protocol}, Remote ID: {target_inbound.remote_id}). | اینباند فعال انتخاب شد.")
        return target_panel, target_inbound

    async def _get_xui_client(self, panel_id: int) -> XuiClient:
        """دریافت یک نمونه XuiClient پیکربندی و لاگین شده برای پنل از طریق PanelService."""
        logger.debug(f"[Panel ID: {panel_id}] Getting configured XUI client via PanelService. | دریافت کلاینت XUI برای پنل از طریق سرویس پنل.")
        try:
            xui_client = await self.panel_service.get_xui_client_by_id(panel_id)
            if not xui_client:
                logger.error(f"[Panel ID: {panel_id}] PanelService returned None for XUI client. | سرویس پنل کلاینت XUI را برنگرداند.")
                raise PanelUnavailableError(f"سرویس پنل نتوانست کلاینت XUI را برای پنل {panel_id} فراهم کند.")
            logger.debug(f"[Panel ID: {panel_id}] Successfully obtained XUI client. | کلاینت XUI با موفقیت دریافت شد.")
            return xui_client
        except (XuiConnectionError, XuiAuthenticationError) as auth_err:
             logger.error(f"[Panel ID: {panel_id}] Failed to get/login XUI client via PanelService: {auth_err}. | دریافت/لاگین کلاینت XUI از طریق سرویس پنل ناموفق بود.")
             raise # Re-raise the specific XUI error
        except Exception as e:
             logger.error(f"[Panel ID: {panel_id}] Unexpected error getting XUI client from PanelService: {e}. | خطای پیش‌بینی نشده در دریافت کلاینت XUI از سرویس پنل.")
             raise PanelUnavailableError(f"خطای نامشخص در دریافت کلاینت XUI برای پنل {panel_id}: {e}") from e

    def _prepare_client_data(self, order_id: int, plan: Plan, panel: Panel, inbound: Inbound) -> Tuple[str, str, str, datetime, Dict[str, Any]]:
        """آماده‌سازی داده‌های کلاینت برای ایجاد در پنل و دیتابیس."""
        client_uuid = str(uuid.uuid4())
        safe_location = "".join(filter(str.isalnum, panel.location_name)) or "LOC"
        client_remark = f"Moonvpn-{safe_location}-{order_id:05}"
        client_email = f"{client_remark}@moonvpn.local"
        expiry_datetime = datetime.utcnow() + timedelta(days=plan.duration_days)
        expiry_timestamp = int(expiry_datetime.timestamp() * 1000)
        total_traffic_bytes = int(plan.traffic_gb * 1024 * 1024 * 1024) if plan.traffic_gb else 0
        flow = getattr(plan, 'flow', '') or ''
        limit_ip = getattr(plan, 'limit_ip', 1)
        if limit_ip is None or limit_ip <= 0:
            limit_ip = 1 # Ensure limitIp is at least 1
        sub_id = str(uuid.uuid4()).replace('-', '')

        client_data_for_panel = {
            "id": client_uuid,
            "email": client_email,
            "flow": flow,
            "limitIp": limit_ip,
            "enable": True,
            "expiryTime": expiry_timestamp,
            "totalGB": total_traffic_bytes,
            "subId": sub_id,
            # "remark": client_remark, # Add if needed
        }
        return client_uuid, client_remark, client_email, expiry_datetime, client_data_for_panel

    async def _create_client_on_panel(self, panel_id: int, inbound_remote_id: int, client_data: Dict[str, Any]) -> str:
        """ایجاد کلاینت در پنل XUI با مدیریت خطا."""
        logger.info(f"[Panel ID: {panel_id}] Creating client on panel. | ایجاد کلاینت در پنل.")
        try:
            panel_xui_client = await self._get_xui_client(panel_id)
            logger.debug(f"[Panel ID: {panel_id}] Executing create_client on XuiClient. | اجرای متد create_client روی XuiClient.")
            panel_response = await panel_xui_client.create_client(
                inbound_id=inbound_remote_id,
                client_data=client_data
            )
            logger.debug(f"[Panel ID: {panel_id}] Panel raw response for client creation: {panel_response}. | پاسخ خام پنل برای ایجاد کلاینت.")

            # Check panel response for success explicitly
            if not panel_response or not panel_response.get("success", False):
                error_msg = panel_response.get("msg", "Unknown error from panel") if panel_response else "No response from panel"
                logger.error(f"[Panel ID: {panel_id}] Panel reported failure on client creation: {error_msg}. | پنل ایجاد کلاینت را ناموفق اعلام کرد.")
                raise ClientCreationFailedError(f"پنل ایجاد کلاینت را ناموفق اعلام کرد: {error_msg}")

            logger.info(f"[Panel ID: {panel_id}] Client successfully created on panel. | کلاینت با موفقیت در پنل ایجاد شد.")
            # Return the UUID that was intended to be created
            return client_data.get("id", "UNKNOWN_UUID")

        except (XuiConnectionError, XuiAuthenticationError, PanelUnavailableError) as comm_err:
            logger.error(f"[Panel ID: {panel_id}] Communication error during client creation: {comm_err}. | خطای ارتباطی حین ایجاد کلاینت.")
            raise
        except ClientCreationFailedError: # Re-raise the error we raised above
             raise
        except Exception as e:
            logger.error(f"[Panel ID: {panel_id}] Unexpected error creating client on panel: {e}. | ایجاد کلاینت در پنل ناموفق بود.")
            raise ClientCreationFailedError(f"خطا در ایجاد کلاینت در پنل {panel_id}: {e}") from e

    async def _delete_client_on_panel(self, panel_id: int, client_uuid: str) -> bool:
        """دریافت یک نمونه XuiClient پیکربندی و لاگین شده برای پنل از طریق PanelService."""
        logger.info(f"[Panel ID: {panel_id}] Attempting to delete client from panel. | تلاش برای حذف کلاینت از پنل.")

        try:
            panel_xui_client = await self._get_xui_client(panel_id)
            logger.debug(f"[Panel ID: {panel_id}] Executing delete_client on XuiClient. | اجرای متد delete_client روی XuiClient.")
            success = await panel_xui_client.delete_client(client_uuid)

            if success:
                logger.info(f"[Panel ID: {panel_id}] Client successfully deleted from panel. | کلاینت با موفقیت از پنل حذف شد.")
                return True
            else:
                # If XuiClient.delete_client returns False, it usually means client not found or panel error
                logger.warning(f"[Panel ID: {panel_id}] Panel reported client deletion as unsuccessful (client might not exist or panel error). | حذف از پنل ناموفق گزارش داد (ممکن است کلاینت یافت نشده باشد یا خطای پنل).")
                # Consider raising an error here if False indicates a failure that needs attention
                # For now, align with the return type bool, but log warning.
                # If XuiClient raises XuiNotFoundError, it will be caught below.
                return False

        except (XuiConnectionError, XuiAuthenticationError, PanelUnavailableError) as comm_err:
            logger.error(f"[Panel ID: {panel_id}] Communication error during client deletion: {comm_err}. | خطای ارتباطی حین حذف کلاینت.")
            raise
        except XuiNotFoundError:
             logger.warning(f"{log_prefix} Panel rollback: Client not found on panel (already deleted or never created?). | بازگردانی پنل: کلاینت در پنل یافت نشد.")
             return False # Client doesn't exist, deletion is effectively "complete" in a sense
        except Exception as e:
            logger.error(f"[Panel ID: {panel_id}] Unexpected error deleting client: {e}. | خطای پیش‌بینی نشده حین حذف کلاینت.")
            raise PanelOperationFailedError(f"خطای پیش‌بینی نشده در حذف کلاینت در پنل {panel_id}: {e}") from e

    async def _update_client_on_panel(self, panel_id: int, client_uuid: str, update_data: Dict[str, Any]) -> bool:
        """تنظیمات یک کلاینت را روی پنل XUI مشخص شده به‌روزرسانی می‌کند."""
        logger.info(f"[Panel ID: {panel_id}] Attempting to update client on panel with data: {update_data}. | تلاش برای به‌روزرسانی کلاینت در پنل.")

        try:
            panel_xui_client = await self._get_xui_client(panel_id)
            logger.debug(f"[Panel ID: {panel_id}] Executing update_client on XuiClient. | اجرای متد update_client روی XuiClient.")
            success = await panel_xui_client.update_client(client_uuid, update_data)

            if success:
                logger.info(f"[Panel ID: {panel_id}] Client successfully updated on panel. | کلاینت با موفقیت در پنل به‌روز شد.")
                return True
            else:
                # XuiClient.update_client typically returns False if the client wasn't found or update failed silently on panel side
                logger.warning(f"[Panel ID: {panel_id}] Panel reported client update as unsuccessful (client might not exist or panel error). | پنل به‌روزرسانی کلاینت را ناموفق گزارش داد.")
                # Raise an error because an update failure usually needs attention
                raise PanelOperationFailedError(f"پنل به‌روزرسانی کلاینت {client_uuid} را ناموفق گزارش داد.")

        except (XuiConnectionError, XuiAuthenticationError, PanelUnavailableError) as comm_err:
            logger.error(f"[Panel ID: {panel_id}] Communication error during client update: {comm_err}. | خطای ارتباطی حین به‌روزرسانی کلاینت.")
            raise
        except XuiNotFoundError:
             logger.error(f"[Panel ID: {panel_id}] Client not found on panel for update. | کلاینت برای به‌روزرسانی در پنل یافت نشد.")
             raise PanelOperationFailedError(f"کلاینت {client_uuid} برای به‌روزرسانی در پنل {panel_id} یافت نشد.")
        except PanelOperationFailedError: # Re-raise the error we raised above
             raise
        except Exception as e:
            logger.error(f"[Panel ID: {panel_id}] Unexpected error updating client on panel: {e}. | خطای پیش‌بینی نشده در به‌روزرسانی کلاینت در پنل.")
            raise PanelOperationFailedError(f"خطای پیش‌بینی نشده در به‌روزرسانی کلاینت در پنل {panel_id}: {e}") from e

    async def _disable_client_on_panel(self, panel_id: int, client_uuid: str) -> bool:
        """یک کلاینت را با تنظیم وضعیت 'enable' آن به false در پنل XUI مشخص شده غیرفعال می‌کند."""
        logger.info(f"[Panel ID: {panel_id}] Attempting to disable client on panel. | تلاش برای غیرفعال کردن کلاینت در پنل.")
        update_data = {"enable": False}
        try:
            # Reuse the update method
            success = await self._update_client_on_panel(panel_id, client_uuid, update_data)
            if success:
                 logger.info(f"[Panel ID: {panel_id}] Client successfully disabled on panel. | کلاینت با موفقیت در پنل غیرفعال شد.")
                 return True
            else:
                 # _update_client_on_panel should raise error on failure, so this path might not be reached
                 # but added for robustness.
                 logger.warning(f"[Panel ID: {panel_id}] Disabling client reported as unsuccessful by underlying update method. | غیرفعال سازی کلاینت توسط متد به‌روزرسانی ناموفق گزارش شد.")
                 return False
        except PanelOperationFailedError as update_err:
             # Catch specific error from _update_client_on_panel
             logger.error(f"[Panel ID: {panel_id}] Failed to disable client on panel (via update): {update_err}. | غیرفعال سازی کلاینت در پنل ناموفق بود.")
             raise # Re-raise the specific failure
        except (XuiConnectionError, XuiAuthenticationError, PanelUnavailableError) as comm_err:
             # These should be caught by _update_client_on_panel but added for clarity
             logger.error(f"[Panel ID: {panel_id}] Communication error during client disable: {comm_err}. | خطای ارتباطی حین غیرفعال سازی کلاینت.")
             raise
        except Exception as e:
             # Catch any unexpected errors not caught by _update_client_on_panel
             logger.error(f"[Panel ID: {panel_id}] Unexpected error disabling client on panel: {e}. | خطای پیش‌بینی نشده در غیرفعال سازی کلاینت.")
             raise PanelOperationFailedError(f"خطای پیش‌بینی نشده در غیرفعال کردن کلاینت در پنل {panel_id}: {e}") from e

    async def _get_config_url_from_panel(self, panel_id: int, client_uuid: str) -> Optional[str]:
        """دریافت URL کانفیگ از پنل با مدیریت خطا."""
        logger.debug(f"[Panel ID: {panel_id}] Attempting to get config URL from panel. | تلاش برای دریافت URL کانفیگ از پنل.")

        try:
            panel_xui_client = await self._get_xui_client(panel_id)
            logger.debug(f"[Panel ID: {panel_id}] Executing get_config on XuiClient. | اجرای متد get_config روی XuiClient.")
            config_url = await panel_xui_client.get_config(client_uuid)

            if config_url and isinstance(config_url, str) and config_url.strip():
                logger.info(f"[Panel ID: {panel_id}] Successfully retrieved config URL. | URL کانفیگ با موفقیت دریافت شد.")
                return config_url.strip()
            else:
                logger.warning(f"[Panel ID: {panel_id}] Received empty or invalid config URL from panel. Type: {type(config_url)}. Returning None. | URL کانفیگ خالی یا نامعتبر دریافت شد.")
                return None
        except (XuiConnectionError, XuiAuthenticationError, PanelUnavailableError) as comm_err:
             logger.error(f"[Panel ID: {panel_id}] Communication error while getting config URL: {comm_err}. | خطای ارتباطی حین دریافت URL کانفیگ.")
             raise # Re-raise communication errors
        except XuiNotFoundError:
             logger.warning(f"{log_prefix} Panel rollback: Client not found on panel when trying to get config URL. Returning None. | کلاینت هنگام تلاش برای دریافت URL یافت نشد.")
             return None
        except Exception as e:
            # Log other errors but don't raise, return None as per original logic/requirement interpretation
            logger.warning(f"{log_prefix} Failed to get config URL from panel due to unexpected error: {e}. Returning None. | دریافت URL کانفیگ به دلیل خطای پیش‌بینی نشده ناموفق بود.")
            return None

    async def _rollback_panel_creation(self, panel_id: int, client_uuid: str, log_prefix: str):
        """تلاش می‌کند یک کلاینت را از پنل حذف کند، معمولاً برای بازگردانی پس از شکست در مراحل بعدی
        (مانند ذخیره دیتابیس) استفاده می‌شود. خطاها را لاگ می‌کند اما آن‌ها را مجدداً raise نمی‌کند.

        Args:
            panel_id: The ID of the panel where the client was potentially created.
            client_uuid: The UUID of the client to attempt to delete.
        """
        logger.warning(f"{log_prefix} Attempting panel rollback: Deleting client. | تلاش برای بازگردانی پنل: حذف کلاینت.")
        try:
            # We can reuse the delete helper method, but catch its specific errors here
            # Or call XuiClient directly for simpler error handling in this specific case
            panel_xui_client = await self._get_xui_client(panel_id)
            logger.debug(f"{log_prefix} Executing delete_client on XuiClient for rollback. | اجرای متد delete_client برای بازگردانی.")
            await panel_xui_client.delete_client(client_uuid)
            logger.info(f"{log_prefix} Panel rollback successful: Client possibly deleted. | بازگردانی پنل موفقیت‌آمیز بود: کلاینت احتمالاً حذف شد.")
        except (XuiConnectionError, XuiAuthenticationError, PanelUnavailableError) as comm_err:
            logger.error(f"{log_prefix} Panel rollback failed: Communication error: {comm_err}. Manual cleanup might be required. | بازگردانی پنل ناموفق بود: خطای ارتباطی.")
        except XuiNotFoundError:
             logger.warning(f"{log_prefix} Panel rollback: Client not found on panel (already deleted or never created?). | بازگردانی پنل: کلاینت در پنل یافت نشد.")
        except Exception as e:
            logger.error(f"{log_prefix} Panel rollback failed: Unexpected error deleting client: {e}. Manual cleanup possibly required. | بازگردانی پنل ناموفق بود: خطای پیش‌بینی نشده.")
        # Do not re-raise any exceptions here

    async def _prepare_order_update(self, order: Order, client_account_id: int, log_prefix: str):
        """آماده‌سازی آبجکت Order برای به‌روزرسانی (بدون flush)."""
        logger.debug(f"{log_prefix} Preparing Order ID: {order.id} status update to COMPLETED. | آماده‌سازی به‌روزرسانی وضعیت سفارش به تکمیل شده.")
        order.status = OrderStatus.COMPLETED
        order.fulfilled_at = datetime.utcnow()
        order.client_account_id = client_account_id
        order.updated_at = datetime.utcnow()
        self.session.add(order) # Add order back to session to mark it for update during flush
        logger.debug(f"{log_prefix} Order entity prepared for update. | موجودیت سفارش برای به‌روزرسانی آماده شد.")

    async def _generate_and_save_qr(self, user_id: int, uuid: str, config_url: str) -> str:
        """
        ساخت و ذخیره QR Code تصویری برای subscription_url و بازگرداندن مسیر فایل ذخیره شده.
        Generate and save QR code image for the subscription_url and return the saved file path.
        مسیر: /data/qrcodes/{user_id}_{uuid}.png
        """
        qr_dir = "/data/qrcodes"
        os.makedirs(qr_dir, exist_ok=True)
        qr_path = os.path.join(qr_dir, f"{user_id}_{uuid}.png")
        qr_img = qrcode.make(config_url)
        qr_img.save(qr_path)
        return qr_path

    async def _get_qr_base64(self, qr_path: str) -> str:
        """
        خواندن فایل QR Code و تبدیل به base64 برای ارسال به ربات.
        """
        if not qr_path or not os.path.exists(qr_path):
            return ""
        with open(qr_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def _delete_old_qr(self, old_path: str):
        """
        حذف فایل QR Code قبلی در صورت وجود.
        Delete previous QR code image file if exists.
        """
        if old_path and os.path.exists(old_path):
            os.remove(old_path)

    async def update_client_account(
        self,
        account_id: int,
        new_uuid: str,
        config_url: str,
        user_id: int
    ):
        """
        بروزرسانی uuid و QR Code کلاینت، حذف QR قبلی و ذخیره جدید.
        """
        account = await self.client_repo.get_by_id(account_id)
        if not account:
            raise ValueError("ClientAccount not found")
        old_qr_path = account.qr_code_path
        # حذف QR قبلی
        await self._delete_old_qr(old_qr_path)
        # ساخت QR جدید
        qr_code_path = await self._generate_and_save_qr(user_id, new_uuid, config_url)
        # بروزرسانی فیلدها
        account.remote_uuid = new_uuid
        account.config_url = config_url
        account.qr_code_path = qr_code_path
        await self.session.commit()
        return account

# Ensure ClientRepository.create exists and accepts a ClientAccount object or kwargs
# Ensure PanelRepository/InboundRepository methods used are correct
# Ensure UserRepository/PlanRepository methods used are correct

    # Ensure the file ends cleanly 