"""
کلاس کلاینت برای ارتباط با پنل‌های 3x-ui بر پایه AsyncApi
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

# استفاده از کلاس AsyncApi از کتابخانه py3xui
from py3xui import AsyncApi

logger = logging.getLogger(__name__)


class XuiClient:
    """
    کلاس کلاینت برای ارتباط با پنل‌های 3x-ui با استفاده از AsyncApi
    این کلاس یک wrapper سبک روی AsyncApi است
    """
    
    def __init__(self, host: str, username: str, password: str, token: str = ""):
        """
        راه‌اندازی کلاینت با آدرس و اطلاعات ورود پنل
        
        Args:
            host: آدرس پنل (همراه با http/https)
            username: نام کاربری پنل
            password: رمز عبور پنل
            token: توکن احراز هویت (اختیاری)
        """
        # حذف اسلش انتهایی اگر وجود داشته باشد
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.token = token
        
        # ایجاد نمونه AsyncApi
        self.api = AsyncApi(self.host, self.username, self.password, self.token)
        logger.info(f"XuiClient initialized for panel at {self.host}")
    
    async def login(self) -> bool:
        """
        احراز هویت و ورود به پنل
        
        Returns:
            True در صورت موفقیت
        """
        try:
            result = await self.api.login()
            logger.info(f"Successfully logged in to panel at {self.host}")
            return result
        except Exception as e:
            logger.error(f"Failed to login to panel at {self.host}: {e}")
            raise
    
    # --------- مدیریت کلاینت‌ها ---------
    
    async def create_client(self, inbound_id: int, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ایجاد کلاینت جدید در یک inbound خاص
        
        Args:
            inbound_id: شناسه inbound
            client_data: داده‌های کلاینت شامل email، uuid، total_gb و...
            
        Returns:
            اطلاعات کلاینت ایجاد شده
        """
        try:
            result = await self.api.client.create(inbound_id, client_data)
            logger.info(f"Successfully created client in inbound {inbound_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create client in inbound {inbound_id}: {e}")
            raise
    
    async def get_client(self, email: str) -> Dict[str, Any]:
        """
        دریافت اطلاعات یک کلاینت با ایمیل/نام آن
        
        Args:
            email: آدرس ایمیل/نام کلاینت
            
        Returns:
            اطلاعات کلاینت
        """
        try:
            result = await self.api.client.get_by_email(email)
            if result:
                logger.info(f"Successfully retrieved client with email {email}")
            else:
                logger.warning(f"Client with email {email} not found")
            return result
        except Exception as e:
            logger.error(f"Failed to get client with email {email}: {e}")
            raise
    
    async def get_client_by_uuid(self, uuid: str) -> Dict[str, Any]:
        """
        دریافت اطلاعات یک کلاینت با UUID آن
        
        Args:
            uuid: UUID کلاینت
            
        Returns:
            اطلاعات کلاینت
        """
        try:
            result = await self.api.client.get(uuid)
            if result:
                logger.info(f"Successfully retrieved client with UUID {uuid}")
            else:
                logger.warning(f"Client with UUID {uuid} not found")
            return result
        except Exception as e:
            logger.error(f"Failed to get client with UUID {uuid}: {e}")
            raise
    
    async def delete_client(self, uuid: str) -> bool:
        """
        حذف یک کلاینت با UUID آن
        
        Args:
            uuid: UUID کلاینت
            
        Returns:
            True در صورت موفقیت
        """
        try:
            result = await self.api.client.delete(uuid)
            logger.info(f"Successfully deleted client with UUID {uuid}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete client with UUID {uuid}: {e}")
            raise
    
    async def update_client(self, uuid: str, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        به‌روزرسانی اطلاعات یک کلاینت
        
        Args:
            uuid: UUID کلاینت
            client_data: داده‌های جدید کلاینت
            
        Returns:
            اطلاعات به‌روز شده کلاینت
        """
        try:
            result = await self.api.client.update(uuid, client_data)
            logger.info(f"Successfully updated client with UUID {uuid}")
            return result
        except Exception as e:
            logger.error(f"Failed to update client with UUID {uuid}: {e}")
            raise
    
    async def reset_client_traffic(self, uuid: str) -> bool:
        """
        ریست کردن ترافیک یک کلاینت
        
        Args:
            uuid: UUID کلاینت
            
        Returns:
            True در صورت موفقیت
        """
        try:
            result = await self.api.client.reset_traffic(uuid)
            logger.info(f"Successfully reset traffic for client with UUID {uuid}")
            return result
        except Exception as e:
            logger.error(f"Failed to reset traffic for client with UUID {uuid}: {e}")
            raise
    
    async def get_client_traffic(self, uuid: str) -> Dict[str, Any]:
        """
        دریافت اطلاعات ترافیک یک کلاینت
        
        Args:
            uuid: UUID کلاینت
            
        Returns:
            اطلاعات ترافیک کلاینت
        """
        try:
            result = await self.api.client.get_traffic(uuid)
            logger.info(f"Successfully retrieved traffic info for client with UUID {uuid}")
            return result
        except Exception as e:
            logger.error(f"Failed to get traffic info for client with UUID {uuid}: {e}")
            raise
    
    async def get_config(self, uuid: str) -> str:
        """
        دریافت لینک کانفیگ یک کلاینت
        
        Args:
            uuid: UUID کلاینت
            
        Returns:
            لینک کانفیگ کلاینت (vmess/vless)
        """
        try:
            # دریافت اطلاعات کلاینت
            client = await self.get_client_by_uuid(uuid)
            if not client:
                raise ValueError(f"Client with UUID {uuid} not found")
                
            # دریافت اطلاعات inbound
            inbound = await self.get_inbound(client["inbound_id"])
            if not inbound:
                raise ValueError(f"Inbound {client['inbound_id']} not found")
            
            # ساخت لینک کانفیگ بر اساس پروتکل
            protocol = inbound["protocol"].lower()
            if protocol == "vmess":
                config = {
                    "v": "2",
                    "ps": client["email"],
                    "add": self.host.replace("http://", "").replace("https://", ""),
                    "port": inbound["port"],
                    "id": uuid,
                    "aid": 0,
                    "net": "tcp",
                    "type": "none",
                    "host": "",
                    "path": "",
                    "tls": ""
                }
                import base64, json
                config_str = base64.b64encode(json.dumps(config).encode()).decode()
                config_url = f"vmess://{config_str}"
            elif protocol == "vless":
                host = self.host.replace("http://", "").replace("https://", "")
                config_url = f"vless://{uuid}@{host}:{inbound['port']}?type=tcp&security=none#{client['email']}"
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")
            
            logger.info(f"Generated {protocol} config URL for client with UUID {uuid}")
            return config_url
            
        except Exception as e:
            logger.error(f"Failed to get config for client with UUID {uuid}: {e}")
            raise
    
    # --------- مدیریت Inbound‌ها ---------
    
    async def get_inbounds(self) -> List[Dict[str, Any]]:
        """
        دریافت لیست تمام inbound‌های پنل
        
        Returns:
            لیست inbound‌ها
        """
        try:
            result = await self.api.inbound.get_list()
            logger.info(f"Successfully retrieved {len(result)} inbounds")
            return result
        except Exception as e:
            logger.error(f"Failed to get inbounds: {e}")
            raise
    
    async def get_inbound(self, inbound_id: int) -> Dict[str, Any]:
        """
        دریافت اطلاعات یک inbound خاص با شناسه آن
        
        Args:
            inbound_id: شناسه inbound
            
        Returns:
            اطلاعات inbound
        """
        try:
            result = await self.api.inbound.get(inbound_id)
            logger.info(f"Successfully retrieved inbound with ID {inbound_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to get inbound with ID {inbound_id}: {e}")
            raise
    
    async def create_inbound(self, inbound_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ایجاد یک inbound جدید
        
        Args:
            inbound_data: داده‌های inbound
            
        Returns:
            اطلاعات inbound ایجاد شده
        """
        try:
            result = await self.api.inbound.create(inbound_data)
            logger.info("Successfully created new inbound")
            return result
        except Exception as e:
            logger.error(f"Failed to create inbound: {e}")
            raise
    
    async def update_inbound(self, inbound_id: int, inbound_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        به‌روزرسانی یک inbound
        
        Args:
            inbound_id: شناسه inbound
            inbound_data: داده‌های جدید inbound
            
        Returns:
            اطلاعات به‌روز شده inbound
        """
        try:
            result = await self.api.inbound.update(inbound_id, inbound_data)
            logger.info(f"Successfully updated inbound with ID {inbound_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to update inbound with ID {inbound_id}: {e}")
            raise
    
    async def delete_inbound(self, inbound_id: int) -> bool:
        """
        حذف یک inbound
        
        Args:
            inbound_id: شناسه inbound
            
        Returns:
            True در صورت موفقیت
        """
        try:
            result = await self.api.inbound.delete(inbound_id)
            logger.info(f"Successfully deleted inbound with ID {inbound_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete inbound with ID {inbound_id}: {e}")
            raise
    
    # --------- مدیریت سرور ---------
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی سرور
        
        Returns:
            آمار سرور شامل CPU، RAM، ترافیک و...
        """
        try:
            result = await self.api.server.get_stats()
            logger.info("Successfully retrieved server stats")
            return result
        except Exception as e:
            logger.error(f"Failed to get server stats: {e}")
            raise
    
    async def restart_core(self) -> bool:
        """
        راه‌اندازی مجدد هسته xray/v2ray
        
        Returns:
            True در صورت موفقیت
        """
        try:
            result = await self.api.server.restart_core()
            logger.info("Successfully restarted xray/v2ray core")
            return result
        except Exception as e:
            logger.error(f"Failed to restart xray/v2ray core: {e}")
            raise
