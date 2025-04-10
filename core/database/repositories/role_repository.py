# core/database/repositories/role_repo.py
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Role  # Assuming Role model is in core.database.models
from core.database.repositories.base_repo import BaseRepository
# Assuming schemas are defined elsewhere, adjust imports if needed
# from core.schemas.role import RoleCreate, RoleUpdate

# Placeholder schemas if real ones aren't available yet
from pydantic import BaseModel
class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
# End Placeholder schemas

class RoleRepository(BaseRepository[Role, RoleCreate, RoleUpdate]):
    """
    Repository for Role model operations.
    Inherits common CRUD operations from BaseRepository.
    """

    def __init__(self):
        super().__init__(model=Role)

    async def get_by_name(
        self, db_session: AsyncSession, *, name: str
    ) -> Optional[Role]:
        """
        Retrieves a single role record by its name.

        Args:
            db_session: The database session.
            name: The name of the role to retrieve.

        Returns:
            The Role model instance if found, otherwise None.
        """
        return await self.get_by_attributes(db_session=db_session, name=name) 