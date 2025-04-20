# 🧬 MoonVPN - Database Structure

> Updated: 2025-04-21  
> Reflecting latest architecture including inbounds, panel sync, and full card-to-card payment logic.

---

## 📦 Overview
این مستند ساختار پایگاه داده پروژه MoonVPN را به شکلی واضح و قابل توسعه شرح می‌دهد. طراحی به‌گونه‌ای انجام شده که پشتیبانی از چندین پنل، چندین اینباند، اکانت تست، تغییر لوکیشن، فروشندگان، سیستم پرداخت کارت‌به‌کارت و تأیید رسیدها به‌صورت هوشمند و تعاملی فراهم باشد.

---

## 🧱 Core Tables

### 1. `user`
- `id`: bigint, PK
- `telegram_id`: bigint, unique
- `username`, `full_name`
- `role`: enum (user, admin, seller)
- `balance`: bigint (stored via `transaction` table only)
- `status`: enum (active, blocked)
- `settings`: json
- `created_at`

### 2. `panel`
- `id`: PK
- `name`
- `url`, `username`, `password`
- `type`: enum (xui)
- `location_name`: string (e.g., "Germany 🇩🇪")
- `status`: active/inactive
- `notes`

### 3. `inbound`
- `id`: PK (internal use)
- `panel_id`: FK → panel.id
- `remote_id`: ID from panel
- `protocol`: enum (vmess, vless, trojan)
- `port`, `settings_json`, `sniffing`, `tag`
- `status`: active/full/disabled
- `max_clients`
- `last_synced`

### 4. `client_account`
- `id`: PK
- `user_id`: FK → user.id
- `panel_id`, `inbound_id`
- `remote_uuid`, `client_name`, `email_name`
- `plan_id`, `order_id`
- `traffic_limit`, `traffic_used`
- `expires_at`, `created_at`
- `status`: active/expired/switched
- `config_url`, `qr_code_path`

### 5. `plan`
- `id`: PK
- `name`, `description`
- `duration_days`, `traffic_gb`
- `price`
- `available_locations`: json or FK
- `created_by`: admin or seller
- `status`

### 6. `order`
- `id`: PK
- `user_id`, `plan_id`, `location_name`
- `client_account_id`: FK
- `amount`, `final_amount`, `discount_code_id`
- `status`: pending/paid/completed/failed/expired
- `timestamps`: created, updated, fulfilled
- `receipt_required`: bool
- `receipt_id`: FK to `receipt_log`

### 7. `transaction`
- `id`: PK
- `user_id`
- `amount`, `type`: (deposit, purchase, refund)
- `related_order_id`
- `status`
- `gateway`, `reference`
- `tracking_code`: internal identifier for user/admin
- `created_at`

### 8. `bank_card`
- `id`, `card_number`, `holder_name`, `bank_name`
- `is_active`: bool
- `rotation_policy`: enum (manual, interval, load_balance)
- `admin_user_id`: FK → user.id
- `telegram_channel_id`: bigint
- `rotation_interval_minutes`: int (e.g., 120)
- `created_at`

### 9. `receipt_log`
- `id`: PK
- `user_id`, `order_id` (optional), `transaction_id` (optional)
- `card_id`: FK → bank_card.id
- `amount`
- `text_reference`, `photo_file_id`
- `status`: pending/approved/rejected/expired
- `admin_id`: FK → user.id
- `responded_at`, `submitted_at`
- `notes`, `rejection_reason`, `is_flagged`
- `tracking_code`: internal string (e.g. RCPT-240421-XYZ)
- `auto_detected_amount`, `auto_validated`: bool (future use)

### 10. `discount_code`
- `id`, `code`
- `type`: percent/fixed
- `value`, `usage_limit`, `usage_count`
- `min_order`, `max_discount`
- `valid_from`, `valid_until`
- `status`

### 11. `test_account_log`
- `id`, `user_id`, `plan_id`, `timestamp`

### 12. `account_transfer`
- `id`, `client_account_id`
- `from_panel_id`, `to_panel_id`
- `from_inbound_id`, `to_inbound_id`
- `moved_at`
- `notes`

### 13. `notification_log`
- `id`, `user_id`
- `type`, `channel`, `status`, `content`
- `summary`: success/failed/pending count (for batch sends)
- `sent_at`

### 14. `setting`
- `key`, `value`, `type`, `scope`, `description`

---

## 🔁 Relationships Summary

| From | To | Type |
|------|----|------|
| User | ClientAccount | 1:N |
| User | Transaction | 1:N |
| User | Order | 1:N |
| Panel | Inbound | 1:N |
| Inbound | ClientAccount | 1:N |
| Plan | ClientAccount | 1:N |
| Plan | Order | 1:N |
| DiscountCode | Order | 1:N |
| ClientAccount | AccountTransfer | 1:N |
| BankCard | ReceiptLog | 1:N |
| ReceiptLog | Order/Transaction | N:1 |

---

## 🔮 Future Enhancements

- `ocr_extracted_text` field in `receipt_log`
- `panel_stats_log` table for monitoring panel load
- Add `reseller_id` to plans and orders
- Add referral program
- Add `card_usage_log` for reporting and commissions

---

## 🛡 Rules & Constraints

- Balance only updated via transaction log
- Unique client naming enforced (location-based prefix + ID)
- Each user limited to 1 test account per free plan
- Receipt TTL = 30min, status auto-expires
- Receipt visibility managed via bot and channel logic
- Superadmin can override actions, review logs, and unflag issues

---

## 📁 References
- `docs/project-requirements.md`
- `docs/project-structure.md`
- `docs/project-relationships.md`

