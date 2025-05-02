"""
Client service for managing VPN client accounts
"""

from typing import List, Optional, Dict, Any, Tuple, Union
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
    """سفارش غیرفعال یا پرداخت نشده است."""
    pass

class PanelUnavailableError(Exception):
    """پنل در دسترس نیست یا غیرفعال است."""
    pass

class InboundUnavailableError(Exception):
    """اینباند در دسترس نیست یا غیرفعال است."""
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
    """عملیات پنل با خطا مواجه شد."""
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
                remote_uuid=created_client_uuid_on_panel,
                client_name=client_remark,
                email_name=client_email,
                data_limit_gb=plan.data_limit_gb, # Store the plan limit
                expires_at=expiry_datetime,
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
        """Gets a client account by UUID from the database."""
        logger.info(f"[ClientService] Fetching account with UUID {client_uuid}")
        try:
            # Use repository method
            return await self.client_repo.get_by_remote_uuid(client_uuid)
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching account with UUID {client_uuid}: {e}", exc_info=True)
            return None
        
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