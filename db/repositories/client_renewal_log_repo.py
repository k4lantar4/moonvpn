"""
ماژول مربوط به ریپازیتوری لاگ تمدید کاربر
This module contains the repository for client renewal logs.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

from core.log_config import logger
from db.models.client_renewal_log import ClientRenewalLog
from db.repositories.base_repository import BaseRepository

class ClientRenewalLogRepository(BaseRepository[ClientRenewalLog]):
    """
    ریپازیتوری برای مدیریت لاگ‌های تمدید کاربر در دیتابیس
    Repository for managing client renewal logs in the database.
    """
    def __init__(self, session: AsyncSession):
        """
        مقداردهی اولیه ریپازیتوری لاگ تمدید کاربر
        Initializes the ClientRenewalLog repository.

        Args:
            session: جلسه دیتابیس ناهمگام (AsyncSession)
                     The asynchronous database session.
        """
        super().__init__(session, ClientRenewalLog)
        logger.debug("ClientRenewalLogRepository initialized.")

    async def create_log(self, client_renewal_log_data: Dict[str, Any]) -> Optional[ClientRenewalLog]:
        """
        یک لاگ تمدید جدید در دیتابیس ایجاد می‌کند.
        Creates a new client renewal log in the database.

        Args:
            client_renewal_log_data: دیکشنری حاوی اطلاعات لاگ تمدید
                                      Dictionary containing the renewal log data.

        Returns:
            آبجکت ClientRenewalLog ایجاد شده یا None در صورت بروز خطا
            The created ClientRenewalLog object or None if an error occurs.
        """
        try:
            db_log = ClientRenewalLog(**client_renewal_log_data)
            self.session.add(db_log)
            await self.session.flush()
            await self.session.refresh(db_log) # Refresh to get updated state like ID
            logger.info(f"لاگ تمدید برای کاربر {client_renewal_log_data.get('user_id')} با موفقیت ایجاد شد (Log ID: {db_log.id}).")
            logger.info(f"Client renewal log created successfully for user {client_renewal_log_data.get('user_id')} (Log ID: {db_log.id}).")
            return db_log
        except SQLAlchemyError as e:
            # Note: We don't commit here, so rollback happens automatically if the outer transaction fails.
            logger.error(f"خطا در ایجاد لاگ تمدید: {e}", exc_info=True)
            logger.error(f"Error creating client renewal log: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده در ایجاد لاگ تمدید: {e}", exc_info=True)
            logger.error(f"Unexpected error creating client renewal log: {e}", exc_info=True)
            return None


    async def get_last_logs(self, user_id: int, limit: int = 5) -> List[ClientRenewalLog]:
        """
        آخرین لاگ‌های تمدید برای یک کاربر خاص را بازیابی می‌کند.
        Retrieves the last renewal logs for a specific user.

        Args:
            user_id: شناسه کاربر (User ID)
                     The ID of the user.
            limit: حداکثر تعداد لاگ‌ها برای بازیابی (پیش‌فرض: 5)
                   The maximum number of logs to retrieve (default: 5).

        Returns:
            لیستی از آبجکت‌های ClientRenewalLog یا لیست خالی در صورت نبود لاگ یا بروز خطا
            A list of ClientRenewalLog objects, or an empty list if no logs are found or an error occurs.
        """
        try:
            stmt = (
                select(ClientRenewalLog)
                .where(ClientRenewalLog.user_id == user_id)
                .order_by(desc(ClientRenewalLog.created_at)) # Assuming 'created_at' exists
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            logs = list(result.scalars().all())
            logger.debug(f"بازیابی {len(logs)} لاگ تمدید اخیر برای کاربر {user_id}.")
            logger.debug(f"Retrieved {len(logs)} recent renewal logs for user {user_id}.")
            return logs
        except SQLAlchemyError as e:
            logger.error(f"خطا در بازیابی لاگ‌های تمدید برای کاربر {user_id}: {e}", exc_info=True)
            logger.error(f"Error retrieving renewal logs for user {user_id}: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده در بازیابی لاگ‌های تمدید برای کاربر {user_id}: {e}", exc_info=True)
            logger.error(f"Unexpected error retrieving renewal logs for user {user_id}: {e}", exc_info=True)
            return [] 