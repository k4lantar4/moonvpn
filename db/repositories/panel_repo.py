"""
Panel repository for database operations
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # Added for potential future eager loading needs

from db.models.panel import Panel, PanelStatus
from db.models.inbound import Inbound, InboundStatus

# Assume logger is configured elsewhere
logger = logging.getLogger(__name__)

class PanelRepository:
    """
    ریپازیتوری برای عملیات مرتبط با پنل‌ها در دیتابیس.
    Repository for panel-related database operations.

    این ریپازیتوری مسئولیت تمام تعاملات مستقیم با جدول `panels` و جداول مرتبط
    مانند `inbounds` را در دیتابیس بر عهده دارد. تمامی متدها آسنکرون هستند
    و از `AsyncSession` برای ارتباط با دیتابیس استفاده می‌کنند.

    **نکته مهم:** این ریپازیتوری هیچگاه تراکنش‌ها را `commit` نمی‌کند.
    عملیات `commit` باید در لایه سرویس انجام شود. در صورت نیاز به دریافت
    شناسه‌های تولید شده توسط دیتابیس یا به‌روزرسانی وضعیت آبجکت‌ها پس از
    عملیات نوشتن، از `flush` و `refresh` استفاده می‌شود.
    This repository handles all direct interactions with the `panels` table
    and related tables like `inbounds` in the database. All methods are
    asynchronous and utilize `AsyncSession` for database communication.

    **Important Note:** This repository never commits transactions.
    The `commit` operation must be handled at the service layer.
    `flush` and `refresh` are used when necessary to obtain database-generated
    IDs or update the state of objects after write operations.
    """
    
    def __init__(self, session: AsyncSession):
        """
        سازنده ریپازیتوری پنل.
        Initializes the Panel Repository.

        Args:
            session (AsyncSession): نشست آسنکرون برای ارتباط با دیتابیس.
                                     The asynchronous session for database interaction.
        """
        self.session = session
        logger.debug("PanelRepository مقداردهی اولیه شد. (PanelRepository initialized.)")
    
    # --- Create Operations ---

    async def create_panel(self, panel_data: Dict[str, Any]) -> Panel:
        """
        ایجاد یک پنل جدید در دیتابیس.
        Creates a new panel in the database.

        این متد یک آبجکت پنل جدید ایجاد کرده، آن را به session اضافه می‌کند،
        `flush` را برای ارسال دستور به دیتابیس و دریافت ID احتمالی اجرا کرده
        و سپس `refresh` را برای به‌روزرسانی کامل آبجکت پنل با اطلاعات
        دیتابیس (مانند مقادیر پیش‌فرض یا تریگرها) فراخوانی می‌کند.

        This method creates a new Panel object, adds it to the session,
        flushes to send the command to the database and potentially get an ID,
        and then refreshes to fully update the Panel object with database
        information (like default values or triggers).

        Args:
            panel_data (Dict[str, Any]): دیکشنری حاوی داده‌های پنل جدید.
                                         A dictionary containing the data for the new panel.

        Returns:
            Panel: آبجکت پنل ایجاد شده. The created Panel object.

        Raises:
            SQLAlchemyError: در صورت بروز خطا در عملیات دیتابیس.
                             If a database operation error occurs.
        """
        logger.info(f"در حال ایجاد پنل جدید با URL: {panel_data.get('url', 'N/A')}. (Attempting to create a new panel with URL: {panel_data.get('url', 'N/A')}).")
        try:
            # Ensure status is set if provided, otherwise rely on model default
            if 'status' in panel_data and isinstance(panel_data['status'], str):
                panel_data['status'] = PanelStatus[panel_data['status'].upper()]

            panel = Panel(**panel_data)
            self.session.add(panel)
            await self.session.flush()  # Send insert to DB, get ID
            await self.session.refresh(panel) # Update panel object with DB state (defaults, etc.)
            logger.info(f"پنل با شناسه {panel.id} و URL '{panel.url}' با موفقیت ایجاد و flush شد. (Panel with ID {panel.id} and URL '{panel.url}' created and flushed successfully.)")
            return panel
        except SQLAlchemyError as e:
            logger.error(f"خطا در ایجاد پنل جدید با URL '{panel_data.get('url', 'N/A')}': {e}. (Error creating new panel with URL '{panel_data.get('url', 'N/A')}': {e}).")
            # Rollback should happen at the service layer managing the transaction
            raise
        except KeyError as e: # Handle potential issues with PanelStatus enum conversion
             logger.error(f"مقدار نامعتبر برای وضعیت پنل ارائه شده: {panel_data.get('status')}. خطا: {e} (Invalid value provided for panel status: {panel_data.get('status')}. Error: {e})")
             raise ValueError(f"مقدار وضعیت نامعتبر: {panel_data.get('status')}") from e

    # --- Read Operations ---

    async def get_panel_by_id(self, panel_id: int) -> Optional[Panel]:
        """
        دریافت پنل بر اساس شناسه یکتا (ID).
        Retrieves a panel by its unique ID.

        Args:
            panel_id (int): شناسه پنل مورد نظر. The ID of the panel to retrieve.

        Returns:
            Optional[Panel]: آبجکت پنل در صورت یافت شدن، در غیر این صورت None.
                             The Panel object if found, otherwise None.
        """
        logger.debug(f"در حال دریافت پنل با شناسه: {panel_id}. (Fetching panel with ID: {panel_id}).")
        try:
            # Use session.get for efficient primary key lookup
            panel = await self.session.get(Panel, panel_id)
            if panel:
                logger.debug(f"پنل با شناسه {panel_id} پیدا شد. (Panel with ID {panel_id} found.)")
            else:
                logger.debug(f"پنل با شناسه {panel_id} پیدا نشد. (Panel with ID {panel_id} not found.)")
            return panel
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت پنل با شناسه {panel_id}: {e}. (Error fetching panel with ID {panel_id}: {e}).")
            raise

    async def get_panel_by_url(self, url: str) -> Optional[Panel]:
        """
        دریافت پنل بر اساس آدرس URL.
        Retrieves a panel by its URL.

        Args:
            url (str): آدرس URL پنل مورد نظر. The URL of the panel to retrieve.

        Returns:
            Optional[Panel]: آبجکت پنل در صورت یافت شدن، در غیر این صورت None.
                             The Panel object if found, otherwise None.
        """
        logger.debug(f"در حال دریافت پنل با URL: {url}. (Fetching panel with URL: {url}).")
        try:
            query = select(Panel).where(Panel.url == url)
            result = await self.session.execute(query)
            panel = result.scalar_one_or_none() # Efficiently gets one or None
            if panel:
                logger.debug(f"پنل با URL '{url}' پیدا شد. (Panel with URL '{url}' found.)")
            else:
                logger.debug(f"پنل با URL '{url}' پیدا نشد. (Panel with URL '{url}' not found.)")
            return panel
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت پنل با URL '{url}': {e}. (Error fetching panel with URL '{url}': {e}).")
            raise

    async def get_all_panels(self) -> List[Panel]:
        """
        دریافت لیستی از تمام پنل‌های موجود در دیتابیس.
        Retrieves a list of all panels from the database.

        Returns:
            List[Panel]: لیستی از آبجکت‌های پنل. A list of Panel objects.
        """
        logger.debug("در حال دریافت تمام پنل‌ها. (Fetching all panels).")
        try:
            query = select(Panel).order_by(Panel.id) # Add ordering for consistency
            result = await self.session.execute(query)
            panels = list(result.scalars().all())
            logger.debug(f"تعداد {len(panels)} پنل دریافت شد. (Fetched {len(panels)} panels.)")
            return panels
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت تمام پنل‌ها: {e}. (Error fetching all panels: {e}).")
            raise

    async def get_panels_by_raw_status(self, raw_status: str) -> List[Panel]:
        """
        دریافت پنل‌ها با استفاده از مقدار خام وضعیت (برای سازگاری با داده‌های قدیمی).
        Get panels using raw status value (for backward compatibility).

        Args:
            raw_status (str): مقدار خام وضعیت (مثلاً 'active' یا 'ACTIVE').
                             Raw status value (e.g., 'active' or 'ACTIVE').

        Returns:
            List[Panel]: لیست پنل‌ها با وضعیت مشخص شده.
                         List of panels with the specified status.
        """
        try:
            # Use raw SQL to bypass SQLAlchemy's enum validation
            query = text("SELECT * FROM panels WHERE status = :status")
            result = await self.session.execute(query, {"status": raw_status})
            panels = [Panel(**dict(row)) for row in result]
            logger.debug(f"تعداد {len(panels)} پنل با وضعیت خام '{raw_status}' دریافت شد. (Fetched {len(panels)} panels with raw status '{raw_status}').")
            return panels
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت پنل‌ها با وضعیت خام '{raw_status}': {e}. (Error fetching panels with raw status '{raw_status}': {e}).")
            raise

    async def get_active_panels(self) -> List[Panel]:
        """
        دریافت لیستی از تمام پنل‌های فعال.
        Retrieves a list of all active panels.

        Returns:
            List[Panel]: لیستی از آبجکت‌های پنل فعال. A list of active Panel objects.
        """
        logger.debug("در حال دریافت پنل‌های فعال. (Fetching active panels).")
        try:
            # Try both uppercase and lowercase status values
            panels = []
            
            # Try with PanelStatus.ACTIVE (uppercase)
            query = select(Panel).where(Panel.status == PanelStatus.ACTIVE).order_by(Panel.id)
            result = await self.session.execute(query)
            panels.extend(result.scalars().all())
            
            # Try with raw 'active' (lowercase) for backward compatibility
            try:
                raw_panels = await self.get_panels_by_raw_status('active')
                # Add only panels that aren't already in the list
                existing_ids = {p.id for p in panels}
                panels.extend([p for p in raw_panels if p.id not in existing_ids])
            except Exception as e:
                logger.warning(f"خطا در دریافت پنل‌ها با وضعیت خام 'active': {e}. ادامه با نتایج موجود. (Error fetching panels with raw status 'active': {e}. Continuing with available results.)")
            
            logger.debug(f"تعداد {len(panels)} پنل فعال دریافت شد. (Fetched {len(panels)} active panels.)")
            return panels
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت پنل‌های فعال: {e}. (Error fetching active panels: {e}).")
            raise

    async def get_panel_inbounds(self, panel_id: int) -> List[Inbound]:
        """
        دریافت لیست تمام اینباندها (inbounds) مربوط به یک پنل خاص.
        Retrieves a list of all inbounds associated with a specific panel.

        Args:
            panel_id (int): شناسه پنلی که اینباندهای آن مورد نظر است.
                             The ID of the panel whose inbounds are to be retrieved.

        Returns:
            List[Inbound]: لیستی از آبجکت‌های اینباند. A list of Inbound objects.
        """
        logger.debug(f"در حال دریافت اینباندهای پنل با شناسه: {panel_id}. (Fetching inbounds for panel ID: {panel_id}).")
        try:
            # Consider using selectinload if panel data is often needed with inbounds
            # query = select(Inbound).options(selectinload(Inbound.panel)).where(Inbound.panel_id == panel_id)
            query = select(Inbound).where(Inbound.panel_id == panel_id).order_by(Inbound.id) # Add ordering
            result = await self.session.execute(query)
            inbounds = list(result.scalars().all())
            logger.debug(f"تعداد {len(inbounds)} اینباند برای پنل {panel_id} دریافت شد. (Fetched {len(inbounds)} inbounds for panel {panel_id}.)")
            return inbounds
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت اینباندهای پنل {panel_id}: {e}. (Error fetching inbounds for panel {panel_id}: {e}).")
            raise

    async def get_inbounds_by_panel_id(
        self,
        panel_id: int,
        status: Optional[InboundStatus] = None
    ) -> List[Inbound]:
        """
        دریافت لیست اینباندها برای یک پنل خاص، با قابلیت فیلتر بر اساس وضعیت.
        Retrieves a list of inbounds for a specific panel, optionally filtered by status.

        Args:
            panel_id (int): شناسه پنل.
                             The ID of the panel.
            status (Optional[InboundStatus]): وضعیت اینباند برای فیلتر (اختیاری).
                                              The inbound status to filter by (optional).

        Returns:
            List[Inbound]: لیستی از آبجکت‌های اینباند مطابق با فیلتر.
                         A list of Inbound objects matching the criteria.

        Raises:
            SQLAlchemyError: در صورت بروز خطا در عملیات دیتابیس.
                             If a database operation error occurs.
        """
        log_msg = f"در حال دریافت اینباندها برای پنل {panel_id} " \
                  f"{' با وضعیت ' + status.name if status else ''}. " \
                  f"(Fetching inbounds for panel {panel_id} " \
                  f"{' with status ' + status.name if status else ''})"
        logger.debug(log_msg)
        try:
            query = select(Inbound).where(Inbound.panel_id == panel_id)
            if status is not None:
                query = query.where(Inbound.status == status)
            query = query.order_by(Inbound.id) # Add ordering

            result = await self.session.execute(query)
            inbounds = list(result.scalars().all())
            logger.debug(f"تعداد {len(inbounds)} اینباند برای پنل {panel_id} " \
                         f"{' با وضعیت ' + status.name if status else ''} دریافت شد. " \
                         f"(Fetched {len(inbounds)} inbounds for panel {panel_id} " \
                         f"{' with status ' + status.name if status else ''}).")
            return inbounds
        except SQLAlchemyError as e:
            error_msg = f"خطا در دریافت اینباندها برای پنل {panel_id} " \
                        f"{' با وضعیت ' + status.name if status else ''}: {e}. " \
                        f"(Error fetching inbounds for panel {panel_id} " \
                        f"{' with status ' + status.name if status else ''}: {e})."
            logger.error(error_msg)
            raise
        except Exception as e: # Catch unexpected errors
            logger.error(f"خطای پیش‌بینی نشده هنگام دریافت اینباندها برای پنل {panel_id}: {e}. (Unexpected error fetching inbounds for panel {panel_id}: {e}).", exc_info=True)
            raise

    async def get_panels_by_status(self, status: PanelStatus) -> List[Panel]:
        """
        دریافت لیستی از پنل‌ها بر اساس وضعیت مشخص شده.
        Retrieves a list of panels based on the specified status.

        Args:
            status (PanelStatus): وضعیت مورد نظر برای فیلتر پنل‌ها (مثلاً ACTIVE, INACTIVE).
                                  The status to filter panels by (e.g., ACTIVE, INACTIVE).

        Returns:
            List[Panel]: لیستی از آبجکت‌های پنل با وضعیت مشخص شده.
                         A list of Panel objects matching the specified status.

        Raises:
            SQLAlchemyError: در صورت بروز خطا در عملیات دیتابیس.
                             If a database operation error occurs.
        """
        logger.debug(f"در حال دریافت پنل‌ها با وضعیت: {status.name}. (Fetching panels with status: {status.name}).")
        try:
            query = select(Panel).where(Panel.status == status).order_by(Panel.id)
            result = await self.session.execute(query)
            panels = list(result.scalars().all())
            logger.debug(f"تعداد {len(panels)} پنل با وضعیت {status.name} دریافت شد. (Fetched {len(panels)} panels with status {status.name}).")
            return panels
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت پنل‌ها با وضعیت {status.name}: {e}. (Error fetching panels with status {status.name}: {e}).")
            raise
        except Exception as e: # Catch unexpected errors like invalid status type, though unlikely with Enum
             logger.error(f"خطای پیش‌بینی نشده هنگام دریافت پنل‌ها با وضعیت {status}: {e}. (Unexpected error fetching panels with status {status}: {e}).", exc_info=True)
             raise

    # --- Update Operations ---

    async def update_panel(self, panel_id: int, update_data: Dict[str, Any]) -> Optional[Panel]:
        """
        به‌روزرسانی اطلاعات یک پنل موجود با استفاده از شناسه آن.
        Updates information for an existing panel using its ID.

        این متد مستقیماً دستور UPDATE را در دیتابیس اجرا می‌کند و نیازی به
        فراخوانی `session.add` ندارد. پس از اجرای دستور UPDATE،
        `flush` را برای ارسال دستور به دیتابیس اجرا می‌کند. برای دریافت
        آبجکت به‌روز شده، پنل را مجدداً از دیتابیس واکشی می‌کند.

        This method executes an UPDATE statement directly in the database,
        eliminating the need for `session.add`. After executing the UPDATE,
        it flushes to send the command to the database. To get the updated
        object, it re-fetches the panel from the database.

        Args:
            panel_id (int): شناسه پنل مورد نظر برای به‌روزرسانی.
                             The ID of the panel to update.
            update_data (Dict[str, Any]): دیکشنری حاوی فیلدهایی که باید به‌روز شوند.
                                         A dictionary containing the fields to update.

        Returns:
            Optional[Panel]: آبجکت پنل به‌روز شده در صورت موفقیت، در غیر این صورت None.
                             The updated Panel object if successful, otherwise None.

        Raises:
            SQLAlchemyError: در صورت بروز خطا در عملیات دیتابیس.
                             If a database operation error occurs.
            ValueError: If the status value in update_data is invalid.
        """
        logger.info(f"در حال به‌روزرسانی پنل با شناسه {panel_id}. داده‌های به‌روزرسانی: {update_data}. (Attempting to update panel with ID {panel_id}. Update data: {update_data}).")
        if not update_data:
            logger.warning(f"داده‌ای برای به‌روزرسانی پنل {panel_id} ارائه نشده است. (No data provided for updating panel {panel_id}).")
            # Return the existing panel without changes?
            return await self.get_panel_by_id(panel_id)

        try:
            # Convert status string to Enum if present
            if 'status' in update_data and isinstance(update_data['status'], str):
                try:
                     update_data['status'] = PanelStatus[update_data['status'].upper()]
                except KeyError as e:
                     logger.error(f"مقدار نامعتبر برای وضعیت پنل در داده‌های به‌روزرسانی ارائه شده: {update_data['status']}. خطا: {e} (Invalid value provided for panel status in update data: {update_data['status']}. Error: {e})")
                     raise ValueError(f"مقدار وضعیت نامعتبر: {update_data['status']}") from e

            # Build and execute the update statement
            stmt = update(Panel).where(Panel.id == panel_id).values(**update_data)
            result = await self.session.execute(stmt)

            # Check if any row was actually updated
            if result.rowcount == 0:
                logger.warning(f"به‌روزرسانی برای پنل {panel_id} انجام نشد. پنل با این شناسه وجود ندارد یا داده‌ها تغییری ایجاد نکردند. (Update for panel {panel_id} did not affect any rows. Panel might not exist or data caused no change.)")
                # Panel might not exist, return None
                return None

            # Flush the session to send the update to the DB
            await self.session.flush()
            logger.info(f"دستور به‌روزرسانی برای پنل {panel_id} اجرا و flush شد. تعداد سطرهای تحت تاثیر: {result.rowcount}. (Update statement for panel {panel_id} executed and flushed. Rows affected: {result.rowcount}).")

            # Re-fetch the updated panel to return the updated state
            # Expire the object in the session cache to force a reload from DB
            # Trying session.expire might be better if the object is already loaded
            panel = await self.session.get(Panel, panel_id, options=[selectinload("*")]) # Expire and reload
            if panel:
                 await self.session.refresh(panel) # Ensure it's fresh
                 logger.info(f"پنل {panel_id} پس از به‌روزرسانی با موفقیت بازخوانی شد. (Panel {panel_id} successfully refreshed after update.)")
            else:
                # Should not happen if rowcount > 0, but log just in case
                 logger.error(f"خطای غیرمنتظره: پنل {panel_id} پس از به‌روزرسانی یافت نشد، با اینکه rowcount > 0 بود. (Unexpected error: Panel {panel_id} not found after update, despite rowcount > 0.)")

            return panel # Return the refreshed panel

        except SQLAlchemyError as e:
            logger.error(f"خطا در به‌روزرسانی پنل با شناسه {panel_id}: {e}. (Error updating panel with ID {panel_id}: {e}).")
            # Rollback should happen at the service layer
            raise

    async def update_panel_status(self, panel_id: int, status: PanelStatus, reason: Optional[str] = None) -> bool:
        """
        به‌روزرسانی وضعیت یک پنل خاص و ثبت دلیل (اختیاری).
        Updates the status of a specific panel and logs the reason.

        Args:
            panel_id (int): شناسه پنلی که باید آپدیت شود.
                             The ID of the panel to update.
            status (PanelStatus): وضعیت جدید برای پنل.
                                   The new status for the panel.
            reason (Optional[str]): دلیل به‌روزرسانی (اختیاری).
                                    The reason for the update (optional).

        Returns:
            bool: True اگر پنل با موفقیت آپدیت شد، False در غیر این صورت (مثلاً اگر پنل وجود نداشته باشد).
                  True if the panel was successfully updated, False otherwise (e.g., if the panel didn't exist).

        Raises:
            SQLAlchemyError: در صورت بروز خطا در عملیات دیتابیس.
                             If a database operation error occurs.
        """
        logger.info(f"در حال آماده سازی آپدیت وضعیت پنل با شناسه {panel_id} به '{status.name}' برای دلیل: {reason}. (Preparing to update panel status to '{status.name}' for panel {panel_id} for reason: {reason}).")
        try:
            stmt = (
                update(Panel)
                .where(Panel.id == panel_id)
                .values(status=status)
                .execution_options(synchronize_session=False) # Important: Don't sync session state
            )
            result = await self.session.execute(stmt)
            rows_affected = result.rowcount
            logger.info(f"آپدیت وضعیت پنل {panel_id} تکمیل شد. {rows_affected} سطر تحت تاثیر قرار گرفت. نیاز به commit در سرویس. (Panel status update for panel {panel_id} completed. {rows_affected} row(s) affected. Commit needed in service.)")
            # No flush or commit needed here. Session objects are NOT updated.
            return rows_affected > 0
        except SQLAlchemyError as e:
            logger.error(f"خطا در آپدیت وضعیت پنل {panel_id}: {e}. (Error updating panel status for panel {panel_id}: {e}).")
            raise # Rollback handled by service layer

    # --- Delete Operations ---

    async def delete_panel(self, panel_id: int) -> bool:
        """
        حذف یک پنل با استفاده از شناسه آن.
        Deletes a panel using its ID.

        Args:
            panel_id (int): شناسه پنل مورد نظر برای حذف.
                             The ID of the panel to delete.

        Returns:
            bool: True اگر پنل با موفقیت حذف شد، False در غیر این صورت (مثلاً اگر پنل وجود نداشته باشد).
                  True if the panel was successfully deleted, False otherwise (e.g., if the panel didn't exist).

        Raises:
            SQLAlchemyError: در صورت بروز خطا در عملیات دیتابیس.
                             If a database operation error occurs.
        """
        logger.info(f"در حال تلاش برای حذف پنل با شناسه: {panel_id}. (Attempting to delete panel with ID: {panel_id}).")
        try:
            # Build and execute the delete statement
            stmt = delete(Panel).where(Panel.id == panel_id)
            result = await self.session.execute(stmt)

            # Check if a row was actually deleted
            if result.rowcount > 0:
                await self.session.flush() # Ensure delete is sent to DB
                logger.info(f"پنل با شناسه {panel_id} با موفقیت حذف و flush شد. (Panel with ID {panel_id} deleted and flushed successfully.)")
                return True
            else:
                logger.warning(f"حذف پنل با شناسه {panel_id} انجام نشد. پنل با این شناسه وجود ندارد. (Deletion of panel with ID {panel_id} failed. Panel not found.)")
                return False

        except SQLAlchemyError as e:
            logger.error(f"خطا در حذف پنل با شناسه {panel_id}: {e}. (Error deleting panel with ID {panel_id}: {e}).")
            # Rollback should happen at the service layer
            raise

    # --- Bulk Operations ---

    async def bulk_add_inbounds(self, inbounds_data: List[Dict[str, Any]]) -> List[Inbound]:
        """
        افزودن دسته‌ای اینباندها به دیتابیس.
        Bulk adds inbounds to the database.

        این متد لیستی از دیکشنری‌های داده اینباند را دریافت کرده، آبجکت‌های
        Inbound را ایجاد و به session اضافه می‌کند. سپس `flush` و `refresh`
        را برای ذخیره در دیتابیس و به‌روزرسانی آبجکت‌ها با ID های تولید شده
        فراخوانی می‌کند.

        This method receives a list of inbound data dictionaries, creates
        Inbound objects, adds them to the session, then calls `flush` and
        `refresh` to save to the database and update the objects with
        generated IDs.

        Args:
            inbounds_data (List[Dict[str, Any]]): لیستی از دیکشنری‌های داده اینباند.
                                                  A list of inbound data dictionaries.

        Returns:
            List[Inbound]: لیستی از آبجکت‌های Inbound ایجاد شده و به‌روزشده.
                           A list of the created and refreshed Inbound objects.

        Raises:
            SQLAlchemyError: در صورت بروز خطا در عملیات دیتابیس.
                             If a database operation error occurs.
            ValueError: اگر وضعیت نامعتبر در داده‌ها وجود داشته باشد.
                        If invalid status is present in the data.
        """
        if not inbounds_data:
            logger.info("لیست خالی برای افزودن دسته‌ای اینباند دریافت شد. (Empty list received for bulk adding inbounds.)")
            return []

        logger.info(f"در حال افزودن دسته‌ای {len(inbounds_data)} اینباند. (Attempting to bulk add {len(inbounds_data)} inbounds.)")
        inbounds_to_add = []
        try:
            for data in inbounds_data:
                 # Ensure status is set if provided, otherwise rely on model default
                if 'status' in data and isinstance(data['status'], str):
                    try:
                        data['status'] = InboundStatus[data['status'].upper()]
                    except KeyError as e:
                        logger.error(f"مقدار وضعیت نامعتبر '{data.get('status')}' در داده‌های اینباند برای پنل {data.get('panel_id')}. خطا: {e} (Invalid status value '{data.get('status')}' in inbound data for panel {data.get('panel_id')}. Error: {e})")
                        raise ValueError(f"مقدار وضعیت نامعتبر: {data.get('status')}") from e
                inbounds_to_add.append(Inbound(**data))

            self.session.add_all(inbounds_to_add)
            await self.session.flush() # Send inserts to DB, get IDs
            for inbound in inbounds_to_add: # Refresh each object individually
                 await self.session.refresh(inbound)
            logger.info(f"تعداد {len(inbounds_to_add)} اینباند با موفقیت ایجاد و flush/refresh شدند. (Successfully created and flushed/refreshed {len(inbounds_to_add)} inbounds.)")
            return inbounds_to_add
        except SQLAlchemyError as e:
            logger.error(f"خطا در افزودن دسته‌ای اینباندها: {e}. (Error during bulk adding inbounds: {e}).")
            raise # Rollback handled by service layer

    async def bulk_update_inbounds(self, inbounds_updates: List[Dict[str, Any]]) -> int:
        """
        به‌روزرسانی دسته‌ای اینباندها با استفاده از مقادیر ارائه شده.
        Bulk updates inbounds using the provided values.

        **نکته مهم:** این متد از دستور `UPDATE` مستقیم در دیتابیس استفاده می‌کند
        و آبجکت‌های Inbound که ممکن است از قبل در session موجود باشند را به‌روز
        نمی‌کند. اگر نیاز به کار با آبجکت‌های به‌روزشده در همان تراکنش دارید،
        باید آن‌ها را مجدداً از دیتابیس بخوانید یا از روش آپدیت تکی استفاده کنید.
        این متد `commit` یا `flush` نمی‌کند.

        **Important Note:** This method uses a direct `UPDATE` statement in the
        database and does **not** update Inbound objects that might already exist
        in the current session. If you need to work with the updated objects within
        the same transaction, you must either re-fetch them from the database or
        use an individual update approach. This method does not commit or flush.

        Args:
            inbounds_updates (List[Dict[str, Any]]): لیستی از دیکشنری‌ها. هر دیکشنری
                باید شامل 'id' اینباند و فیلدهایی باشد که باید آپدیت شوند.
                A list of dictionaries. Each dictionary must contain the 'id'
                of the inbound and the fields to be updated.

        Returns:
            int: تعداد رکوردهایی که تحت تأثیر قرار گرفتند (ممکن است صفر باشد).
                 The total number of rows affected across all updates (could be zero).

        Raises:
            SQLAlchemyError: در صورت بروز خطا در عملیات دیتابیس.
                             If a database operation error occurs.
            ValueError: اگر داده‌های ورودی نامعتبر باشند (مثلاً 'id' موجود نباشد).
                        If the input data is invalid (e.g., 'id' is missing).
        """
        if not inbounds_updates:
             logger.info("لیست خالی برای آپدیت دسته‌ای اینباند دریافت شد. (Empty list received for bulk updating inbounds.)")
             return 0

        logger.info(f"در حال آماده سازی آپدیت دسته‌ای برای {len(inbounds_updates)} اینباند. (Preparing bulk update for {len(inbounds_updates)} inbounds).")
        total_rows_affected = 0
        try:
            # We execute updates one by one to get individual row counts,
            # though SQLAlchemy 2.0 might offer more direct bulk update mapping later.
            # This approach avoids complex bulk_update_mappings for now.
            for update_data in inbounds_updates:
                inbound_id = update_data.get('id')
                if inbound_id is None:
                    logger.error("داده‌های آپدیت اینباند فاقد 'id' است. (Inbound update data is missing 'id.') Data: %s", update_data)
                    raise ValueError("هر آیتم آپدیت اینباند باید شامل 'id' باشد. (Each inbound update item must include an 'id'.)")

                values_to_update = {k: v for k, v in update_data.items() if k != 'id'}
                if not values_to_update:
                    logger.warning(f"هیچ فیلدی برای آپدیت اینباند با شناسه {inbound_id} ارائه نشده است. (No fields provided for update for inbound ID {inbound_id}).")
                    continue

                 # Handle status enum conversion
                if 'status' in values_to_update and isinstance(values_to_update['status'], str):
                    try:
                        values_to_update['status'] = InboundStatus[values_to_update['status'].upper()]
                    except KeyError as e:
                         logger.error(f"مقدار وضعیت نامعتبر '{values_to_update['status']}' برای اینباند {inbound_id}. خطا: {e} (Invalid status value '{values_to_update['status']}' for inbound {inbound_id}. Error: {e})")
                         raise ValueError(f"مقدار وضعیت نامعتبر: {values_to_update['status']}") from e

                stmt = (
                    update(Inbound)
                    .where(Inbound.id == inbound_id)
                    .values(**values_to_update)
                    .execution_options(synchronize_session=False) # Important: Don't sync session state
                )
                result = await self.session.execute(stmt)
                rows_affected = result.rowcount
                if rows_affected > 0:
                    logger.debug(f"آپدیت برای اینباند {inbound_id} اجرا شد، {rows_affected} سطر تحت تاثیر قرار گرفت. (Update executed for inbound {inbound_id}, {rows_affected} row(s) affected.)")
                    total_rows_affected += rows_affected
                else:
                     logger.warning(f"آپدیت برای اینباند {inbound_id} هیچ سطری را تحت تاثیر قرار نداد (ممکن است وجود نداشته باشد). (Update for inbound {inbound_id} affected 0 rows (might not exist)).")


            logger.info(f"آپدیت دسته‌ای اینباندها تکمیل شد. مجموع سطرهای تحت تاثیر: {total_rows_affected}. نیاز به commit در سرویس. (Bulk inbound update completed. Total rows affected: {total_rows_affected}. Commit needed in service.)")
            # No flush or commit needed here as execute() runs the UPDATE directly.
            # Session objects are NOT updated by this.
            return total_rows_affected
        except SQLAlchemyError as e:
            logger.error(f"خطا در اجرای آپدیت دسته‌ای اینباندها: {e}. (Error executing bulk inbound update: {e}).")
            raise # Rollback handled by service layer

    async def update_inbounds_status_by_panel_id(self, panel_id: int, status: InboundStatus) -> int:
        """
        به‌روزرسانی وضعیت تمام اینباندهای مربوط به یک پنل خاص.
        Updates the status of all inbounds associated with a specific panel.

        **نکته مهم:** این متد از دستور `UPDATE` مستقیم در دیتابیس استفاده می‌کند
        و آبجکت‌های Inbound که ممکن است از قبل در session موجود باشند را به‌روز
        نمی‌کند. این متد `commit` یا `flush` نمی‌کند.

        **Important Note:** This method uses a direct `UPDATE` statement in the
        database and does **not** update Inbound objects that might already exist
        in the current session. This method does not commit or flush.

        Args:
            panel_id (int): شناسه پنلی که اینباندهای آن باید آپدیت شوند.
                             The ID of the panel whose inbounds should be updated.
            status (InboundStatus): وضعیت جدید برای اینباندها.
                                   The new status for the inbounds.

        Returns:
            int: تعداد رکوردهای اینباندی که وضعیت آن‌ها تغییر کرد.
                 The number of inbound records whose status was changed.

        Raises:
            SQLAlchemyError: در صورت بروز خطا در عملیات دیتابیس.
                             If a database operation error occurs.
        """
        logger.info(f"در حال آماده سازی آپدیت وضعیت اینباندها به '{status.name}' برای پنل {panel_id}. (Preparing to update inbounds status to '{status.name}' for panel {panel_id}).")
        try:
            stmt = (
                update(Inbound)
                .where(Inbound.panel_id == panel_id)
                .values(status=status)
                .execution_options(synchronize_session=False) # Important: Don't sync session state
            )
            result = await self.session.execute(stmt)
            rows_affected = result.rowcount
            logger.info(f"آپدیت وضعیت اینباندها برای پنل {panel_id} تکمیل شد. {rows_affected} سطر تحت تاثیر قرار گرفت. نیاز به commit در سرویس. (Inbound status update for panel {panel_id} completed. {rows_affected} row(s) affected. Commit needed in service.)")
            # No flush or commit needed here. Session objects are NOT updated.
            return rows_affected
        except SQLAlchemyError as e:
            logger.error(f"خطا در آپدیت وضعیت اینباندها برای پنل {panel_id}: {e}. (Error updating inbound statuses for panel {panel_id}: {e}).")
            raise # Rollback handled by service layer

# Potential Helper methods can be added below if needed
# Example:
# async def count_active_inbounds(self, panel_id: int) -> int:
#     ...

# Example of how logger might be set up (e.g., in core or main app file)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
# You would typically import the configured logger, not redefine it here. 