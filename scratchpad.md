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
- [ ] بررسی و اصلاح منطق ربات برای نمایش دکمه پرداخت بعد از انتخاب لوکیشن
- [ ] پیاده‌سازی ارسال درخواست خرید به backend و دریافت نتیجه
- [ ] اطمینان از ثبت کامل و صحیح اطلاعات اکانت و رابطه‌ها در client_accounts
- [ ] تست end-to-end با پنل واقعی و بررسی دیتابیس
- [ ] مستندسازی و ثبت تغییرات در CHANGELOG

Current Phase: PHASE-2
Mode Context: Implementation Type (New Features) - تکمیل فرایند خرید و ثبت اکانت واقعی
Status: Active
Confidence: 95%
Last Updated: v0.2.1

Tasks:
[ID-008] اضافه کردن دکمه پرداخت (wallet/receipt) بعد از انتخاب لوکیشن در ربات
Status: [X] Priority: [High]
Dependencies: None
Progress Notes:
- [v0.2.1] منطق نمایش دکمه پرداخت و جزئیات اکانت بعد از انتخاب پروتکل (inbound) پیاده‌سازی و تست اولیه انجام شد.

[ID-009] ارسال درخواست خرید به backend و مدیریت پاسخ (ثبت سفارش، پرداخت، ساخت اکانت)
Status: [-] Priority: [High]
Dependencies: [ID-008]
Progress Notes:
- [v0.2.1] سفارش بعد از انتخاب پروتکل ایجاد می‌شود و کاربر مستقیماً وارد مرحله پرداخت می‌شود. آماده تست ثبت صحیح اطلاعات و روابط در دیتابیس.

[ID-010] اطمینان از ثبت صحیح اطلاعات و رابطه‌ها در client_accounts پس از ساخت اکانت
Status: [X] Priority: [High]
Dependencies: [ID-009]
Progress Notes:
- [v0.2.1] در انتظار تست عملیاتی.
- [v0.2.2] فیلدهای `account_data` در متد `provision_account` با مدل `ClientAccount` هماهنگ شد.
- [v0.2.2] فیلدهای متد `renew_account` برای هماهنگی با مدل و سرویس `ClientService` اصلاح شد.
- [v0.2.2] فیلد `enable` در متد `deactivate_account` هنگام آپدیت دیتابیس هماهنگ شد.
- [v0.2.2] متد `delete_account` برای استفاده صحیح از سرویس `ClientService` و فیلد `remote_uuid` اصلاح شد.

[ID-011] تست end-to-end با پنل واقعی و بررسی دیتابیس
Status: [ ] Priority: [High]
Dependencies: [ID-010]
Progress Notes:
- [ ] در انتظار تست.

[ID-012] مستندسازی و ثبت تغییرات در CHANGELOG
Status: [ ] Priority: [Medium]
Dependencies: [ID-011]
Progress Notes:
- [ ] پس از اتمام پیاده‌سازی و تست.

# Mode: READY ✅
Current Task: ---
Status: Scratchpad cleaned and ready for new tasks.

Current Phase: PHASE-1
Mode Context: Implementation Type (New Features) - ذخیره و مدیریت QR Code تصویری برای کلاینت‌ها
Status: Active
Confidence: 100%
Last Updated: v0.1.0

Tasks:
[ID-001] افزودن فیلد qr_code_path به مدل و اسکیما ClientAccount
Status: [X] Priority: [High]
Dependencies: None
Progress Notes:
- [v0.1.0] فیلد qr_code_path به مدل و اسکیما اضافه شد و مستندسازی کامل انجام شد.

[ID-002] پیاده‌سازی ساخت و ذخیره QR Code تصویری هنگام ساخت/آپدیت کلاینت
Status: [X] Priority: [High]
Dependencies: [ID-001]
Progress Notes:
- [v0.1.0] منطق ساخت و ذخیره QR Code تصویری با استفاده از پکیج qrcode پیاده‌سازی شد.

[ID-003] حذف خودکار QR قبلی هنگام تغییر uuid کلاینت
Status: [X] Priority: [High]
Dependencies: [ID-002]
Progress Notes:
- [v0.1.0] متد حذف QR قبلی هنگام تغییر uuid اضافه شد و تست عملیاتی انجام شد.

[ID-004] نصب و اطمینان از وجود پکیج qrcode در محیط داکر و Poetry
Status: [X] Priority: [High]
Dependencies: [ID-002]
Progress Notes:
- [v0.1.0] poetry install و poetry lock داخل کانتینر app اجرا شد و مشکل ModuleNotFoundError رفع شد.

[ID-005] تست عملیاتی و بررسی لاگ‌ها برای اطمینان از عملکرد صحیح
Status: [-] Priority: [High]
Dependencies: [ID-004]
Progress Notes:
- [v0.1.0] سرویس بدون خطا اجرا شد و آماده تست عملیاتی QR Code است.

[ID-006] بهبود UX و مستندسازی نهایی (در صورت نیاز)
Status: [ ] Priority: [Medium]
Dependencies: [ID-005]
Progress Notes:
- [ ] در انتظار بازخورد و تست عملیاتی.

[ID-007] تکمیل ساخت اکانت واقعی (ClientAccount) در پنل با py3xui و xui_client.py و ذخیره اطلاعات کامل کلاینت در دیتابیس
Status: [-] Priority: [High]
Dependencies: [ID-002]
Progress Notes:
- [v1.0.0] شروع بررسی و اصلاح متدهای ساخت اکانت در AccountService/ClientService برای ارتباط کامل با پنل و ذخیره uuid و subscription_url و QR در دیتابیس. بررسی API پنل برای دریافت اطلاعات کلاینت.

# 📝 اسکرچ‌پد MoonVPN – وضعیت تا این لحظه

## ۱. رفع خطاهای Enum و State
- مقدار `INACTIVE` به Enum مربوط به `InboundStatus` در مدل و migrationها اضافه شد.
- مقدار `select_payment` به جای `payment` در State خرید (`BuyState`) قرار گرفت تا با کد هماهنگ باشد.
- migrationها اصلاح و اجرا شدند.
- سرویس با دستور `moonvpn restart` ریستارت شد.

## ۲. رفع خطای دیتابیس (Data truncated for column 'status')
- پس از migration، خطای Data truncated برای مقدار INACTIVE در ستون status جدول inbound ظاهر شد.
- علت: Enum جدول در دیتابیس MySQL هنوز مقدار INACTIVE را نداشت.
- راه‌حل: اجرای مستقیم دستور ALTER TABLE برای اصلاح Enum ستون status جدول inbound با:
  ```sql
  ALTER TABLE inbound MODIFY COLUMN status ENUM('ACTIVE','DISABLED','INACTIVE','DELETED') NOT NULL;
  ```
- پس از اجرای دستور و ریستارت مجدد، خطا به طور کامل رفع شد و همگام‌سازی اینباندها و پنل‌ها موفق بود.

## ۳. وضعیت فعلی – مشکل دکمه لیست اینباند
- همگام‌سازی و وضعیت دیتابیس اکنون سالم است.
- دکمه "لیست اینباند" در پنل ادمین هیچ پاسخی نمی‌دهد.
- بررسی کد نشان داد:
  - هیچ هندلری برای نمایش لیست اینباندهای یک پنل در panel_callbacks.py یا inbound_callbacks.py وجود ندارد.
  - فقط هندلر لیست کلاینت‌های یک اینباند (`inbound_clients:<panel_id>:<inbound_id>`) وجود دارد.
- راه‌حل پیشنهادی: ایجاد هندلر جدید برای لیست اینباندهای یک پنل و اتصال آن به دکمه مناسب.

---

## اقدامات بعدی (در انتظار تایید محمدرضا)
- دریافت callback_data دقیق دکمه لیست اینباند یا تایید برای پیاده‌سازی هندلر جدید.
- پیاده‌سازی کامل نمایش لیست اینباندها با دکمه‌های عملیاتی (در صورت نیاز).

---

آخرین وضعیت: همه خطاهای دیتابیس و همگام‌سازی رفع شده و فقط مشکل UX/دکمه باقی مانده است. 🚀
