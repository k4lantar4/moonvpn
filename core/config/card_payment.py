import logging
import uuid
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Transaction, CardPayment, CardOwner
from .ocr_verification import ReceiptOCRProcessor
# from notifications.telegram import send_admin_notification, send_user_notification
from django.db import transaction
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDate

logger = logging.getLogger(__name__)

# Placeholder functions for notifications
def send_admin_notification(message, **kwargs):
    """Placeholder for admin notification function"""
    logger.info(f"[ADMIN NOTIFICATION] {message}")
    
def send_user_notification(user_id, message, **kwargs):
    """Placeholder for user notification function"""
    logger.info(f"[USER NOTIFICATION] To user {user_id}: {message}")

class CardPaymentProcessor:
    """Process card to card payments with OCR verification and card owner tracking"""
    
    def __init__(self):
        """Initialize the card payment processor"""
        self.admin_notification_enabled = getattr(settings, 'ADMIN_NOTIFICATION_ENABLED', True)
        self.verification_timeout_minutes = getattr(settings, 'CARD_PAYMENT_VERIFICATION_TIMEOUT_MINUTES', 30)
        self.card_number = getattr(settings, 'CARD_PAYMENT_NUMBER', '')
        self.card_holder = getattr(settings, 'CARD_PAYMENT_HOLDER', '')
        self.bank_name = getattr(settings, 'CARD_PAYMENT_BANK', '')
        self.ocr_processor = ReceiptOCRProcessor()
    
    def create_payment(self, user, amount, card_owner_id=None, verification_method='manual'):
        """Create a new card payment"""
        try:
            with transaction.atomic():
                # Create transaction
                tx = Transaction.objects.create(
                    user=user,
                    amount=amount,
                    type='deposit',
                    description='Card to card payment'
                )
                
                # Get card owner if provided
                card_owner = None
                if card_owner_id:
                    try:
                        card_owner = CardOwner.objects.get(id=card_owner_id, is_active=True)
                    except CardOwner.DoesNotExist:
                        logger.warning(f"Card owner {card_owner_id} not found or inactive")
                
                # Create card payment
                payment = CardPayment.objects.create(
                    transaction=tx,
                    card_owner=card_owner,
                    card_number=card_owner.card_number if card_owner else None,
                    verification_method=verification_method
                )
                
                # Send notifications
                self._notify_payment_created(payment)
                
                return payment
                
        except Exception as e:
            logger.error(f"Error creating card payment: {str(e)}")
            raise
    
    def verify_payment(self, payment_id, admin_user, receipt_image=None, admin_note=''):
        """Verify a card payment with optional OCR verification"""
        try:
            payment = CardPayment.objects.select_for_update().get(id=payment_id)
            
            if payment.is_expired():
                payment.status = 'expired'
                payment.save()
                self._notify_payment_expired(payment)
                return False, "Payment has expired"
            
            # Perform OCR verification if receipt image is provided
            ocr_verified = False
            if receipt_image and payment.verification_method in ['ocr', 'both']:
                ocr_verified, ocr_message = self.ocr_processor.verify_payment(payment_id, receipt_image)
                if not ocr_verified and payment.verification_method == 'ocr':
                    payment.status = 'retry'
                    payment.admin_note = f"OCR verification failed: {ocr_message}"
                    payment.save()
                    self._notify_payment_retry(payment)
                    return False, ocr_message
            
            # Manual verification by admin
            if payment.verification_method in ['manual', 'both']:
                with transaction.atomic():
                    # Update payment status
                    payment.status = 'verified'
                    payment.verified_by = admin_user
                    payment.verified_at = timezone.now()
                    payment.admin_note = admin_note
                    payment.save()
                    
                    # Update transaction status
                    payment.transaction.status = 'completed'
                    payment.transaction.save()
                    
                    # Update card owner if exists
                    if payment.card_owner and not payment.card_owner.is_verified:
                        payment.card_owner.verify(admin_user)
                    
                    # Send notifications
                    self._notify_payment_verified(payment)
                    
                    return True, "Payment verified successfully"
            
            return False, "Invalid verification method"
            
        except CardPayment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return False, "Payment not found"
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return False, str(e)
    
    def reject_payment(self, payment_id, admin_user, reason=''):
        """Reject a card payment"""
        try:
            with transaction.atomic():
                payment = CardPayment.objects.select_for_update().get(id=payment_id)
                
                if payment.status == 'verified':
                    return False, "Cannot reject a verified payment"
                
                payment.status = 'rejected'
                payment.verified_by = admin_user
                payment.verified_at = timezone.now()
                payment.admin_note = reason
                payment.save()
                
                payment.transaction.status = 'failed'
                payment.transaction.save()
                
                # Send notifications
                self._notify_payment_rejected(payment)
                
                return True, "Payment rejected successfully"
                
        except CardPayment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return False, "Payment not found"
        except Exception as e:
            logger.error(f"Error rejecting payment: {str(e)}")
            return False, str(e)
    
    def retry_payment(self, payment_id):
        """Retry a failed or expired payment with exponential backoff"""
        try:
            payment = CardPayment.objects.get(id=payment_id)
            
            if payment.can_retry():
                # Calculate exponential backoff delay
                base_delay = 5  # Base delay in minutes
                max_delay = 60  # Maximum delay in minutes
                delay = min(base_delay * (2 ** payment.retry_count), max_delay)
                
                # Update payment for retry
                payment.retry_count += 1
                payment.status = 'pending'
                payment.created_at = timezone.now()
                payment.expires_at = timezone.now() + timedelta(minutes=self.verification_timeout_minutes)
                payment.save()
                
                # Send notifications
                self._notify_payment_retry(payment, delay)
                
                return True, f"Payment retry initiated. New timeout: {delay} minutes"
            else:
                return False, "Payment cannot be retried"
                
        except CardPayment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return False, "Payment not found"
        except Exception as e:
            logger.error(f"Error retrying payment: {str(e)}")
            return False, str(e)
    
    def _notify_payment_created(self, payment):
        """Send notifications for new payment"""
        user_msg = (
            f"🏦 پرداخت جدید ایجاد شد!\n\n"
            f"💰 مبلغ: {payment.transaction.amount:,} تومان\n"
            f"🔑 کد پیگیری: {payment.verification_code}\n"
            f"⏰ مهلت پرداخت: {payment.expires_at.strftime('%H:%M:%S')}\n\n"
            f"لطفا مبلغ را به کارت زیر واریز کنید:\n"
            f"💳 {payment.card_number if payment.card_number else 'در انتظار تخصیص کارت'}"
        )
        
        admin_msg = (
            f"💫 درخواست پرداخت جدید\n\n"
            f"👤 کاربر: {payment.transaction.user.username}\n"
            f"💰 مبلغ: {payment.transaction.amount:,} تومان\n"
            f"🔑 کد پیگیری: {payment.verification_code}"
        )
        
        send_user_notification(payment.transaction.user.telegram_id, user_msg)
        send_admin_notification(admin_msg)
    
    def _notify_payment_verified(self, payment):
        """Send notifications for verified payment"""
        user_msg = (
            f"✅ پرداخت شما تایید شد!\n\n"
            f"💰 مبلغ: {payment.transaction.amount:,} تومان\n"
            f"🔑 کد پیگیری: {payment.verification_code}"
        )
        
        admin_msg = (
            f"✅ پرداخت تایید شد\n\n"
            f"👤 کاربر: {payment.transaction.user.username}\n"
            f"💰 مبلغ: {payment.transaction.amount:,} تومان\n"
            f"🔑 کد پیگیری: {payment.verification_code}\n"
            f"👨‍💼 تایید کننده: {payment.verified_by.username}"
        )
        
        send_user_notification(payment.transaction.user.telegram_id, user_msg)
        send_admin_notification(admin_msg)
    
    def _notify_payment_rejected(self, payment):
        """Send notifications for rejected payment"""
        user_msg = (
            f"❌ پرداخت شما رد شد\n\n"
            f"💰 مبلغ: {payment.transaction.amount:,} تومان\n"
            f"🔑 کد پیگیری: {payment.verification_code}\n"
            f"📝 دلیل: {payment.admin_note}"
        )
        
        admin_msg = (
            f"❌ پرداخت رد شد\n\n"
            f"👤 کاربر: {payment.transaction.user.username}\n"
            f"💰 مبلغ: {payment.transaction.amount:,} تومان\n"
            f"🔑 کد پیگیری: {payment.verification_code}\n"
            f"👨‍💼 رد کننده: {payment.verified_by.username}\n"
            f"📝 دلیل: {payment.admin_note}"
        )
        
        send_user_notification(payment.transaction.user.telegram_id, user_msg)
        send_admin_notification(admin_msg)
    
    def _notify_payment_expired(self, payment):
        """Send notifications for expired payment"""
        user_msg = (
            f"⏰ پرداخت شما منقضی شد\n\n"
            f"💰 مبلغ: {payment.transaction.amount:,} تومان\n"
            f"🔑 کد پیگیری: {payment.verification_code}"
        )
        
        admin_msg = (
            f"⏰ پرداخت منقضی شد\n\n"
            f"👤 کاربر: {payment.transaction.user.username}\n"
            f"💰 مبلغ: {payment.transaction.amount:,} تومان\n"
            f"🔑 کد پیگیری: {payment.verification_code}"
        )
        
        send_user_notification(payment.transaction.user.telegram_id, user_msg)
        send_admin_notification(admin_msg)
    
    def _notify_payment_retry(self, payment, delay):
        """Send notifications for payment retry with delay information"""
        user_msg = (
            f"🔄 درخواست پرداخت مجدد\n\n"
            f"💰 مبلغ: {payment.transaction.amount:,} تومان\n"
            f"🔑 کد پیگیری: {payment.verification_code}\n"
            f"⏰ مهلت جدید: {payment.expires_at.strftime('%H:%M:%S')}\n"
            f"⏳ تاخیر: {delay} دقیقه"
        )
        
        admin_msg = (
            f"🔄 درخواست پرداخت مجدد\n\n"
            f"👤 کاربر: {payment.transaction.user.username}\n"
            f"💰 مبلغ: {payment.transaction.amount:,} تومان\n"
            f"🔑 کد پیگیری: {payment.verification_code}\n"
            f"🔢 تعداد تلاش: {payment.retry_count}/{payment.max_retries}\n"
            f"⏳ تاخیر: {delay} دقیقه"
        )
        
        send_user_notification(payment.transaction.user.telegram_id, user_msg)
        send_admin_notification(admin_msg)
    
    def get_payment_details(self):
        """Get card payment details for display to users"""
        return {
            "card_number": self.card_number,
            "card_holder": self.card_holder,
            "bank_name": self.bank_name,
            "verification_timeout_minutes": self.verification_timeout_minutes
        }
    
    def _notify_admin_new_payment(self, card_payment):
        """Send notification to admin about new card payment"""
        try:
            from telegrambot.services.notifications import AdminNotificationService
            
            transaction = card_payment.transaction
            user = transaction.user
            
            message = f"🔔 *New Card Payment*\n\n"
            message += f"👤 User: {user.username}\n"
            message += f"💰 Amount: {transaction.amount} Toman\n"
            message += f"💳 Card: {card_payment.card_number}\n"
            message += f"📝 Reference: {card_payment.reference_number}\n"
            message += f"⏱ Transfer Time: {card_payment.transfer_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"🔑 Verification Code: {card_payment.verification_code}\n"
            message += f"⏳ Expires at: {card_payment.expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            message += f"Use the admin panel to verify this payment."
            
            notification_service = AdminNotificationService()
            notification_service.send_message(message)
            
            return True
        except ImportError:
            logger.warning("AdminNotificationService not available, admin notification not sent")
            return False
        except Exception as e:
            logger.error(f"Error sending admin notification: {str(e)}")
            return False
    
    def _notify_user_payment_status(self, card_payment):
        """Send notification to user about payment status"""
        try:
            from telegrambot.services.notifications import UserNotificationService
            
            transaction = card_payment.transaction
            user = transaction.user
            
            if card_payment.status == 'verified':
                message = f"✅ *Payment Verified*\n\n"
                message += f"💰 Amount: {transaction.amount} Toman\n"
                message += f"🔑 Verification Code: {card_payment.verification_code}\n"
                message += f"⏱ Verified at: {card_payment.verified_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                message += f"Your account has been credited with {transaction.amount} Toman."
            
            elif card_payment.status == 'rejected':
                message = f"❌ *Payment Rejected*\n\n"
                message += f"💰 Amount: {transaction.amount} Toman\n"
                message += f"🔑 Verification Code: {card_payment.verification_code}\n"
                message += f"⏱ Rejected at: {card_payment.verified_at.strftime('%Y-%m-%d %H:%M:%S') if card_payment.verified_at else 'N/A'}\n"
                
                if card_payment.admin_note:
                    message += f"📝 Reason: {card_payment.admin_note}\n\n"
                else:
                    message += f"\nPlease contact support for more information."
            
            elif card_payment.status == 'expired':
                message = f"⌛ *Payment Expired*\n\n"
                message += f"💰 Amount: {transaction.amount} Toman\n"
                message += f"🔑 Verification Code: {card_payment.verification_code}\n"
                message += f"⏱ Expired at: {card_payment.expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                message += f"Please create a new payment if you wish to continue."
            
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
    
    def create_card_owner(self, name, card_number, bank_name, admin_user=None):
        """Create a new card owner"""
        try:
            with transaction.atomic():
                card_owner = CardOwner.objects.create(
                    name=name,
                    card_number=card_number,
                    bank_name=bank_name
                )
                
                if admin_user:
                    card_owner.verify(admin_user)
                
                self._notify_card_owner_created(card_owner)
                return card_owner
                
        except Exception as e:
            logger.error(f"Error creating card owner: {str(e)}")
            raise
    
    def update_card_owner(self, card_owner_id, name=None, bank_name=None, is_active=None, admin_user=None):
        """Update a card owner's details"""
        try:
            with transaction.atomic():
                card_owner = CardOwner.objects.select_for_update().get(id=card_owner_id)
                
                if name:
                    card_owner.name = name
                if bank_name:
                    card_owner.bank_name = bank_name
                if is_active is not None:
                    card_owner.is_active = is_active
                
                card_owner.save()
                
                if admin_user and not card_owner.is_verified:
                    card_owner.verify(admin_user)
                
                self._notify_card_owner_updated(card_owner)
                return card_owner
                
        except CardOwner.DoesNotExist:
            logger.error(f"Card owner {card_owner_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error updating card owner: {str(e)}")
            raise
    
    def get_active_card_owners(self):
        """Get all active card owners"""
        return CardOwner.objects.filter(is_active=True).order_by('-created_at')
    
    def get_verified_card_owners(self):
        """Get all verified card owners"""
        return CardOwner.objects.filter(is_verified=True, is_active=True).order_by('-created_at')
    
    def _notify_card_owner_created(self, card_owner):
        """Send notifications for new card owner"""
        admin_msg = (
            f"💳 کارت جدید اضافه شد\n\n"
            f"👤 صاحب کارت: {card_owner.name}\n"
            f"🏦 بانک: {card_owner.bank_name}\n"
            f"💳 شماره کارت: {card_owner.card_number}\n"
            f"✅ وضعیت تایید: {'تایید شده' if card_owner.is_verified else 'در انتظار تایید'}"
        )
        
        send_admin_notification(admin_msg)
    
    def _notify_card_owner_updated(self, card_owner):
        """Send notifications for updated card owner"""
        admin_msg = (
            f"🔄 اطلاعات کارت بروزرسانی شد\n\n"
            f"👤 صاحب کارت: {card_owner.name}\n"
            f"🏦 بانک: {card_owner.bank_name}\n"
            f"💳 شماره کارت: {card_owner.card_number}\n"
            f"✅ وضعیت تایید: {'تایید شده' if card_owner.is_verified else 'در انتظار تایید'}\n"
            f"🔄 وضعیت: {'فعال' if card_owner.is_active else 'غیرفعال'}"
        )
        
        send_admin_notification(admin_msg)
    
    def get_payment_stats(self, start_date=None, end_date=None, card_owner_id=None):
        """Get payment statistics for a given period"""
        try:
            # Base queryset
            payments = CardPayment.objects.all()
            
            # Apply filters
            if start_date:
                payments = payments.filter(created_at__gte=start_date)
            if end_date:
                payments = payments.filter(created_at__lte=end_date)
            if card_owner_id:
                payments = payments.filter(card_owner_id=card_owner_id)
            
            # Calculate daily stats
            daily_stats = payments.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                total_count=Count('id'),
                total_amount=Sum('transaction__amount'),
                verified_count=Count('id', filter=models.Q(status='verified')),
                verified_amount=Sum('transaction__amount', filter=models.Q(status='verified')),
                rejected_count=Count('id', filter=models.Q(status='rejected')),
                rejected_amount=Sum('transaction__amount', filter=models.Q(status='rejected')),
                expired_count=Count('id', filter=models.Q(status='expired')),
                expired_amount=Sum('transaction__amount', filter=models.Q(status='expired')),
                avg_verification_time=Avg(
                    models.F('verified_at') - models.F('created_at'),
                    filter=models.Q(status='verified')
                )
            ).order_by('date')
            
            # Calculate overall stats
            total_stats = {
                'total_count': payments.count(),
                'total_amount': payments.aggregate(total=Sum('transaction__amount'))['total'] or 0,
                'verified_count': payments.filter(status='verified').count(),
                'verified_amount': payments.filter(status='verified').aggregate(total=Sum('transaction__amount'))['total'] or 0,
                'rejected_count': payments.filter(status='rejected').count(),
                'rejected_amount': payments.filter(status='rejected').aggregate(total=Sum('transaction__amount'))['total'] or 0,
                'expired_count': payments.filter(status='expired').count(),
                'expired_amount': payments.filter(status='expired').aggregate(total=Sum('transaction__amount'))['total'] or 0,
                'success_rate': (payments.filter(status='verified').count() / payments.count() * 100) if payments.count() > 0 else 0,
                'avg_verification_time': payments.filter(status='verified').aggregate(
                    avg_time=Avg(models.F('verified_at') - models.F('created_at'))
                )['avg_time']
            }
            
            return {
                'daily_stats': list(daily_stats),
                'total_stats': total_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting payment stats: {str(e)}")
            raise
    
    def get_card_owner_stats(self, card_owner_id):
        """Get statistics for a specific card owner"""
        try:
            payments = CardPayment.objects.filter(card_owner_id=card_owner_id)
            
            stats = {
                'total_payments': payments.count(),
                'total_amount': payments.aggregate(total=Sum('transaction__amount'))['total'] or 0,
                'verified_payments': payments.filter(status='verified').count(),
                'verified_amount': payments.filter(status='verified').aggregate(total=Sum('transaction__amount'))['total'] or 0,
                'rejected_payments': payments.filter(status='rejected').count(),
                'rejected_amount': payments.filter(status='rejected').aggregate(total=Sum('transaction__amount'))['total'] or 0,
                'expired_payments': payments.filter(status='expired').count(),
                'expired_amount': payments.filter(status='expired').aggregate(total=Sum('transaction__amount'))['total'] or 0,
                'success_rate': (payments.filter(status='verified').count() / payments.count() * 100) if payments.count() > 0 else 0,
                'avg_verification_time': payments.filter(status='verified').aggregate(
                    avg_time=Avg(models.F('verified_at') - models.F('created_at'))
                )['avg_time']
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting card owner stats: {str(e)}")
            raise
    
    def generate_payment_report(self, start_date=None, end_date=None, card_owner_id=None):
        """Generate a detailed payment report"""
        try:
            stats = self.get_payment_stats(start_date, end_date, card_owner_id)
            
            report = {
                'period': {
                    'start': start_date.strftime('%Y-%m-%d') if start_date else 'All time',
                    'end': end_date.strftime('%Y-%m-%d') if end_date else 'Present'
                },
                'summary': {
                    'total_payments': stats['total_stats']['total_count'],
                    'total_amount': stats['total_stats']['total_amount'],
                    'success_rate': f"{stats['total_stats']['success_rate']:.2f}%",
                    'avg_verification_time': str(stats['total_stats']['avg_verification_time']).split('.')[0] if stats['total_stats']['avg_verification_time'] else 'N/A'
                },
                'status_breakdown': {
                    'verified': {
                        'count': stats['total_stats']['verified_count'],
                        'amount': stats['total_stats']['verified_amount']
                    },
                    'rejected': {
                        'count': stats['total_stats']['rejected_count'],
                        'amount': stats['total_stats']['rejected_amount']
                    },
                    'expired': {
                        'count': stats['total_stats']['expired_count'],
                        'amount': stats['total_stats']['expired_amount']
                    }
                },
                'daily_stats': stats['daily_stats']
            }
            
            # Add card owner info if specified
            if card_owner_id:
                card_owner = CardOwner.objects.get(id=card_owner_id)
                report['card_owner'] = {
                    'name': card_owner.name,
                    'bank_name': card_owner.bank_name,
                    'card_number': card_owner.card_number,
                    'is_verified': card_owner.is_verified
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating payment report: {str(e)}")
            raise
    
    def notify_payment_report(self, report, admin_user):
        """Send payment report notification to admin"""
        try:
            admin_msg = (
                f"📊 گزارش پرداخت‌ها\n\n"
                f"📅 دوره: {report['period']['start']} تا {report['period']['end']}\n"
                f"💰 مجموع پرداخت‌ها: {report['summary']['total_amount']:,} تومان\n"
                f"✅ نرخ موفقیت: {report['summary']['success_rate']}\n"
                f"⏱ میانگین زمان تایید: {report['summary']['avg_verification_time']}\n\n"
                f"📈 وضعیت پرداخت‌ها:\n"
                f"✅ تایید شده: {report['status_breakdown']['verified']['count']} پرداخت\n"
                f"❌ رد شده: {report['status_breakdown']['rejected']['count']} پرداخت\n"
                f"⏰ منقضی شده: {report['status_breakdown']['expired']['count']} پرداخت"
            )
            
            if 'card_owner' in report:
                admin_msg += f"\n\n💳 اطلاعات کارت:\n"
                admin_msg += f"👤 صاحب کارت: {report['card_owner']['name']}\n"
                admin_msg += f"🏦 بانک: {report['card_owner']['bank_name']}\n"
                admin_msg += f"💳 شماره کارت: {report['card_owner']['card_number']}"
            
            send_admin_notification(admin_msg)
            return True
            
        except Exception as e:
            logger.error(f"Error sending payment report notification: {str(e)}")
            return False
    
    def bulk_verify_payments(self, payment_ids, admin_user, note=None):
        """Verify multiple payments in bulk"""
        try:
            with transaction.atomic():
                payments = CardPayment.objects.filter(
                    id__in=payment_ids,
                    status='pending'
                ).select_related('transaction', 'transaction__user')
                
                verified_count = 0
                failed_count = 0
                results = []
                
                for payment in payments:
                    try:
                        # Verify payment
                        payment.status = 'verified'
                        payment.verified_at = timezone.now()
                        payment.verified_by = admin_user
                        payment.admin_note = note
                        payment.save()
                        
                        # Update transaction
                        payment.transaction.status = 'completed'
                        payment.transaction.save()
                        
                        # Send notifications
                        self._notify_user_payment_status(payment)
                        self._notify_admin_payment_status(payment)
                        
                        verified_count += 1
                        results.append({
                            'payment_id': payment.id,
                            'status': 'success',
                            'message': 'Payment verified successfully'
                        })
                        
                    except Exception as e:
                        failed_count += 1
                        results.append({
                            'payment_id': payment.id,
                            'status': 'error',
                            'message': str(e)
                        })
                        logger.error(f"Error verifying payment {payment.id}: {str(e)}")
                
                # Send bulk verification summary
                self._notify_bulk_verification_summary(
                    verified_count,
                    failed_count,
                    admin_user,
                    note
                )
                
                return {
                    'success': True,
                    'verified_count': verified_count,
                    'failed_count': failed_count,
                    'results': results
                }
                
        except Exception as e:
            logger.error(f"Error in bulk payment verification: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _notify_bulk_verification_summary(self, verified_count, failed_count, admin_user, note):
        """Send notification for bulk verification summary"""
        try:
            admin_msg = (
                f"✅ تایید گروهی پرداخت‌ها\n\n"
                f"👤 ادمین: {admin_user.username}\n"
                f"✅ تایید شده: {verified_count} پرداخت\n"
                f"❌ ناموفق: {failed_count} پرداخت\n"
                f"📝 یادداشت: {note if note else 'بدون یادداشت'}"
            )
            
            send_admin_notification(admin_msg)
            
        except Exception as e:
            logger.error(f"Error sending bulk verification summary: {str(e)}") 