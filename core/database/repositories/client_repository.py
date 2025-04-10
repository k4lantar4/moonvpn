from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Any, Sequence
from datetime import datetime, timedelta
from sqlalchemy.sql import func

from .base_repo import BaseRepository
from core.database.models.client_account import ClientAccount # Assuming model
from core.schemas.client_account import ClientAccountCreate, ClientAccountUpdate # Assuming schemas

class ClientRepository(BaseRepository[ClientAccount, ClientAccountCreate, ClientAccountUpdate]):
    def __init__(self):
        # BaseRepository only takes model
        super().__init__(model=ClientAccount)
        # Do NOT store session here

    # Add db_session argument to all custom methods
    async def get_client_with_details(self, db_session: AsyncSession, *, client_id: int) -> Optional[ClientAccount]:
        statement = (
            select(self._model)
            .options(
                selectinload(self._model.user),
                selectinload(self._model.panel),
                selectinload(self._model.location),
                selectinload(self._model.plan),
                selectinload(self._model.inbound)
            )
            .where(self._model.id == client_id)
        )
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id_with_relations(
        self, 
        db_session: AsyncSession, 
        client_id: int, 
        relations: Sequence[Any] = None
    ) -> Optional[ClientAccount]:
        """
        Retrieve a client by ID with specified relationships loaded.
        
        Args:
            db_session: The database session
            client_id: ID of the client to retrieve
            relations: A sequence of relationship attributes to load (e.g., [ClientAccount.user, ClientAccount.plan])
            
        Returns:
            The ClientAccount with loaded relationships, or None if not found
        """
        stmt = select(self._model).where(self._model.id == client_id)
        
        if relations:
            # Add each relationship as a selectinload option
            options = [selectinload(relation) for relation in relations]
            stmt = stmt.options(*options)
            
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def find_by_remark_with_relations(
        self, 
        db_session: AsyncSession, 
        remark: str, 
        relations: Sequence[Any] = None
    ) -> Optional[ClientAccount]:
        """
        Retrieve a client by remark with specified relationships loaded.
        
        Args:
            db_session: The database session
            remark: Remark of the client to retrieve
            relations: A sequence of relationship attributes to load (e.g., [ClientAccount.user, ClientAccount.plan])
            
        Returns:
            The ClientAccount with loaded relationships, or None if not found
        """
        stmt = select(self._model).where(self._model.remark == remark)
        
        if relations:
            # Add each relationship as a selectinload option
            options = [selectinload(relation) for relation in relations]
            stmt = stmt.options(*options)
            
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_services_for_user(self, db_session: AsyncSession, *, user_id: int) -> List[ClientAccount]:
        statement = (
            select(self._model)
            .where(self._model.user_id == user_id)
            .where(self._model.status == 'ACTIVE')
            .order_by(self._model.created_at.desc())
        )
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalars().all()

    async def get_all_services_for_user(self, db_session: AsyncSession, *, user_id: int) -> List[ClientAccount]:
        statement = (
            select(self._model)
            .where(self._model.user_id == user_id)
            .order_by(self._model.created_at.desc())
        )
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalars().all()

    async def find_by_uuid(self, db_session: AsyncSession, *, client_uuid: str) -> Optional[ClientAccount]:
        statement = select(self._model).where(self._model.client_uuid == client_uuid)
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalar_one_or_none()

    async def find_by_remark(self, db_session: AsyncSession, *, remark: str) -> Optional[ClientAccount]:
        statement = select(self._model).where(self._model.remark == remark)
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalar_one_or_none()

    async def get_expired_clients(self, db_session: AsyncSession) -> List[ClientAccount]:
        statement = select(self._model).where(self._model.expire_date < datetime.now()).where(self._model.status == 'ACTIVE')
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalars().all()

    async def get_clients_nearing_expiry(self, db_session: AsyncSession, *, days: int = 3) -> List[ClientAccount]:
        threshold_date = datetime.now() + timedelta(days=days)
        statement = (
            select(self._model)
            .where(self._model.expire_date >= datetime.now())
            .where(self._model.expire_date < threshold_date)
            .where(self._model.status == 'ACTIVE')
        )
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalars().all()

    async def count_active_clients_on_panel(self, db_session: AsyncSession, *, panel_id: int) -> int:
        statement = select(func.count(self._model.id)).where(self._model.panel_id == panel_id).where(self._model.status == 'ACTIVE')
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalar_one()

    async def get_by_user_id(self, db_session: AsyncSession, *, user_id: int) -> List[ClientAccount]:
        statement = select(self._model).where(self._model.user_id == user_id)
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalars().all()

    async def get_by_email(self, db_session: AsyncSession, *, email: str) -> Optional[ClientAccount]:
        statement = select(self._model).where(self._model.email == email)
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_by_subscription_url(self, db_session: AsyncSession, *, url: str) -> Optional[ClientAccount]:
        statement = select(self._model).where(self._model.subscription_url == url)
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalar_one_or_none()

    async def get_expired_services(self, db_session: AsyncSession) -> List[ClientAccount]:
        statement = (
            select(self._model)
            .where(self._model.expire_date < datetime.utcnow(), self._model.status == 'EXPIRED')
        )
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalars().all()

    async def count_active_services_by_panel(self, db_session: AsyncSession, *, panel_id: int) -> int:
        statement = (
            select(func.count())
            .select_from(self._model)
            .where(self._model.panel_id == panel_id, self._model.status == 'ACTIVE')
        )
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalar_one()
        
    async def find_by_panel_inbound_and_email(self, db_session: AsyncSession, *, panel_inbound_id: int, email: str) -> Optional[ClientAccount]:
        statement = select(self._model).where(
            self._model.inbound_id == panel_inbound_id,
            self._model.email == email
        )
        # Use the passed-in session
        result = await db_session.execute(statement)
        return result.scalar_one_or_none() 