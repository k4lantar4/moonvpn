from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from db.models.client_renewal_log import ClientRenewalLog
from db.models.user import User
from db.models.client_account import ClientAccount

class ClientRenewalLogService:
    """Service for handling client renewal logs."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_last_logs(self, limit: int = 10) -> List[ClientRenewalLog]:
        """
        Get the last renewal logs ordered by creation date.
        
        Args:
            limit (int): Maximum number of logs to return
            
        Returns:
            List[ClientRenewalLog]: List of renewal logs
        """
        query = (
            select(ClientRenewalLog)
            .options(
                joinedload(ClientRenewalLog.user),
                joinedload(ClientRenewalLog.client)
            )
            .order_by(ClientRenewalLog.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().unique()) 