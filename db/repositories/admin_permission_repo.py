from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from db.models.admin_permission import AdminPermission

class AdminPermissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> Optional[AdminPermission]:
        query = select(AdminPermission).where(AdminPermission.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_or_update(self, user_id: int, **permissions) -> AdminPermission:
        perm = await self.get_by_user_id(user_id)
        if perm:
            for key, value in permissions.items():
                setattr(perm, key, value)
        else:
            perm = AdminPermission(user_id=user_id, **permissions)
            self.session.add(perm)
        await self.session.commit()
        await self.session.refresh(perm)
        return perm

    async def delete_by_user_id(self, user_id: int) -> bool:
        perm = await self.get_by_user_id(user_id)
        if perm:
            await self.session.delete(perm)
            await self.session.commit()
            return True
        return False 