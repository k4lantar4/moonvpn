# py3xui (XuiClient) API Method Reference for 3x-ui Panel

این مستند لیست کامل و دسته‌بندی‌شده‌ای از متدهای موجود در کتابخانه `py3xui` (و در نتیجه قابل استفاده در `XuiClient` پروژه MoonVPN) برای تعامل با API پنل 3x-ui ارائه می‌دهد.

**علائم:**
*   ✅: متد در `core/integrations/xui_client.py` پیاده‌سازی و استفاده شده است.
*   ❌: متد در `py3xui` وجود دارد (یا انتظار می‌رود وجود داشته باشد) اما در `core/integrations/xui_client.py` مستقیماً استفاده نشده است.

---

## Authentication

| نام متد       | عملکرد                       | Endpoint API | ورودی اصلی     | خروجی اصلی    | وضعیت پیاده‌سازی |
| :------------ | :--------------------------- | :----------- | :------------ | :------------ | :--------------- |
| `login()`     | احراز هویت و دریافت کوکی | `/login`     | Credentials | `bool`, Session Token | ✅               |

---

## Inbound Management

| نام متد                                 | عملکرد                               | Endpoint API                       | ورودی اصلی           | خروجی اصلی         | وضعیت پیاده‌سازی |
| :-------------------------------------- | :----------------------------------- | :--------------------------------- | :------------------- | :----------------- | :--------------- |
| `inbound.get_list()`                    | دریافت لیست تمام Inbound ها         | `/panel/api/inbounds/list`         | -                    | `List[Dict]`    | ✅               |
| `inbound.get(inbound_id)`               | دریافت اطلاعات یک Inbound با ID     | `/panel/api/inbounds/get/{id}`     | `inbound_id` (int)   | `Dict` / `None`  | ✅               |
| `inbound.create(inbound_data)`          | افزودن یک Inbound جدید              | `/panel/api/inbounds/add`          | `Dict` (inbound data)| `Dict` (result)  | ✅               |
| `inbound.update(inbound_id, inbound_data)`| به‌روزرسانی یک Inbound موجود        | `/panel/api/inbounds/update/{id}`  | `id`, `Dict` (data)  | `Dict` (result)  | ✅               |
| `inbound.delete(inbound_id)`            | حذف یک Inbound                      | `/panel/api/inbounds/del/{id}`     | `inbound_id` (int)   | `bool` (result)  | ✅               |
| `inbound.add_client(...)`               | افزودن کلاینت به Inbound (مستقیم) | `/panel/api/inbounds/addClient/`   | `id`, `Client` obj   | Result             | ❌ (از `client.create` استفاده می‌شود) |
| `inbound.update_client(...)`            | به‌روزرسانی کلاینت در Inbound     | `/panel/api/inbounds/updateClient/{uuid}`(?) | `id`, `uuid`, `Client` obj | Result | ❌ (از `client.update` استفاده می‌شود) |
| `inbound.delete_client(...)`            | حذف کلاینت از Inbound              | `/panel/api/inbounds/delClient/{uuid}`(?) | `id`, `uuid`         | Result             | ❌ (از `client.delete` استفاده می‌شود) |
| `inbound.reset_client_traffic(...)`     | ریست ترافیک کلاینت در Inbound    | `/panel/api/inbounds/{id}/resetClientTraffic/{uuid}`(?) | `id`, `uuid`         | Result             | ❌ (از `client.reset_traffic` استفاده می‌شود) |

---

## Client Management

*توجه: پیاده‌سازی فعلی در `XuiClient` از دسترسی مستقیم `api.client` استفاده می‌کند.*

| نام متد                        | عملکرد                           | Endpoint API                        | ورودی اصلی            | خروجی اصلی          | وضعیت پیاده‌سازی |
| :----------------------------- | :------------------------------- | :---------------------------------- | :-------------------- | :------------------ | :--------------- |
| `client.create(inbound_id, client_data)` | افزودن کلاینت به Inbound مشخص   | `/panel/api/inbounds/addClient` (?) | `id`, `Dict` (data)   | `Dict` (result)   | ✅               |
| `client.get_by_email(email)`   | دریافت کلاینت با ایمیل           | (احتمالا از /list و فیلتر داخلی استفاده می‌کند) | `email` (str)     | `Dict` / `None`   | ✅               |
| `client.get(uuid)`             | دریافت کلاینت با UUID            | (احتمالا از /list و فیلتر داخلی استفاده می‌کند) | `uuid` (str)      | `Dict` / `None`   | ✅               |
| `client.update(uuid, client_data)`  | به‌روزرسانی کلاینت با UUID       | `/panel/api/inbounds/updateClient/{uuid}` (?) | `uuid`, `Dict` (data) | `Dict` (result)   | ✅               |
| `client.delete(uuid)`          | حذف کلاینت با UUID               | `/panel/api/inbounds/delClient/{uuid}` (?) | `uuid` (str)      | `bool` (result)   | ✅               |
| `client.reset_traffic(uuid)`   | ریست ترافیک کلاینت با UUID       | `/panel/api/inbounds/resetClientTraffic/{uuid}`(?) | `uuid` (str)      | `bool` (result)   | ✅               |
| `client.get_traffic(uuid)`     | دریافت اطلاعات ترافیک کلاینت   | (احتمالا از /list و فیلتر داخلی استفاده می‌کند) | `uuid` (str)      | `Dict`            | ✅               |
| `client.get_config(uuid)`      | دریافت کانفیگ (لینک) کلاینت    | (احتمالا از /list و فیلتر داخلی استفاده می‌کند) | `uuid` (str)      | `str` (config link)| ✅               |

---

## Server Management

| نام متد                 | عملکرد                     | Endpoint API               | ورودی اصلی | خروجی اصلی      | وضعیت پیاده‌سازی |
| :---------------------- | :------------------------- | :------------------------- | :--------- | :-------------- | :--------------- |
| `server.stats()`        | دریافت آمار کلی سرور     | `/server/status` (?)       | -          | `Dict` / `None` | ✅               |
| `server.restart_xray()` | ری‌استارت سرویس Xray     | `/server/restartXrayService` | -          | `bool` (result) | ✅               |
| `server.get_status()`   | دریافت وضعیت سرور (قدیمی؟)| `/server/status`           | -          | ServerStatus    | ❌               |
| `server.get_config()`   | دریافت تنظیمات سرور      | `/server/config`           | -          | Dict            | ❌               |
| `server.get_xray_version()` | دریافت نسخه Xray          | `/server/version`          | -          | Dict            | ❌               |
| `server.stop_xray()`    | توقف سرویس Xray          | `/server/stopXrayService`  | -          | Result          | ❌               |
| `server.get_xray_logs()`| دریافت لاگ‌های Xray       | `/server/logs`             | -          | Dict            | ❌               |
| `server.restart_panel()`| ری‌استارت پنل 3x-ui       | `/server/restartPanel`     | -          | Result          | ❌               |

---

## Settings Management

| نام متد               | عملکرد                     | Endpoint API             | ورودی اصلی | خروجی اصلی | وضعیت پیاده‌سازی |
| :-------------------- | :------------------------- | :----------------------- | :--------- | :--------- | :--------------- |
| `settings.get_all()`  | دریافت تمام تنظیمات پنل | `/panel/api/settings/all`  | -          | Settings   | ❌               |
| `settings.update(settings)` | به‌روزرسانی تنظیمات پنل | `/panel/api/settings/update` | Settings   | Result     | ❌               |

---

## Database Management

| نام متد                   | عملکرد                   | Endpoint API       | ورودی اصلی | خروجی اصلی | وضعیت پیاده‌سازی |
| :------------------------ | :----------------------- | :----------------- | :--------- | :--------- | :--------------- |
| `database.backup()`       | ایجاد بکاپ از دیتابیس  | `/server/backupDB` | -          | Result     | ❌               |
| `database.restore(path)` | بازیابی دیتابیس از بکاپ | `/server/restoreDB`| `file_path`| Result     | ❌               |

---
