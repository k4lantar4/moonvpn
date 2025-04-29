# مستندات کامل متدهای async_api کتابخانه py3xui (سازگار با XuiClient)

این فایل تمام متدهای مهم و قابل استفاده برای ارتباط با پنل XUI را با دسته‌بندی و توضیح کامل (ورودی/خروجی/مثال) ارائه می‌دهد.

---

## احراز هویت و وضعیت (Authentication & Status)

| نام متد | مسیر | ورودی | خروجی | توضیح | مثال |
|---------|------|-------|--------|-------|------|
| login | async_api/async_api.py | host, username, password, token | bool/dict | ورود و دریافت session | await api.login() |
| logout | (در صورت وجود) | - | bool | خروج از پنل | await api.logout() |
| get_status | async_api/async_api_server.py | - | dict | وضعیت سرور (CPU, RAM, ...) | await api.server.get_status() |
| verify_connection | (ترکیبی) | - | bool | تست اتصال با دریافت inbounds | await api.inbound.get_list() |

---

## مدیریت اینباند (Inbound Management)

| نام متد | مسیر | ورودی | خروجی | توضیح | مثال |
|---------|------|-------|--------|-------|------|
| get_list | async_api/async_api_inbound.py | - | list[Inbound] | لیست همه اینباندها | await api.inbound.get_list() |
| get_by_id | async_api/async_api_inbound.py | inbound_id | Inbound | دریافت یک اینباند خاص | await api.inbound.get_by_id(1) |
| add | async_api/async_api_inbound.py | Inbound | None | افزودن اینباند جدید | await api.inbound.add(inbound) |
| update | async_api/async_api_inbound.py | inbound_id, Inbound | None | به‌روزرسانی اینباند | await api.inbound.update(id, inbound) |
| delete | async_api/async_api_inbound.py | inbound_id | None | حذف اینباند | await api.inbound.delete(id) |
| reset_stats | async_api/async_api_inbound.py | - | None | ریست آمار همه اینباندها | await api.inbound.reset_stats() |
| reset_client_stats | async_api/async_api_inbound.py | inbound_id | None | ریست آمار کلاینت‌های یک اینباند | await api.inbound.reset_client_stats(id) |

---

## مدیریت کلاینت (Client Management)

| نام متد | مسیر | ورودی | خروجی | توضیح | مثال |
|---------|------|-------|--------|-------|------|
| get_list | async_api/async_api_client.py | - | list[Client] | لیست همه کلاینت‌ها | await api.client.get_list() |
| get_by_email | async_api/async_api_client.py | email | Client | دریافت کلاینت با ایمیل | await api.client.get_by_email(email) |
| get | async_api/async_api_client.py | uuid | Client | دریافت کلاینت با UUID | await api.client.get(uuid) |
| add | async_api/async_api_client.py | inbound_id, Client | None | افزودن کلاینت به اینباند | await api.client.add(inbound_id, client) |
| update | async_api/async_api_client.py | uuid, Client | None | به‌روزرسانی کلاینت | await api.client.update(uuid, client) |
| delete | async_api/async_api_client.py | uuid | None | حذف کلاینت | await api.client.delete(uuid) |
| reset_traffic | async_api/async_api_client.py | uuid | None | ریست ترافیک کلاینت | await api.client.reset_traffic(uuid) |
| get_traffic | async_api/async_api_client.py | uuid | dict | دریافت ترافیک کلاینت | await api.client.get_traffic(uuid) |

---

## مدیریت سرور و دیتابیس (Server & Database Management)

| نام متد | مسیر | ورودی | خروجی | توضیح | مثال |
|---------|------|-------|--------|-------|------|
| get_status | async_api/async_api_server.py | - | dict | وضعیت سرور | await api.server.get_status() |
| get_db | async_api/async_api_server.py | save_path | None | دانلود بکاپ دیتابیس | await api.server.get_db('db_backup.db') |
| export | async_api/async_api_database.py | - | None | ایجاد و ارسال بکاپ (تلگرام) | await api.database.export() |
| restart_core | async_api/async_api_server.py | - | None | ری‌استارت هسته Xray | await api.server.restart_core() |

---

## نکات مهم
- ورودی/خروجی دقیق هر متد ممکن است بسته به نسخه py3xui تغییر کند.
- برای استفاده از مدل‌های داده (Inbound, Client) باید از py3xui.models استفاده شود.
- مثال‌ها بر اساس مستندات رسمی و کد پروژه نوشته شده‌اند.

---

منبع: [py3xui async_api](https://github.com/iwatkot/py3xui/tree/main/py3xui/async_api)
