# py3xui (XuiClient) API Method Reference for 3x-ui Panel

این مستند لیست کامل و دسته‌بندی‌شده‌ای از متدهای موجود در کتابخانه `py3xui` (و در نتیجه قابل استفاده در `XuiClient` پروژه MoonVPN) برای تعامل با API پنل 3x-ui ارائه می‌دهد.

**علائم:**
*   ✅: متد در `core/integrations/xui_client.py` پیاده‌سازی و استفاده شده است.
*   ❌: متد در `py3xui` وجود دارد اما در `core/integrations/xui_client.py` استفاده نشده است.

---

## Authentication

| نام متد       | عملکرد                       | Endpoint API | ورودی اصلی     | خروجی اصلی    | وضعیت پیاده‌سازی |
| :------------ | :--------------------------- | :----------- | :------------ | :------------ | :--------------- |
| `login()`     | احراز هویت و دریافت کوکی | `/login`     | Credentials | Session Token | ✅               |

---

## Inbound Management

| نام متد                                 | عملکرد                               | Endpoint API                       | ورودی اصلی           | خروجی اصلی         | وضعیت پیاده‌سازی |
| :-------------------------------------- | :----------------------------------- | :--------------------------------- | :------------------- | :----------------- | :--------------- |
| `inbound.get_list()`                    | دریافت لیست تمام Inbound ها         | `/panel/api/inbounds/list`         | -                    | `List[Inbound]`    | ✅               |
| `inbound.get_by_id(inbound_id)`         | دریافت اطلاعات یک Inbound با ID     | `/panel/api/inbounds/get/{id}`     | `inbound_id` (int)   | `Inbound`          | ✅               |
| `inbound.add(inbound)`                  | افزودن یک Inbound جدید              | `/panel/api/inbounds/add`          | `Inbound` object     | Result, Inbound    | ✅               |
| `inbound.update(inbound_id, inbound)`   | به‌روزرسانی یک Inbound موجود        | `/panel/api/inbounds/update/{id}`  | `id`, `Inbound` obj  | Result, Inbound    | ✅               |
| `inbound.delete(inbound_id)`            | حذف یک Inbound                      | `/panel/api/inbounds/del/{id}`     | `inbound_id` (int)   | Result             | ✅               |
| `inbound.add_client(inbound_id, client)`| افزودن کلاینت به Inbound (مستقیم) | `/panel/api/inbounds/addClient/`   | `id`, `Client` obj   | Result             | ❌               |
| `inbound.update_client(...)`            | به‌روزرسانی کلاینت در Inbound     | `/panel/api/inbounds/updateClient/{uuid}` | `id`, `uuid`, `Client` obj | Result | ❌               |
| `inbound.delete_client(...)`            | حذف کلاینت از Inbound              | `/panel/api/inbounds/delClient/{uuid}` | `id`, `uuid`         | Result             | ❌               |
| `inbound.reset_client_traffic(...)`     | ریست ترافیک کلاینت در Inbound    | `/panel/api/inbounds/{id}/resetClientTraffic/{uuid}` | `id`, `uuid`         | Result             | ❌               |

---

## Client Management

*توجه: برخی متدهای کلاینت ممکن است به صورت مستقیم یا از طریق Inbound مربوطه فراخوانی شوند. پیاده‌سازی فعلی در `XuiClient` از دسترسی مستقیم `api.client` استفاده می‌کند.*

| نام متد                        | عملکرد                           | Endpoint API                        | ورودی اصلی        | خروجی اصلی       | وضعیت پیاده‌سازی |
| :----------------------------- | :------------------------------- | :---------------------------------- | :---------------- | :--------------- | :--------------- |
| `client.add(inbound_id, clients)` | افزودن یک یا چند کلاینت به Inbound | `/panel/api/inbounds/addClient/`    | `id`, `List[Client]` | Result         | ✅               |
| `client.get_by_email(email)`   | دریافت کلاینت با ایمیل           | `/panel/api/clients/get/{email}`(?) | `email` (str)     | `Client`         | ✅               |
| `client.get(uuid)`             | دریافت کلاینت با UUID            | ?                                   | `uuid` (str)      | `Client`         | ✅               |
| `client.update(uuid, client)`  | به‌روزرسانی کلاینت با UUID       | `/panel/api/inbounds/updateClient/{uuid}` | `uuid`, `Client` obj | Result, Client | ✅               |
| `client.delete(uuid)`          | حذف کلاینت با UUID               | `/panel/api/inbounds/delClient/{uuid}` | `uuid` (str)      | Result           | ✅               |
| `client.reset_traffic(uuid)`   | ریست ترافیک کلاینت با UUID       | `/panel/api/inbounds/resetClientTraffic/{uuid}`(?) | `uuid` (str) | Result           | ✅               |
| `client.get_traffic(uuid)`     | دریافت اطلاعات ترافیک کلاینت   | ?                                   | `uuid` (str)      | Traffic Info   | ✅               |

---

## Server Management

| نام متد                 | عملکرد                     | Endpoint API               | ورودی اصلی | خروجی اصلی   | وضعیت پیاده‌سازی |
| :---------------------- | :------------------------- | :------------------------- | :--------- | :----------- | :--------------- |
| `server.get_status()`   | دریافت وضعیت سرور        | `/server/status`           | -          | ServerStatus | ✅               |
| `server.get_config()`   | دریافت تنظیمات سرور      | `/server/config`           | -          | Dict         | ❌               |
| `server.get_xray_version()` | دریافت نسخه Xray          | `/server/version`          | -          | Dict         | ❌               |
| `server.restart_xray()` | ری‌استارت سرویس Xray     | `/server/restartXrayService` | -          | Result       | ✅               |
| `server.stop_xray()`    | توقف سرویس Xray          | `/server/stopXrayService`  | -          | Result       | ❌               |
| `server.get_xray_logs()`| دریافت لاگ‌های Xray       | `/server/logs`             | -          | Dict         | ❌               |
| `server.restart_panel()`| ری‌استارت پنل 3x-ui       | `/server/restartPanel`     | -          | Result       | ❌               |

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