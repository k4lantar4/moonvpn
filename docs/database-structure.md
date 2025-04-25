# 🧩 Database Structure (MoonVPN)

## ✅ Tables Overview

### `users`
- `telegram_id` (unique)
- `username`, `full_name`
- `role`: USER / ADMIN / SELLER
- `status`: ACTIVE / BLOCKED
- `balance`: Decimal (تراکنش‌محور)
- `settings`: JSON

### `panels`
- `name`, `location_name`, `url`
- `username`, `password`
- `type`: XUI
- `status`: ACTIVE / DISABLED / DELETED

### `inbound`
- `panel_id` (FK)
- `port`, `protocol`, `tag`
- `listen`, `stream_settings`: JSON
- `allocate_settings`, `security_settings`: JSON
- `receive_original_dest`, `allow_transparent`: bool
- `sniffing_settings`: JSON
- `remark`: string

### `plans`
- `name`, `traffic_gb`, `duration_days`, `price`
- `status`: ACTIVE / INACTIVE
- `available_locations`: JSON
- `created_by_id`: FK to users
- `created_at`: datetime

### `orders`
- `user_id`, `plan_id`, `amount`, `final_amount`
- `location_name`, `receipt_required`
- `status`: PENDING / PAID / COMPLETED / FAILED / EXPIRED
- `discount_code_id`, `client_account_id`

### `transactions`
- `user_id`, `related_order_id`
- `amount`, `type`: DEPOSIT / PURCHASE / REFUND
- `status`: PENDING / SUCCESS / FAILED
- `tracking_code`, `gateway`, `reference`

### `client_accounts`
- `user_id`, `panel_id`, `inbound_id`, `plan_id`, `order_id`
- `remote_uuid`, `client_name`, `email_name`
- `traffic_limit`, `traffic_used`
- `status`: ACTIVE / DISABLED / EXPIRED / SWITCHED
- `config_url`, `qr_code_path`

### `bank_cards`
- `card_number`, `holder_name`, `bank_name`
- `rotation_policy`: MANUAL / INTERVAL / LOAD_BALANCE
- `rotation_interval_minutes`, `telegram_channel_id`

### `receipt_log`
- `amount`, `photo_file_id`, `text_reference`, `status`
- `auto_detected_amount`, `auto_validated`, `submitted_at`
- `card_id`, `admin_id`, `transaction_id`

### `test_account_log`
- `user_id`, `plan_id`, `created_at`

---

## 🧠 Notes
- تمام تراکنش‌ها در جدول `transactions` ثبت شده و وضعیت مالی کاربران از آن استخراج می‌شود.
- جدول `client_accounts` اطلاعات نهایی اکانت‌های ساخته‌شده در پنل را نگه می‌دارد.
- جدول `inbound` اکنون با پشتیبانی کامل از streamSettings و allocate و ... تعریف شده.
