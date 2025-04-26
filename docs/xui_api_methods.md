# py3xui (XuiClient) API Method Reference for 3x-ui Panel

این مستند لیست کامل و دسته‌بندی‌شده‌ای از متدهای موجود در کلاس `XuiClient` پروژه MoonVPN برای تعامل با API پنل 3x-ui ارائه می‌دهد. این متدها معمولا متناظر با متدهای کتابخانه `py3xui` هستند.

**علائم:**
*   ✅: متد در `core/integrations/xui_client.py` پیاده‌سازی شده است.
*   🔄: متد در `py3xui` وجود دارد اما پیاده‌سازی آن در `XuiClient` نیاز به بررسی بیشتر یا اصلاح دارد (مثلا نوع ورودی/خروجی).
*   ❌: متد در `py3xui` وجود دارد (یا انتظار می‌رود وجود داشته باشد) اما در `XuiClient` پیاده‌سازی نشده است.

---

## Authentication & Status

| نام متد (`XuiClient`) | نام متد (`py3xui`)   | عملکرد                               | Endpoint API | ورودی اصلی     | خروجی اصلی    | وضعیت پیاده‌سازی |
| :-------------------- | :------------------- | :----------------------------------- | :----------- | :------------ | :------------ | :--------------- |
| `login()`             | `login()`            | احراز هویت و دریافت کوکی/session     | `/login`     | Credentials | `bool`        | ✅               |
| `get_status()`        | `login()` (indirect) | بررسی وضعیت اتصال با تلاش مجدد لاگین | `/login`     | -           | `bool`        | ✅               |
| `logout()`            | `logout()` (?)       | خروج از پنل (در صورت پشتیبانی)      | (?)          | -           | `bool`        | ✅ (فقط هشدار) |
| `verify_connection()` | `inbound.get_list()` (indirect) | تایید اتصال با دریافت لیست inboundها | `/panel/api/inbounds/list` | - | `bool` | ✅               |

---

## Inbound Management

| نام متد (`XuiClient`)            | نام متد (`py3xui`)   | عملکرد                                    | Endpoint API                       | ورودی اصلی           | خروجی اصلی         | وضعیت پیاده‌سازی |
| :------------------------------- | :------------------- | :---------------------------------------- | :--------------------------------- | :------------------- | :----------------- | :--------------- |
| `get_inbounds()`                 | `inbound.get_list()` | دریافت لیست تمام Inbound ها              | `/panel/api/inbounds/list`         | -                    | `List[Dict]`    | ✅               |
| `sync_inbounds()`                | `inbound.get_list()` (indirect) | همگام‌سازی (دریافت) لیست inboundها   | `/panel/api/inbounds/list`         | -                    | `List[Dict]`    | ✅               |
| `get_inbound_by_id(id)`          | `inbound.get_by_id()`| دریافت اطلاعات یک Inbound با ID          | `/panel/api/inbounds/get/{id}`     | `inbound_id` (int)   | `Dict` / `None`  | ✅               |
| `add_inbound(data)`              | `inbound.add()`      | افزودن یک Inbound جدید                   | `/panel/api/inbounds/add`          | `Dict` (inbound data)| `Dict` / `None`  | ✅ (نیاز به تست نوع ورودی) |
| `update_inbound(id, data)`       | `inbound.update()`   | به‌روزرسانی یک Inbound موجود             | `/panel/api/inbounds/update/{id}`  | `id`, `Dict` (data)  | `Dict` / `None`  | ✅ (نیاز به تست نوع ورودی) |
| `delete_inbound(id)`             | `inbound.delete()`   | حذف یک Inbound                           | `/panel/api/inbounds/del/{id}`     | `inbound_id` (int)   | `bool`           | ✅               |
| `reset_all_inbound_stats()`      | `inbound.reset_stats()`| ریست آمار ترافیک تمام inboundها         | `/panel/api/inbounds/resetAllStats`(?) | -                   | `bool`           | ✅               |
| `reset_inbound_client_stats(id)` | `inbound.reset_client_stats()` | ریست آمار کلاینت‌های یک inbound خاص | `/panel/api/inbounds/{id}/resetAllClientTraffics`(?) | `inbound_id` (int) | `bool`           | ✅               |

---

## Client Management

| نام متد (`XuiClient`)            | نام متد (`py3xui`)   | عملکرد                            | Endpoint API                        | ورودی اصلی            | خروجی اصلی          | وضعیت پیاده‌سازی |
| :------------------------------- | :------------------- | :-------------------------------- | :---------------------------------- | :-------------------- | :------------------ | :--------------- |
| `get_all_clients()`              | `client.get_list()`  | دریافت لیست تمام کلاینت‌ها         | (از `inbounds/list` استفاده می‌کند؟) | -                     | `List[Dict]`     | ✅               |
| `create_client(id, data)`        | `client.create()`    | افزودن کلاینت به Inbound مشخص    | `/panel/api/inbounds/addClient` (?) | `id`, `Dict` (data)   | `Dict` / `None`   | ✅ (نیاز به تست نوع ورودی) |
| `get_client_by_email(email)`   | `client.get_by_email()`| دریافت کلاینت با ایمیل            | (فیلتر داخلی؟)                     | `email` (str)         | `Dict` / `None`   | ✅               |
| `get_client_by_uuid(uuid)`     | `client.get()`       | دریافت کلاینت با UUID             | (فیلتر داخلی؟)                     | `uuid` (str)          | `Dict` / `None`   | ✅               |
| `update_client(uuid, data)`      | `client.update()`    | به‌روزرسانی کلاینت با UUID        | `/panel/api/inbounds/updateClient/{uuid}` (?) | `uuid`, `Dict` (data) | `Dict` / `None`   | ✅ (نیاز به تست نوع ورودی) |
| `delete_client(uuid)`            | `client.delete()`    | حذف کلاینت با UUID                | `/panel/api/inbounds/delClient/{uuid}` (?) | `uuid` (str)          | `bool`            | ✅               |
| `reset_client_traffic(uuid)`   | `client.reset_traffic()`| ریست ترافیک کلاینت با UUID       | `/panel/api/inbounds/resetClientTraffic/{uuid}`(?) | `uuid` (str)          | `bool`            | ✅               |
| `get_client_traffic(uuid)`     | `client.get_traffic()`?| دریافت اطلاعات ترافیک کلاینت    | (فیلتر داخلی؟)                     | `uuid` (str)          | `Dict` / `None`   | ✅               |
| `get_config(uuid)`             | (ترکیبی)             | دریافت/ساخت کانفیگ (لینک) کلاینت | (ترکیبی)                           | `uuid` (str)          | `str` (config link)| ✅               |

---

## Server & Core Management

| نام متد (`XuiClient`)       | نام متد (`py3xui`)   | عملکرد                     | Endpoint API                 | ورودی اصلی | خروجی اصلی      | وضعیت پیاده‌سازی |
| :------------------------- | :------------------- | :------------------------- | :--------------------------- | :--------- | :-------------- | :--------------- |
| `get_server_status()`      | `server.get_status()`| دریافت وضعیت لحظه‌ای سرور  | `/server/status`             | -          | `Dict` / `None` | ✅               |
| `restart_core()`           | `restart_core()` or `server.restart_core()` | ری‌استارت سرویس Xray/Core | `/server/restartXrayService` (?) | -          | `bool`          | ✅               |
| `server.get_config()`      | `server.get_config()`? | دریافت تنظیمات سرور       | `/server/config` (?)         | -          | Dict            | ❌               |
| `server.get_xray_version()`| `server.get_version()`?| دریافت نسخه Xray           | `/server/version` (?)        | -          | Dict            | ❌               |
| `server.stop_xray()`       | `server.stop_core()`?  | توقف سرویس Xray           | `/server/stopXrayService` (?) | -          | Result          | ❌               |
| `server.get_xray_logs()`   | `server.get_logs()`?   | دریافت لاگ‌های Xray        | `/server/logs` (?)           | -          | Dict            | ❌               |
| `server.restart_panel()`   | `server.restart_panel()`?| ری‌استارت پنل 3x-ui       | `/server/restartPanel` (?)   | -          | Result          | ❌               |

---

## Settings Management (Not Implemented in XuiClient)

| نام متد (`py3xui`)          | عملکرد                     | Endpoint API             | ورودی اصلی | خروجی اصلی | وضعیت پیاده‌سازی |
| :------------------------- | :------------------------- | :----------------------- | :--------- | :--------- | :--------------- |
| `settings.get_all()`     | دریافت تمام تنظیمات پنل | `/panel/api/settings/all`  | -          | Settings   | ❌               |
| `settings.update(settings)`| به‌روزرسانی تنظیمات پنل | `/panel/api/settings/update` | Settings   | Result     | ❌               |

---

## Database Management

| نام متد (`XuiClient`)         | نام متد (`py3xui`)   | عملکرد                     | Endpoint API         | ورودی اصلی      | خروجی اصلی | وضعیت پیاده‌سازی |
| :--------------------------- | :------------------- | :------------------------- | :------------------- | :--------------- | :--------- | :--------------- |
| `download_db_backup(path)` | `server.get_db()`    | دانلود فایل بکاپ دیتابیس | `/server/db`         | `save_path` (str)| `bool`     | ✅               |
| `export_database()`        | `database.export()`  | ایجاد و ارسال بکاپ (تلگرام)| `/panel/api/database/export` (?) | -            | `bool`     | ✅               |
| `database.restore(path)`   | `database.import_db()`?| بازیابی دیتابیس از بکاپ   | `/server/restoreDB` (?) | `file_path`  | Result     | ❌               |

---
