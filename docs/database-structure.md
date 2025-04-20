# 🗃️ Database Structure (MoonVPN)

> طراحی پایگاه داده برای مدیریت کاربران، پنل‌ها، سفارشات، اکانت‌ها، تخفیف‌ها و تراکنش‌ها با قابلیت توسعه‌پذیری بالا و عملکرد بهینه در پروژه MoonVPN.

---

## ✅ جداول اصلی

### 1. `users`
| Field         | Type         | Description                       |
|---------------|--------------|-----------------------------------|
| id            | BIGINT (PK)  | شناسه یکتا                       |
| telegram_id   | BIGINT       | آیدی تلگرام کاربر                |
| username      | VARCHAR      | نام کاربری (اختیاری)            |
| role          | ENUM         | user / admin / reseller          |
| balance       | DECIMAL      | موجودی کیف پول                  |
| created_at    | DATETIME     | زمان ثبت‌نام                     |
| status        | BOOLEAN      | فعال / غیرفعال                  |

---

### 2. `panels`
| Field       | Type         | Description                       |
|-------------|--------------|-----------------------------------|
| id          | INT (PK)     | شناسه یکتا پنل                   |
| name        | VARCHAR      | نام اختیاری یا پیش‌فرض           |
| location    | VARCHAR      | کشور یا لوکیشن (مثلاً France)   |
| flag_emoji  | VARCHAR(5)   | ایموجی پرچم                      |
| url         | TEXT         | آدرس پنل                         |
| username    | VARCHAR      | یوزرنیم پنل                      |
| password    | VARCHAR      | پسورد پنل                        |
| status      | BOOLEAN      | وضعیت فعال یا غیرفعال            |
| default_label | VARCHAR    | پیشوند نام اکانت دیفالت         |

---

### 3. `inbounds`
| Field       | Type         | Description                       |
|-------------|--------------|-----------------------------------|
| id          | INT (PK)     | شناسه یکتا inbound               |
| panel_id    | INT (FK)     | مرجع به جدول panels              |
| inbound_id  | INT          | آیدی inbound روی پنل             |
| protocol    | VARCHAR      | vmess, vless, trojan              |
| tag         | VARCHAR      | تگ اختصاصی                      |
| client_limit| INT          | حداکثر کلاینت مجاز              |
| traffic_limit | INT        | محدودیت ترافیک کلی (GB)         |

---

### 4. `client_accounts`
| Field         | Type         | Description                           |
|---------------|--------------|---------------------------------------|
| id            | INT (PK)     | شناسه یکتا                            |
| user_id       | BIGINT (FK)  | مرجع به جدول users                   |
| panel_id      | INT (FK)     | مرجع به جدول panels                  |
| inbound_id    | INT (FK)     | مرجع به inbounds                     |
| uuid          | UUID         | UUID ایجاد شده توسط پنل             |
| label         | VARCHAR      | نام نمایشی/ایمیل در پنل              |
| transfer_id   | VARCHAR      | شناسه ثابت تغییر لوکیشن             |
| transfer_count| INT          | شمارنده تغییر لوکیشن                |
| expires_at    | DATETIME     | تاریخ انقضا                          |
| traffic_total | INT          | حجم کل اختصاص داده شده (GB)         |
| traffic_used  | INT          | حجم مصرف‌شده                         |
| status        | ENUM         | active / expired / disabled          |
| config_url    | TEXT         | لینک کانفیگ نهایی                    |

---

### 5. `plans`
| Field         | Type         | Description                     |
|---------------|--------------|---------------------------------|
| id            | INT (PK)     | شناسه پلن                      |
| name          | VARCHAR      | نام پلن                        |
| traffic       | INT          | حجم GB                         |
| duration_days | INT          | مدت اعتبار                     |
| price         | DECIMAL      | قیمت                           |
| available_locations | JSON   | لیست لوکیشن‌های مجاز          |
| is_trial      | BOOLEAN      | تست رایگان هست یا نه          |

---

### 6. `orders`
| Field         | Type         | Description                             |
|---------------|--------------|-----------------------------------------|
| id            | INT (PK)     | شناسه سفارش                            |
| user_id       | BIGINT (FK)  | خریدار                                 |
| plan_id       | INT (FK)     | پلن انتخاب شده                        |
| amount        | DECIMAL      | مبلغ کل                                |
| discount_code_id | INT (FK)  | کد تخفیف اعمال‌شده (در صورت وجود)     |
| status        | ENUM         | pending / paid / processing / done     |
| created_at    | DATETIME     | تاریخ ایجاد سفارش                      |
| processed_at  | DATETIME     | زمان تحویل کانفیگ                      |

---

### 7. `transactions`
| Field       | Type         | Description                     |
|-------------|--------------|---------------------------------|
| id          | INT (PK)     | شناسه تراکنش                   |
| user_id     | BIGINT (FK)  | کاربر مربوطه                   |
| order_id    | INT (FK)     | مرجع سفارش (در صورت وجود)     |
| amount      | DECIMAL      | مبلغ تراکنش                    |
| type        | ENUM         | deposit / purchase / refund     |
| status      | ENUM         | pending / success / failed      |
| created_at  | DATETIME     | تاریخ تراکنش                   |

---

### 8. `discount_codes`
| Field         | Type         | Description                             |
|---------------|--------------|-----------------------------------------|
| id            | INT (PK)     | شناسه کد                               |
| code          | VARCHAR      | کد یکتا                                |
| type          | ENUM         | percent / fixed                        |
| value         | DECIMAL      | درصد یا مبلغ تخفیف                    |
| start_date    | DATETIME     | شروع اعتبار                           |
| end_date      | DATETIME     | پایان اعتبار                          |
| usage_limit   | INT          | سقف تعداد استفاده                     |
| used_count    | INT          | دفعات استفاده شده                     |
| active        | BOOLEAN      | وضعیت کد                              |
| max_discount  | DECIMAL      | سقف تخفیف (برای درصدی‌ها)            |
| min_order     | DECIMAL      | حداقل مبلغ سفارش برای اعمال تخفیف    |

---

### 9. `test_account_log`
| Field         | Type         | Description                     |
|---------------|--------------|---------------------------------|
| id            | INT (PK)     | شناسه یکتا                     |
| user_id       | BIGINT (FK)  | کاربر دریافت‌کننده تست       |
| plan_id       | INT (FK)     | پلن تستی دریافت‌شده          |
| created_at    | DATETIME     | زمان دریافت                    |

---

### 10. `account_transfer`
| Field            | Type         | Description                      |
|------------------|--------------|----------------------------------|
| id               | INT (PK)     | شناسه انتقال                    |
| old_account_id   | INT (FK)     | شناسه اکانت مبدا                |
| new_account_id   | INT (FK)     | شناسه اکانت جدید (مقصد)         |
| from_panel_id    | INT (FK)     | پنل مبدا                         |
| to_panel_id      | INT (FK)     | پنل مقصد                         |
| created_at       | DATETIME     | زمان انتقال                      |

---

## 🔗 روابط مهم بین جداول

- `users` 1:N `client_accounts`
- `users` 1:N `orders`, `transactions`, `test_account_log`
- `orders` 1:1 `transactions`
- `orders` N:1 `plans`
- `orders` N:1 `discount_codes`
- `client_accounts` N:1 `panels`, `inbounds`, `users`
- `panels` 1:N `inbounds`

---

✅ این طراحی به صورت ساده، آینده‌پذیر و کاملاً منطبق با نیازهای پروژه MoonVPN پیاده‌سازی شده و قابلیت توسعه سریع دارد.

