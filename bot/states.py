from telegram.ext import ConversationHandler

# وضعیت‌های مکالمه کاربر در هنگام خرید پلن
class PurchaseStates:
    # وضعیت‌های اصلی خرید
    SELECT_CATEGORY = 1
    SELECT_PLAN = 2
    SELECT_LOCATION = 3
    SELECT_PROTOCOL = 4
    CONFIRM_PURCHASE = 5
    SELECT_PAYMENT_METHOD = 6
    PROCESS_PAYMENT = 7
    
    # وضعیت‌های مربوط به پرداخت کارت به کارت
    CARD_TO_CARD_PAYMENT = 10
    UPLOAD_RECEIPT = 11
    PAYMENT_DETAILS = 12
    
    # وضعیت‌های مربوط به پرداخت از کیف پول
    WALLET_PAYMENT_CONFIRM = 20
    
    # وضعیت‌های نهایی
    PAYMENT_COMPLETE = 30
    ORDER_COMPLETE = 31
    
    # خروج از مکالمه
    CANCEL = ConversationHandler.END

# وضعیت‌های مکالمه کاربر در هنگام شارژ کیف پول
class WalletStates:
    SELECT_AMOUNT = 1
    SELECT_PAYMENT_METHOD = 2
    CARD_TO_CARD_PAYMENT = 3
    UPLOAD_RECEIPT = 4
    PAYMENT_DETAILS = 5
    PAYMENT_COMPLETE = 6
    CANCEL = ConversationHandler.END

# وضعیت‌های مکالمه کاربر در هنگام مدیریت سرویس‌ها
class ServiceStates:
    SELECT_SERVICE = 1
    SERVICE_ACTIONS = 2
    CHANGE_LOCATION = 3
    CONFIRM_CHANGE = 4
    CHANGE_PROTOCOL = 5
    FREEZE_SERVICE = 6
    RENEW_SERVICE = 7
    CANCEL = ConversationHandler.END
