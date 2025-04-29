from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from db.repositories.admin_permission_repo import AdminPermissionRepository
from db.models.admin_permission import AdminPermission
from db.models.user import User, UserRole

class AdminPermissionService:
    def __init__(self, session: AsyncSession):
        self.repo = AdminPermissionRepository(session)
        self.session = session

    async def get_permissions(self, user: User) -> Optional[AdminPermission]:
        if user.role == UserRole.SUPERADMIN:
            # سوپرادمین همه مجوزها را دارد
            return None
        return await self.repo.get_by_user_id(user.id)

    async def has_permission(self, user: User, permission: str) -> bool:
        if user.role == UserRole.SUPERADMIN:
            return True
        perms = await self.repo.get_by_user_id(user.id)
        if not perms:
            return False
        return getattr(perms, permission, False)

    async def set_permissions(self, user_id: int, **permissions) -> AdminPermission:
        return await self.repo.create_or_update(user_id, **permissions) 