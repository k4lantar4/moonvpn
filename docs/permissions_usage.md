# راهنمای استفاده از سیستم مجوز ادمین‌ها در MoonVPN

این مستند نحوه استفاده از سرویس مجوز ادمین‌ها را برای توسعه‌دهندگان توضیح می‌دهد.

## معرفی
برای کنترل دسترسی ادمین‌ها به بخش‌های مختلف ربات و پنل، از کلاس `AdminPermissionService` استفاده کنید. این سرویس به شما اجازه می‌دهد به سادگی مجوزهای هر ادمین را بررسی یا تنظیم کنید.

---

## مثال کاربردی: چک مجوز قبل از انجام عملیات

```python
from core.services.admin_permission_service import AdminPermissionService

# فرض: user یک شیء مدل User است و session یک AsyncSession فعال
perm_service = AdminPermissionService(session)

# بررسی اینکه آیا ادمین مجوز تایید رسید دارد یا نه
if await perm_service.has_permission(user, "can_approve_receipt"):
    # عملیات تایید رسید
    ...
else:
    # نمایش پیام خطا
    ...
```

## لیست مجوزهای پیشنهادی
- can_approve_receipt: تایید رسید
- can_reject_receipt: رد رسید
- can_view_approved_receipts: مشاهده لیست رسیدهای تاییدشده
- can_view_rejected_receipts: مشاهده لیست رسیدهای ردشده
- can_view_all_receipts: مشاهده همه رسیدها

## نکات مهم
- سوپرادمین همیشه به همه مجوزها دسترسی دارد و نیازی به چک مجوز برای او نیست.
- برای افزودن مجوز جدید، کافیست آن را به مدل و سرویس اضافه کنید.
- پیام‌های خطا را به صورت کاربرپسند و فارسی نمایش دهید.

---

🌟 هر سوالی داشتی، با خیال راحت بپرس! موفق باشی 😊 