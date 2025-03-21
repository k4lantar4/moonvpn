"""
SMS Service for MoonVPN.

This module handles SMS verification and notifications using
various SMS providers with fallback support.
"""

import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import aiohttp
import json
import hashlib
import hmac
import base64
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.models import User, SMSVerification
from app.core.exceptions import SMSError

logger = logging.getLogger(__name__)

class SMSService:
    """Service for handling SMS operations."""
    
    def __init__(self, db):
        """Initialize SMS service."""
        self.db = db
        self.config = settings.SMS_CONFIG
        self.providers = {
            'kavenegar': self._send_kavenegar,
            'ghasedak': self._send_ghasedak,
            'melipayamak': self._send_melipayamak
        }
        
    async def send_verification_code(
        self,
        phone: str,
        user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Send verification code via SMS.
        
        Args:
            phone: Phone number to send code to
            user_id: Optional user ID for tracking
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Clean phone number
            phone = self._clean_phone_number(phone)
            
            # Generate verification code
            code = self._generate_verification_code()
            
            # Create verification record
            verification = SMSVerification(
                phone=phone,
                code=code,
                user_id=user_id,
                expires_at=datetime.utcnow() + timedelta(minutes=10),
                attempts=0
            )
            self.db.add(verification)
            self.db.commit()
            
            # Try each provider until successful
            for provider in self.config['providers']:
                if provider not in self.providers:
                    logger.warning(f"Unknown SMS provider: {provider}")
                    continue
                    
                try:
                    success = await self.providers[provider](phone, code)
                    if success:
                        return True, None
                except Exception as e:
                    logger.error(f"Error with provider {provider}: {str(e)}")
                    continue
            
            # All providers failed
            return False, "Failed to send verification code"
            
        except Exception as e:
            logger.error(f"Error sending verification code: {str(e)}")
            return False, str(e)
    
    async def verify_code(
        self,
        phone: str,
        code: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify SMS code.
        
        Args:
            phone: Phone number
            code: Verification code
            
        Returns:
            Tuple of (is_verified, error_message)
        """
        try:
            # Clean phone number
            phone = self._clean_phone_number(phone)
            
            # Get verification record
            verification = self.db.query(SMSVerification).filter(
                SMSVerification.phone == phone,
                SMSVerification.is_used == False,
                SMSVerification.expires_at > datetime.utcnow()
            ).order_by(SMSVerification.created_at.desc()).first()
            
            if not verification:
                return False, "No valid verification code found"
            
            # Check attempts
            if verification.attempts >= 3:
                return False, "Too many attempts"
            
            # Update attempts
            verification.attempts += 1
            
            # Verify code
            if verification.code != code:
                self.db.commit()
                return False, "Invalid code"
            
            # Mark as used
            verification.is_used = True
            verification.verified_at = datetime.utcnow()
            
            # Update user if exists
            if verification.user_id:
                user = self.db.query(User).get(verification.user_id)
                if user:
                    user.is_phone_verified = True
                    user.verified_phone = phone
            
            self.db.commit()
            return True, None
            
        except Exception as e:
            logger.error(f"Error verifying code: {str(e)}")
            return False, str(e)
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and validate phone number."""
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Add country code if missing
        if not phone.startswith('98'):
            if phone.startswith('0'):
                phone = '98' + phone[1:]
            else:
                phone = '98' + phone
        
        # Validate length
        if len(phone) != 12:
            raise SMSError("Invalid phone number format")
        
        return phone
    
    def _generate_verification_code(self) -> str:
        """Generate a random verification code."""
        import random
        return str(random.randint(100000, 999999))
    
    async def _send_kavenegar(self, phone: str, code: str) -> bool:
        """Send SMS using Kavenegar."""
        try:
            if not self.config.get('kavenegar'):
                return False
            
            api_key = self.config['kavenegar']['api_key']
            template = self.config['kavenegar']['template']
            
            url = f"https://api.kavenegar.com/v1/{api_key}/verify/lookup.json"
            params = {
                'receptor': phone,
                'token': code,
                'template': template
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise SMSError(f"Kavenegar API error: {response.status}")
                    
                    data = await response.json()
                    return data['return']['status'] == 200
                    
        except Exception as e:
            logger.error(f"Kavenegar error: {str(e)}")
            return False
    
    async def _send_ghasedak(self, phone: str, code: str) -> bool:
        """Send SMS using Ghasedak."""
        try:
            if not self.config.get('ghasedak'):
                return False
            
            api_key = self.config['ghasedak']['api_key']
            template = self.config['ghasedak']['template']
            
            url = "https://api.ghasedak.me/v2/verification/send/simple"
            headers = {
                'apikey': api_key,
                'content-type': 'application/x-www-form-urlencoded'
            }
            data = {
                'receptor': phone,
                'template': template,
                'type': '1',
                'param1': code
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status != 200:
                        raise SMSError(f"Ghasedak API error: {response.status}")
                    
                    data = await response.json()
                    return data['result']['code'] == 200
                    
        except Exception as e:
            logger.error(f"Ghasedak error: {str(e)}")
            return False
    
    async def _send_melipayamak(self, phone: str, code: str) -> bool:
        """Send SMS using Melipayamak."""
        try:
            if not self.config.get('melipayamak'):
                return False
            
            username = self.config['melipayamak']['username']
            password = self.config['melipayamak']['password']
            from_number = self.config['melipayamak']['from_number']
            
            url = "https://rest.payamak-panel.com/api/SendSMS/SendSMS"
            data = {
                'username': username,
                'password': password,
                'to': phone,
                'from': from_number,
                'text': f"Your MoonVPN verification code is: {code}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        raise SMSError(f"Melipayamak API error: {response.status}")
                    
                    data = await response.json()
                    return data['RetStatus'] == 1
                    
        except Exception as e:
            logger.error(f"Melipayamak error: {str(e)}")
            return False 