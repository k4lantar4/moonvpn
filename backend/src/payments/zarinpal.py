import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from .models import Transaction, ZarinpalPayment

logger = logging.getLogger(__name__)

class ZarinpalGateway:
    """Zarinpal payment gateway integration"""
    
    def __init__(self):
        """Initialize the Zarinpal gateway"""
        self.merchant_id = getattr(settings, 'ZARINPAL_MERCHANT', '')
        self.sandbox = getattr(settings, 'ZARINPAL_SANDBOX', True)
        self.callback_url = getattr(settings, 'ZARINPAL_CALLBACK_URL', '')
        self.admin_notification_enabled = getattr(settings, 'ADMIN_NOTIFICATION_ENABLED', True)
        
        # Set API endpoints based on sandbox mode
        if self.sandbox:
            self.request_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
            self.verify_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
            self.payment_url = "https://sandbox.zarinpal.com/pg/StartPay/"
        else:
            self.request_url = "https://api.zarinpal.com/pg/v4/payment/request.json"
            self.verify_url = "https://api.zarinpal.com/pg/v4/payment/verify.json"
            self.payment_url = "https://www.zarinpal.com/pg/StartPay/"
    
    def request_payment(self, transaction_id, amount, description, email=None, mobile=None):
        """Request a payment from Zarinpal"""
        try:
            # Validate parameters
            if not self.merchant_id:
                logger.error("ZARINPAL_MERCHANT not set in settings")
                return {"success": False, "error_message": "Payment gateway not configured properly"}
            
            if not self.callback_url:
                logger.error("ZARINPAL_CALLBACK_URL not set in settings")
                return {"success": False, "error_message": "Payment gateway callback URL not configured"}
            
            # Get transaction
            transaction = Transaction.objects.get(id=transaction_id)
            
            # Convert amount from Toman to Rial (Zarinpal uses Rial)
            amount_rial = int(amount * 10)
            
            # Prepare request data
            data = {
                "merchant_id": self.merchant_id,
                "amount": amount_rial,
                "description": description,
                "callback_url": self.callback_url,
            }
            
            # Add optional parameters if provided
            if email:
                data["email"] = email
            if mobile:
                data["mobile"] = mobile
            
            # Make request to Zarinpal
            response = requests.post(self.request_url, json=data, timeout=10)
            
            # Log the response
            logger.info(f"Zarinpal payment request response: {response.text}")
            
            # Check response status code
            if response.status_code != 200:
                logger.error(f"Zarinpal API error: HTTP {response.status_code}")
                return {
                    "success": False,
                    "error_message": f"Payment gateway error: HTTP {response.status_code}"
                }
            
            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response from Zarinpal API: {response.text}")
                return {
                    "success": False,
                    "error_message": "Invalid response from payment gateway"
                }
            
            if self.sandbox:
                # Sandbox response format
                if result.get("Status") == 100:
                    authority = result.get("Authority")
                    payment_url = f"{self.payment_url}{authority}"
                    
                    # Create Zarinpal payment record
                    zarinpal_payment = ZarinpalPayment.objects.create(
                        transaction=transaction,
                        authority=authority,
                        status='pending',
                        payment_url=payment_url
                    )
                    
                    # Send notification to admin if enabled
                    if self.admin_notification_enabled:
                        self._notify_admin_new_payment(zarinpal_payment)
                    
                    return {
                        "success": True,
                        "authority": authority,
                        "payment_url": payment_url
                    }
                else:
                    error_code = result.get("Status")
                    error_message = self._get_error_message(error_code)
                    logger.error(f"Zarinpal payment request failed: {error_message} (Code: {error_code})")
                    
                    return {
                        "success": False,
                        "error_code": error_code,
                        "error_message": error_message
                    }
            else:
                # Production response format
                if result.get("data", {}).get("code") == 100:
                    authority = result.get("data", {}).get("authority")
                    payment_url = f"{self.payment_url}{authority}"
                    
                    # Create Zarinpal payment record
                    zarinpal_payment = ZarinpalPayment.objects.create(
                        transaction=transaction,
                        authority=authority,
                        status='pending',
                        payment_url=payment_url
                    )
                    
                    # Send notification to admin if enabled
                    if self.admin_notification_enabled:
                        self._notify_admin_new_payment(zarinpal_payment)
                    
                    return {
                        "success": True,
                        "authority": authority,
                        "payment_url": payment_url
                    }
                else:
                    error_code = result.get("errors", {}).get("code")
                    error_message = result.get("errors", {}).get("message", "Unknown error")
                    logger.error(f"Zarinpal payment request failed: {error_message} (Code: {error_code})")
                    
                    return {
                        "success": False,
                        "error_code": error_code,
                        "error_message": error_message
                    }
        except Transaction.DoesNotExist:
            logger.error(f"Transaction with ID {transaction_id} does not exist")
            return {
                "success": False,
                "error_message": "Transaction not found"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error to Zarinpal API: {str(e)}")
            return {
                "success": False,
                "error_message": f"Connection error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error requesting Zarinpal payment: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            }
    
    def verify_payment(self, authority, amount):
        """Verify a payment with Zarinpal"""
        try:
            # Validate parameters
            if not self.merchant_id:
                logger.error("ZARINPAL_MERCHANT not set in settings")
                return {"success": False, "error_message": "Payment gateway not configured properly"}
            
            # Get Zarinpal payment
            try:
                zarinpal_payment = ZarinpalPayment.objects.get(authority=authority)
                transaction = zarinpal_payment.transaction
            except ZarinpalPayment.DoesNotExist:
                logger.error(f"Zarinpal payment with authority {authority} does not exist")
                return {"success": False, "error_message": "Payment not found"}
            
            # Check if payment is already verified
            if zarinpal_payment.status == 'verified':
                return {
                    "success": True,
                    "status": "already_verified",
                    "ref_id": zarinpal_payment.ref_id,
                    "transaction_id": transaction.id
                }
            
            # Convert amount from Toman to Rial (Zarinpal uses Rial)
            amount_rial = int(amount * 10)
            
            # Prepare verification data
            data = {
                "merchant_id": self.merchant_id,
                "authority": authority,
                "amount": amount_rial
            }
            
            # Make request to Zarinpal
            response = requests.post(self.verify_url, json=data, timeout=10)
            
            # Log the response
            logger.info(f"Zarinpal payment verification response: {response.text}")
            
            # Check response status code
            if response.status_code != 200:
                logger.error(f"Zarinpal API error: HTTP {response.status_code}")
                return {
                    "success": False,
                    "error_message": f"Payment gateway error: HTTP {response.status_code}"
                }
            
            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response from Zarinpal API: {response.text}")
                return {
                    "success": False,
                    "error_message": "Invalid response from payment gateway"
                }
            
            if self.sandbox:
                # Sandbox response format
                if result.get("Status") == 100:
                    ref_id = result.get("RefID")
                    
                    # Update Zarinpal payment record
                    zarinpal_payment.ref_id = ref_id
                    zarinpal_payment.status = 'verified'
                    zarinpal_payment.save()
                    
                    # Update transaction
                    transaction.status = 'completed'
                    transaction.transaction_id = ref_id
                    transaction.transaction_data = result
                    transaction.save()
                    
                    # Handle transaction type specific actions
                    self._handle_completed_transaction(transaction)
                    
                    # Notify user
                    self._notify_user_payment_status(zarinpal_payment)
                    
                    return {
                        "success": True,
                        "ref_id": ref_id,
                        "transaction_id": transaction.id
                    }
                else:
                    error_code = result.get("Status")
                    error_message = self._get_error_message(error_code)
                    logger.error(f"Zarinpal payment verification failed: {error_message} (Code: {error_code})")
                    
                    # Update Zarinpal payment record
                    zarinpal_payment.status = 'failed'
                    zarinpal_payment.save()
                    
                    # Update transaction
                    transaction.status = 'failed'
                    transaction.transaction_data = result
                    transaction.save()
                    
                    return {
                        "success": False,
                        "error_code": error_code,
                        "error_message": error_message
                    }
            else:
                # Production response format
                if result.get("data", {}).get("code") == 100:
                    ref_id = result.get("data", {}).get("ref_id")
                    
                    # Update Zarinpal payment record
                    zarinpal_payment.ref_id = ref_id
                    zarinpal_payment.status = 'verified'
                    zarinpal_payment.save()
                    
                    # Update transaction
                    transaction.status = 'completed'
                    transaction.transaction_id = ref_id
                    transaction.transaction_data = result
                    transaction.save()
                    
                    # Handle transaction type specific actions
                    self._handle_completed_transaction(transaction)
                    
                    # Notify user
                    self._notify_user_payment_status(zarinpal_payment)
                    
                    return {
                        "success": True,
                        "ref_id": ref_id,
                        "transaction_id": transaction.id
                    }
                else:
                    error_code = result.get("errors", {}).get("code")
                    error_message = result.get("errors", {}).get("message", "Unknown error")
                    logger.error(f"Zarinpal payment verification failed: {error_message} (Code: {error_code})")
                    
                    # Update Zarinpal payment record
                    zarinpal_payment.status = 'failed'
                    zarinpal_payment.save()
                    
                    # Update transaction
                    transaction.status = 'failed'
                    transaction.transaction_data = result
                    transaction.save()
                    
                    return {
                        "success": False,
                        "error_code": error_code,
                        "error_message": error_message
                    }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error to Zarinpal API: {str(e)}")
            return {
                "success": False,
                "error_message": f"Connection error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error verifying Zarinpal payment: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            }
    
    def _handle_completed_transaction(self, transaction):
        """Handle actions after a successful transaction"""
        try:
            # Update user wallet if this was a deposit
            if transaction.type == 'deposit':
                user = transaction.user
                user.wallet_balance += transaction.amount
                user.save()
                logger.info(f"Updated user {user.username} wallet balance to {user.wallet_balance}")
            
            # Activate subscription if this was a purchase
            if transaction.type == 'purchase' and hasattr(transaction, 'subscription'):
                subscription = transaction.subscription
                if subscription and subscription.status == 'pending':
                    subscription.status = 'active'
                    subscription.save()
                    
                    # Create client in 3X-UI panel
                    from v2ray.api_client import create_client
                    success = create_client(subscription.id)
                    
                    if success:
                        logger.info(f"Created client for subscription {subscription.id}")
                    else:
                        logger.error(f"Failed to create client for subscription {subscription.id}")
        except Exception as e:
            logger.error(f"Error handling completed transaction: {str(e)}")
    
    def _notify_admin_new_payment(self, zarinpal_payment):
        """Send notification to admin about new Zarinpal payment"""
        try:
            from telegrambot.services.notifications import AdminNotificationService
            
            transaction = zarinpal_payment.transaction
            user = transaction.user
            
            message = f"🔔 *New Zarinpal Payment*\n\n"
            message += f"👤 User: {user.username}\n"
            message += f"💰 Amount: {transaction.amount} Toman\n"
            message += f"🔑 Authority: {zarinpal_payment.authority}\n"
            message += f"🔗 Payment URL: {zarinpal_payment.payment_url}\n"
            message += f"⏱ Created at: {transaction.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            message += f"Payment is being processed by Zarinpal."
            
            notification_service = AdminNotificationService()
            notification_service.send_message(message)
            
            return True
        except ImportError:
            logger.warning("AdminNotificationService not available, admin notification not sent")
            return False
        except Exception as e:
            logger.error(f"Error sending admin notification: {str(e)}")
            return False
    
    def _notify_user_payment_status(self, zarinpal_payment):
        """Send notification to user about payment status"""
        try:
            from telegrambot.services.notifications import UserNotificationService
            
            transaction = zarinpal_payment.transaction
            user = transaction.user
            
            if zarinpal_payment.status == 'verified':
                message = f"✅ *Zarinpal Payment Successful*\n\n"
                message += f"💰 Amount: {transaction.amount} Toman\n"
                message += f"🔑 Reference ID: {zarinpal_payment.ref_id}\n"
                message += f"⏱ Completed at: {transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                message += f"Your account has been credited with {transaction.amount} Toman."
            
            elif zarinpal_payment.status == 'failed':
                message = f"❌ *Zarinpal Payment Failed*\n\n"
                message += f"💰 Amount: {transaction.amount} Toman\n"
                message += f"🔑 Authority: {zarinpal_payment.authority}\n"
                message += f"⏱ Time: {transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                message += f"Please try again or contact support if the problem persists."
            
            else:
                return False
                
            notification_service = UserNotificationService()
            notification_service.send_message(user, message)
            
            return True
        except ImportError:
            logger.warning("UserNotificationService not available, user notification not sent")
            return False
        except Exception as e:
            logger.error(f"Error sending user notification: {str(e)}")
            return False
    
    def _get_error_message(self, error_code):
        """Get error message for Zarinpal error code"""
        error_messages = {
            -1: "Information submitted is incomplete.",
            -2: "Merchant ID or IP address is not correct.",
            -3: "Amount should be above 1,000 Rial.",
            -4: "Approved level of Merchant ID is lower than the silver.",
            -11: "Request not found.",
            -12: "Edit request not possible.",
            -21: "Financial operations for this transaction was not found.",
            -22: "Transaction is unsuccessful.",
            -33: "Transaction amount does not match the payment amount.",
            -34: "Limit of transaction division has been reached.",
            -40: "There is no access to the method.",
            -41: "Additional data format is invalid.",
            -42: "Initiator IP or Merchant ID is invalid.",
            -54: "Request archived.",
            100: "Operation was successful.",
            101: "Operation was successful but verification operation on this transaction has already been done."
        }
        
        return error_messages.get(error_code, "Unknown error") 