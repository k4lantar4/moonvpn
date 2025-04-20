"""
کلاس کلاینت برای ارتباط با پنل‌های 3x-ui
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import time

# استفاده از کلاس‌های اصلی کتابخانه py3xui
from py3xui import Api, Client

logger = logging.getLogger(__name__)


class XUIClient:
    """
    کلاس کلاینت برای ارتباط با پنل‌های 3x-ui با استفاده از SDK py3xui
    """
    
    def __init__(self, panel_url: str, username: str, password: str):
        """
        راه‌اندازی کلاینت با آدرس و اطلاعات ورود پنل
        """
        self.panel_url = panel_url.rstrip("/")  # حذف اسلش انتهایی اگر وجود داشته باشد
        self.username = username
        self.password = password
        self.client = None
        self._connect()
    
    def _connect(self) -> None:
        """
        اتصال به پنل و احراز هویت
        """
        try:
            self.client = Api(self.panel_url, self.username, self.password)
            self.client.login()
            logger.info(f"Successfully connected to panel at {self.panel_url}")
        except Exception as e:
            logger.error(f"Failed to connect to panel at {self.panel_url}: {e}")
            raise
    
    def get_inbounds(self) -> List[Dict[str, Any]]:
        """
        دریافت لیست تمام inbound‌های پنل
        """
        if not self.client:
            self._connect()
        
        try:
            inbounds = self.client.inbound.get_list()
            logger.info(f"Retrieved {len(inbounds)} inbounds from panel")
            return inbounds
        except Exception as e:
            logger.error(f"Failed to get inbounds: {e}")
            raise
    
    def get_inbound(self, inbound_id: int) -> Dict[str, Any]:
        """
        دریافت اطلاعات یک inbound خاص با شناسه آن
        """
        if not self.client:
            self._connect()
        
        try:
            inbound = self.client.inbound.get_by_id(inbound_id)
            return inbound
        except Exception as e:
            logger.error(f"Failed to get inbound {inbound_id}: {e}")
            raise
    
    def create_client(self, inbound_id: int, email: str, traffic: int = None,
                     expires_at: datetime = None, uuid: Optional[str] = None,
                     flow: Optional[str] = None) -> Dict[str, Any]:
        """
        ایجاد کلاینت جدید در یک inbound خاص
        
        Args:
            inbound_id: شناسه inbound
            email: آدرس ایمیل/نام کلاینت
            traffic: مقدار کل حجم مصرفی به GB
            expires_at: زمان انقضا به صورت شیء datetime
            uuid: UUID اختیاری (اگر نباشد، به صورت خودکار ساخته می‌شود)
            flow: جریان داده برای پروتکل vless
        
        Returns:
            اطلاعات کلاینت ایجاد شده
        """
        if not self.client:
            self._connect()
        
        try:
            # تبدیل تاریخ انقضا به میلی‌ثانیه (timestamp در فرمت 3x-ui)
            expire_time = None
            if expires_at:
                expire_timestamp = int(time.mktime(expires_at.timetuple())) * 1000  # تبدیل به میلی‌ثانیه
                expire_time = expire_timestamp
                logger.debug(f"Setting expiry time to {expires_at} ({expire_timestamp})")
            
            # تبدیل ترافیک به بایت (براساس فرمت 3x-ui)
            total_gb = None
            if traffic:
                total_gb = traffic
                logger.debug(f"Setting traffic to {traffic} GB")
                
            # ایجاد یک کلاینت جدید
            new_client = Client(email=email, id=uuid, enable=True)
            if total_gb is not None:
                new_client.total_gb = total_gb
            if expire_time is not None:
                new_client.expiry_time = expire_time
            if flow is not None:
                new_client.flow = flow
            
            logger.info(f"Creating new client in inbound {inbound_id} with email {email}, UUID {uuid}")    
            client_data = self.client.client.add(inbound_id, [new_client])
            logger.info(f"Successfully created client: {client_data}")
            return client_data
        except Exception as e:
            logger.error(f"Failed to create client for inbound {inbound_id}: {e}")
            raise
    
    def delete_client(self, uuid: str) -> bool:
        """
        حذف یک کلاینت با UUID آن
        
        Args:
            uuid: UUID کلاینت
        
        Returns:
            True در صورت موفقیت
        """
        if not self.client:
            self._connect()
        
        try:
            logger.info(f"Deleting client with UUID {uuid}")
            success = self.client.client.remove(uuid)
            if success:
                logger.info(f"Successfully deleted client with UUID {uuid}")
            else:
                logger.warning(f"Failed to delete client with UUID {uuid}")
            return success
        except Exception as e:
            logger.error(f"Error deleting client with UUID {uuid}: {e}")
            raise
    
    def delete_client_by_email(self, inbound_id: int, email: str) -> bool:
        """
        حذف یک کلاینت از inbound با ایمیل/نام آن
        
        Args:
            inbound_id: شناسه inbound
            email: آدرس ایمیل/نام کلاینت
        
        Returns:
            True در صورت موفقیت
        """
        if not self.client:
            self._connect()
        
        try:
            # ابتدا باید شناسه کلاینت را پیدا کنیم
            client = self.client.client.get_by_email(email)
            if client:
                success = self.client.client.remove(client.id)
                return success
            else:
                raise ValueError(f"Client {email} not found")
        except Exception as e:
            logger.error(f"Failed to delete client {email} from inbound {inbound_id}: {e}")
            raise
    
    def reset_client_traffic(self, inbound_id: int, email: str) -> bool:
        """
        ریست کردن ترافیک یک کلاینت
        
        Args:
            inbound_id: شناسه inbound
            email: آدرس ایمیل/نام کلاینت
        
        Returns:
            True در صورت موفقیت
        """
        if not self.client:
            self._connect()
        
        try:
            # ابتدا باید شناسه کلاینت را پیدا کنیم
            client = self.client.client.get_by_email(email)
            if client:
                success = self.client.client.reset_traffic(client.id)
                return success
            else:
                raise ValueError(f"Client {email} not found")
        except Exception as e:
            logger.error(f"Failed to reset traffic for client {email} in inbound {inbound_id}: {e}")
            raise
    
    def get_client_usage(self, inbound_id: int, email: str) -> Tuple[int, int]:
        """
        دریافت میزان مصرف ترافیک و تاریخ انقضای یک کلاینت
        
        Args:
            inbound_id: شناسه inbound
            email: آدرس ایمیل/نام کلاینت
        
        Returns:
            (traffic_used, expire_time) ترافیک مصرف شده و زمان انقضا
        """
        if not self.client:
            self._connect()
        
        try:
            client = self.client.client.get_by_email(email)
            if client:
                # مصرف ترافیک و زمان انقضا در کلاینت
                return client.up + client.down, client.expiry_time
            raise ValueError(f"Client {email} not found")
        except Exception as e:
            logger.error(f"Failed to get usage for client {email} in inbound {inbound_id}: {e}")
            raise
            
    def get_panel_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی پنل
        
        Returns:
            آمار کلی شامل CPU، RAM، و ترافیک
        """
        if not self.client:
            self._connect()
        
        try:
            stats = self.client.server.get_status()
            return stats
        except Exception as e:
            logger.error(f"Failed to get panel stats: {e}")
            raise
