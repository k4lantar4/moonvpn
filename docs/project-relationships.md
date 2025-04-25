# 🔗 Project Relationships (MoonVPN)

این مستند روابط بین مدل‌های اصلی دیتابیس (`db/models/`) و نحوه تعامل سرویس‌ها (`core/services/`) با آن‌ها را شرح می‌دهد.

## 🧑‍💼 User & Authentication
- **Model:** `User` (`db/models/user.py`)
- **Service:** `UserService` (`core/services/user_service.py`)
- **Relationships:**
    - **One-to-Many:** `User` -> `Order` (یک کاربر می‌تواند چندین سفارش داشته باشد)
    - **One-to-Many:** `User` -> `Transaction` (یک کاربر می‌تواند چندین تراکنش داشته باشد)
    - **One-to-Many:** `User` -> `NotificationLog` (گزارشات نوتیفیکیشن‌های ارسال شده به کاربر)
    - **One-to-Many:** `User` -> `ClientAccount` (اکانت‌های ساخته شده برای کاربر)
    - **One-to-Many:** `User` -> `BankCard` (کارت‌های بانکی ثبت شده توسط کاربر)
- **Notes:** مدیریت اطلاعات کاربران، وضعیت (فعال/غیرفعال)، نقش‌ها (ادمین/کاربر عادی)، و کیف پول.

## 🛒 Order & Plan
- **Models:** `Order` (`db/models/order.py`), `Plan` (`db/models/plan.py`)
- **Service:** `OrderService` (`core/services/order_service.py`), `PlanService` (`core/services/plan_service.py`)
- **Relationships:**
    - **Many-to-One:** `Order` -> `User` (هر سفارش متعلق به یک کاربر است)
    - **Many-to-One:** `Order` -> `Plan` (هر سفارش برای یک پلن مشخص است)
    - **One-to-Many:** `Plan` -> `Order` (یک پلن می‌تواند در چندین سفارش استفاده شود)
    - **One-to-One:** `Order` -> `Transaction` (ممکن است یک سفارش با یک تراکنش پرداخت مرتبط باشد)
    - **One-to-Many:** `Order` -> `ReceiptLog` (رسیدهای ثبت شده برای یک سفارش)
    - **One-to-One:** `Order` -> `ClientAccount` (سفارش خرید/تمدید منجر به ایجاد/آپدیت اکانت می‌شود)
- **Notes:** مدیریت سفارشات خرید و تمدید پلن‌ها توسط کاربران. پلن‌ها شامل جزئیات حجم، زمان و قیمت هستند.

## 💳 Transaction, Wallet & Payment
- **Models:** `Transaction` (`db/models/transaction.py`), `BankCard` (`db/models/bank_card.py`), `ReceiptLog` (`db/models/receipt_log.py`)
- **Services:** `TransactionService` (`core/services/transaction_service.py`), `WalletService` (`core/services/wallet_service.py`), `PaymentService` (`core/services/payment_service.py`)
- **Relationships:**
    - **Many-to-One:** `Transaction` -> `User` (هر تراکنش متعلق به یک کاربر است)
    - **Many-to-One:** `Transaction` -> `Order` (هر تراکنش ممکن است مربوط به یک سفارش باشد)
    - **Many-to-One:** `ReceiptLog` -> `Order` (هر رسید مربوط به یک سفارش است)
    - **Many-to-One:** `ReceiptLog` -> `BankCard` (هر رسید با یک کارت بانکی ثبت می‌شود)
    - **Many-to-One:** `ReceiptLog` -> `User` (ادمین تأیید کننده رسید)
    - **Many-to-One:** `BankCard` -> `User` (هر کارت متعلق به یک کاربر است)
- **Notes:** `Transaction` برای ثبت تمام تغییرات مالی (واریز، برداشت، خرید) استفاده می‌شود. موجودی کیف پول (`User.wallet_balance`) بر اساس جمع تراکنش‌های موفق محاسبه می‌شود. `PaymentService` عملیات پرداخت (کارت به کارت و درگاه) را مدیریت کرده و `ReceiptLog` سوابق تأیید پرداخت‌های کارت به کارت توسط ادمین را نگه می‌دارد.

## 🖥️ Panel, Inbound & Client Account
- **Models:** `Panel` (`db/models/panel.py`), `Inbound` (`db/models/inbound.py`), `ClientAccount` (`db/models/client_account.py`)
- **Services:** `PanelService` (`core/services/panel_service.py`), `InboundService` (`core/services/inbound_service.py`), `ClientService` (`core/services/client_service.py`), `AccountService` (`core/services/account_service.py`)
- **Relationships:**
    - **One-to-Many:** `Panel` -> `Inbound` (هر پنل می‌تواند چندین Inbound داشته باشد)
    - **Many-to-One:** `Inbound` -> `Panel` (هر Inbound متعلق به یک پنل است)
    - **One-to-Many:** `Panel` -> `ClientAccount` (اکانت‌های کلاینت‌ها روی پنل‌ها ساخته می‌شوند)
    - **Many-to-One:** `ClientAccount` -> `User` (هر اکانت متعلق به یک کاربر است)
    - **Many-to-One:** `ClientAccount` -> `Order` (اکانت با سفارش خرید/تمدید مرتبط است)
    - **Many-to-One:** `ClientAccount` -> `Panel` (اکانت روی یک پنل خاص قرار دارد)
    - **Many-to-Many:** `ClientAccount` <-> `Inbound` (یک اکانت می‌تواند روی چندین Inbound یک پنل فعال باشد - از طریق فیلد `inbound_ids` در `ClientAccount`)
- **Notes:** `Panel` اطلاعات دسترسی به پنل‌های X-UI را ذخیره می‌کند. `Inbound` تنظیمات ورودی‌های هر پنل را نگه می‌دارد. `ClientAccount` اطلاعات اکانت ساخته شده برای کاربر (UUID، ایمیل، حجم مصرفی، تاریخ انقضا و...) را ذخیره می‌کند و `AccountService` وظیفه ساخت، آپدیت و حذف اکانت‌ها در پنل‌ها را از طریق API پنل بر عهده دارد.

## 🔄 Client Renewal Log
- **Model:** `ClientRenewalLog` (`db/models/client_renewal_log.py`)
- **Service:** `ClientRenewalLogService` (`core/services/client_renewal_log_service.py`)
- **Relationships:**
    - **Many-to-One:** `ClientRenewalLog` -> `User`
    - **Many-to-One:** `ClientRenewalLog` -> `ClientAccount`
    - **Many-to-One:** `ClientRenewalLog` -> `Order`
- **Notes:** این جدول تاریخچه تمدید هر اکانت کلاینت را ثبت می‌کند، شامل اطلاعات سفارش و وضعیت تمدید.

## 🔔 Notification Log
- **Model:** `NotificationLog` (`db/models/notification_log.py`)
- **Service:** `NotificationService` (`core/services/notification_service.py`)
- **Relationships:**
    - **Many-to-One:** `NotificationLog` -> `User` (کاربری که نوتیفیکیشن را دریافت کرده)
- **Notes:** سوابق تمام نوتیفیکیشن‌های ارسال شده به کاربران (مثلاً از طریق بات تلگرام) را ذخیره می‌کند.

## 🧪 Test Account Log
- **Model:** `TestAccountLog` (`db/models/test_account_log.py`)
- **Relationships:**
    - **Many-to-One:** `TestAccountLog` -> `User` (کاربری که اکانت تست دریافت کرده)
    - **Many-to-One:** `TestAccountLog` -> `Panel` (پنلی که اکانت تست روی آن ساخته شده)
- **Notes:** سوابق درخواست و ایجاد اکانت‌های تست توسط کاربران را نگه می‌دارد.

## ⚙️ Settings
- **Model:** `Setting` (`db/models/setting.py`)
- **Service:** `SettingsService` (`core/services/settings_service.py`)
- **Notes:** برای ذخیره تنظیمات کلی برنامه به صورت Key-Value استفاده می‌شود.

## 🏷️ Discount Code
- **Model:** `DiscountCode` (`db/models/discount_code.py`)
- **Relationships:**
    - **Many-to-One:** `DiscountCode` -> `User` (اختیاری، اگر کد تخفیف مخصوص کاربر خاصی باشد)
    - **Many-to-Many:** `DiscountCode` <-> `Plan` (اختیاری، اگر کد تخفیف مخصوص پلن(های) خاصی باشد)
- **Notes:** مدیریت کدهای تخفیف، شامل درصد/مقدار تخفیف، تاریخ انقضا، محدودیت استفاده و...

## ↔️ Account Transfer
- **Model:** `AccountTransfer` (`db/models/account_transfer.py`)
- **Relationships:**
    - **Many-to-One:** `AccountTransfer` -> `ClientAccount` (اکانتی که منتقل شده)
    - **Many-to-One:** `AccountTransfer` -> `Panel` (پنل مبدأ و مقصد)
- **Notes:** سوابق انتقال اکانت‌ها بین پنل‌ها را ذخیره می‌کند (جزئیات پنل مبدأ و مقصد).
