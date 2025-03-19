import logging
import json
import uuid
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.urls import reverse
import requests

from .models import Payment, PaymentMethod, PaymentPlan, DiscountCode

logger = logging.getLogger(__name__)

class PaymentService:
    """
    Service for handling payment operations
    """
    @staticmethod
    def create_payment(user, plan, payment_method_name, discount_code=None):
        """
        Create a new payment record
        
        Args:
            user: User making the payment
            plan: PaymentPlan to purchase
            payment_method_name: String name of payment method (card, zarinpal)
            discount_code: Optional discount code to apply
            
        Returns:
            tuple: (payment, error_message)
        """
        try:
            # Validate plan
            if not plan.is_active:
                return None, "Selected plan is not available"
            
            # Get payment method
            try:
                payment_method = PaymentMethod.objects.get(
                    name=payment_method_name, 
                    is_active=True
                )
            except PaymentMethod.DoesNotExist:
                return None, "Payment method is not available"
            
            # Calculate amount
            amount = plan.display_price
            original_amount = plan.price
            
            # Apply discount if provided
            applied_discount = None
            if discount_code:
                try:
                    discount = DiscountCode.objects.get(code=discount_code)
                    if not discount.is_valid:
                        return None, "Discount code has expired or reached maximum uses"
                    
                    # Check if discount applies to this plan
                    if discount.plans.exists() and not discount.plans.filter(id=plan.id).exists():
                        return None, "Discount code cannot be used with this plan"
                    
                    # Apply discount
                    amount = discount.apply_discount(amount)
                    applied_discount = discount
                    
                except DiscountCode.DoesNotExist:
                    return None, "Invalid discount code"
            
            # Create payment record
            with transaction.atomic():
                payment = Payment.objects.create(
                    user=user,
                    plan=plan,
                    payment_method=payment_method,
                    discount_code=applied_discount,
                    amount=amount,
                    original_amount=original_amount,
                    traffic_amount=plan.traffic_bytes,
                    duration_days=plan.duration_days,
                    server_id=plan.server_id,
                    inbound_id=plan.inbound_id,
                    description=f"Payment for plan: {plan.name}"
                )
                
                logger.info(f"Created payment {payment.id} for user {user.username}, amount: {amount} IRR")
                
                return payment, None
                
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            return None, f"An error occurred: {str(e)}"
    
    @staticmethod
    def get_payment_instructions(payment):
        """
        Get payment instructions based on payment method
        
        Args:
            payment: Payment object
            
        Returns:
            dict: Payment instructions
        """
        if not payment:
            return {"error": "Invalid payment"}
        
        if payment.status != Payment.PENDING:
            return {"error": "Payment is not in pending state"}
        
        if payment.payment_method.name == PaymentMethod.CARD:
            # Card payment instructions
            return {
                "payment_id": str(payment.id),
                "amount": payment.amount,
                "method": "card",
                "card_number": payment.payment_method.card_number,
                "card_holder": payment.payment_method.card_holder,
                "bank_name": payment.payment_method.bank_name,
                "reference_code": str(payment.id)[:8].upper(),  # First 8 chars of payment ID as reference
                "expires_at": payment.expires_at,
                "expires_in_minutes": int((payment.expires_at - timezone.now()).total_seconds() / 60) if payment.expires_at else None,
                "next_step": "verification"
            }
        
        elif payment.payment_method.name == PaymentMethod.ZARINPAL:
            # For Zarinpal, we need to initialize the payment on their gateway
            try:
                # Initialize Zarinpal payment
                result = PaymentService._initialize_zarinpal_payment(payment)
                
                if result.get("success"):
                    return {
                        "payment_id": str(payment.id),
                        "amount": payment.amount,
                        "method": "zarinpal",
                        "redirect_url": result.get("redirect_url"),
                        "authority": result.get("authority"),
                        "expires_at": payment.expires_at,
                        "next_step": "redirect"
                    }
                else:
                    return {"error": result.get("error", "Failed to initialize online payment")}
                    
            except Exception as e:
                logger.error(f"Error initializing Zarinpal payment: {str(e)}")
                return {"error": f"Payment gateway error: {str(e)}"}
        
        return {"error": "Unsupported payment method"}
    
    @staticmethod
    def _initialize_zarinpal_payment(payment):
        """
        Initialize a Zarinpal payment
        
        Args:
            payment: Payment object
            
        Returns:
            dict: Result with success, redirect_url, and authority if successful
        """
        if not settings.ZARINPAL_MERCHANT_ID:
            return {"success": False, "error": "Zarinpal is not configured"}
        
        try:
            merchant_id = payment.payment_method.merchant_id or settings.ZARINPAL_MERCHANT_ID
            callback_url = payment.payment_method.callback_url or settings.PAYMENT_CALLBACK_URL
            
            # Add payment ID to callback URL
            if '?' in callback_url:
                callback_url = f"{callback_url}&payment_id={payment.id}"
            else:
                callback_url = f"{callback_url}?payment_id={payment.id}"
            
            # Prepare request data
            request_data = {
                "merchant_id": merchant_id,
                "amount": payment.amount,  # Amount in Tomans
                "description": f"Payment for VPN service - {payment.plan.name if payment.plan else 'Custom payment'}",
                "callback_url": callback_url,
                "metadata": {
                    "mobile": payment.user.phone_number if hasattr(payment.user, 'phone_number') else "",
                    "email": payment.user.email
                }
            }
            
            # Send request to Zarinpal
            zarinpal_url = "https://api.zarinpal.com/pg/v4/payment/request.json"
            response = requests.post(
                zarinpal_url,
                json=request_data,
                timeout=10
            )
            
            result = response.json()
            
            # Store response in payment object
            payment.gateway_response = result
            
            if result.get('data', {}).get('code') == 100:
                # Success, get authority
                authority = result.get('data', {}).get('authority')
                payment.transaction_id = authority
                payment.status = Payment.PROCESSING
                payment.save()
                
                # Generate redirect URL
                redirect_url = f"https://www.zarinpal.com/pg/StartPay/{authority}"
                
                return {
                    "success": True,
                    "redirect_url": redirect_url,
                    "authority": authority
                }
            else:
                # Failed
                error_code = result.get('errors', {}).get('code')
                error_message = result.get('errors', {}).get('message', "Unknown error")
                
                logger.error(f"Zarinpal payment initialization failed: {error_code} - {error_message}")
                
                payment.status = Payment.FAILED
                payment.description = f"{payment.description or ''}\nZarinpal error: {error_code} - {error_message}"
                payment.save()
                
                return {
                    "success": False,
                    "error": f"Payment gateway error: {error_message}"
                }
                
        except Exception as e:
            logger.exception(f"Error in Zarinpal payment initialization: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def verify_card_payment(payment_id, payer_card, payer_name, payer_bank=None, payment_time=None):
        """
        Verify a card payment manually
        
        Args:
            payment_id: Payment ID to verify
            payer_card: Last 4 digits of payer's card
            payer_name: Name of the person who made the payment
            payer_bank: Bank name (optional)
            payment_time: When the payment was made (optional)
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Get payment
            try:
                payment = Payment.objects.get(id=payment_id)
            except Payment.DoesNotExist:
                return False, "Payment not found"
            
            # Check payment status
            if payment.status != Payment.PENDING:
                if payment.status == Payment.COMPLETED:
                    return True, "Payment already verified"
                return False, f"Payment cannot be verified (status: {payment.get_status_display()})"
            
            # Check if payment is expired
            if payment.is_expired:
                return False, "Payment has expired"
            
            # Store verification data
            payment.card_number = payer_card[-4:] if payer_card and len(payer_card) >= 4 else payer_card
            payment.payer_name = payer_name
            payment.payer_bank = payer_bank
            
            if payment_time:
                try:
                    payment.payment_time = payment_time
                except (ValueError, TypeError):
                    payment.payment_time = timezone.now()
            else:
                payment.payment_time = timezone.now()
            
            # Mark as processing (pending admin verification)
            payment.status = Payment.PROCESSING
            payment.save()
            
            # For demo/development, auto-verify
            if settings.DEBUG or getattr(settings, 'AUTO_VERIFY_CARD_PAYMENTS', False):
                payment.mark_as_completed(
                    reference_code=f"CARD-{uuid.uuid4().hex[:8].upper()}",
                    tracking_code=f"VERIFY-{uuid.uuid4().hex[:6].upper()}"
                )
                
                # Create VPN account (will be implemented in AccountService)
                return True, "Payment verified successfully"
            
            return True, "Payment verification submitted, awaiting admin approval"
            
        except Exception as e:
            logger.exception(f"Error verifying card payment: {str(e)}")
            return False, f"Verification error: {str(e)}"
    
    @staticmethod
    def verify_zarinpal_payment(authority, status):
        """
        Verify Zarinpal payment after user returns from gateway
        
        Args:
            authority: Zarinpal authority code
            status: Status returned by Zarinpal (OK or NOK)
            
        Returns:
            tuple: (success, message, payment)
        """
        # Find payment by authority
        try:
            payment = Payment.objects.get(transaction_id=authority)
        except Payment.DoesNotExist:
            logger.error(f"No payment found for Zarinpal authority: {authority}")
            return False, "No payment found for this transaction", None
        
        # Check if payment has already been verified
        if payment.status == Payment.COMPLETED:
            return True, "Payment already verified", payment
        
        # If status is not OK, mark as failed
        if status.upper() != 'OK':
            payment.mark_as_failed("Payment was canceled or failed at the gateway")
            return False, "Payment was not successful", payment
        
        try:
            # Verify payment with Zarinpal
            merchant_id = payment.payment_method.merchant_id or settings.ZARINPAL_MERCHANT_ID
            
            verify_data = {
                "merchant_id": merchant_id,
                "authority": authority,
                "amount": payment.amount
            }
            
            verify_url = "https://api.zarinpal.com/pg/v4/payment/verify.json"
            response = requests.post(
                verify_url,
                json=verify_data,
                timeout=10
            )
            
            result = response.json()
            
            # Store verification response
            if payment.gateway_response:
                if isinstance(payment.gateway_response, str):
                    try:
                        existing_response = json.loads(payment.gateway_response)
                    except json.JSONDecodeError:
                        existing_response = {}
                else:
                    existing_response = payment.gateway_response
                
                existing_response['verification'] = result
                payment.gateway_response = existing_response
            else:
                payment.gateway_response = {'verification': result}
            
            # Check verification result
            if result.get('data', {}).get('code') == 100:
                # Success
                ref_id = result.get('data', {}).get('ref_id')
                
                payment.verification_code = ref_id
                payment.mark_as_completed(
                    reference_code=ref_id,
                    tracking_code=f"ZP-{ref_id}"
                )
                
                # Create VPN account (will be implemented in AccountService)
                return True, "Payment verified successfully", payment
            
            else:
                # Failed verification
                error_code = result.get('errors', {}).get('code')
                error_message = result.get('errors', {}).get('message', "Unknown error")
                
                payment.mark_as_failed(f"Zarinpal verification failed: {error_code} - {error_message}")
                return False, f"Payment verification failed: {error_message}", payment
                
        except Exception as e:
            logger.exception(f"Error verifying Zarinpal payment: {str(e)}")
            payment.mark_as_failed(f"Verification error: {str(e)}")
            return False, f"Verification error: {str(e)}", payment
    
    @staticmethod
    def get_active_plans():
        """
        Get all active payment plans
        
        Returns:
            QuerySet: Active payment plans
        """
        return PaymentPlan.objects.filter(is_active=True).order_by('order', 'price')
    
    @staticmethod
    def get_active_payment_methods():
        """
        Get all active payment methods
        
        Returns:
            QuerySet: Active payment methods
        """
        return PaymentMethod.objects.filter(is_active=True)
    
    @staticmethod
    def get_user_payments(user, limit=10, include_expired=False):
        """
        Get user's payment history
        
        Args:
            user: User object
            limit: Maximum number of payments to return
            include_expired: Whether to include expired payments
            
        Returns:
            QuerySet: User's payments
        """
        payments = Payment.objects.filter(user=user)
        
        if not include_expired:
            payments = payments.exclude(status=Payment.EXPIRED)
            
        return payments.order_by('-created_at')[:limit]
    
    @staticmethod
    def validate_discount_code(code, plan=None):
        """
        Validate a discount code
        
        Args:
            code: Discount code string
            plan: Optional plan to check if discount applies
            
        Returns:
            tuple: (valid, discount_obj, message)
        """
        try:
            discount = DiscountCode.objects.get(code=code)
            
            if not discount.is_active:
                return False, None, "Discount code is not active"
                
            now = timezone.now()
            
            if discount.valid_from and discount.valid_from > now:
                return False, None, "Discount code is not yet valid"
                
            if discount.valid_until and discount.valid_until < now:
                return False, None, "Discount code has expired"
                
            if discount.max_uses and discount.used_count >= discount.max_uses:
                return False, None, "Discount code has reached maximum uses"
                
            # Check if plan-specific
            if plan and discount.plans.exists() and not discount.plans.filter(id=plan.id).exists():
                return False, None, "Discount code cannot be used with this plan"
                
            return True, discount, f"Valid discount: {discount.discount_percentage}% off"
            
        except DiscountCode.DoesNotExist:
            return False, None, "Invalid discount code" 