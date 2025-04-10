import logging
import asyncio
import aiohttp
import httpx
import json
import random
import string
from typing import Dict, Any, Optional, List, Tuple, Union, Sequence
from datetime import datetime, timedelta
from enum import Enum

# Imports needed for token management
import redis.asyncio as redis
from cryptography.fernet import Fernet
from core.config import settings # Changed from get_settings
from core.security import encrypt_text, decrypt_text # Corrected import path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload # Import selectinload
from core.database.models import Panel, Location, PanelInbound # Assuming PanelInbound, Client exist
from core.database.models.panel import PanelType
from core.database.repositories.panel_repository import PanelRepository
from core.database.repositories.location_repository import LocationRepository
from core.database.repositories.client_repository import ClientRepository
from core.database.repositories.setting_repository import SettingRepository
from core.database.repositories.panel_inbound_repository import PanelInboundRepository

# Import the integration client with the correct class name
from integrations.panels.xui_client import XuiPanelClient #, XUIPanelError
from integrations.panels.exceptions import PanelAuthenticationError, PanelAPIError

from core.exceptions import NotFoundError, ConfigurationError, ServiceError
from core.schemas.panel_inbound import PanelInboundCreateSchema, PanelInboundUpdate # Corrected import
from core.schemas.panel import PanelCreate, PanelUpdate # Import panel schemas

logger = logging.getLogger(__name__)

PanelConnectionInfo = Dict[str, Union[str, int]] # Expects 'url', 'username', 'password'

# --- Define Enums used by the service --- #
class SelectionStrategy(str, Enum):
    """Strategy for panel selection."""
    LEAST_LOAD = "LEAST_LOAD"
    ROUND_ROBIN = "ROUND_ROBIN"
    # BEST_HEALTH = "BEST_HEALTH" # Requires health score logic
    PRIORITY = "PRIORITY"
    BALANCED = "BALANCED" # Default, simple implementation for now

# --- Redis Connection for Token Cache --- #
_redis_pool = None

async def get_redis_connection() -> redis.Redis:
    """Get a Redis connection from the connection pool for panel token caching."""
    global _redis_pool
    if _redis_pool is None:
        logger.info(f"Initializing Redis connection pool for panel tokens at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        _redis_pool = redis.ConnectionPool.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS
        )
    return redis.Redis(connection_pool=_redis_pool)

class PanelService:
    """
    Service for managing Panels in DB, syncing Inbounds, checking health,
    and selecting panels for client placement.
    Assumes commit/rollback is handled by the caller unless otherwise specified (e.g., periodic tasks).
    """
    DEFAULT_SESSION_TTL_SECONDS = 6 * 3600

    def __init__(self, db: AsyncSession):
        """Initializes repositories with the provided session and the HTTP client."""
        if db is None:
            raise ConfigurationError("Database session (db) is required for PanelService")
        self.db = db
        # Instantiate repositories - don't pass session to them 
        self.panel_repo = PanelRepository()
        self.panel_inbound_repo = PanelInboundRepository()
        self.client_account_repo = ClientRepository()
        self.location_repo = LocationRepository()
        self.setting_repo = SettingRepository()
        # HTTP client remains independent of the session for now
        self.http_client = httpx.AsyncClient(timeout=settings.PANEL_API_TIMEOUT)
        self.TOKEN_CACHE_PREFIX = f"{settings.CACHE_KEY_PREFIX}:panel_session:"
        logger.debug(f"PanelService initialized with session {db}. TOKEN_CACHE_PREFIX set to: {self.TOKEN_CACHE_PREFIX}")
        # Pass repositories to the helper
        self._selector = _PanelSelectorHelper(self.panel_repo, self.client_account_repo, self.setting_repo)

    async def get_all_panels(self, skip: int = 0, limit: int = 100) -> Sequence[Panel]:
        """Gets all panels with pagination, eager loading the location."""
        logger.debug("Fetching all panels with location")
        return await self.panel_repo.get_all_with_location(self.db, skip=skip, limit=limit)

    async def get_active_panels(self, eager_load_location: bool = False) -> Sequence[Panel]:
        logger.debug("Fetching active panels")
        return await self.panel_repo.get_active_panels(self.db, eager_load_location=eager_load_location)

    async def get_panel_by_id(self, panel_id: int, eager_load_location: bool = False) -> Optional[Panel]:
        logger.debug(f"Fetching panel with id={panel_id}")
        options = [selectinload(Panel.location)] if eager_load_location else []
        return await self.panel_repo.get(self.db, id=panel_id, options=options)

    async def create_panel(self, panel_in: PanelCreate) -> Panel:
        """Creates a new panel. Assumes commit by caller."""
        logger.info(f"Attempting to create new panel: {panel_in.name} ({panel_in.url})")
        # Use self.db for repository calls
        location = await self.location_repo.get(self.db, id=panel_in.location_id)
        if not location: raise NotFoundError(f"Location with id={panel_in.location_id} not found.")
        existing_panel = await self.panel_repo.get_by_url(self.db, url=panel_in.url)
        if existing_panel: raise ValueError(f"Panel with URL '{panel_in.url}' already exists.")
        try:
            encrypted_username = encrypt_text(panel_in.username.encode())
            encrypted_password = encrypt_text(panel_in.password.encode())
            if not encrypted_username or not encrypted_password: raise ConfigurationError("SECRET_KEY missing/invalid.")
        except Exception as e: raise ServiceError(f"Failed to encrypt credentials: {e}")

        panel_data_for_repo = panel_in.model_dump(exclude={'username', 'password'}) # Exclude plain text
        panel_data_for_repo['username'] = encrypted_username
        panel_data_for_repo['password'] = encrypted_password
        panel_data_for_repo['is_healthy'] = None # Start as None

        created_panel = await self.panel_repo.create(self.db, obj_in=panel_data_for_repo)
        # NO COMMIT HERE - Handled by caller
        logger.info(f"Panel '{created_panel.name}' added to session with ID: {created_panel.id}")
        return created_panel

    async def update_panel(self, panel_id: int, panel_in: PanelUpdate) -> Optional[Panel]:
        """Updates an existing panel. Assumes commit by caller."""
        logger.info(f"Updating panel id={panel_id}")
        # Use self.db for repository calls
        panel_to_update = await self.panel_repo.get(self.db, id=panel_id)
        if not panel_to_update: return None

        update_data = panel_in.model_dump(exclude_unset=True)

        if 'url' in update_data and update_data['url'] != panel_to_update.url:
            existing = await self.panel_repo.get_by_url(self.db, url=update_data['url'])
            if existing: raise ValueError(f"Panel with URL '{update_data['url']}' already exists.")

        if 'location_id' in update_data:
            location = await self.location_repo.get(self.db, id=update_data['location_id'])
            if not location: raise NotFoundError(f"Location id={update_data['location_id']} not found.")

        if 'username' in update_data:
            try: update_data['username'] = encrypt_text(update_data['username'].encode())
            except Exception as e: raise ServiceError(f"Encrypt username failed: {e}")
        if 'password' in update_data:
            try: update_data['password'] = encrypt_text(update_data['password'].encode())
            except Exception as e: raise ServiceError(f"Encrypt password failed: {e}")

        if not update_data: return panel_to_update

        # Correct call to repository update using self.db
        updated_panel = await self.panel_repo.update(self.db, db_obj=panel_to_update, obj_in=update_data)
        # NO COMMIT HERE - Handled by caller
        logger.info(f"Panel id={panel_id} marked for update in session.")
        return updated_panel

    async def delete_panel(self, panel_id: int) -> Optional[Panel]:
        """Marks a panel for deletion. Assumes commit by caller. Raises ServiceError if active clients exist."""
        logger.info(f"Attempting to delete panel id={panel_id}")
        # Use self.db for repository calls
        active_client_count = await self.client_account_repo.count_active_clients_on_panel(self.db, panel_id=panel_id)
        if active_client_count > 0:
            error_msg = f"Panel ID {panel_id} cannot be deleted: {active_client_count} active client(s) found."
            logger.warning(error_msg)
            raise ServiceError(error_msg)

        # BaseRepo.delete now returns the object marked for deletion or None, use self.db
        deleted_panel = await self.panel_repo.delete(self.db, id=panel_id)

        if deleted_panel:
            # NO COMMIT HERE - Handled by caller
            logger.info(f"Successfully marked panel ID {panel_id} ({deleted_panel.name}) for deletion.")
            # Clear cache AFTER successful commit (should be done by caller ideally, but ok here for now)
            try:
                redis_conn = await get_redis_connection()
                cache_key = f"{self.TOKEN_CACHE_PREFIX}{panel_id}"
                await redis_conn.delete(cache_key)
                logger.info(f"Cleared cached session token for deleted panel ID {panel_id}.")
            except Exception as redis_err:
                logger.error(f"Failed to clear cached token for panel ID {panel_id}: {redis_err}", exc_info=True)
            return deleted_panel # Return the object that was marked for deletion
        else:
            logger.warning(f"Panel ID {panel_id} not found for deletion.")
            return None

    async def select_panel_for_location( # Renamed from select_panel_for_client for clarity
        self,
        location_id: int,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        protocol: Optional[str] = None,
        is_premium_required: bool = False,
        exclude_panel_ids: Optional[List[int]] = None
    ) -> Optional[Panel]:
        """Selects the most suitable panel using the helper (uses self.db)."""
        return await self._selector.select_panel(
            self.db, location_id, strategy, protocol, is_premium_required, exclude_panel_ids
        )

    # --- Health Check Logic (uses self.db) ---
    async def check_panel_health(self, panel_id: int) -> Tuple[bool, str]:
        """ Checks panel health and updates status in the session (uses self.db, without commit). Returns (health_status, error_message). """
        # Uses self.db for panel_repo call
        panel = await self.panel_repo.get(self.db, id=panel_id)
        if not panel or not panel.is_active:
            msg = f"Skipping health check for inactive/non-existent panel_id={panel_id}"
            logger.warning(msg)
            return False, msg

        logger.debug(f"Checking health for panel: {panel.name} (ID: {panel.id}, URL: {panel.url})")
        current_health_status = panel.is_healthy
        new_health_status = False
        error_message = ""

        try:
            try:
                username = decrypt_text(panel.username).decode()
                password = decrypt_text(panel.password).decode()
                if not username or not password: raise ServiceError("Decrypted credentials are empty.")
            except Exception as decrypt_err: raise ServiceError(f"Credential decryption failed: {decrypt_err}")

            if panel.panel_type == PanelType.XUI:
                client = XuiPanelClient(base_url=panel.url, username=username, password=password, panel_id=panel.id, http_client=self.http_client)
                await client.login() # Check login
                # Optionally, perform another lightweight check like fetching system status
                new_health_status = True
                logger.info(f"✅ Panel {panel.name} (ID: {panel.id}) health check successful.")
            else:
                error_message = f"Health check not implemented for panel type: {panel.panel_type}"
                logger.warning(error_message)

        except PanelAuthenticationError as e:
            error_message = f"Panel Authentication Error: {e}"
            logger.error(f"Authentication failed for panel {panel.name} (ID: {panel.id}): {e}")
        except PanelAPIError as e:
            error_message = f"Panel Connection/API Error: {e}"
            logger.error(f"Connection/API error for panel {panel.name} (ID: {panel.id}): {e}")
        except ServiceError as e:
            error_message = str(e)
            logger.error(f"Service error during health check for panel {panel.name} (ID: {panel.id}): {e}")
        except Exception as e:
            error_message = f"Unexpected Error during health check: {type(e).__name__}: {e}"
            logger.exception(f"Unexpected error during health check for panel {panel.name} (ID: {panel.id})")

        # Update panel health status in session (no commit)
        if panel.is_healthy != new_health_status:
            panel.is_healthy = new_health_status
            panel.updated_at = datetime.now() # Or utcnow()
            panel.last_checked = datetime.now() # Or utcnow()
            self.db.add(panel) # Add to session for update tracking
            await self.db.flush() # Keep transaction open
            logger.info(f"Panel {panel.name} (ID: {panel.id}) health status updated to {new_health_status} in session.")
        else:
            # Even if health status didn't change, update last_checked time
            panel.last_checked = datetime.now() # Or utcnow()
            self.db.add(panel)
            await self.db.flush()
            logger.debug(f"Panel {panel.name} (ID: {panel.id}) health status remains {current_health_status}. Updated last_checked time.")

        return new_health_status, error_message

    async def run_periodic_health_checks(self, session_factory: async_sessionmaker[AsyncSession], interval_seconds: int = 300):
        """ Periodically checks health of all active panels. Manages its own session per cycle. """
        logger.info(f"Starting periodic panel health check runner every {interval_seconds}s.")
        while True:
            await asyncio.sleep(interval_seconds)
            logger.debug("--- Starting periodic health check cycle ---")
            panels_to_check = []
            async with session_factory() as cycle_session:
                # Instantiate service with this cycle's session
                panel_service_instance = PanelService(cycle_session)
                try:
                    # Get active panels using the instance's method (which uses instance's session)
                    panels_to_check = await panel_service_instance.get_active_panels()
                    if not panels_to_check:
                        logger.debug("No active panels found to check health for.")
                        continue # Skip to next interval

                    logger.info(f"Found {len(panels_to_check)} active panels to check health for.")
                    tasks = [panel_service_instance.check_panel_health(panel.id) for panel in panels_to_check]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Process results and commit changes within the cycle session
                    successful_updates = 0
                    error_count = 0
                    needs_commit = False
                    for i, result in enumerate(results):
                        panel_id = panels_to_check[i].id
                        panel_name = panels_to_check[i].name
                        if isinstance(result, Exception):
                            logger.error(f"Error checking health for panel {panel_name} (ID: {panel_id}): {result}", exc_info=False)
                            # Optionally try to set health to False if error occurred?
                            # panel_service_instance.update_panel_health(panel_id, False, str(result)) # Needs this method
                            error_count += 1
                        elif isinstance(result, tuple):
                             # check_panel_health already updates the status in the session
                             health_status, error_msg = result
                             # Log if status changed or an error message exists
                             if error_msg:
                                 logger.warning(f"Health check for {panel_name} (ID: {panel_id}) completed with message: {error_msg}")
                             # Check if the internal update happened (flush() was called)
                             if panel_service_instance.db.is_modified(panels_to_check[i]): # Check if object is dirty
                                 needs_commit = True
                                 successful_updates += 1 # Count potentially updated panels

                    if needs_commit:
                        try:
                             await cycle_session.commit()
                             logger.info(f"Committed health status updates for {successful_updates} panels.")
                        except Exception as commit_err:
                             logger.error(f"Error committing health check cycle: {commit_err}", exc_info=True)
                             await cycle_session.rollback()
                    logger.debug(f"Finished health check cycle with {error_count} errors.")

                except Exception as cycle_err:
                    logger.error(f"Critical error in periodic health check cycle setup or panel fetch: {cycle_err}", exc_info=True)
                    await cycle_session.rollback() # Ensure rollback

            logger.debug("--- Finished periodic health check cycle ---")

    # --- Sync Inbounds Logic (uses self.db) ---
    async def sync_panel_inbounds(self, panel_id: int) -> Tuple[int, int]:
        """Syncs inbounds for a single panel. Uses self.db. Commit handled by caller."""
        logger.info(f"Starting inbound sync for panel_id={panel_id}")
        panel = await self.panel_repo.get(self.db, id=panel_id)
        if not panel: raise NotFoundError(f"Panel id={panel_id} not found.")
        if not panel.is_active: logger.warning(f"Panel {panel.id} inactive, skipping sync."); return 0, 0

        try:
            username = decrypt_text(panel.username).decode()
            password = decrypt_text(panel.password).decode()
            if not username or not password: raise ServiceError("Decrypted panel credentials empty.")
        except Exception as decrypt_err: raise ServiceError(f"Credential decryption failed for panel {panel.id}: {decrypt_err}")

        raw_inbounds = []
        fetched_count = 0
        processed_count = 0

        if panel.panel_type != PanelType.XUI: logger.warning(f"Inbound sync not implemented for panel type: {panel.panel_type} (ID: {panel_id}). Skipping."); return 0, 0

        try:
            panel_client = XuiPanelClient(base_url=panel.url, username=username, password=password, panel_id=panel.id, http_client=self.http_client)
            logger.info(f"Fetching inbounds from panel {panel.name} (ID: {panel_id}) at {panel.url}")
            raw_inbounds = await panel_client.get_inbounds()
            fetched_count = len(raw_inbounds)
            logger.info(f"Fetched {fetched_count} raw inbounds from panel {panel.name} (ID: {panel_id}).")

        except (PanelAuthenticationError, PanelAPIError, ServiceError) as e:
            logger.error(f"Panel connection/auth failed for panel {panel.id}: {e}")
            # Mark unhealthy but don't commit here, let caller handle transaction
            await self.panel_repo.update(self.db, db_obj=panel, obj_in={"is_healthy": False})
            raise ServiceError(f"Panel connection/auth failed for panel {panel.id}: {e}") from e
        except Exception as e:
            logger.exception(f"Unexpected error fetching inbounds from panel {panel.id}: {e}")
            await self.panel_repo.update(self.db, db_obj=panel, obj_in={"is_healthy": False})
            raise ServiceError(f"Unexpected error fetching inbounds for panel {panel.id}: {e}") from e

        # --- DB Operations (Process fetched data) ---
        # Get existing inbounds for this panel from DB
        existing_db_inbounds_list = await self.panel_inbound_repo.get_by_panel_id(self.db, panel_id)
        existing_db_inbounds = {db_inb.panel_inbound_id: db_inb for db_inb in existing_db_inbounds_list}
        logger.debug(f"Found {len(existing_db_inbounds)} existing DB inbounds for panel {panel_id}.")

        panel_inbound_ids_in_panel = set()
        inbounds_to_add: List[PanelInboundCreateSchema] = []
        inbounds_to_update: List[Tuple[PanelInbound, PanelInboundUpdate]] = []

        for raw_inbound in raw_inbounds:
            if not isinstance(raw_inbound, dict): continue
            panel_inbound_id = raw_inbound.get('id')
            if not panel_inbound_id: continue
            panel_inbound_ids_in_panel.add(panel_inbound_id)

            schema = self._transform_raw_inbound(raw_inbound, panel_id)
            if not schema: continue # Skip if transformation failed

            existing_db_inbound = existing_db_inbounds.get(panel_inbound_id)
            if existing_db_inbound:
                # Check for changes and create update schema if needed
                update_schema_data = {}
                for k, v in PanelInboundUpdate.__fields__.items():
                    if k in raw_inbound and raw_inbound.get(k) != getattr(existing_db_inbound, k, None):
                        update_schema_data[k] = raw_inbound.get(k)
                # Ensure is_active remains True unless explicitly set otherwise by admin later
                if 'is_active' not in update_schema_data:
                    update_schema_data['is_active'] = True

                # Remove keys not present in PanelInboundUpdate schema before creating
                valid_update_keys = PanelInboundUpdate.__fields__.keys()
                update_schema_data = {k: v for k, v in update_schema_data.items() if k in valid_update_keys}

                update_schema = PanelInboundUpdate(**update_schema_data)
                inbounds_to_update.append((existing_db_inbound, update_schema))
            else:
                # New inbound found in panel
                inbounds_to_add.append(schema)

        # Find inbounds in DB that are no longer in the panel (mark as inactive or delete?)
        inbounds_to_deactivate: List[PanelInbound] = []
        for db_inbound_id, db_inbound in existing_db_inbounds.items():
            if db_inbound_id not in panel_inbound_ids_in_panel:
                if db_inbound.is_active: # Only deactivate if currently active
                    inbounds_to_deactivate.append(db_inbound)

        # Perform DB modifications (Add, Update, Deactivate)
        # These repo methods should NOT commit
        added_count = 0
        updated_count = 0
        deactivated_count = 0

        if inbounds_to_add:
            added_inbounds_result = await self.panel_inbound_repo.bulk_add_inbounds(self.db, inbounds_to_add)
            added_count = len(added_inbounds_result)
            logger.info(f"Added {added_count} new inbounds for panel {panel_id} to session.")

        if inbounds_to_update:
            updated_inbounds_result = await self.panel_inbound_repo.bulk_update_inbounds(self.db, inbounds_to_update)
            updated_count = len(updated_inbounds_result)
            logger.info(f"Updated {updated_count} existing inbounds for panel {panel_id} in session.")

        if inbounds_to_deactivate:
            deactivated_inbounds_result = await self.panel_inbound_repo.bulk_deactivate_inbounds(self.db, inbounds_to_deactivate)
            deactivated_count = len(deactivated_inbounds_result)
            logger.info(f"Deactivated {deactivated_count} stale inbounds for panel {panel_id} in session.")

        processed_count = added_count + updated_count + deactivated_count
        logger.info(f"Inbound sync DB changes for panel {panel_id} prepared: Adds={added_count}, Updates={updated_count}, Deactivates={deactivated_count}.")

        # Mark panel as healthy after successful fetch and processing (before commit)
        if panel.is_healthy is not True:
             await self.panel_repo.update(self.db, db_obj=panel, obj_in={"is_healthy": True})

        # NO COMMIT HERE - Caller (e.g., the handler) should commit
        # await session.commit()

        return fetched_count, processed_count # Return fetched and processed count

    async def sync_inbounds_from_panels(self) -> Dict[str, Any]:
        """ Periodically syncs inbounds from all active, healthy panels. Manages its own session. """
        from core.database import async_session_factory # Import locally
        logger.info("Starting periodic inbound sync from panels...")
        results = {}
        async with async_session_factory() as cycle_session:
            # Instantiate service with this cycle's session
            panel_service_instance = PanelService(cycle_session)
            try:
                # Get active and healthy panels using instance method
                panels = await panel_service_instance.panel_repo.find_active_and_healthy(cycle_session)
                if not panels:
                    logger.info("No active and healthy panels found to sync inbounds from.")
                    return {}

                logger.info(f"Found {len(panels)} panels to sync inbounds from.")
                tasks = {panel.id: panel_service_instance.sync_panel_inbounds(panel.id) for panel in panels}
                task_results = await asyncio.gather(*tasks.values(), return_exceptions=True)

                # Process results and commit changes
                needs_commit = False
                for i, panel_id in enumerate(tasks.keys()):
                    result = task_results[i]
                    panel_name = next((p.name for p in panels if p.id == panel_id), f"ID:{panel_id}")
                    if isinstance(result, Exception):
                        logger.error(f"Error syncing inbounds for panel {panel_name}: {result}", exc_info=False)
                        results[panel_name] = f"Error: {result}"
                    elif isinstance(result, tuple):
                        added, updated = result
                        results[panel_name] = f"Added: {added}, Updated: {updated}"
                        if added > 0 or updated > 0:
                            needs_commit = True
                    else:
                         results[panel_name] = "Unexpected result type."

                if needs_commit:
                    try:
                        await cycle_session.commit()
                        logger.info(f"Committed inbound sync changes. Results: {results}")
                    except Exception as commit_err:
                        logger.error(f"Error committing inbound sync cycle: {commit_err}", exc_info=True)
                        await cycle_session.rollback()
                else:
                    logger.info("No changes detected during inbound sync cycle.")

            except Exception as cycle_err:
                logger.error(f"Critical error in periodic inbound sync cycle setup or panel fetch: {cycle_err}", exc_info=True)
                await cycle_session.rollback() # Ensure rollback

        logger.info("Finished periodic inbound sync from panels.")
        return results

    def _transform_raw_inbound(self, raw_inbound: Dict[str, Any], panel_id: int) -> Optional[PanelInboundCreateSchema]:
        """Transforms raw XUI inbound data to PanelInboundCreateSchema."""
        panel_inbound_id = raw_inbound.get('id')
        tag = raw_inbound.get('tag')
        log_prefix = f"[Panel-{panel_id}/Inbound-{panel_inbound_id or '?'}/Tag-{tag or '?'}]"

        try:
            settings_dict = json.loads(raw_inbound.get('settings', '{}') or '{}')
            stream_settings_dict = json.loads(raw_inbound.get('streamSettings', '{}') or '{}')
            total_bytes = raw_inbound.get('total')
            total_gb = round(total_bytes / (1024**3), 2) if isinstance(total_bytes, (int, float)) and total_bytes > 0 else 0.0

            # Map to schema fields
            transformed_data = {
                'panel_id': panel_id,
                'panel_inbound_id': panel_inbound_id,
                'tag': tag,
                'remark': raw_inbound.get('remark'),
                'protocol': raw_inbound.get('protocol'),
                'port': raw_inbound.get('port'),
                'panel_enabled': raw_inbound.get('enable', False),
                'expiry_time': raw_inbound.get('expiryTime'),
                'listen_ip': raw_inbound.get('listen'),
                'settings': settings_dict,
                'stream_settings': stream_settings_dict,
                'total_gb': total_gb,
                # 'is_active': True, # Let's sync actual status if possible, or maybe remove?
            }
            # Use PanelInboundCreateSchema for validation
            schema = PanelInboundCreateSchema(**transformed_data)
            return schema

        except json.JSONDecodeError as e:
            logger.warning(f"{log_prefix} Failed to decode settings/streamSettings JSON. Error: {e}.")
            return None
        except Exception as e: # Catch Pydantic validation errors and others
             logger.warning(f"{log_prefix} Failed to transform or validate inbound. Error: {type(e).__name__}: {e}. Raw Data: {raw_inbound}")
             return None

    async def _get_panel_client(self, panel_id: int) -> XuiPanelClient:
        """Helper to get an authenticated XUI panel client instance."""
        panel = await self.panel_repo.get(self.db, id=panel_id)
        if not panel: raise NotFoundError(f"Panel with ID {panel_id} not found.")
        if panel.panel_type != PanelType.XUI: raise ConfigurationError(f"Panel {panel_id} is not an XUI panel.")

        try:
            username = decrypt_text(panel.username).decode()
            password = decrypt_text(panel.password).decode()
            if not username or not password: raise ConfigurationError("Panel credentials could not be decrypted or are empty.")
        except Exception as e:
            raise ServiceError(f"Failed to decrypt credentials for panel {panel_id}: {e}")

        # Consider caching the client instance with its token? For now, create new.
        xui_client = XuiPanelClient(
            base_url=panel.url,
            username=username,
            password=password,
            panel_id=panel.id,
            http_client=self.http_client # Reuse the service's http client
        )
        # Ensure client is logged in (login handles token caching internally)
        await xui_client.login()
        return xui_client

    async def add_client_to_panel(self, panel_id: int, inbound_id: int, client_settings: Dict[str, Any], protocol: str) -> Dict[str, Any]:
        """Adds a client to a specific inbound on the panel.

        Args:
            panel_id: ID of the panel.
            inbound_id: ID of the inbound on the panel.
            client_settings: Dictionary containing client details (uuid, email, totalGB, expiryTime, etc.).
            protocol: The protocol of the client (e.g., 'vmess', 'trojan'). Needed for identifier handling.

        Returns:
            Dict containing 'native_identifier' and 'subscription_url' (and potentially other info).
        """
        logger.info(f"Adding client ({client_settings.get('email')}, proto:{protocol}) to panel {panel_id}, inbound {inbound_id}")
        xui_client = await self._get_panel_client(panel_id)
        try:
            # Pass all three parameters to XuiPanelClient.add_client
            panel_response = await xui_client.add_client(inbound_id, client_settings, protocol)

            # Extract the returned data
            native_identifier = panel_response.get("native_identifier")
            if not native_identifier:
                logger.error(f"Panel native identifier could not be determined for panel {panel_id}, protocol {protocol}.")
                raise ServiceError("Could not determine native identifier for the client created on the panel.")

            subscription_url = panel_response.get("subscription_url")

            logger.info(f"Successfully added client {client_settings.get('email')} to panel {panel_id}. Native ID: {native_identifier}")
            return {
                "native_identifier": native_identifier,
                "subscription_url": subscription_url
            }
        except (PanelAuthenticationError, PanelAPIError, ServiceError, ConfigurationError, NotFoundError) as e:
            logger.error(f"Failed to add client ({client_settings.get('email')}) to panel {panel_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error adding client ({client_settings.get('email')}) to panel {panel_id}")
            raise ServiceError(f"Unexpected error adding client to panel {panel_id}: {e}")

    async def update_client_on_panel(self, panel_id: int, client_identifier: str, protocol: str, inbound_id: int, updates: Dict[str, Any], reset_traffic: bool = False) -> bool:
        """Updates a client on the panel.

        Args:
            panel_id: ID of the panel.
            client_identifier: The native identifier of the client on the panel.
            protocol: The client's protocol.
            inbound_id: The ID of the inbound the client belongs to.
            updates: Dictionary of settings to update (e.g., {'enable': True, 'totalGB': 50}).
            reset_traffic: If True, also attempt to reset the client's traffic.

        Returns:
            True if successful, False otherwise (though exceptions are preferred).
        """
        logger.info(f"Updating client {client_identifier} (proto:{protocol}, inbound:{inbound_id}) on panel {panel_id} with updates: {updates}, reset: {reset_traffic}")
        xui_client = await self._get_panel_client(panel_id)
        try:
            # Pass client_identifier, protocol, updates to update_client
            success = await xui_client.update_client(client_identifier, protocol, updates)

            if reset_traffic:
                logger.info(f"Attempting to reset traffic for client {client_identifier} (proto:{protocol}, inbound:{inbound_id}) on panel {panel_id}")
                # Pass client_identifier, protocol, inbound_id to reset_client_traffic
                reset_success = await xui_client.reset_client_traffic(client_identifier, protocol, inbound_id)
                if not reset_success:
                    logger.warning(f"Panel traffic reset for {client_identifier} (proto:{protocol}) on panel {panel_id} might have failed.")
                else:
                    logger.info(f"Panel traffic reset successful for {client_identifier} (proto:{protocol}) on panel {panel_id}.")

            logger.info(f"Update operation for client {client_identifier} (proto:{protocol}) on panel {panel_id} completed (Success={success}).")
            return success

        except (PanelAuthenticationError, PanelAPIError, ServiceError, ConfigurationError, NotFoundError) as e:
            logger.error(f"Failed to update client {client_identifier} (proto:{protocol}) on panel {panel_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error updating client {client_identifier} (proto:{protocol}) on panel {panel_id}")
            raise ServiceError(f"Unexpected error updating client {client_identifier} on panel {panel_id}: {e}")

    async def delete_client_from_panel(self, panel_id: int, inbound_id: int, client_identifier: str, protocol: str) -> bool:
        """Deletes a client from a specific inbound on the panel.

        Args:
            panel_id: ID of the panel.
            inbound_id: ID of the inbound the client belongs to (required by some panel APIs).
            client_identifier: The native identifier of the client on the panel.
            protocol: The client's protocol.

        Returns:
            True if successful, False otherwise.
        """
        logger.info(f"Deleting client {client_identifier} (proto:{protocol}) from panel {panel_id}, inbound {inbound_id}")
        xui_client = await self._get_panel_client(panel_id)
        try:
            # Pass all three parameters to XuiPanelClient.delete_client in correct order
            success = await xui_client.delete_client(inbound_id, client_identifier, protocol)
            logger.info(f"Deletion operation for client {client_identifier} (proto:{protocol}) on panel {panel_id} completed (Success={success}).")
            return success
        except (PanelAuthenticationError, PanelAPIError, ServiceError, ConfigurationError, NotFoundError) as e:
            logger.error(f"Failed to delete client {client_identifier} (proto:{protocol}) from panel {panel_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error deleting client {client_identifier} (proto:{protocol}) from panel {panel_id}")
            raise ServiceError(f"Unexpected error deleting client {client_identifier} from panel {panel_id}: {e}")

    async def get_client_usage_from_panel(self, panel_id: int, client_identifier: str, protocol: str) -> Optional[Dict[str, int]]:
        """Gets traffic usage (up, down) for a client from the panel.

        Args:
            panel_id: ID of the panel.
            client_identifier: The native identifier of the client on the panel.
            protocol: The client's protocol.

        Returns:
            Dict with {'up': bytes, 'down': bytes} or None if not found/error.
        """
        logger.debug(f"Getting usage for client {client_identifier} (proto:{protocol}) from panel {panel_id}")
        xui_client = await self._get_panel_client(panel_id)
        try:
            # Pass client_identifier and protocol to get_client_traffics
            usage_data = await xui_client.get_client_traffics(client_identifier, protocol)
            if usage_data:
                 logger.debug(f"Usage data for {client_identifier} (proto:{protocol}) on panel {panel_id}: {usage_data}")
                 return usage_data
            else:
                 logger.warning(f"No usage data returned for client {client_identifier} (proto:{protocol}) on panel {panel_id}.")
                 return None
        except (PanelAuthenticationError, PanelAPIError, ServiceError, ConfigurationError, NotFoundError) as e:
            logger.error(f"Failed to get usage for client {client_identifier} (proto:{protocol}) from panel {panel_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting usage for client {client_identifier} (proto:{protocol}) from panel {panel_id}")
            raise ServiceError(f"Unexpected error getting usage for client {client_identifier} from panel {panel_id}: {e}")

    async def get_client_config_from_panel(self, panel_id: int, client_identifier: str, protocol: str, inbound_id: int) -> Dict[str, Any]:
        """Gets detailed configuration/connection info for a client from the panel.

        Args:
            panel_id: ID of the panel.
            client_identifier: The native identifier of the client on the panel.
            protocol: The client's protocol (needed to interpret config and find client).
            inbound_id: ID of the inbound the client belongs to.

        Returns:
            A dictionary containing panel-specific configuration details.
        """
        logger.debug(f"Getting config for client {client_identifier} (protocol: {protocol}, inbound: {inbound_id}) from panel {panel_id}")
        xui_client = await self._get_panel_client(panel_id)
        try:
            # Pass all necessary parameters to get_client_details
            config_data = await xui_client.get_client_details(client_identifier, protocol, inbound_id)
            if config_data:
                 logger.debug(f"Config data for {client_identifier} (proto:{protocol}) on panel {panel_id}: {config_data}")
                 return config_data
            else:
                 logger.warning(f"No config data returned for client {client_identifier} (proto:{protocol}) on panel {panel_id}.")
                 raise NotFoundError(f"Client {client_identifier} not found on panel {panel_id} or no config available.")

        except NotImplementedError:
             logger.error(f"Fetching client config details from panel {panel_id} is not implemented in xui_client for protocol {protocol}.")
             raise NotImplementedError(f"Client config retrieval not implemented for protocol {protocol}.")
        except (PanelAuthenticationError, PanelAPIError, ServiceError, ConfigurationError, NotFoundError) as e:
            logger.error(f"Failed to get config for client {client_identifier} (proto:{protocol}) from panel {panel_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting config for client {client_identifier} (proto:{protocol}) from panel {panel_id}")
            raise ServiceError(f"Unexpected error getting config for client {client_identifier} from panel {panel_id}: {e}")

    async def get_panel_inbounds_by_panel_id(self, panel_id: int) -> Sequence[PanelInbound]:
        """Gets all panel inbounds for a specific panel.
        
        Args:
            panel_id: ID of the panel to get inbounds for
            
        Returns:
            Sequence of PanelInbound objects
            
        Raises:
            NotFoundError: If panel not found
        """
        logger.debug(f"Fetching inbounds for panel_id={panel_id}")
        
        # Check if panel exists
        panel = await self.panel_repo.get(self.db, id=panel_id)
        if not panel:
            raise NotFoundError(f"Panel with id={panel_id} not found")
            
        # Get inbounds
        return await self.panel_inbound_repo.get_by_panel_id(self.db, panel_id)

# --- Helper Class for Panel Selection ---
class _PanelSelectorHelper:
    def __init__(self, panel_repo: PanelRepository, client_repo: ClientRepository, setting_repo: SettingRepository):
        self.panel_repo = panel_repo
        self.client_repo = client_repo
        self.setting_repo = setting_repo

    async def _get_panel_client_counts(self, session: AsyncSession, panel_ids: List[int]) -> Dict[int, int]:
        """ Correctly passes session to the repository method. """
        return await self.client_repo.count_active_clients_per_panel(session, panel_ids=panel_ids)

    async def select_panel(
        self,
        session: AsyncSession,
        location_id: int,
        strategy: SelectionStrategy,
        protocol: Optional[str] = None,
        is_premium_required: bool = False,
        exclude_panel_ids: Optional[List[int]] = None
    ) -> Optional[Panel]:
        logger.debug(f"Selecting panel for location {location_id}, strategy: {strategy.value}")
        exclude_panel_ids = exclude_panel_ids or []

        # Pass session to repository method
        candidate_panels = await self.panel_repo.get_active_healthy_panels_by_location(
            session, location_id=location_id, exclude_ids=exclude_panel_ids
        )

        if not candidate_panels: logger.warning(f"No suitable panels found for location {location_id}"); return None

        selected_panel: Optional[Panel] = None
        if strategy == SelectionStrategy.LEAST_LOAD or strategy == SelectionStrategy.BALANCED:
            panel_ids = [p.id for p in candidate_panels]
            # Pass session to helper method which passes it to repo
            client_counts = await self._get_panel_client_counts(session, panel_ids)
            selected_panel = min(candidate_panels, key=lambda p: client_counts.get(p.id, 0))

        elif strategy == SelectionStrategy.ROUND_ROBIN:
            setting_key = f"round_robin_last_panel_{location_id}"
            # Pass session to repository method
            last_used_id_str = await self.setting_repo.get_value(session, key=setting_key)
            last_used_id = int(last_used_id_str) if last_used_id_str else None
            candidate_ids = [p.id for p in candidate_panels]
            try: current_index = candidate_ids.index(last_used_id) if last_used_id in candidate_ids else -1
            except ValueError: current_index = -1
            next_index = (current_index + 1) % len(candidate_ids)
            selected_panel_id = candidate_ids[next_index]
            selected_panel = next((p for p in candidate_panels if p.id == selected_panel_id), candidate_panels[0])
            # Pass session to repository method
            await self.setting_repo.set_value(session, key=setting_key, value=str(selected_panel_id))

        elif strategy == SelectionStrategy.PRIORITY:
             selected_panel = candidate_panels[0]
        else:
            logger.error(f"Unknown selection strategy: {strategy}. Falling back to priority.")
            selected_panel = candidate_panels[0]

        if selected_panel: logger.info(f"Selected panel '{selected_panel.name}' (ID: {selected_panel.id}) using strategy: {strategy.value}")
        return selected_panel
