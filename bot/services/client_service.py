"""
ClientAccount Service

This module provides a service layer for managing clients,
including client creation, updating, and proxying operations to panels.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import uuid
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from core.database import get_db_session
from core.config import settings
from .panel_service import PanelService, SelectionStrategy
from core.exceptions import NotFoundError, ServiceError, InsufficientBalanceError, ConfigurationError
from core.database.models import ClientAccount, User, Plan, Panel, PanelInbound, Location
from core.database.models.client_account import ClientStatus # مطمئن شید ClientStatus اینجا یا در __init__ مدل‌ها export شده

# Import necessary repositories
from core.database.repositories import (
    ClientAccountRepository,
    LocationRepository,
    PanelRepository,
    PlanRepository,
    UserRepository,
    SettingRepository,
)

logger = logging.getLogger(__name__)


class ClientService:
    """Service for managing clients.
    
    This service provides methods for:
    - ClientAccount creation and management (CRUD operations)
    - ClientAccount traffic management
    - Proxying operations to panels via PanelService
    """
    
    def __init__(self, db: AsyncSession, panel_service: PanelService):
        """Initialize client service.
        
        Args:
            db: Active database session.
            panel_service: Configured PanelService instance.
        """
        if db is None:
            raise ConfigurationError("Database session (db) is required for ClientService")
        if panel_service is None:
            raise ConfigurationError("PanelService instance is required for ClientService")

        self.db = db
        self.panel_service = panel_service
        # Instantiate repositories with the provided session
        self.client_repo = ClientAccountRepository(self.db)
        self.location_repo = LocationRepository(self.db)
        self.panel_repo = PanelRepository(self.db)
        self.plan_repo = PlanRepository(self.db)
        self.user_repo = UserRepository(self.db)
        self.setting_repo = SettingRepository(self.db) # Need SettingRepository for settings
    
    async def create_client(self, client_data: Dict[str, Any]) -> ClientAccount:
        """Create a new client in the database and on the panel.
        
        Args:
            client_data: ClientAccount data including user_id, plan_id, location_id, protocol, etc.
            
        Returns:
            ClientAccount: Created client object (uncommitted).
            
        Raises:
            NotFoundError: If user, plan, location, or a suitable panel is not found.
            ServiceError: If panel interaction fails or configuration is missing.
            ConfigurationError: If essential settings are missing.
        """
        location_id = client_data.get("location_id")
        plan_id = client_data.get("plan_id")
        user_id = client_data.get("user_id")

        # Fetch related entities using repositories
        location = await self.location_repo.get_by_id(location_id)
        if not location:
            raise NotFoundError(f"Location با شناسه {location_id} پیدا نشد.")

        plan = await self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise NotFoundError(f"پلن با شناسه {plan_id} پیدا نشد.")

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"کاربر با شناسه {user_id} پیدا نشد.")

        # Select an appropriate panel for this client (delegated to PanelService)
        # PanelService now needs the session
        panel = await self.panel_service.select_panel_for_location(location_id, strategy=SelectionStrategy.ROUND_ROBIN) # Or other strategy
        if not panel:
            raise NotFoundError(f"هیچ پنل فعالی برای لوکیشن {location.name} پیدا نشد.")

        # Generate UUID for the client
        client_uuid = client_data.get("client_uuid", str(uuid.uuid4()))

        # Generate remark using the appropriate pattern
        # This logic might be better placed within a dedicated utility or helper function
        # Fetch settings using SettingRepository
        settings_map = await self.setting_repo.get_settings_map()
        use_new_prefix_key = f"USE_NEW_PREFIX_FOR_{location.name}" # Potential issue: Location name might contain characters not suitable for env var names
        use_new_prefix = settings_map.get(use_new_prefix_key, "true").lower() == "true"

        if use_new_prefix:
            remark = await self._generate_remark(location, user, None, client_data.get("custom_name"))
        else:
            old_prefix = location.default_remark_prefix or location.name
            sequence = await self._get_next_client_id(location_id) # This needs repo access now
            remark = f"{old_prefix}-{sequence}"
            if client_data.get("custom_name"):
                remark = f"{remark}-{client_data.get('custom_name')}"

        # Calculate expiry date based on plan
        now = datetime.now()
        expire_date = now + timedelta(days=plan.days)

        # Create client object (without committing yet)
        client = ClientAccount(
            user_id=user_id,
            panel_id=panel.id,
            location_id=location_id,
            plan_id=plan_id,
            order_id=client_data.get("order_id"),
            client_uuid=client_uuid,
            email=f"{remark}@moonvpn.com", # Email based on remark for uniqueness
            remark=remark,
            expire_date=expire_date,
            traffic_limit_gb=plan.traffic_gb, # Assuming model uses traffic_limit_gb
            used_traffic_bytes=0, # Assuming model uses used_traffic_bytes
            status=ClientStatus.ACTIVE, # Use Enum value
            protocol=client_data.get("protocol", "vmess"),
            is_trial=client_data.get("is_trial", False),
            created_at=now
            # panel_native_identifier will be set after panel creation
        )

        # Add to session but DO NOT commit here
        self.db.add(client)
        await self.db.flush() # Flush to get the client ID if needed, but keep transaction open

        # Now create the client on the panel using PanelService
        panel_client_data = {
            "uuid": client_uuid,
            "email": client.email,
            "remark": remark,
            "enable": True,
            "totalGB": plan.traffic_gb * (1024**3), # Convert GB to Bytes for panel API
            "expiryTime": int(expire_date.timestamp() * 1000), # Panel might expect milliseconds
            # Add other necessary fields based on PanelService/xui_client requirements
            # e.g., "limitIp", "alterId" might depend on protocol/plan
            "limitIp": client_data.get("limit_ip", 0), # Example
            "flow": plan.flow or "", # Example, check actual Plan model and Panel API
        }

        # Determine inbound ID
        inbound_id = client_data.get("inbound_id", location.default_inbound_id)
        if not inbound_id:
            # PanelService should ideally handle finding a suitable inbound if not specified
            try:
                inbounds = await self.panel_service.get_panel_inbounds_by_panel_id(panel.id) # Assuming PanelService has this
                if inbounds:
                    # Simple strategy: pick the first one. More complex logic might be needed.
                    inbound_id = inbounds[0].id # Get the database ID of the inbound
                else:
                    raise ServiceError(f"هیچ ورودی (inbound) روی پنل {panel.name} برای لوکیشن {location.name} یافت نشد.")
            except Exception as e: # Catch potential PanelService errors
                 logger.error(f"Error fetching inbounds for panel {panel.id}: {e}")
                 raise ServiceError(f"خطا در یافتن ورودی (inbound) برای پنل {panel.name}.")

        if not inbound_id:
             raise ConfigurationError(f"شناسه ورودی (inbound) برای لوکیشن {location.name} مشخص نشده و هیچ ورودی پیش‌فرضی یافت نشد.")


        try:
            # PanelService handles the actual API call and potential errors
            # PanelService.add_client should return the native identifier
            panel_result = await self.panel_service.add_client_to_panel(
                panel_id=panel.id,
                inbound_id=inbound_id, # Use the determined inbound_id
                client_settings=panel_client_data
            )

            # --- IMPORTANT ---
            # Store the panel_native_identifier and subscription_url returned by PanelService
            if panel_result and isinstance(panel_result, dict):
                 client.panel_native_identifier = panel_result.get("native_identifier")
                 client.subscription_url = panel_result.get("subscription_url")
                 # Update other fields if necessary from panel_result
            else:
                 # Handle cases where panel creation might succeed but doesn't return expected data
                 logger.warning(f"Panel client creation for {remark} might have succeeded but returned unexpected data: {panel_result}")
                 # Decide if this is critical - perhaps raise an error?
                 # For now, log a warning. If native_identifier is missing, subsequent updates will fail.
                 raise ServiceError(f"ایجاد کاربر روی پنل {panel.name} موفق بود اما شناسه لازم بازگردانده نشد.")

            if not client.panel_native_identifier:
                 logger.error(f"Panel native identifier was not set for client {remark} after panel creation.")
                 # This IS critical because we can't manage the client later
                 raise ServiceError(f"ایجاد کاربر روی پنل {panel.name} موفق بود اما شناسه لازم برای مدیریت بعدی دریافت نشد.")

            # No commit here - let the caller handle the transaction
            # await self.db.commit() # REMOVED
            # await self.db.refresh(client) # REMOVED (caller should refresh if needed after commit)

        except (ServiceError, ConfigurationError, NotFoundError) as e:
            # Specific errors from PanelService or earlier steps
            logger.error(f"Error during client creation ({remark}) panel step: {e}")
            # No rollback needed here, caller handles transaction
            raise e # Re-raise the specific error
        except Exception as e:
            # Catch unexpected errors during panel interaction
            logger.exception(f"Unexpected error creating client {remark} on panel {panel.id}: {e}")
            # No rollback needed here, caller handles transaction
            raise ServiceError(f"خطای پیش‌بینی نشده در هنگام ایجاد کاربر روی پنل: {e}")

        return client # Return the populated ClientAccount object (still needs commit by caller)
    
    async def get_client(self, client_id: int) -> Optional[ClientAccount]:
        """Get a client by ID using the repository.
        
        Args:
            client_id: ClientAccount ID
            
        Returns:
            Optional[ClientAccount]: ClientAccount if found, None otherwise
        """
        # Use the repository to get the client with necessary relationships loaded
        return await self.client_repo.get_by_id_with_relations(
            client_id,
            relations=[
                ClientAccount.user,
                ClientAccount.panel,
                ClientAccount.location,
                ClientAccount.plan
            ]
        )
    
    async def get_client_by_remark(self, remark: str) -> Optional[ClientAccount]:
        """Get a client by remark using the repository.
        
        Args:
            remark: ClientAccount remark
            
        Returns:
            Optional[ClientAccount]: ClientAccount if found, None otherwise
        """
        # Use the repository to find the client by remark with relationships
        return await self.client_repo.find_by_remark_with_relations(
            remark,
            relations=[
                ClientAccount.user,
                ClientAccount.panel,
                ClientAccount.location,
                ClientAccount.plan
            ]
        )
    
    async def get_client_config(self, client_id: int) -> Dict[str, Any]:
        """Get client configuration details including connection information.
        
        Args:
            client_id: ClientAccount ID
            
        Returns:
            Dict[str, Any]: ClientAccount configuration
            
        Raises:
            NotFoundError: If client is not found.
            ServiceError: If panel interaction fails.
        """
        client = await self.client_repo.get_by_id_with_relations(
            client_id, 
            relations=[ClientAccount.panel, ClientAccount.location, ClientAccount.inbound]
        )
        if not client:
            raise NotFoundError(f"Client with ID {client_id} not found")

        # Delegate fetching detailed config from panel to PanelService
        try:
            panel_config = await self.panel_service.get_client_config_from_panel(
                panel_id=client.panel_id,
                client_identifier=client.panel_native_identifier,
                protocol=client.protocol.value, # ارسال پروتکل به صورت رشته (نه Enum)
                inbound_id=client.inbound_id
            )
        except Exception as e:
             logger.error(f"Failed to get panel config for client {client_id} (remark: {client.remark}): {e}")
             raise ServiceError(f"Failed to retrieve configuration from panel for client {client.remark}")

        # Combine DB data with panel data
        config = {
            "id": client.id,
            "remark": client.remark,
            "protocol": client.protocol.value,
            "expire_date": client.expire_date.isoformat() if client.expire_date else None,
            "traffic_limit_gb": client.traffic_limit_gb,
            "used_traffic_gb": round(client.used_traffic_bytes / (1024**3), 2) if client.used_traffic_bytes else 0,
            "status": client.status.value if client.status else None,
            "location": client.location.name if client.location else None,
            "subscription_url": client.subscription_url,
            "panel_config": panel_config
        }
        return config
    
    async def update_client_status(self, client_id: int, status: ClientStatus) -> Optional[ClientAccount]:
        """Updates the client status in DB and on the panel.
        
        Args:
            client_id: The ID of the client to update.
            status: The new status (ClientStatus Enum).
            
        Returns:
            The updated ClientAccount object (uncommitted), or None if not found.
            
        Raises:
            NotFoundError: If the client is not found.
            ServiceError: If updating the client on the panel fails.
        """
        client = await self.client_repo.get_by_id_with_relations(client_id, relations=[ClientAccount.panel, ClientAccount.inbound])
        if not client:
            raise NotFoundError(f"Client with ID {client_id} not found.")

        if not client.panel_native_identifier:
             logger.error(f"Cannot update status on panel for client {client_id}: missing panel_native_identifier.")
             raise ConfigurationError(f"Cannot manage client {client.remark} on panel: missing native identifier.")

        old_status = client.status
        client.status = status
        self.db.add(client) # Add to session for update tracking
        await self.db.flush() # Keep transaction open

        # Determine panel action based on status change
        enable_on_panel = status == ClientStatus.ACTIVE

        try:
            await self.panel_service.update_client_on_panel(
                panel_id=client.panel_id,
                client_identifier=client.panel_native_identifier,
                protocol=client.protocol.value, # استفاده از پروتکل کلاینت به صورت رشته
                inbound_id=client.inbound_id, # استفاده از inbound_id کلاینت
                updates={"enable": enable_on_panel},
                reset_traffic=False
            )
            logger.info(f"Client {client_id} ({client.remark}) status updated to {status} in DB and panel (enabled={enable_on_panel}).")
        except Exception as e:
            # Log the error but potentially proceed with DB update? Or raise?
            # For consistency, let's raise an error if panel update fails.
            logger.error(f"Failed to update client {client_id} ({client.remark}) status on panel {client.panel_id}: {e}")
            # No rollback here, caller handles transaction
            raise ServiceError(f"Failed to update client status on panel: {e}")

        return client # Return updated object (needs commit by caller)

    async def _get_location(self, location_id: int) -> Optional[Location]:
        """Helper to get location using repository (kept for internal use for now)."""
        return await self.location_repo.get_by_id(location_id)
    
    async def _get_plan(self, plan_id: int) -> Optional[Plan]:
         """Helper to get plan using repository (kept for internal use for now)."""
         return await self.plan_repo.get_by_id(plan_id)
    
    async def _get_user(self, user_id: int) -> Optional[User]:
         """Helper to get user using repository (kept for internal use for now)."""
         return await self.user_repo.get_by_id(user_id)
    
    async def _select_panel_for_client(self, location_id: int) -> Optional[Panel]:
        """Selects a suitable panel for a given location.
        
        This is now primarily handled by PanelService, but keeping a simplified
        version here for reference or potential direct use if needed later.
        Uses PanelRepository directly.
        
        Args:
            location_id: The ID of the location.
            
        Returns:
            Optional[Panel]: An active panel associated with the location, or None.
            
        Raises:
             ServiceError: If multiple panels found without clear selection logic (should use PanelService).
             NotFoundError: If no active panel found for the location.
        """
        # Ideally, this logic should live solely within PanelService.
        # Using PanelRepository directly here for demonstration of repo usage.
        active_panels = await self.panel_repo.find_active_by_location(location_id)

        if not active_panels:
             logger.warning(f"No active panel found for location_id {location_id}")
             return None # Or raise NotFoundError("No active panel found...")

        if len(active_panels) > 1:
             logger.warning(f"Multiple active panels found for location {location_id}. Using the first one. Consider using PanelService for specific selection strategy.")
             # Raise ServiceError("Multiple active panels found, use PanelService for specific strategy.") ?

        return active_panels[0] # Simplistic: return the first active panel
    
    async def _generate_remark(self, location: Location, user: User,
                             sequence: Optional[int] = None,
                             custom_name: Optional[str] = None) -> str:
        """Generates a client remark based on location, user, and settings."""
        # This method now uses injected location/user objects
        # Needs access to SettingRepository if settings logic remains complex,
        # but basic prefix logic is fine as is.
        settings_map = await self.setting_repo.get_settings_map()
        use_new_prefix_key = f"USE_NEW_PREFIX_FOR_{location.name}" # Still has potential issue with special chars in name
        use_new_prefix = settings_map.get(use_new_prefix_key, "true").lower() == "true"

        if use_new_prefix:
            # Using new prefix logic (example: UserID-LocationTag-CustomName)
            # This requires a defined standard for the new remark format
            prefix = f"{user.id}-{location.short_name or location.name[:3].upper()}"
            if custom_name:
                return f"{prefix}-{custom_name}"
            return prefix
        else:
            # Keep using old prefix for compatibility (LocationPrefix-Sequence-CustomName)
            old_prefix = location.default_remark_prefix or location.name
            if sequence is None:
                 # If sequence wasn't pre-fetched (e.g., because use_new_prefix was true initially)
                 sequence = await self._get_next_client_id(location.id)

            remark_base = f"{old_prefix}-{sequence}"
            if custom_name:
                return f"{remark_base}-{custom_name}"
            return remark_base


    async def _get_next_client_id(self, location_id: int) -> int:
        """Gets the next sequence number for client remarks for a location."""
        # This method now needs to use the ClientAccountRepository
        # It might involve a count query or a dedicated sequence table/mechanism

        # Example using count (might be slow on large tables without good indexing)
        # Consider a dedicated sequence generator or atomic counter if performance is critical
        count = await self.client_repo.count_by_location(location_id)
        return count + 1 # Simple increment based on existing clients for that location

    async def sync_client_usage(self, client_id: int) -> Optional[ClientAccount]:
        """Fetches usage from the panel and updates the local DB record."""
        logger.debug(f"Syncing usage for client {client_id}")
        client = await self.client_repo.get_with_panel(client_id)
        if not client: raise NotFoundError(f"ClientAccount {client_id} not found.")
        if client.status != ClientStatus.ACTIVE: # Only sync active clients?
            logger.debug(f"Skipping usage sync for non-active client {client_id} (status: {client.status})")
            return client

        try:
            # PanelService should provide a method to get usage
            usage_data = await self.panel_service.get_client_usage_from_panel(
                panel_id=client.panel_id,
                client_identifier=client.panel_client_email # Assuming email identifier
            )

            if usage_data:
                up = usage_data.get("up", 0)
                down = usage_data.get("down", 0)
                total_used_bytes = up + down
                logger.debug(f"Panel usage for {client.panel_client_email}: Up={up}, Down={down}, Total={total_used_bytes}")

                # Update only if usage has changed significantly?
                if client.used_traffic_bytes != total_used_bytes:
                    updated_client = await self.client_repo.update(
                        client_id,
                        used_traffic_bytes=total_used_bytes,
                        updated_at=datetime.utcnow()
                    )
                    await self.db.commit()
                    logger.info(f"Updated DB usage for client {client_id} to {total_used_bytes} bytes.")
                    return updated_client
                else:
                    logger.debug(f"DB usage for client {client_id} is already up-to-date.")
                    return client
            else:
                logger.warning(f"No usage data returned from panel for client {client_id}")
                return client # Return current state

        except (PanelAPIError, PanelAuthenticationError, ServiceError) as e:
            logger.error(f"Panel error syncing usage for client {client_id}: {e}")
            # Don't raise, just log and return current state
            return client
        except Exception as e:
            logger.exception(f"Unexpected error syncing usage for client {client_id}")
            return client

    async def renew_client(self, client_id: int) -> Optional[ClientAccount]:
        """Renews an existing client's subscription."""
        logger.info(f"Renewing client {client_id}")
        client = await self.client_repo.get_with_relations(client_id)
        if not client: raise NotFoundError(f"ClientAccount {client_id} not found.")
        if not client.user: raise ServiceError(f"ClientAccount {client_id} has no associated user.")
        if not client.plan: raise ServiceError(f"ClientAccount {client_id} has no associated plan.")

        # TODO: Check user balance
        # if client.plan.price > 0 and (client.user.balance is None or client.user.balance < client.plan.price):
        #     raise InsufficientBalanceError(f"User {client.user_id} insufficient balance for renewal.")

        # Calculate new expiry date
        now = datetime.utcnow()
        current_expiry = client.expire_date or now # Use now if no expiry exists
        start_date = max(now, current_expiry) # Renewal starts from now or current expiry, whichever is later
        new_expiry_date = start_date + timedelta(days=client.plan.duration_days)

        # Reset traffic (convert GB to bytes)
        new_traffic_limit_bytes = client.plan.traffic_gb * (1024**3) if client.plan.traffic_gb else 0

        # --- Update Panel --- #
        update_payload = {
            "enable": True,
            "totalGB": client.plan.traffic_gb or 0,
            "expireTime": int(new_expiry_date.timestamp() * 1000), # Milliseconds for XUI
            # Potentially reset traffic on panel too if API allows
        }
        try:
            # Pass db to update_client_on_panel
            panel_updated = await self.panel_service.update_client_on_panel( 
                panel_id=client.panel_id,
                client_identifier=client.panel_client_email, # Assuming email identifier
                updates=update_payload,
                reset_traffic=True # Add flag to panel service method
            )
            if not panel_updated:
                logger.warning(f"Panel update/reset might have failed for client {client_id} renewal.")
                # Decide handling: proceed or raise?
        except (PanelAPIError, PanelAuthenticationError, ServiceError) as e:
            logger.error(f"Panel error during renewal for client {client_id}: {e}")
            raise ServiceError(f"Panel communication failed during renewal: {e}")
        except Exception as e:
            logger.exception(f"Unexpected panel error during renewal for client {client_id}")
            raise ServiceError(f"Unexpected panel error during renewal: {e}")

        # --- Update Database --- #
        updated_client = await self.client_repo.update(
            client_id,
            status=ClientStatus.ACTIVE,
            expire_date=new_expiry_date,
            traffic_limit_bytes=new_traffic_limit_bytes,
            used_traffic_bytes=0, # Reset used traffic in DB
            updated_at=now
        )

        # TODO: Deduct price, add transaction
        # if client.plan.price > 0:
        #     await self.user_repo.decrease_balance(client.user_id, client.plan.price)
        #     # Add transaction record

        await self.db.commit()
        logger.info(f"ClientAccount {client_id} renewed successfully. New expiry: {new_expiry_date}")
        return updated_client

    async def reset_client_traffic(self, client_id: int) -> ClientAccount:
        """Resets the client's traffic usage on the panel and in the database.

        Assumes caller handles transaction commit.

        Args:
            client_id: The ID of the client to reset traffic for.

        Returns:
            The updated ClientAccount object (uncommitted).

        Raises:
            NotFoundError: If the client is not found.
            ConfigurationError: If the client is missing the panel native identifier.
            ServiceError: If communication with the panel fails.
        """
        logger.info(f"Attempting to reset traffic for client {client_id}")
        client = await self.client_repo.get_by_id_with_relations(
            client_id, 
            relations=[ClientAccount.panel, ClientAccount.inbound]
        )
        if not client:
            raise NotFoundError(f"ClientAccount {client_id} not found for traffic reset.")
        if not client.panel_native_identifier:
             logger.error(f"Cannot reset traffic for client {client_id} on panel: missing panel_native_identifier.")
             raise ConfigurationError(f"Cannot manage client {client.remark} on panel: missing native identifier.")

        try:
            # Ask PanelService to reset traffic. This might be part of update_client or a separate call.
            # Assuming update_client_on_panel can handle it via reset_traffic=True flag
            await self.panel_service.update_client_on_panel(
                panel_id=client.panel_id,
                client_identifier=client.panel_native_identifier,
                protocol=client.protocol.value, # استفاده از پروتکل کلاینت به صورت رشته
                inbound_id=client.inbound_id, # استفاده از inbound_id کلاینت
                updates={}, # No other updates needed, just reset
                reset_traffic=True
            )
            logger.info(f"Panel traffic reset successful for client {client_id}.")
        except (ServiceError, ConfigurationError, NotFoundError) as e:
            logger.error(f"Panel error resetting traffic for client {client_id}: {e}")
            raise e
        except Exception as e:
            logger.exception(f"Unexpected panel error resetting traffic for client {client_id}")
            raise ServiceError(f"Unexpected panel error resetting traffic for client {client.remark}: {e}")

        # Update Database
        client.used_traffic_bytes = 0
        # Optionally reactivate if disabled due to traffic
        if client.status == ClientStatus.DISABLED_TRAFFIC:
             logger.info(f"Reactivating client {client_id} after traffic reset.")
             client.status = ClientStatus.ACTIVE
             # We might need to update panel status again if reset didn't automatically enable
             try:
                 await self.panel_service.update_client_on_panel(
                     panel_id=client.panel_id,
                     client_identifier=client.panel_native_identifier,
                     protocol=client.protocol.value, # استفاده از پروتکل کلاینت به صورت رشته
                     inbound_id=client.inbound_id, # استفاده از inbound_id کلاینت
                     updates={"enable": True} # Ensure enabled
                 )
             except Exception as e:
                 logger.error(f"Failed to ensure client {client_id} is enabled on panel after traffic reset: {e}")
                 # Log error but proceed with DB update

        client.updated_at = datetime.now()
        self.db.add(client)
        await self.db.flush()

        logger.info(f"ClientAccount {client_id} traffic reset successfully in DB (uncommitted).")
        return client

    # --- Placeholder for change_location ---
    async def change_location(self, client_id: int, new_location_id: int,
                              reason: Optional[str] = None,
                              performed_by: Optional[int] = None,
                              force: bool = False) -> ClientAccount:
         """Changes the client's location, migrating it to a new panel.

         This is a complex operation that:
         1. Validates the client and locations
         2. Checks change limits (unless forced)
         3. Selects a new panel in the new location
         4. Creates the client on the new panel
         5. Deletes the client from the old panel
         6. Updates the client record and migration history in the DB

         Args:
             client_id: ID of the client to migrate.
             new_location_id: ID of the target location.
             reason: Optional reason for the change.
             performed_by: Optional ID of the user performing the change.
             force: If True, ignore daily change limits.

         Returns:
             The updated ClientAccount object (uncommitted).

         Raises:
             NotFoundError: If client, location, or suitable panel not found.
             ServiceError: If panel operations fail or limits are exceeded.
             ConfigurationError: If required data is missing.
         """
         logger.info(f"Changing location for client {client_id} to location {new_location_id}")
         
         # 1. Get client with all necessary relations
         client = await self.client_repo.get_by_id_with_relations(
             client_id, 
             relations=[
                 ClientAccount.user, 
                 ClientAccount.panel, 
                 ClientAccount.location,
                 ClientAccount.plan,
                 ClientAccount.inbound
             ]
         )
         if not client:
             raise NotFoundError(f"Client with ID {client_id} not found.")
         
         # 2. Validate request
         if client.location_id == new_location_id:
             logger.warning(f"Client {client_id} is already in location {new_location_id}")
             return client
             
         # 3. Check migration limits (unless force=True)
         if not force:
             settings_map = await self.setting_repo.get_settings_map()
             max_changes_per_day = int(settings_map.get("MAX_LOCATION_CHANGES_PER_DAY", "1"))
             
             # Implement daily change limit check - This depends on your migration history implementation
             # For simplicity, we'll check the migration_count for now
             if client.migration_count and client.migration_count >= max_changes_per_day:
                 raise ServiceError(f"محدودیت تغییر لوکیشن روزانه ({max_changes_per_day}) برای این اکانت به پایان رسیده است.")
         
         # 4. Get new location
         new_location = await self.location_repo.get_by_id(new_location_id)
         if not new_location:
             raise NotFoundError(f"Location with ID {new_location_id} not found.")
         
         # 5. Select new panel
         new_panel = await self.panel_service.select_panel_for_location(
             location_id=new_location_id,
             protocol=client.protocol.value,
             exclude_panel_ids=[client.panel_id]  # Avoid selecting the same panel
         )
         if not new_panel:
             raise NotFoundError(f"No suitable panel found for location {new_location_id} and protocol {client.protocol.value}")
         
         # 6. Store old details
         old_location_id = client.location_id
         old_panel_id = client.panel_id
         old_remark = client.remark
         old_uuid = client.client_uuid
         old_native_identifier = client.panel_native_identifier
         old_inbound_id = client.inbound_id
         
         # 7. Generate new identifiers
         new_uuid = str(uuid.uuid4())
         new_remark = await self._generate_remark(new_location, client.user, None, client.custom_name)
         
         # 8. Find appropriate inbound on new panel
         # For simplicity, we'll select the first active inbound for the protocol
         inbounds = await self.panel_service.get_panel_inbounds_by_panel_id(new_panel.id) 
         suitable_inbounds = [i for i in inbounds if i.protocol.upper() == client.protocol.value.upper() and i.is_active]
         if not suitable_inbounds:
             raise NotFoundError(f"No suitable inbound found on panel {new_panel.id} for protocol {client.protocol.value}")
         
         new_inbound_id = suitable_inbounds[0].id  # Select first suitable inbound
         
         # 9. Prepare data for new panel client
         # Calculate remaining traffic and time
         now = datetime.now()
         remaining_days = (client.expire_date - now).days if client.expire_date > now else 0
         
         # If client already used some traffic, subtract from total
         total_gb = client.traffic_limit_gb
         used_gb = client.used_traffic_bytes / (1024**3) if client.used_traffic_bytes else 0
         remaining_gb = max(0, total_gb - used_gb)
         
         # Prepare panel client data
         panel_client_data = {
             "uuid": new_uuid,
             "email": f"{new_remark}@moonvpn.com",
             "remark": new_remark,
             "enable": client.status == ClientStatus.ACTIVE,
             "totalGB": int(remaining_gb * (1024**3)),  # Convert GB to Bytes for panel API
             "expiryTime": int(client.expire_date.timestamp() * 1000),  # Panel expects milliseconds
             "flow": client.plan.flow or "",  # Example, check actual Plan model
         }
         
         # 10. Create client on new panel
         try:
             new_panel_result = await self.panel_service.add_client_to_panel(
                 panel_id=new_panel.id,
                 inbound_id=new_inbound_id,
                 client_settings=panel_client_data,
                 protocol=client.protocol.value
             )
             
             if not new_panel_result or not new_panel_result.get("native_identifier"):
                 raise ServiceError("Failed to create client on new panel: no native identifier returned")
             
             new_native_identifier = new_panel_result.get("native_identifier")
             new_subscription_url = new_panel_result.get("subscription_url")
             
             # 11. Delete client from old panel
             try:
                 delete_success = await self.panel_service.delete_client_from_panel(
                     panel_id=old_panel_id,
                     inbound_id=old_inbound_id, 
                     client_identifier=old_native_identifier,
                     protocol=client.protocol.value
                 )
                 if not delete_success:
                     logger.warning(f"Failed to delete client {client_id} from old panel {old_panel_id}. "
                                    f"Manual cleanup may be needed.")
             except Exception as delete_err:
                 logger.error(f"Error deleting client from old panel: {delete_err}")
                 # Continue despite error - client is on new panel, old one will need manual cleanup
             
             # 12. Update client record in database
             # Prepare migration history as JSON
             migration_history = json.loads(client.migration_history or "[]")
             migration_history.append({
                 "timestamp": datetime.now().isoformat(),
                 "from_location_id": old_location_id,
                 "to_location_id": new_location_id,
                 "from_panel_id": old_panel_id,
                 "to_panel_id": new_panel.id,
                 "reason": reason,
                 "performed_by": performed_by,
                 "forced": force
             })
             
             # Update client object
             client.location_id = new_location_id
             client.panel_id = new_panel.id
             client.inbound_id = new_inbound_id
             client.client_uuid = new_uuid
             client.remark = new_remark
             client.email = f"{new_remark}@moonvpn.com"
             client.panel_native_identifier = new_native_identifier
             client.subscription_url = new_subscription_url
             client.previous_panel_id = old_panel_id
             client.migration_count = (client.migration_count or 0) + 1
             client.migration_history = json.dumps(migration_history)
             client.updated_at = datetime.now()
             
             # Store original details if this is first migration
             if not client.original_remark:
                 client.original_remark = old_remark
             if not client.original_client_uuid:
                 client.original_client_uuid = old_uuid
             
             self.db.add(client)
             await self.db.flush()
             
             logger.info(f"Successfully migrated client {client_id} from location {old_location_id} to {new_location_id}")
             return client
             
         except Exception as e:
             logger.exception(f"Error during location change for client {client_id}")
             raise ServiceError(f"Failed to change client location: {e}")

    # --- Periodic Tasks ---
    # These run outside the request cycle and need their own session management.
    # They should instantiate the necessary services with a session per cycle.

    async def run_periodic_usage_sync(self, interval_seconds: int = 3600):
        """Periodically syncs usage for all active clients."""
        from core.database import async_session_factory # Import factory locally

        logger.info(f"Starting periodic usage sync runner every {interval_seconds}s.")
        while True:
            await asyncio.sleep(interval_seconds)
            logger.debug("--- Starting periodic usage sync cycle ---")
            async with async_session_factory() as cycle_session:
                # Instantiate services with the cycle-specific session
                try:
                    panel_service_instance = PanelService(cycle_session)
                    client_service_instance = ClientService(cycle_session, panel_service_instance)
                    client_repo = ClientAccountRepository(cycle_session) # Use repo directly for fetching list

                    active_clients = await client_repo.get_by_status(ClientStatus.ACTIVE)
                    logger.info(f"Found {len(active_clients)} active clients to sync usage for.")

                    tasks = []
                    for client in active_clients:
                        # Call the *instance* method for each client
                        tasks.append(client_service_instance.sync_client_usage(client.id))

                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Process results and commit the session if successful tasks exist
                    successful_syncs = 0
                    error_count = 0
                    for i, result in enumerate(results):
                        client_id = active_clients[i].id
                        if isinstance(result, Exception):
                            logger.error(f"Error syncing usage for client {client_id}: {result}", exc_info=False)
                            error_count += 1
                        elif result is not None: # sync_client_usage returns the client object
                             successful_syncs += 1
                             # Further checks could be done here if needed

                    if successful_syncs > 0 or error_count > 0: # Commit if any work was attempted/done, let errors rollback implicitly
                        try:
                             await cycle_session.commit()
                             logger.debug(f"Committed usage sync changes for {successful_syncs} clients.")
                        except Exception as commit_err:
                             logger.error(f"Error committing usage sync cycle: {commit_err}", exc_info=True)
                             await cycle_session.rollback() # Explicit rollback on commit error

                    logger.debug(f"Finished usage sync cycle with {error_count} errors.")

                except Exception as cycle_err:
                    logger.error(f"Critical error in periodic usage sync cycle setup or client fetch: {cycle_err}", exc_info=True)
                    await cycle_session.rollback() # Ensure rollback on cycle error

            logger.debug("--- Finished periodic usage sync cycle ---")


    async def run_periodic_expiry_check(self, interval_seconds: int = 3600):
        """Periodically checks for expired clients and updates their status."""
        from core.database import async_session_factory # Import factory locally

        logger.info(f"Starting periodic expiry check runner every {interval_seconds}s.")
        while True:
            await asyncio.sleep(interval_seconds)
            logger.debug("--- Starting periodic expiry check cycle ---")
            async with async_session_factory() as cycle_session:
                 # Instantiate services with the cycle-specific session
                try:
                    panel_service_instance = PanelService(cycle_session)
                    client_service_instance = ClientService(cycle_session, panel_service_instance)
                    client_repo = ClientAccountRepository(cycle_session) # Use repo directly for fetching list

                    now = datetime.now() # Use aware datetime if needed
                    # Find active clients whose expiry date is in the past
                    expired_clients = await client_repo.get_expired_active_clients(now)

                    if expired_clients:
                        logger.info(f"Found {len(expired_clients)} active clients that have expired.")
                        tasks = []
                        for client in expired_clients:
                             # Call the *instance* method to update status
                             tasks.append(client_service_instance.update_client_status(client.id, ClientStatus.EXPIRED))

                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        # Process results and commit
                        successful_updates = 0
                        error_count = 0
                        for i, result in enumerate(results):
                             client_id = expired_clients[i].id
                             if isinstance(result, Exception):
                                 logger.error(f"Error setting status to EXPIRED for client {client_id}: {result}", exc_info=False)
                                 error_count += 1
                             elif result is not None: # update_client_status returns the client
                                 successful_updates += 1

                        if successful_updates > 0 or error_count > 0: # Commit if work was attempted
                            try:
                                await cycle_session.commit()
                                logger.debug(f"Committed expiry status updates for {successful_updates} clients.")
                            except Exception as commit_err:
                                logger.error(f"Error committing expiry check cycle: {commit_err}", exc_info=True)
                                await cycle_session.rollback()
                        logger.debug(f"Finished expiry check cycle with {error_count} errors.")
                    else:
                        logger.debug("No active clients found to be expired in this cycle.")

                except Exception as cycle_err:
                    logger.error(f"Critical error in periodic expiry check cycle setup or client fetch: {cycle_err}", exc_info=True)
                    await cycle_session.rollback() # Ensure rollback

            logger.debug("--- Finished periodic expiry check cycle ---")

    # TODO: Add methods for admin actions like manual status change, deletion, etc.
    # TODO: Add periodic check for traffic limit reached 