*This scratchpad file serves as a phase-specific task tracker and implementation planner. The Mode System on Line 1 is critical and must never be deleted. It defines two core modes: Implementation Type for new feature development and Bug Fix Type for issue resolution. Each mode requires specific documentation formats, confidence tracking, and completion criteria. Use "plan" trigger for planning phase (🎯) and "agent" trigger for execution phase (⚡) after reaching 95% confidence. Follow strict phase management with clear documentation transfer process.*

`MODE SYSTEM TYPES (DO NOT DELETE!):
1. Implementation Type (New Features):
   - Trigger: User requests new implementation
   - Format: MODE: Implementation, FOCUS: New functionality
   - Requirements: Detailed planning, architecture review, documentation
   - Process: Plan mode (🎯) → 95% confidence → Agent mode (⚡)

2. Bug Fix Type (Issue Resolution):
   - Trigger: User reports bug/issue
   - Format: MODE: Bug Fix, FOCUS: Issue resolution
   - Requirements: Problem diagnosis, root cause analysis, solution verification
   - Process: Plan mode (🎯) → Chain of thought analysis → Agent mode (⚡)

Cross-reference with @memories.md and @lessons-learned.md for context and best practices.`

# Mode: PLAN 🎯
Current Task: ریفکتور کردن کامل دایرکتوری `bot/` برای افزایش خوانایی، ماژولار بودن و قابلیت نگهداری کد ربات تلگرام.
Understanding:
- بازسازی ساختار پوشه `bot/` بر اساس ویژگی‌ها (features) به جای نوع فایل (commands, callbacks).
- انتقال تمام منطق مربوط به هر ویژگی (هندلرها، کیبوردها، وضعیت‌ها) به پوشه مخصوص خودش در `bot/features/`.
- جایگزینی `MemoryStorage` با `RedisStorage` برای مدیریت پایدار وضعیت‌های FSM.
- استفاده از روترهای (`aiogram.Router`) مجزا برای هر ویژگی و ثبت آن‌ها در `main.py`.
- ساده‌سازی `main.py` و حذف توابع `register_*` قدیمی.
- اطمینان از تزریق وابستگی‌ها (مثل `session` و `user`) از طریق میدل‌ورها.
- حذف پوشه‌ها و فایل‌های قدیمی و منسوخ شده.
- انتقال تدریجی منطق هر ویژگی (start, common, buy, wallet, profile, my_accounts, admin, panel_management) به ساختار جدید.
- ری‌استارت و تست ربات بعد از هر مرحله مهم برای اطمینان از صحت عملکرد.

Questions:
1. (در طول مسیر ممکن است سوالات فنی جزئی پیش بیاید)

Confidence: 98%

Next Steps:
- [X] ایجاد ساختار پوشه جدید (`features/`, `middlewares/`)
- [X] انتقال میدل‌ورها (`AuthMiddleware`, `ErrorMiddleware`)
- [X] تغییر `main.py` برای استفاده از `RedisStorage` و روترهای جدید
- [X] حذف پوشه‌ها و فایل‌های قدیمی اولیه
- [X] انتقال هندلر `/start` به `features/common/`
- [ ] رفع خطای `ModuleNotFoundError` در `AuthMiddleware`
- [ ] انتقال ویژگی `wallet`
- [ ] انتقال ویژگی `buy`
- [ ] انتقال ویژگی `profile`
- [ ] انتقال ویژگی `my_accounts`
- [ ] انتقال ویژگی `admin`
- [ ] انتقال ویژگی `panel_management`
- [ ] بررسی و انتقال سایر کدهای مشترک یا باقی‌مانده
- [ ] تست نهایی و جامع ربات
- [ ] مستندسازی و ثبت تغییرات در CHANGELOG

Current Phase: PHASE-RefactorBot
Mode Context: Implementation Type (New Features) - ریفکتور ساختار ربات
Status: Active
Confidence: 98%
Last Updated: v0.3.0

Tasks:
[ID-RB01] ایجاد ساختار پوشه جدید و انتقال میدل‌ورها
Status: [X] Priority: [High]
Dependencies: None
Progress Notes:
- [v0.3.0] پوشه‌های features و middlewares ایجاد و میدل‌ورها منتقل شدند.

[ID-RB02] به‌روزرسانی `main.py` (RedisStorage, Routers)
Status: [X] Priority: [High]
Dependencies: [ID-RB01]
Progress Notes:
- [v0.3.0] main.py برای استفاده از RedisStorage و روترهای جدید ویژگی‌ها آپدیت شد.

[ID-RB03] حذف پوشه‌ها و فایل‌های قدیمی
Status: [X] Priority: [High]
Dependencies: [ID-RB02]
Progress Notes:
- [v0.3.0] پوشه‌های commands, callbacks, buttons و فایل states.py قدیمی حذف شدند.

[ID-RB04] انتقال ویژگی `common` (شامل `/start`)
Status: [X] Priority: [High]
Dependencies: [ID-RB03]
Progress Notes:
- [v0.3.0] هندلر و کیبورد /start به features/common منتقل شد.

[ID-RB05] رفع خطای `ModuleNotFoundError` در `AuthMiddleware`
Status: [X] Priority: [High]
Dependencies: [ID-RB01]
Progress Notes:
- [v0.3.0] لاگ‌ها بررسی شد، علت خطا (نام اشتباه فایل user_repo.py) مشخص شد. آماده اصلاح import.
- [v0.3.1] فایل `bot/middlewares/auth.py` با import صحیح `UserRepository` از `user_repo.py` اصلاح و ربات با موفقیت ری‌استارت شد.

[ID-RB06] انتقال ویژگی `wallet`
Status: [X] Priority: [High]
Dependencies: [ID-RB05]
Progress Notes:
- [v0.3.1] شروع انتقال فایل‌ها و منطق مربوط به کیف پول.
- [v0.3.1] بررسی ساختار انجام شد، کدها قبلاً منتقل شده بودند.
- [v0.3.1] رفع خطای `TypeError` در `AuthMiddleware` مربوط به `get_or_create_user`.
- [v0.3.1] رفع خطای `AttributeError` در `common/handlers.py` مربوط به `user.first_name`.
- [v0.3.1] تست ری‌استارت و اجرای دستور /start و /wallet موفق بود. انتقال wallet تکمیل شد.

[ID-RB07] انتقال ویژگی `buy`
Status: [ ] Priority: [Medium]
Dependencies: [ID-RB06]
Progress Notes:
- [ ] در انتظار تکمیل RB06.

[ID-RB08] انتقال ویژگی `profile`
Status: [ ] Priority: [Medium]
Dependencies: [ID-RB07]
Progress Notes:
- [ ] در انتظار تکمیل RB07.

[ID-RB09] انتقال ویژگی `my_accounts`
Status: [ ] Priority: [Medium]
Dependencies: [ID-RB08]
Progress Notes:
- [ ] در انتظار تکمیل RB08.

[ID-RB10] انتقال ویژگی `admin`
Status: [ ] Priority: [Medium]
Dependencies: [ID-RB09]
Progress Notes:
- [ ] در انتظار تکمیل RB09.

[ID-RB11] انتقال ویژگی `panel_management`
Status: [ ] Priority: [Medium]
Dependencies: [ID-RB10]
Progress Notes:
- [ ] در انتظار تکمیل RB10.

[ID-RB12] تست نهایی و مستندسازی
Status: [ ] Priority: [Low]
Dependencies: [ID-RB11]
Progress Notes:
- [ ] پس از اتمام تمام مراحل انتقال.

---
*قدیمی (مربوط به فازهای قبلی)*
# Mode: PLAN 🎯
Current Task: تکمیل فرایند خرید سرویس در ربات MoonVPN تا مرحله پرداخت (wallet/receipt) و ثبت کامل اکانت در جدول client_accounts با رابطه‌های صحیح (user, plan, panel, inbound و ...)، به همراه نمایش دکمه پرداخت بعد از انتخاب لوکیشن و تست end-to-end با پنل واقعی.
Understanding:
- بعد از انتخاب لوکیشن، باید دکمه‌های پرداخت (پرداخت با کیف پول، پرداخت با رسید) نمایش داده شود.
- با کلیک روی دکمه پرداخت، درخواست خرید به backend ارسال می‌شود و منطق خرید، پرداخت و ساخت اکانت اجرا می‌گردد.
- پس از پرداخت موفق، اکانت در پنل ساخته شده و اطلاعات کامل آن (user_id, plan_id, panel_id, inbound_id, uuid, config_url, qr_code_path و ...) در client_accounts ذخیره می‌شود.
- باید اطمینان حاصل شود که تمام رابطه‌ها و فیلدهای لازم به‌درستی مقداردهی و ذخیره شوند.
- پیام و QR Code به کاربر ارسال می‌شود.
- تست عملیاتی و بررسی دیتابیس برای صحت ثبت اطلاعات الزامی است.

Questions:
1. آیا نیاز به انتخاب نوع پرداخت (wallet/receipt) توسط کاربر هست یا فقط یکی کافی است؟
2. آیا بعد از پرداخت موفق، پیام و QR Code باید همزمان ارسال شود یا جداگانه؟
3. آیا نیاز به ثبت لاگ یا گزارش خاصی برای هر خرید وجود دارد؟

Confidence: 90%

Next Steps:
- [X] بررسی و اصلاح منطق ربات برای نمایش دکمه پرداخت بعد از انتخاب لوکیشن
- [X] پیاده‌سازی ارسال درخواست خرید به backend و دریافت نتیجه
- [X] اطمینان از ثبت کامل و صحیح اطلاعات اکانت و رابطه‌ها در client_accounts
- [X] تست end-to-end با پنل واقعی و بررسی دیتابیس
- [X] مستندسازی و ثبت تغییرات در CHANGELOG

Current Phase: PHASE-2
Mode Context: Implementation Type (New Features) - تکمیل فرایند خرید و ثبت اکانت واقعی
Status: Archived
Confidence: 100%
Last Updated: v0.2.2

Tasks:
[ID-008] اضافه کردن دکمه پرداخت (wallet/receipt) بعد از انتخاب لوکیشن در ربات - Status: [X]
[ID-009] ارسال درخواست خرید به backend و مدیریت پاسخ (ثبت سفارش، پرداخت، ساخت اکانت) - Status: [X]
[ID-010] اطمینان از ثبت صحیح اطلاعات و رابطه‌ها در client_accounts پس از ساخت اکانت - Status: [X]
[ID-011] تست end-to-end با پنل واقعی و بررسی دیتابیس - Status: [X]
[ID-012] مستندسازی و ثبت تغییرات در CHANGELOG - Status: [X]

# Mode: READY ✅
Current Task: ---
Status: Scratchpad cleaned and ready for new tasks.

Current Phase: PHASE-1
Mode Context: Implementation Type (New Features) - ذخیره و مدیریت QR Code تصویری برای کلاینت‌ها
Status: Archived
Confidence: 100%
Last Updated: v0.1.0

Tasks:
[ID-001] افزودن فیلد qr_code_path به مدل و اسکیما ClientAccount - Status: [X]
[ID-002] پیاده‌سازی ساخت و ذخیره QR Code تصویری هنگام ساخت/آپدیت کلاینت - Status: [X]
[ID-003] حذف خودکار QR قبلی هنگام تغییر uuid کلاینت - Status: [X]
[ID-004] نصب و اطمینان از وجود پکیج qrcode در محیط داکر و Poetry - Status: [X]
[ID-005] تست عملیاتی و بررسی لاگ‌ها برای اطمینان از عملکرد صحیح - Status: [X]
[ID-006] بهبود UX و مستندسازی نهایی (در صورت نیاز) - Status: [X]
[ID-007] تکمیل ساخت اکانت واقعی (ClientAccount) در پنل با py3xui و xui_client.py و ذخیره اطلاعات کامل کلاینت در دیتابیس - Status: [X]

# 📝 اسکرچ‌پد MoonVPN – وضعیت تا این لحظه (آرشیوشده)

## ۱. رفع خطاهای Enum و State (آرشیوشده)
...
## ۲. رفع خطای دیتابیس (Data truncated for column 'status') (آرشیوشده)
...
## ۳. وضعیت فعلی – مشکل دکمه لیست اینباند (آرشیوشده)
...
---

آخرین وضعیت: همه خطاهای دیتابیس و همگام‌سازی رفع شده و فقط مشکل UX/دکمه باقی مانده است. 🚀
