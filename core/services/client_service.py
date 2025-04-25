"""
Client service for managing VPN client accounts
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Repositories
from db.repositories.client_repo import ClientRepository
from db.repositories.order_repo import OrderRepository
from db.repositories.panel_repo import PanelRepository
from db.repositories.inbound_repo import InboundRepository  # Assuming this exists
from db.repositories.user_repo import UserRepository  # Assuming this exists
from db.repositories.plan_repo import PlanRepository  # Assuming this exists

# Models
from db.models import (
    ClientAccount, AccountStatus, Order, OrderStatus, 
    Panel, PanelStatus, Inbound, InboundStatus, User, Plan
)
from db.models.client_renewal_log import ClientRenewalLog, OperationType

# Integrations
from core.integrations.xui_client import XuiClient

# Exceptions (Define these or import from a common exceptions module)
class OrderNotFoundError(Exception): pass
class OrderInactiveError(Exception): pass
class PanelUnavailableError(Exception): pass
class InboundUnavailableError(Exception): pass
class ClientCreationFailedError(Exception): pass


logger = logging.getLogger(__name__)


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
        xui_client: XuiClient # Assuming XuiClient is passed configured
    ):
        self.session = session
        self.client_repo = client_repo
        self.order_repo = order_repo
        self.panel_repo = panel_repo
        self.inbound_repo = inbound_repo
        self.user_repo = user_repo
        self.plan_repo = plan_repo
        self.xui_client = xui_client # Use the passed instance
    
    async def create_client_account_for_order(self, order_id: int) -> ClientAccount:
        """
        Creates a VPN client account based on a paid order.

        Args:
            order_id: The ID of the order to fulfill.

        Returns:
            The created ClientAccount object.

        Raises:
            OrderNotFoundError: If the order doesn't exist.
            OrderInactiveError: If the order is not in a paid state.
            PanelUnavailableError: If no active panel is found for the order's location.
            InboundUnavailableError: If no active inbound is found on the selected panel.
            ClientCreationFailedError: If the client creation fails on the panel or database.
        """
        logger.info(f"Attempting to create client account for order_id: {order_id}")

        # 1. Get Order and related data
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            logger.error(f"Order not found for order_id: {order_id}")
            raise OrderNotFoundError(f"Order با شناسه {order_id} یافت نشد.")

        # Eagerly load related entities if not already loaded by the repository
        # Example: await self.order_repo.get_by_id(order_id, load_related=["user", "plan"])
        # For now, assume they are loaded or fetch them separately if needed.
        user = await self.user_repo.get_by_id(order.user_id)
        plan = await self.plan_repo.get_by_id(order.plan_id)

        if not user or not plan:
             logger.error(f"User or Plan not found for order_id: {order_id}")
             # Or raise a specific error
             raise OrderNotFoundError(f"User or Plan related to order {order_id} not found.")


        # 2. Check order status
        if order.status != OrderStatus.PAID:
            logger.warning(f"Order {order_id} is not in PAID state (current: {order.status}). Cannot create account.")
            raise OrderInactiveError(f"سفارش {order_id} پرداخت نشده یا وضعیت نامعتبر ({order.status}) دارد.")

        # 3. Find an active Panel for the location
        location_name = order.location_name
        active_panels = await self.panel_repo.get_active_panels()
        target_panel: Optional[Panel] = None
        for panel in active_panels:
            if panel.location_name == location_name:
                target_panel = panel
                break
        
        if not target_panel:
            logger.error(f"No active panel found for location: {location_name} (Order ID: {order_id})")
            raise PanelUnavailableError(f"هیچ پنل فعالی برای لوکیشن '{location_name}' یافت نشد.")

        logger.info(f"Found active panel {target_panel.id} ({target_panel.name}) for location {location_name}")

        # 4. Find an active Inbound on the panel
        # Assuming InboundRepository has a method like get_active_inbounds_by_panel_id
        active_inbounds = await self.inbound_repo.get_active_inbounds_by_panel_id(target_panel.id) 
        
        if not active_inbounds:
             logger.error(f"No active inbounds found for panel {target_panel.id} (Order ID: {order_id})")
             raise InboundUnavailableError(f"هیچ inbound فعالی روی پنل {target_panel.name} یافت نشد.")

        # Simple selection strategy: Pick the first active inbound
        target_inbound = active_inbounds[0]
        logger.info(f"Selected active inbound {target_inbound.id} (Tag: {target_inbound.tag}, Remote ID: {target_inbound.remote_id}) on panel {target_panel.id}")

        # 5. Generate client details (remark/email)
        # Using a combination of prefix, location (assuming panel.location_name is like 'TR'), and order_id
        client_remark = f"Moonvpn-{target_panel.location_name}-{order_id:05}" # e.g., Moonvpn-TR-00123
        client_email = f"{client_remark}@moonvpn.local" # Using a local domain
        client_uuid = str(uuid.uuid4())

        # Calculate expiry time and traffic limit from plan
        # Add duration to current time. Consider potential timezone issues.
        expiry_datetime = datetime.utcnow() + timedelta(days=plan.duration_days)
        expiry_timestamp = int(expiry_datetime.timestamp() * 1000) # XUI uses milliseconds
        
        # Convert GB to bytes for XUI
        total_traffic_bytes = plan.traffic_gb * 1024 * 1024 * 1024 
        
        # 6. Create client using XuiClient
        # Configure XuiClient for the target panel
        panel_xui_client = XuiClient(
            host=target_panel.url, 
            username=target_panel.username, 
            password=target_panel.password
        )
        await panel_xui_client.login() # Ensure logged in

        client_data_for_panel = {
            "id": client_uuid, # Specify UUID
            "email": client_email, # Use generated email/remark
            "remark": client_remark, # Optional: Can add remark field if supported/needed
            "enable": True,
            "expiryTime": expiry_timestamp,
            "totalGB": total_traffic_bytes, # Send bytes
            "flow": "", # Default flow or specify if needed
            "limitIp": 1, # Default limit or get from plan/settings
            # Add other necessary fields based on py3xui library and panel requirements
            # "subId": "", # Subscription ID if needed
        }

        try:
            logger.info(f"Creating client on panel {target_panel.id} for inbound {target_inbound.remote_id} with data: {client_data_for_panel}")
            panel_response = await panel_xui_client.create_client(
                inbound_id=target_inbound.remote_id, 
                client_data=client_data_for_panel
            )
            logger.info(f"Panel response for client creation: {panel_response}")

            if not panel_response or not panel_response.get("success", False):
                 raise ClientCreationFailedError("Panel returned failure on client creation.")

            # Attempt to get config URL immediately after creation
            # Note: Panel might need some time, or this might need a separate call
            # The panel_response itself might contain useful info, but let's try get_config
            try:
                # Use the same authenticated client instance
                config_url = await panel_xui_client.get_config(client_uuid) 
                logger.info(f"Successfully retrieved config URL for UUID {client_uuid}: {config_url}")
            except Exception as config_err:
                 logger.warning(f"Failed to get config URL immediately after creation for UUID {client_uuid}: {config_err}. Setting to None.")
                 config_url = None # Handle inability to get config URL gracefully

        except Exception as e:
            logger.error(f"Failed to create client on panel {target_panel.id} for order {order_id}: {e}")
            # Consider cleanup/rollback steps if necessary
            raise ClientCreationFailedError(f"خطا در ایجاد کلاینت در پنل {target_panel.name}: {e}")

        # 7. Save ClientAccount to database
        # Convert bytes back to GB for storage if needed, based on model definition
        traffic_limit_for_db = plan.traffic_gb # Assuming model stores GB

        new_client_account_data = {
            "user_id": user.id,
            "panel_id": target_panel.id,
            "inbound_id": target_inbound.id,
            "plan_id": plan.id,
            "order_id": order.id,
            "remote_uuid": client_uuid,
            "client_name": client_remark, # Using remark as client name for now
            "email_name": client_email,
            "expires_at": expiry_datetime, # Store datetime object
            "traffic_limit": traffic_limit_for_db, # Store GB
            "traffic_used": 0, # Initial usage is 0
            "status": AccountStatus.ACTIVE,
            "config_url": config_url,
            "qr_code_path": None, # QR code generation might be a separate step
            "created_at": datetime.utcnow()
        }

        try:
            logger.info(f"Saving new ClientAccount to database for order {order_id} with data: {new_client_account_data}")
            created_account = await self.client_repo.create_account(**new_client_account_data)
            
            # Link order to client account
            order.client_account_id = created_account.id
            order.status = OrderStatus.COMPLETED # Update order status
            order.fulfilled_at = datetime.utcnow()
            self.session.add(order) # Add order to session for update
            
            await self.session.commit() # Commit both account creation and order update
            await self.session.refresh(created_account) # Refresh to get final state
            await self.session.refresh(order) # Refresh order as well

            logger.info(f"Successfully created and saved ClientAccount {created_account.id} for order {order_id}")

        except Exception as db_err:
            logger.error(f"Failed to save ClientAccount or update order {order_id} in database: {db_err}")
            # CRITICAL: Need to handle potential inconsistency. 
            # The client might be created on the panel but not saved in DB.
            # Options: 
            # 1. Attempt to delete the client from the panel.
            # 2. Log the inconsistency for manual review.
            # For now, just raise the error.
            raise ClientCreationFailedError(f"خطا در ذخیره اطلاعات کلاینت در دیتابیس: {db_err}")

        # 8. Return the created ClientAccount
        return created_account
    
    async def get_user_active_accounts(self, user_id: int) -> List[ClientAccount]:
        """Get all active VPN accounts for a user"""
        return await self.client_repo.get_active_accounts_by_user_id(user_id)
    
    async def get_account_by_id(self, account_id: int) -> Optional[ClientAccount]:
        """Get a client account by ID"""
        return await self.client_repo.get_by_id(account_id)
    
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
    
    async def delete_account(self, account_id: int) -> bool:
        """
        Deletes a client account from the database and attempts to delete from the panel.
        Note: Panel deletion is best-effort.
        """
        logger.info(f"Attempting to delete client account with ID: {account_id}")
        account = await self.client_repo.get_by_id(account_id)
        if not account:
            logger.warning(f"Client account {account_id} not found in database for deletion.")
            return False

        # Attempt to delete from panel first (best-effort)
        if account.remote_uuid and account.panel:
            try:
                panel = account.panel # Access related panel object
                panel_xui_client = XuiClient(host=panel.url, username=panel.username, password=panel.password)
                await panel_xui_client.login()
                success = await panel_xui_client.delete_client(account.remote_uuid)
                if success:
                    logger.info(f"Successfully deleted client {account.remote_uuid} from panel {panel.id}")
                else:
                    logger.warning(f"Failed to delete client {account.remote_uuid} from panel {panel.id}. Proceeding with DB deletion.")
            except Exception as e:
                 logger.error(f"Error deleting client {account.remote_uuid} from panel {account.panel_id}: {e}. Proceeding with DB deletion.")
        
        # Delete from database
        try:
            success = await self.client_repo.delete_account(account_id)
            if success:
                 logger.info(f"Successfully deleted client account {account_id} from database.")
            else:
                 # This might happen if delete_account implementation returns False on failure
                 logger.error(f"Database deletion failed for client account {account_id}.")
            return success
        except Exception as db_err:
            logger.error(f"Error deleting client account {account_id} from database: {db_err}")
            return False
    
    async def get_expired_accounts(self) -> List[ClientAccount]:
        """Get all accounts whose expiry date is in the past"""
        # This might be better implemented in the repository
        query = select(ClientAccount).where(ClientAccount.expires_at < datetime.utcnow())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_accounts_by_panel(self, panel_id: int) -> List[ClientAccount]:
        """Get all accounts associated with a specific panel ID"""
        # This might be better implemented in the repository
        query = select(ClientAccount).where(ClientAccount.panel_id == panel_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_account_traffic(self, account_id: int, traffic_used_gb: int) -> Optional[ClientAccount]:
        """
        Update account traffic usage (in GB).
        Note: Assumes the input 'traffic_used_gb' is the *total* used traffic, not incremental.
        """
        account = await self.client_repo.get_by_id(account_id)
        if account:
            account.traffic_used = traffic_used_gb # Assuming model stores GB
            self.session.add(account)
            await self.session.commit()
            await self.session.refresh(account)
        return account
    
    async def extend_client_account(
        self,
        client_uuid: str,
        executed_by: int,
        extra_days: Optional[int] = None,
        extra_gb: Optional[int] = None,
        note: Optional[str] = None
    ) -> dict:
        """
        Extend a client account's expiry time and/or traffic limit.
        Refactored to use injected XuiClient instance and repository.
        """
        logger.info(f"Attempting to extend client account UUID: {client_uuid} by user {executed_by}")
        
        # Get client account from database first
        account = await self.client_repo.get_account_by_uuid(client_uuid) # Needs get_account_by_uuid in repo
        
        if not account:
            logger.error(f"Client with UUID {client_uuid} not found in database.")
            raise ValueError(f"کلاینت با uuid {client_uuid} در دیتابیس یافت نشد.")
            
        # We need panel info to interact with the correct panel
        panel = await self.panel_repo.get_panel_by_id(account.panel_id)
        if not panel:
             logger.error(f"Panel {account.panel_id} not found for client UUID {client_uuid}.")
             raise ValueError(f"پنل مربوط به کلاینت {client_uuid} یافت نشد.")

        # Configure XuiClient for this specific panel
        panel_xui_client = XuiClient(host=panel.url, username=panel.username, password=panel.password)
        await panel_xui_client.login()

        # Get current client info from panel
        try:
            panel_client_info = await panel_xui_client.get_client_by_uuid(client_uuid)
            if not panel_client_info:
                raise ValueError(f"کلاینت با uuid {client_uuid} در پنل {panel.name} یافت نشد.")
        except Exception as e:
            logger.error(f"Failed to get client info from panel {panel.name} for UUID {client_uuid}: {e}")
            raise ValueError(f"خطا در دریافت اطلاعات کلاینت {client_uuid} از پنل: {e}")
        
        # Store previous values for logging (use panel data as source of truth for current state)
        # Panel provides expiryTime in ms and totalGB in bytes
        prev_expiry_ms = panel_client_info.get("expiryTime", 0)
        prev_total_bytes = panel_client_info.get("totalGB", 0)
        
        prev_expiry_dt = datetime.fromtimestamp(prev_expiry_ms / 1000) if prev_expiry_ms > 0 else datetime.utcnow()
        prev_total_gb = prev_total_bytes / (1024 * 1024 * 1024)

        # Calculate new expiry time if extra_days provided
        new_expiry_ms = prev_expiry_ms
        if extra_days is not None:
            # Use current time if already expired, otherwise extend from previous expiry
            base_date = prev_expiry_dt if prev_expiry_dt > datetime.utcnow() else datetime.utcnow()
            new_expiry_dt = base_date + timedelta(days=extra_days)
            new_expiry_ms = int(new_expiry_dt.timestamp() * 1000) # Convert to ms
            
        # Calculate new total GB if extra_gb provided
        new_total_bytes = prev_total_bytes
        if extra_gb is not None:
            new_total_bytes = prev_total_bytes + (extra_gb * 1024 * 1024 * 1024) # Add bytes
            
        # Data to update in panel
        update_data = {
            "enable": True # Ensure client is enabled
            # Only include fields if they change
        }
        if extra_days is not None:
            update_data["expiryTime"] = new_expiry_ms
        if extra_gb is not None:
             update_data["totalGB"] = new_total_bytes

        if not update_data:
             logger.warning(f"No changes requested for client {client_uuid}. Skipping panel update.")
             # Or return current state
             return {
                 "client_uuid": client_uuid,
                 "new_expiry_time": prev_expiry_ms,
                 "new_total_gb": prev_total_bytes / (1024 * 1024 * 1024), # Return GB
                 "status": account.status.value
             }

        # Update client in panel
        try:
            logger.info(f"Updating client {client_uuid} on panel {panel.id} with data: {update_data}")
            result = await panel_xui_client.update_client(client_uuid, update_data)
            
            if not result or not result.get("success", False):
                raise Exception("Panel returned failure on client update.")
                
            logger.info(f"Successfully updated client {client_uuid} on panel {panel.id}.")
            
        except Exception as e:
            logger.error(f"خطا در بروزرسانی اطلاعات کلاینت {client_uuid} در پنل {panel.name}: {e}")
            raise Exception(f"خطا در بروزرسانی اطلاعات کلاینت در پنل: {e}")
            
        # Update account in database
        new_expiry_dt_for_db = datetime.fromtimestamp(new_expiry_ms / 1000) if new_expiry_ms > 0 else account.expires_at
        new_total_gb_for_db = new_total_bytes / (1024 * 1024 * 1024)

        if extra_days is not None:
            account.expires_at = new_expiry_dt_for_db
        if extra_gb is not None:
            account.traffic_limit = new_total_gb_for_db # Assuming DB stores GB
            
        # Reactivate if expired and time was added
        if account.status == AccountStatus.EXPIRED and extra_days is not None:
            if account.expires_at > datetime.utcnow():
                account.status = AccountStatus.ACTIVE
                logger.info(f"Reactivated client account {account.id} (UUID: {client_uuid}) due to expiry extension.")
                
        # Create renewal log
        operation_type = OperationType.FULL_RENEW
        if extra_days is not None and extra_gb is None:
            operation_type = OperationType.EXTEND_TIME
        elif extra_days is None and extra_gb is not None:
            operation_type = OperationType.EXTEND_TRAFFIC
            
        log = ClientRenewalLog(
            client_account_id=account.id, # Link to client_account.id
            panel_id=account.panel_id,
            user_id=account.user_id,
            executed_by=executed_by,
            operation_type=operation_type,
            extra_days=extra_days,
            extra_gb=extra_gb,
            prev_expiry=prev_expiry_dt,
            new_expiry=new_expiry_dt_for_db,
            prev_total_gb=prev_total_gb,
            new_total_gb=new_total_gb_for_db,
            note=note,
            created_at=datetime.utcnow()
        )
        
        try:
            self.session.add(account)
            self.session.add(log)
            await self.session.commit()
            await self.session.refresh(account) # Refresh account
            await self.session.refresh(log) # Refresh log

            logger.info(f"Successfully extended client {client_uuid} and logged operation {log.id}.")

        except Exception as db_err:
            logger.error(f"Database error during client extension for UUID {client_uuid}: {db_err}")
            # Consider rollback or logging inconsistency
            raise Exception(f"Database error during client extension: {db_err}")
        
        return {
            "client_uuid": client_uuid,
            "new_expiry_time": new_expiry_ms, # Return ms timestamp
            "new_total_gb": new_total_gb_for_db, # Return GB
            "status": account.status.value
        } 