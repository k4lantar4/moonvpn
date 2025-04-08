"""
Client Service

This module provides a service layer for managing clients,
including client creation, updating, and proxying operations to panels.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from core.database import get_db
from core.config import get_settings
from api.models import Client, User, Panel, Location, Plan, Settings, ClientMigration
from api.services.panel_service import PanelService

logger = logging.getLogger(__name__)
settings = get_settings()


class ClientService:
    """Service for managing clients.
    
    This service provides methods for:
    - Client creation and management (CRUD operations)
    - Client traffic management
    - Proxying operations to panels via PanelService
    """
    
    def __init__(self, db: AsyncSession = None):
        """Initialize client service.
        
        Args:
            db: Database session (optional, will be created if needed)
        """
        self.db = db
        self.panel_service = PanelService(db)
    
    async def _get_db(self) -> AsyncSession:
        """Get database session, creating one if not provided in constructor.
        
        Returns:
            AsyncSession: Database session
        """
        if self.db is None:
            self.db = await anext(get_db())
        return self.db
    
    async def create_client(self, client_data: Dict[str, Any]) -> Client:
        """Create a new client.
        
        Args:
            client_data: Client data including user_id, plan_id, location_id, etc.
            
        Returns:
            Client: Created client
            
        Raises:
            HTTPException: If creation fails
        """
        db = await self._get_db()
        
        # Get location and verify it exists
        location_id = client_data.get("location_id")
        location = await self._get_location(location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location with ID {location_id} not found"
            )
        
        # Select an appropriate panel for this client
        panel = await self._select_panel_for_client(location_id)
        if not panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active panel found for location {location.name}"
            )
        
        # Get plan and verify it exists
        plan_id = client_data.get("plan_id")
        plan = await self._get_plan(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan with ID {plan_id} not found"
            )
        
        # Get user and verify it exists
        user_id = client_data.get("user_id")
        user = await self._get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Generate UUID for the client
        client_uuid = client_data.get("client_uuid", str(uuid.uuid4()))
        
        # Generate remark using the appropriate pattern
        # Check if we should use new prefix for this location
        use_new_prefix_key = f"USE_NEW_PREFIX_FOR_{location.name}"
        settings = await self.panel_service.get_settings()
        use_new_prefix = settings.get(use_new_prefix_key, "true").lower() == "true"
        
        if use_new_prefix:
            # Using new prefix for newly created clients
            remark = await self._generate_remark(location, user, None, client_data.get("custom_name"))
        else:
            # Keep using old prefix for compatibility
            old_prefix = location.default_remark_prefix or location.name
            # Check if we have a count 
            sequence = await self._get_next_client_id(location_id)
            remark = f"{old_prefix}-{sequence}"
            if client_data.get("custom_name"):
                remark = f"{remark}-{client_data.get('custom_name')}"
        
        # Calculate expiry date based on plan
        now = datetime.now()
        expire_date = now + timedelta(days=plan.days)
        
        # Create client in our DB
        client = Client(
            user_id=user_id,
            panel_id=panel.id,
            location_id=location_id,
            plan_id=plan_id,
            order_id=client_data.get("order_id"),
            client_uuid=client_uuid,
            email=f"{remark}@moonvpn.com",  # Email based on remark for uniqueness
            remark=remark,
            expire_date=expire_date,
            traffic=plan.traffic,
            used_traffic=0,
            status="ACTIVE",
            protocol=client_data.get("protocol", "vmess"),
            is_trial=client_data.get("is_trial", False),
            created_at=now
        )
        
        db.add(client)
        await db.commit()
        await db.refresh(client)
        
        # Now create the client on the panel using PanelService
        panel_client_data = {
            "uuid": client_uuid,
            "email": client.email,
            "alter_id": 0,
            "limit_ip": client_data.get("limit_ip", 0),
            "total_gb": plan.traffic,
            "remark": remark,
            "enable": True,
            "expire_time": int(expire_date.timestamp())
        }
        
        # Get inbound ID from location or client data
        inbound_id = client_data.get("inbound_id", location.default_inbound_id)
        if not inbound_id:
            # No inbound specified, try to get one from the panel
            inbounds = await self.panel_service.get_panel_inbounds(panel.id)
            if inbounds and len(inbounds) > 0:
                inbound_id = inbounds[0].get("id")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No inbound ID specified and none found on panel"
                )
        
        # Create on panel
        try:
            result = await self.panel_service.add_panel_client(panel.id, inbound_id, panel_client_data)
            
            # Update client with panel data if needed
            # For example, we might want to store the subscription URL
            if "subscription_url" in result:
                client.subscription_url = result["subscription_url"]
                await db.commit()
                await db.refresh(client)
            
        except HTTPException as e:
            # If panel creation fails, delete the client from our DB
            await db.delete(client)
            await db.commit()
            raise e
        
        return client
    
    async def get_client(self, client_id: int) -> Optional[Client]:
        """Get a client by ID.
        
        Args:
            client_id: Client ID
            
        Returns:
            Optional[Client]: Client if found, None otherwise
        """
        db = await self._get_db()
        result = await db.execute(
            select(Client)
            .options(
                selectinload(Client.user),
                selectinload(Client.panel),
                selectinload(Client.location),
                selectinload(Client.plan)
            )
            .filter(Client.id == client_id)
        )
        return result.scalars().first()
    
    async def get_client_by_remark(self, remark: str) -> Optional[Client]:
        """Get a client by remark.
        
        Args:
            remark: Client remark
            
        Returns:
            Optional[Client]: Client if found, None otherwise
        """
        db = await self._get_db()
        result = await db.execute(
            select(Client)
            .options(
                selectinload(Client.user),
                selectinload(Client.panel),
                selectinload(Client.location),
                selectinload(Client.plan)
            )
            .filter(Client.remark == remark)
        )
        return result.scalars().first()
    
    async def get_client_config(self, client_id: int) -> Dict[str, Any]:
        """Get client configuration details including connection information.
        
        Args:
            client_id: Client ID
            
        Returns:
            Dict[str, Any]: Client configuration
            
        Raises:
            HTTPException: If client not found
        """
        client = await self.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found"
            )
        
        # Get the correct server details for this client
        server_details = await self.panel_service.get_server_for_remark(client.remark)
        
        if not server_details:
            # Use current panel details
            server_details = {
                "server_ip": client.panel.server_ip,
                "url": client.panel.url,
                "panel_id": client.panel.id
            }
        
        # Get additional configuration details from panel if needed
        # This might include subscription URL, QR codes, etc.
        # But for now, let's just return basic info
        
        return {
            "id": client.id,
            "remark": client.remark,
            "uuid": client.client_uuid,
            "server_ip": server_details["server_ip"],
            "panel_url": server_details["url"], 
            "expire_date": client.expire_date.isoformat(),
            "traffic": client.traffic,
            "used_traffic": client.used_traffic,
            "status": client.status,
            "protocol": client.protocol,
            "subscription_url": client.subscription_url,
            "location": client.location.name if client.location else None,
            "plan": client.plan.name if client.plan else None,
        }
    
    async def update_client_traffic(self, client_id: int) -> Optional[Client]:
        """Update client traffic usage from panel.
        
        Args:
            client_id: Client ID
            
        Returns:
            Optional[Client]: Updated client if found, None otherwise
            
        Raises:
            HTTPException: If update fails
        """
        db = await self._get_db()
        client = await self.get_client(client_id)
        
        if not client:
            return None
        
        try:
            # Get traffic from panel
            result = await self.panel_service.get_client_traffic(client.panel_id, client.email)
            
            # Update client with new traffic data
            if "used_traffic" in result:
                client.used_traffic = result["used_traffic"]
            
            # Check if expired
            if client.expire_date < datetime.now():
                client.status = "EXPIRED"
            
            # Check if traffic exceeded
            if client.used_traffic >= client.traffic:
                client.status = "DISABLED"
            
            await db.commit()
            await db.refresh(client)
            return client
            
        except HTTPException as e:
            logger.error(f"Failed to update client traffic: {e.detail}")
            raise
    
    async def reset_client_traffic(self, client_id: int) -> Optional[Client]:
        """Reset client traffic on panel and in our DB.
        
        Args:
            client_id: Client ID
            
        Returns:
            Optional[Client]: Updated client if found, None otherwise
            
        Raises:
            HTTPException: If reset fails
        """
        db = await self._get_db()
        client = await self.get_client(client_id)
        
        if not client:
            return None
        
        try:
            # Find the inbound ID for this client
            inbounds = await self.panel_service.get_panel_inbounds(client.panel_id)
            inbound_id = None
            
            for inbound in inbounds:
                # Look for client in inbound settings
                if "settings" in inbound and "clients" in inbound["settings"]:
                    for inbound_client in inbound["settings"]["clients"]:
                        if inbound_client.get("email") == client.email:
                            inbound_id = inbound["id"]
                            break
                
                if inbound_id:
                    break
            
            if not inbound_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not find client on panel"
                )
            
            # Reset traffic on panel
            await self.panel_service.reset_client_traffic(client.panel_id, inbound_id, client.email)
            
            # Update client in our DB
            client.used_traffic = 0
            if client.status == "DISABLED" and client.expire_date > datetime.now():
                client.status = "ACTIVE"
            
            await db.commit()
            await db.refresh(client)
            return client
            
        except HTTPException as e:
            logger.error(f"Failed to reset client traffic: {e.detail}")
            raise
    
    async def change_location(self, client_id: int, new_location_id: int, 
                            reason: Optional[str] = None, 
                            performed_by: Optional[int] = None,
                            force: bool = False) -> Client:
        """
        تغییر لوکیشن یک کلاینت با حفظ تاریخچه و انتقال به پنل جدید

        Args:
            client_id: آیدی کلاینت
            new_location_id: آیدی لوکیشن جدید
            reason: دلیل تغییر لوکیشن
            performed_by: آیدی کاربری که درخواست تغییر لوکیشن داده
            force: نادیده گرفتن محدودیت‌های تغییر روزانه

        Returns:
            Client: کلاینت به‌روزشده

        Raises:
            HTTPException: اگر تغییر لوکیشن با خطا مواجه شود
        """
        db = await self._get_db()
        
        # دریافت کلاینت
        client = await self.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"کلاینت با آیدی {client_id} یافت نشد"
            )
        
        # دریافت تنظیمات مربوط به محدودیت تغییر لوکیشن
        settings = await self.panel_service.get_settings()
        max_changes = int(settings.get("MAX_LOCATION_CHANGES_PER_DAY", "3"))
        
        # بررسی محدودیت تغییر لوکیشن روزانه، مگر اینکه force=True باشد
        if not force and not client.can_change_location(max_changes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"محدودیت تغییر لوکیشن روزانه ({max_changes} بار) به پایان رسیده است"
            )
        
        # بررسی یکسان نبودن لوکیشن فعلی و جدید
        if client.location_id == new_location_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="لوکیشن جدید با لوکیشن فعلی یکسان است"
            )

        # دریافت لوکیشن جدید
        new_location = await self._get_location(new_location_id)
        if not new_location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"لوکیشن با آیدی {new_location_id} یافت نشد"
            )
        
        # انتخاب پنل مناسب در لوکیشن جدید
        new_panel = await self._select_panel_for_client(new_location_id)
        if not new_panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"پنل فعالی در لوکیشن {new_location.name} یافت نشد"
            )
        
        # ذخیره اطلاعات قبلی
        old_location_id = client.location_id
        old_panel_id = client.panel_id
        old_remark = client.remark
        old_uuid = client.client_uuid
        
        # اگر اولین تغییر لوکیشن است، مقادیر اولیه را ذخیره کن
        if client.original_location_id is None:
            client.original_location_id = client.location_id
            client.original_remark = client.remark
            client.original_client_uuid = client.client_uuid
        
        # تولید ریمارک جدید بر اساس الگوی تعریف شده
        # استفاده از الگوی migration_remark_pattern، یا اضافه کردن Mn به انتهای ریمارک فعلی
        migration_pattern = new_location.migration_remark_pattern or '{original}-M{count}'
        new_migration_count = client.migration_count + 1
        
        # بررسی آیا الگو استفاده می‌شود
        if '{original}' in migration_pattern and client.original_remark:
            base_remark = client.original_remark
        else:
            base_remark = client.remark.split('-M')[0] if '-M' in client.remark else client.remark
        
        # تولید ریمارک جدید با جایگزینی متغیرها
        new_remark = migration_pattern.replace('{original}', base_remark)
        new_remark = new_remark.replace('{count}', str(new_migration_count))
        new_remark = new_remark.replace('{location}', new_location.name)
        if client.custom_name:
            new_remark = new_remark.replace('{custom}', client.custom_name)
        else:
            new_remark = new_remark.replace('-{custom}', '')
            new_remark = new_remark.replace('{custom}', '')
        
        # تولید UUID جدید
        new_uuid = str(uuid.uuid4())
        
        # به‌روزرسانی اطلاعات کلاینت
        client.previous_panel_id = client.panel_id
        client.panel_id = new_panel.id
        client.location_id = new_location_id
        client.client_uuid = new_uuid
        client.email = f"{new_remark}@moonvpn.com"
        client.remark = new_remark
        client.migration_count = new_migration_count
        client.last_location_change = datetime.now()
        
        # افزایش شمارنده تغییرات روزانه
        if client.location_changes_reset_date and client.location_changes_reset_date.date() == datetime.now().date():
            client.location_changes_today += 1
        else:
            client.location_changes_today = 1
            client.location_changes_reset_date = datetime.now()
        
        # افزودن رکورد به تاریخچه مهاجرت
        client.add_migration_record(
            old_location_id=old_location_id, 
            new_location_id=new_location_id,
            old_panel_id=old_panel_id, 
            new_panel_id=new_panel.id,
            old_remark=old_remark, 
            new_remark=new_remark,
            reason=reason
        )
        
        # ایجاد رکورد مهاجرت در جدول تاریخچه
        migration = ClientMigration(
            client_id=client.id,
            user_id=client.user_id,
            old_location_id=old_location_id,
            new_location_id=new_location_id,
            old_panel_id=old_panel_id,
            new_panel_id=new_panel.id,
            old_remark=old_remark,
            new_remark=new_remark,
            old_uuid=old_uuid,
            new_uuid=new_uuid,
            reason=reason,
            transferred_traffic=client.traffic - client.used_traffic,
            transferred_expiry=True,
            performed_by=performed_by,
            created_at=datetime.now()
        )
        
        db.add(migration)
        
        # ذخیره تغییرات در دیتابیس
        await db.commit()
        await db.refresh(client)
        
        # ایجاد کلاینت در پنل جدید
        panel_client_data = {
            "uuid": new_uuid,
            "email": client.email,
            "alter_id": 0,
            "limit_ip": 0,  # می‌توان از مقدار قبلی استفاده کرد
            "total_gb": client.traffic,
            "remark": new_remark,
            "enable": True,
            "expire_time": int(client.expire_date.timestamp())
        }
        
        # دریافت inbound_id مناسب
        inbound_id = new_location.default_inbound_id
        if not inbound_id:
            # اگر inbound_id تعیین نشده، اولین inbound را استفاده کن
            inbounds = await self.panel_service.get_panel_inbounds(new_panel.id)
            if inbounds and len(inbounds) > 0:
                inbound_id = inbounds[0].get("id")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="هیچ inbound_id برای پنل جدید یافت نشد"
                )
        
        # ایجاد کلاینت در پنل جدید
        try:
            result = await self.panel_service.add_panel_client(new_panel.id, inbound_id, panel_client_data)
            
            # به‌روزرسانی اطلاعات اضافی کلاینت
            if "subscription_url" in result:
                client.subscription_url = result["subscription_url"]
                await db.commit()
                await db.refresh(client)
            
            # حذف کلاینت از پنل قبلی
            try:
                # پیدا کردن inbound_id در پنل قبلی
                old_inbounds = await self.panel_service.get_panel_inbounds(old_panel_id)
                old_inbound_id = None
                
                for inbound in old_inbounds:
                    if "settings" in inbound and "clients" in inbound["settings"]:
                        for panel_client in inbound["settings"]["clients"]:
                            if panel_client.get("email") == f"{old_remark}@moonvpn.com":
                                old_inbound_id = inbound["id"]
                                break
                    
                    if old_inbound_id:
                        break
                
                if old_inbound_id:
                    await self.panel_service.delete_panel_client(old_panel_id, old_inbound_id, old_uuid)
            except Exception as e:
                # خطای حذف از پنل قبلی نباید منجر به خطا در کل فرآیند شود
                logger.error(f"خطا در حذف کلاینت از پنل قبلی: {str(e)}")
            
        except HTTPException as e:
            # در صورت خطا در ایجاد کلاینت در پنل جدید، وضعیت قبلی را بازگردان
            client.panel_id = old_panel_id
            client.location_id = old_location_id
            client.client_uuid = old_uuid
            client.email = f"{old_remark}@moonvpn.com"
            client.remark = old_remark
            client.migration_count -= 1
            client.previous_panel_id = None
            
            # کاهش شمارنده تغییرات روزانه
            client.location_changes_today -= 1
            
            # حذف آخرین رکورد تاریخچه
            history = client.migration_history_list
            if history:
                history.pop()
                client.migration_history = json.dumps(history)
            
            # حذف رکورد مهاجرت
            await db.delete(migration)
            
            await db.commit()
            await db.refresh(client)
            
            # ارسال خطا به کاربر
            raise HTTPException(
                status_code=e.status_code,
                detail=f"خطا در ایجاد کلاینت در پنل جدید: {e.detail}"
            )
        
        return client
    
    async def _get_location(self, location_id: int) -> Optional[Location]:
        """Get a location by ID.
        
        Args:
            location_id: Location ID
            
        Returns:
            Optional[Location]: Location if found, None otherwise
        """
        db = await self._get_db()
        result = await db.execute(
            select(Location).filter(Location.id == location_id)
        )
        return result.scalars().first()
    
    async def _get_plan(self, plan_id: int) -> Optional[Plan]:
        """Get a plan by ID.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Optional[Plan]: Plan if found, None otherwise
        """
        db = await self._get_db()
        result = await db.execute(
            select(Plan).filter(Plan.id == plan_id)
        )
        return result.scalars().first()
    
    async def _get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        db = await self._get_db()
        result = await db.execute(
            select(User).filter(User.id == user_id)
        )
        return result.scalars().first()
    
    async def _select_panel_for_client(self, location_id: int) -> Optional[Panel]:
        """Select an appropriate panel for a new client.
        
        Args:
            location_id: Location ID
            
        Returns:
            Optional[Panel]: Selected panel if found, None otherwise
        """
        db = await self._get_db()
        
        # Get all active panels for this location
        result = await db.execute(
            select(Panel)
            .filter(
                (Panel.location_id == location_id) &
                (Panel.is_active == True) &
                (Panel.is_healthy == True)
            )
            .order_by(
                Panel.current_clients.asc(),  # Prioritize panels with fewer clients
                Panel.priority.desc()         # Then by priority
            )
        )
        
        panels = result.scalars().all()
        
        if not panels:
            return None
        
        # Return the first panel (least loaded)
        return panels[0]
    
    async def _generate_remark(self, location: Location, user: User, 
                             sequence: Optional[int] = None, 
                             custom_name: Optional[str] = None) -> str:
        """Generate a remark for a client based on location and user.
        
        Args:
            location: Location
            user: User
            sequence: Optional sequence number (if None, will be generated)
            custom_name: Optional custom name part
            
        Returns:
            str: Generated remark
        """
        if sequence is None:
            sequence = await self._get_next_client_id(location.id)
        
        # Get prefix from location
        prefix = location.default_remark_prefix or location.name
        
        # Form the base remark
        remark = f"{prefix}-{sequence}"
        
        # Add custom name if provided
        if custom_name:
            remark = f"{remark}-{custom_name}"
            
        return remark
    
    async def _get_next_client_id(self, location_id: int) -> int:
        """Get the next client ID sequence for a location.
        
        Args:
            location_id: Location ID
            
        Returns:
            int: Next client ID
        """
        db = await self._get_db()
        
        # Get the sequence for this location
        result = await db.execute(
            select(ClientIdSequence)
            .filter(ClientIdSequence.location_id == location_id)
            .with_for_update()  # Lock the row to prevent race conditions
        )
        
        sequence = result.scalars().first()
        
        if sequence:
            # Increment the existing sequence
            next_id = sequence.last_id + 1
            sequence.last_id = next_id
        else:
            # Create a new sequence
            next_id = 1
            sequence = ClientIdSequence(
                location_id=location_id,
                last_id=next_id
            )
            db.add(sequence)
        
        await db.commit()
        
        return next_id
    
    async def get_client_migrations(self, client_id: int) -> List[Dict[str, Any]]:
        """دریافت تاریخچه تغییرات لوکیشن یک کلاینت
        
        Args:
            client_id: آیدی کلاینت
            
        Returns:
            List[Dict[str, Any]]: لیستی از تغییرات لوکیشن
        """
        db = await self._get_db()
        
        # جستجوی کلاینت و بررسی وجود آن
        client = await self.get_client(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"کلاینت با آیدی {client_id} یافت نشد"
            )
        
        # دریافت رکوردهای تاریخچه از جدول مهاجرت‌ها
        query = (
            select(ClientMigration)
            .where(ClientMigration.client_id == client_id)
            .order_by(ClientMigration.created_at.desc())
        )
        
        result = await db.execute(query)
        migrations = result.scalars().all()
        
        # افزودن نام‌های لوکیشن‌ها به نتیجه
        migration_data = []
        for migration in migrations:
            # دریافت نام لوکیشن قدیم
            old_location = await self._get_location(migration.old_location_id)
            old_location_name = old_location.name if old_location else "Unknown"
            
            # دریافت نام لوکیشن جدید
            new_location = await self._get_location(migration.new_location_id)
            new_location_name = new_location.name if new_location else "Unknown"
            
            # دریافت نام کاربر مجری تغییر (در صورت وجود)
            performed_by_name = None
            if migration.performed_by:
                admin = await self._get_user(migration.performed_by)
                if admin:
                    performed_by_name = admin.username
            
            # تبدیل رکورد به دیکشنری با اطلاعات اضافی
            migration_dict = {
                "id": migration.id,
                "client_id": migration.client_id,
                "old_location_id": migration.old_location_id,
                "old_location_name": old_location_name,
                "new_location_id": migration.new_location_id,
                "new_location_name": new_location_name,
                "old_panel_id": migration.old_panel_id,
                "new_panel_id": migration.new_panel_id,
                "old_remark": migration.old_remark,
                "new_remark": migration.new_remark,
                "old_uuid": migration.old_uuid,
                "new_uuid": migration.new_uuid,
                "reason": migration.reason,
                "transferred_traffic": migration.transferred_traffic,
                "transferred_expiry": migration.transferred_expiry,
                "created_at": migration.created_at.isoformat() if migration.created_at else None,
                "performed_by": migration.performed_by,
                "performed_by_name": performed_by_name,
            }
            
            migration_data.append(migration_dict)
        
        # همچنین اطلاعات ذخیره شده در فیلد migration_history کلاینت را اضافه می‌کنیم
        # این به طور معمول برای مهاجرت‌های قدیمی‌تر استفاده می‌شود
        if client.migration_history:
            try:
                historic_migrations = client.migration_history_list
                for historic in historic_migrations:
                    # اضافه کردن هر رکورد تاریخی اگر در نتایج فعلی وجود ندارد
                    
                    # دریافت نام لوکیشن قدیم
                    old_location_id = historic.get("old_location_id")
                    old_location_name = "Unknown"
                    if old_location_id:
                        old_location = await self._get_location(old_location_id)
                        if old_location:
                            old_location_name = old_location.name
                    
                    # دریافت نام لوکیشن جدید
                    new_location_id = historic.get("new_location_id")
                    new_location_name = "Unknown"
                    if new_location_id:
                        new_location = await self._get_location(new_location_id)
                        if new_location:
                            new_location_name = new_location.name
                    
                    # اضافه کردن نام‌های لوکیشن‌ها به دیکشنری
                    historic["old_location_name"] = old_location_name
                    historic["new_location_name"] = new_location_name
                    
                    # بررسی تکراری نبودن رکورد
                    is_duplicate = False
                    for existing in migration_data:
                        if (existing.get("old_remark") == historic.get("old_remark") and
                            existing.get("new_remark") == historic.get("new_remark") and
                            existing.get("created_at") == historic.get("created_at")):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        migration_data.append(historic)
            except Exception as e:
                logger.error(f"خطا در پردازش تاریخچه مهاجرت کلاینت {client_id}: {str(e)}")
        
        # مرتب‌سازی تاریخچه بر اساس زمان (نزولی - جدیدترین اول)
        migration_data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return migration_data 