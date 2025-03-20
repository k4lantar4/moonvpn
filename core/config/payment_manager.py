import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
from django.conf import settings
import requests
from ..models import Transaction

logger = logging.getLogger(__name__)

class PaymentGateway(ABC):
    """Abstract base class for payment gateways"""
    
    @abstractmethod
    def create_payment(self, amount: float, description: str, **kwargs) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a payment request
        
        Args:
            amount: Payment amount
            description: Payment description
            **kwargs: Additional gateway-specific parameters
            
        Returns:
            Tuple of (payment_id, payment_url) or (None, error_message)
        """
        pass
    
    @abstractmethod
    def verify_payment(self, payment_id: str) -> Tuple[bool, Optional[str]]:
        """
        Verify a payment
        
        Args:
            payment_id: Payment identifier
            
        Returns:
            Tuple of (is_verified, error_message)
        """
        pass

class ZarinPalGateway(PaymentGateway):
    """ZarinPal payment gateway implementation"""
    
    def __init__(self):
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        self.is_sandbox = getattr(settings, 'ZARINPAL_SANDBOX', True)
        self.callback_url = settings.ZARINPAL_CALLBACK_URL
        
        if self.is_sandbox:
            self.base_url = "https://sandbox.zarinpal.com/pg/rest/WebGate"
            self.payment_url = "https://sandbox.zarinpal.com/pg/StartPay/{}"
        else:
            self.base_url = "https://www.zarinpal.com/pg/rest/WebGate"
            self.payment_url = "https://www.zarinpal.com/pg/StartPay/{}"
    
    def create_payment(self, amount: float, description: str, **kwargs) -> Tuple[Optional[str], Optional[str]]:
        try:
            data = {
                "MerchantID": self.merchant_id,
                "Amount": int(amount),
                "Description": description,
                "CallbackURL": self.callback_url,
                "Email": kwargs.get('email'),
                "Mobile": kwargs.get('mobile')
            }
            
            response = requests.post(f"{self.base_url}/PaymentRequest.json", json=data)
            result = response.json()
            
            if result["Status"] == 100:
                payment_id = result["Authority"]
                payment_url = self.payment_url.format(payment_id)
                return payment_id, payment_url
            else:
                logger.error(f"ZarinPal payment creation failed: {result}")
                return None, f"Payment creation failed: {result.get('Message', 'Unknown error')}"
                
        except Exception as e:
            logger.error(f"Error creating ZarinPal payment: {str(e)}")
            return None, str(e)
    
    def verify_payment(self, payment_id: str) -> Tuple[bool, Optional[str]]:
        try:
            data = {
                "MerchantID": self.merchant_id,
                "Authority": payment_id,
                "Amount": int(amount)
            }
            
            response = requests.post(f"{self.base_url}/PaymentVerification.json", json=data)
            result = response.json()
            
            if result["Status"] == 100:
                return True, None
            else:
                logger.error(f"ZarinPal payment verification failed: {result}")
                return False, f"Payment verification failed: {result.get('Message', 'Unknown error')}"
                
        except Exception as e:
            logger.error(f"Error verifying ZarinPal payment: {str(e)}")
            return False, str(e)

class WalletGateway(PaymentGateway):
    """Internal wallet payment gateway"""
    
    def create_payment(self, amount: float, description: str, **kwargs) -> Tuple[Optional[str], Optional[str]]:
        try:
            user = kwargs.get('user')
            if not user:
                return None, "User is required for wallet payments"
            
            if user.wallet.balance < amount:
                return None, "Insufficient wallet balance"
            
            # Generate payment ID
            payment_id = f"wallet_{uuid.uuid4().hex[:12]}"
            return payment_id, None
            
        except Exception as e:
            logger.error(f"Error creating wallet payment: {str(e)}")
            return None, str(e)
    
    def verify_payment(self, payment_id: str) -> Tuple[bool, Optional[str]]:
        # Wallet payments are verified immediately during creation
        return True, None

class PaymentManager:
    """Service for managing payments across different gateways"""
    
    GATEWAYS = {
        'zarinpal': ZarinPalGateway,
        'wallet': WalletGateway
    }
    
    @classmethod
    def get_gateway(cls, payment_method: str) -> Optional[PaymentGateway]:
        """Get payment gateway instance by method"""
        gateway_class = cls.GATEWAYS.get(payment_method)
        if gateway_class:
            return gateway_class()
        return None
    
    @classmethod
    def create_payment(
        cls,
        user,
        amount: float,
        payment_method: str,
        description: str,
        **kwargs
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Create a new payment
        
        Args:
            user: User object
            amount: Payment amount
            payment_method: Payment method identifier
            description: Payment description
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (payment_data, error_message)
        """
        try:
            gateway = cls.get_gateway(payment_method)
            if not gateway:
                return None, f"Unsupported payment method: {payment_method}"
            
            # Create payment with gateway
            payment_id, payment_url = gateway.create_payment(
                amount=amount,
                description=description,
                user=user,
                **kwargs
            )
            
            if not payment_id:
                return None, payment_url  # Error message
            
            # Create transaction record
            transaction = Transaction.objects.create(
                user=user,
                transaction_type=kwargs.get('transaction_type', 'new'),
                status='pending',
                amount=amount,
                payment_method=payment_method,
                payment_id=payment_id,
                notes=description
            )
            
            return {
                'transaction_id': transaction.id,
                'payment_id': payment_id,
                'payment_url': payment_url,
                'amount': amount,
                'status': 'pending'
            }, None
            
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            return None, str(e)
    
    @classmethod
    def verify_payment(
        cls,
        payment_id: str,
        payment_method: str
    ) -> Tuple[Optional[Transaction], Optional[str]]:
        """
        Verify a payment
        
        Args:
            payment_id: Payment identifier
            payment_method: Payment method identifier
            
        Returns:
            Tuple of (transaction, error_message)
        """
        try:
            # Get transaction
            transaction = Transaction.objects.get(payment_id=payment_id)
            
            # Skip if already completed
            if transaction.status == 'completed':
                return transaction, None
            
            # Get gateway
            gateway = cls.get_gateway(payment_method)
            if not gateway:
                return None, f"Unsupported payment method: {payment_method}"
            
            # Verify with gateway
            is_verified, error = gateway.verify_payment(payment_id)
            
            if is_verified:
                # Update transaction
                transaction.status = 'completed'
                transaction.save()
                
                # Process subscription if this was a subscription payment
                if transaction.subscription:
                    if transaction.transaction_type == 'new':
                        # Activate new subscription
                        subscription.status = 'active'
                        subscription.save()
                    elif transaction.transaction_type == 'renewal':
                        # Process renewal
                        from .subscription_manager import SubscriptionManager
                        SubscriptionManager.process_renewal(subscription)
                
                return transaction, None
            else:
                transaction.status = 'failed'
                transaction.notes = f"Verification failed: {error}"
                transaction.save()
                return None, error
                
        except Transaction.DoesNotExist:
            return None, "Transaction not found"
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return None, str(e) 