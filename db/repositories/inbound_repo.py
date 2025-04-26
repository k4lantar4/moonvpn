from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import logging

from db.models.inbound import Inbound, InboundStatus
from db.models.panel import Panel
from db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class InboundRepository(BaseRepository[Inbound]):
    """
    ریپازیتوری برای عملیات مرتبط با inboundها در دیتابیس.
    Repository for inbound-related database operations.

    این ریپازیتوری مسئولیت تمام تعاملات مستقیم با جدول `inbound` را در دیتابیس بر عهده دارد.
    تمامی متدها آسنکرون هستند و از `AsyncSession` برای ارتباط با دیتابیس استفاده می‌کنند.

    **نکته مهم:** این ریپازیتوری هیچگاه تراکنش‌ها را `commit` نمی‌کند.
    عملیات `commit` باید در لایه سرویس انجام شود. در صورت نیاز به دریافت
    شناسه‌های تولید شده توسط دیتابیس یا به‌روزرسانی وضعیت آبجکت‌ها پس از
    عملیات نوشتن، از `flush` و `refresh` استفاده می‌شود.
    """

    def __init__(self, session: AsyncSession):
        """
        سازنده ریپازیتوری inbound.
        Initializes the Inbound Repository.

        Args:
            session (AsyncSession): نشست آسنکرون برای ارتباط با دیتابیس.
                                     The asynchronous session for database interaction.
        """
        super().__init__(session, Inbound)
        logger.debug("InboundRepository مقداردهی اولیه شد. (InboundRepository initialized.)")

    async def get_by_remote_id_and_panel(self, remote_id: int, panel_id: int) -> Optional[Inbound]:
        """
        دریافت inbound بر اساس remote_id و panel_id.
        فقط inbound‌های غیرحذف‌شده را برمی‌گرداند.

        Args:
            remote_id (int): شناسه inbound در پنل خارجی (remote_id).
            panel_id (int): شناسه پنل.

        Returns:
            Optional[Inbound]: آبجکت Inbound در صورت یافت شدن، در غیر این صورت None.
        """
        logger.debug(f"در حال دریافت inbound با remote_id: {remote_id} از پنل: {panel_id}. (Fetching inbound with remote_id: {remote_id} from panel: {panel_id}).")
        try:
            query = select(self.model).where(
                self.model.remote_id == remote_id,
                self.model.panel_id == panel_id,
                self.model.status != InboundStatus.DELETED
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت inbound با remote_id {remote_id} از پنل {panel_id}: {e}. (Error fetching inbound with remote_id {remote_id} from panel {panel_id}: {e}).")
            raise

    async def get_by_panel_id(self, panel_id: int, status: Optional[InboundStatus] = None) -> List[Inbound]:
        """
        دریافت لیست تمام inboundهای مرتبط با یک پنل خاص، با امکان فیلتر بر اساس وضعیت.

        Args:
            panel_id (int): شناسه پنل.
            status (Optional[InboundStatus]): وضعیت inbound برای فیلتر (اختیاری).

        Returns:
            List[Inbound]: لیستی از آبجکت‌های Inbound مطابق با فیلتر.
        """
        logger.debug(f"در حال دریافت inboundها برای پنل {panel_id} با وضعیت: {status if status else 'همه'}")
        try:
            query = select(self.model).where(self.model.panel_id == panel_id)
            if status is not None:
                query = query.where(self.model.status == status)
            query = query.order_by(self.model.id)  # مرتب‌سازی بر اساس شناسه
            result = await self.session.execute(query)
            inbounds = list(result.scalars().all())
            logger.debug(f"تعداد {len(inbounds)} inbound برای پنل {panel_id} دریافت شد.")
            return inbounds
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت inboundهای پنل {panel_id}: {e}", exc_info=True)
            raise

    async def get_active_inbounds(self) -> List[Inbound]:
        """
        دریافت لیست تمام inboundهای فعال.

        Returns:
            List[Inbound]: لیستی از آبجکت‌های Inbound فعال.
        """
        logger.debug("در حال دریافت inboundهای فعال.")
        try:
            query = select(self.model).where(self.model.status == InboundStatus.ACTIVE).order_by(self.model.id)
            result = await self.session.execute(query)
            inbounds = list(result.scalars().all())
            logger.debug(f"تعداد {len(inbounds)} inbound فعال دریافت شد.")
            return inbounds
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت inboundهای فعال: {e}", exc_info=True)
            raise

    async def create_inbound(self, inbound_data: Dict[str, Any]) -> Inbound:
        """
        ایجاد یک inbound جدید در دیتابیس.

        Args:
            inbound_data (Dict[str, Any]): دیکشنری حاوی داده‌های inbound جدید.

        Returns:
            Inbound: آبجکت Inbound ایجاد شده.
        """
        logger.info(f"در حال ایجاد inbound جدید برای پنل ID: {inbound_data.get('panel_id', 'N/A')}")
        try:
            # تبدیل وضعیت از رشته به Enum در صورت نیاز
            if 'status' in inbound_data and isinstance(inbound_data['status'], str):
                inbound_data['status'] = InboundStatus[inbound_data['status'].upper()]

            inbound = Inbound(**inbound_data)
            self.session.add(inbound)
            await self.session.flush()  # ارسال دستور به دیتابیس، دریافت ID
            await self.session.refresh(inbound)  # به‌روزرسانی آبجکت با مقادیر دیتابیس
            logger.info(f"inbound جدید با ID {inbound.id} برای پنل {inbound.panel_id} با موفقیت ایجاد شد.")
            return inbound
        except SQLAlchemyError as e:
            logger.error(f"خطا در ایجاد inbound جدید: {e}", exc_info=True)
            # Rollback باید در لایه سرویس انجام شود
            raise
        except KeyError as e:
            logger.error(f"مقدار نامعتبر برای وضعیت inbound ارائه شده: {inbound_data.get('status')}. خطا: {e}")
            raise ValueError(f"مقدار وضعیت نامعتبر: {inbound_data.get('status')}") from e

    async def bulk_add_inbounds(self, inbounds_data: List[Dict[str, Any]]) -> int:
        """
        افزودن دسته‌ای inboundها به دیتابیس.

        Args:
            inbounds_data (List[Dict[str, Any]]): لیستی از دیکشنری‌های داده inbound.

        Returns:
            int: تعداد inboundهای اضافه شده.
        """
        if not inbounds_data:
            logger.info("لیست خالی برای افزودن دسته‌ای inbound دریافت شد.")
            return 0

        logger.info(f"در حال افزودن دسته‌ای {len(inbounds_data)} inbound.")
        inbounds_to_add = []
        try:
            for data in inbounds_data:
                # تبدیل وضعیت از رشته به Enum در صورت نیاز
                if 'status' in data and isinstance(data['status'], str):
                    try:
                        data['status'] = InboundStatus[data['status'].upper()]
                    except KeyError as e:
                        logger.error(f"مقدار وضعیت نامعتبر '{data.get('status')}' در داده‌های inbound. خطا: {e}")
                        raise ValueError(f"مقدار وضعیت نامعتبر: {data.get('status')}") from e
                inbounds_to_add.append(Inbound(**data))

            self.session.add_all(inbounds_to_add)
            await self.session.flush()  # ارسال دستورات به دیتابیس، دریافت IDها
            for inbound in inbounds_to_add:
                await self.session.refresh(inbound)  # به‌روزرسانی هر آبجکت با مقادیر دیتابیس
            logger.info(f"تعداد {len(inbounds_to_add)} inbound با موفقیت ایجاد و flush شدند.")
            return len(inbounds_to_add)
        except SQLAlchemyError as e:
            logger.error(f"خطا در افزودن دسته‌ای inboundها: {e}", exc_info=True)
            # Rollback باید در لایه سرویس انجام شود
            raise

    async def bulk_update_inbounds(self, inbounds_updates: List[Dict[str, Any]]) -> int:
        """
        به‌روزرسانی دسته‌ای inboundها با استفاده از مقادیر ارائه شده.

        **نکته مهم:** این متد از دستور `UPDATE` مستقیم در دیتابیس استفاده می‌کند
        و آبجکت‌های Inbound که ممکن است از قبل در session موجود باشند را به‌روز
        نمی‌کند. این متد `commit` نمی‌کند.

        Args:
            inbounds_updates (List[Dict[str, Any]]): لیستی از دیکشنری‌ها. هر دیکشنری
                باید شامل 'id' inbound و فیلدهایی باشد که باید آپدیت شوند.

        Returns:
            int: تعداد رکوردهایی که تحت تأثیر قرار گرفتند.
        """
        if not inbounds_updates:
            logger.info("لیست خالی برای آپدیت دسته‌ای inbound دریافت شد.")
            return 0

        logger.info(f"در حال آماده سازی آپدیت دسته‌ای برای {len(inbounds_updates)} inbound.")
        total_rows_affected = 0
        try:
            # آپدیت تک به تک برای دریافت تعداد رکوردهای تحت تاثیر
            for update_data in inbounds_updates:
                inbound_id = update_data.get('id')
                if inbound_id is None:
                    logger.error(f"داده‌های آپدیت inbound فاقد 'id' است. (Inbound update data is missing 'id') Data: {update_data}")
                    raise ValueError("هر آیتم آپدیت inbound باید شامل 'id' باشد.")

                values_to_update = {k: v for k, v in update_data.items() if k != 'id'}
                if not values_to_update:
                    logger.warning(f"هیچ فیلدی برای آپدیت inbound با شناسه {inbound_id} ارائه نشده است.")
                    continue

                # تبدیل وضعیت از رشته به Enum در صورت نیاز
                if 'status' in values_to_update and isinstance(values_to_update['status'], str):
                    try:
                        values_to_update['status'] = InboundStatus[values_to_update['status'].upper()]
                    except KeyError as e:
                        logger.error(f"مقدار وضعیت نامعتبر '{values_to_update['status']}' برای inbound {inbound_id}. خطا: {e}")
                        raise ValueError(f"مقدار وضعیت نامعتبر: {values_to_update['status']}") from e

                stmt = (
                    update(Inbound)
                    .where(Inbound.id == inbound_id)
                    .values(**values_to_update)
                    .execution_options(synchronize_session=False)  # عدم همگام‌سازی با وضعیت session
                )
                result = await self.session.execute(stmt)
                rows_affected = result.rowcount
                if rows_affected > 0:
                    logger.debug(f"آپدیت برای inbound {inbound_id} اجرا شد، {rows_affected} سطر تحت تاثیر قرار گرفت.")
                    total_rows_affected += rows_affected
                else:
                    logger.warning(f"آپدیت برای inbound {inbound_id} هیچ سطری را تحت تاثیر قرار نداد (ممکن است وجود نداشته باشد).")

            logger.info(f"آپدیت دسته‌ای inboundها تکمیل شد. مجموع سطرهای تحت تاثیر: {total_rows_affected}.")
            # نیازی به flush نیست زیرا execute دستور UPDATE را مستقیماً اجرا می‌کند.
            return total_rows_affected
        except SQLAlchemyError as e:
            logger.error(f"خطا در اجرای آپدیت دسته‌ای inboundها: {e}", exc_info=True)
            # Rollback باید در لایه سرویس انجام شود
            raise

    async def update_inbound_status(self, remote_id: int, panel_id: int, status: InboundStatus) -> bool:
        """
        به‌روزرسانی وضعیت یک inbound بر اساس remote_id و panel_id.

        Args:
            remote_id (int): شناسه inbound در پنل خارجی.
            panel_id (int): شناسه پنل.
            status (InboundStatus): وضعیت جدید inbound.

        Returns:
            bool: True اگر آپدیت موفق بود، False در غیر این صورت.
        """
        logger.info(f"در حال به‌روزرسانی وضعیت inbound با remote_id {remote_id} در پنل {panel_id} به {status.value}")
        try:
            stmt = (
                update(Inbound)
                .where(
                    and_(
                        Inbound.remote_id == remote_id,
                        Inbound.panel_id == panel_id
                    )
                )
                .values(status=status)
                .execution_options(synchronize_session=False)
            )
            result = await self.session.execute(stmt)
            rows_affected = result.rowcount
            success = rows_affected > 0
            if success:
                logger.info(f"وضعیت inbound با remote_id {remote_id} در پنل {panel_id} با موفقیت به {status.value} تغییر یافت.")
            else:
                logger.warning(f"inbound با remote_id {remote_id} در پنل {panel_id} یافت نشد، آپدیت وضعیت انجام نشد.")
            return success
        except SQLAlchemyError as e:
            logger.error(f"خطا در به‌روزرسانی وضعیت inbound با remote_id {remote_id} در پنل {panel_id}: {e}", exc_info=True)
            # Rollback باید در لایه سرویس انجام شود
            raise

    async def update_inbounds_status_by_panel_id(self, panel_id: int, status: InboundStatus) -> int:
        """
        به‌روزرسانی وضعیت تمام inboundهای مرتبط با یک پنل خاص.

        Args:
            panel_id (int): شناسه پنل.
            status (InboundStatus): وضعیت جدید برای inboundها.

        Returns:
            int: تعداد رکوردهای inbound که وضعیت آن‌ها تغییر کرد.
        """
        logger.info(f"در حال آماده سازی آپدیت وضعیت inboundها به '{status.value}' برای پنل {panel_id}.")
        try:
            stmt = (
                update(Inbound)
                .where(Inbound.panel_id == panel_id)
                .values(status=status)
                .execution_options(synchronize_session=False)
            )
            result = await self.session.execute(stmt)
            rows_affected = result.rowcount
            logger.info(f"آپدیت وضعیت inboundها برای پنل {panel_id} تکمیل شد. {rows_affected} سطر تحت تاثیر قرار گرفت.")
            return rows_affected
        except SQLAlchemyError as e:
            logger.error(f"خطا در آپدیت وضعیت inboundها برای پنل {panel_id}: {e}", exc_info=True)
            # Rollback باید در لایه سرویس انجام شود
            raise 