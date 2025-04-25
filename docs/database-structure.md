# Database Structure

این سند ساختار جداول پایگاه داده پروژه MoonVPN را بر اساس مایگریشن اولیه (`5821b73312a3`) شرح می‌دهد.

## Table: `discount_codes`

| Column Name    | Data Type          | Constraints                                  | Nullable | Comment |
| -------------- | ------------------ | -------------------------------------------- | -------- | ------- |
| `id`           | `Integer`          | Primary Key, Autoincrement                   | No       |         |
| `code`         | `String(50)`       | Unique                                       | No       |         |
| `type`         | `Enum(PERCENT, FIXED)` |                                              | No       |         |
| `value`        | `DECIMAL(10, 2)`   |                                              | No       |         |
| `start_date`   | `DateTime`         |                                              | No       |         |
| `end_date`     | `DateTime`         |                                              | No       |         |
| `usage_limit`  | `Integer`          |                                              | No       |         |
| `used_count`   | `Integer`          |                                              | No       |         |
| `active`       | `Boolean`          |                                              | No       |         |
| `max_discount` | `DECIMAL(10, 2)`   |                                              | Yes      |         |
| `min_order`    | `DECIMAL(10, 2)`   |                                              | Yes      |         |

## Table: `panels`

| Column Name     | Data Type                      | Constraints                | Nullable | Comment |
| --------------- | ------------------------------ | -------------------------- | -------- | ------- |
| `id`            | `Integer`                      | Primary Key, Autoincrement | No       |         |
| `name`          | `String(255)`                  |                            | No       |         |
| `location_name` | `String(100)`                  |                            | No       |         |
| `url`           | `Text`                         |                            | No       |         |
| `username`      | `String(100)`                  |                            | No       |         |
| `password`      | `String(255)`                  |                            | No       |         |
| `type`          | `Enum(XUI)`                    |                            | No       |         |
| `status`        | `Enum(ACTIVE, DISABLED, DELETED)` |                            | No       |         |
| `notes`         | `Text`                         |                            | Yes      |         |

## Table: `settings`

| Column Name   | Data Type     | Constraints   | Nullable | Comment |
| ------------- | ------------- | ------------- | -------- | ------- |
| `key`         | `String(255)` | Primary Key   | No       |         |
| `value`       | `Text`        |               | No       |         |
| `type`        | `String(50)`  |               | No       |         |
| `scope`       | `String(50)`  |               | No       |         |
| `description` | `Text`        |               | Yes      |         |

## Table: `users`

| Column Name   | Data Type                 | Constraints                                    | Nullable | Comment |
| ------------- | ------------------------- | ---------------------------------------------- | -------- | ------- |
| `id`          | `BigInteger`              | Primary Key, Autoincrement                     | No       |         |
| `telegram_id` | `BigInteger`              | Unique Index                                   | No       |         |
| `username`    | `String(255)`             |                                                | Yes      |         |
| `full_name`   | `String(255)`             |                                                | Yes      |         |
| `role`        | `Enum(USER, ADMIN, SELLER)` |                                                | No       |         |
| `created_at`  | `DateTime`                |                                                | No       |         |
| `status`      | `Enum(ACTIVE, BLOCKED)`   |                                                | No       |         |
| `settings`    | `JSON`                    |                                                | Yes      |         |
| `balance`     | `DECIMAL(10, 2)`          |                                                | No       |         |

## Table: `bank_cards`

| Column Name               | Data Type                              | Constraints                | Nullable | Comment |
| ------------------------- | -------------------------------------- | -------------------------- | -------- | ------- |
| `id`                      | `BigInteger`                           | Primary Key, Autoincrement | No       |         |
| `card_number`             | `String(16)`                           |                            | No       |         |
| `holder_name`             | `String(255)`                          |                            | No       |         |
| `bank_name`               | `String(255)`                          |                            | No       |         |
| `is_active`               | `Boolean`                              |                            | No       |         |
| `rotation_policy`         | `Enum(MANUAL, INTERVAL, LOAD_BALANCE)` |                            | No       |         |
| `rotation_interval_minutes` | `Integer`                              |                            | Yes      |         |
| `telegram_channel_id`     | `BigInteger`                           |                            | Yes      |         |
| `created_at`              | `DateTime`                             |                            | No       |         |
| `admin_user_id`           | `BigInteger`                           | Foreign Key (`users.id`)   | No       |         |

## Table: `inbound`

| Column Name             | Data Type                      | Constraints                           | Nullable | Comment |
| ----------------------- | ------------------------------ | ------------------------------------- | -------- | ------- |
| `id`                    | `Integer`                      | Primary Key                           | No       |         |
| `panel_id`              | `Integer`                      | Foreign Key (`panels.id`, ON DELETE CASCADE), Index | No       |         |
| `remote_id`             | `Integer`                      |                                       | No       |         |
| `protocol`              | `String(50)`                   |                                       | No       |         |
| `tag`                   | `String(100)`                  |                                       | No       |         |
| `port`                  | `Integer`                      |                                       | No       |         |
| `settings_json`         | `JSON`                         |                                       | Yes      |         |
| `sniffing`              | `JSON`                         |                                       | Yes      |         |
| `status`                | `Enum(ACTIVE, DISABLED, DELETED)` |                                       | No       |         |
| `max_clients`           | `Integer`                      |                                       | Yes      |         |
| `last_synced`           | `DateTime`                     |                                       | Yes      |         |
| `listen`                | `String(100)`                  |                                       | Yes      |         |
| `stream_settings`       | `JSON`                         |                                       | Yes      |         |
| `allocate_settings`     | `JSON`                         |                                       | Yes      |         |
| `receive_original_dest` | `Boolean`                      |                                       | Yes      |         |
| `allow_transparent`     | `Boolean`                      |                                       | Yes      |         |
| `security_settings`     | `JSON`                         |                                       | Yes      |         |
| `remark`                | `String(255)`                  |                                       | Yes      |         |

## Table: `notification_logs`

| Column Name  | Data Type                                           | Constraints                | Nullable | Comment |
| ------------ | --------------------------------------------------- | -------------------------- | -------- | ------- |
| `id`         | `BigInteger`                                        | Primary Key, Autoincrement | No       |         |
| `type`       | `Enum(RECEIPT, ORDER, EXPIRY, BALANCE, SYSTEM)`     |                            | No       |         |
| `channel`    | `Enum(TELEGRAM, EMAIL, SMS)`                        |                            | No       |         |
| `status`     | `Enum(PENDING, SENT, FAILED)`                       |                            | No       |         |
| `content`    | `Text`                                              |                            | No       |         |
| `summary`    | `JSON`                                              |                            | Yes      |         |
| `sent_at`    | `DateTime`                                          |                            | Yes      |         |
| `created_at` | `DateTime`                                          |                            | No       |         |
| `user_id`    | `BigInteger`                                        | Foreign Key (`users.id`)   | No       |         |

## Table: `plans`

| Column Name           | Data Type          | Constraints                | Nullable | Comment                    |
| --------------------- | ------------------ | -------------------------- | -------- | -------------------------- |
| `id`                  | `Integer`          | Primary Key, Autoincrement | No       | شناسه پلن                 |
| `name`                | `String(100)`      | Index                      | No       | نام پلن                    |
| `description`         | `Text`             |                            | Yes      | توضیحات پلن                |
| `traffic_gb`          | `Integer`          |                            | No       | حجم ترافیک به گیگابایت    |
| `duration_days`       | `Integer`          |                            | No       | مدت اعتبار به روز          |
| `price`               | `DECIMAL(10, 2)`   |                            | No       | قیمت                       |
| `available_locations` | `JSON`             |                            | Yes      | لیست لوکیشن‌های مجاز       |
| `created_by_id`       | `BigInteger`       | Foreign Key (`users.id`)   | Yes      |                            |
| `status`              | `Enum(ACTIVE, INACTIVE)` |                            | No       | آیا پلن فعال است؟         |
| `created_at`          | `DateTime`         |                            | No       | زمان ایجاد                 |

## Table: `client_accounts`

| Column Name    | Data Type                             | Constraints                           | Nullable | Comment |
| -------------- | ------------------------------------- | ------------------------------------- | -------- | ------- |
| `id`           | `Integer`                             | Primary Key, Autoincrement            | No       |         |
| `user_id`      | `BigInteger`                          | Foreign Key (`users.id`)              | No       |         |
| `panel_id`     | `Integer`                             | Foreign Key (`panels.id`)             | No       |         |
| `inbound_id`   | `Integer`                             | Foreign Key (`inbound.id`, ON DELETE CASCADE) | No       |         |
| `remote_uuid`  | `String(36)`                          |                                       | No       |         |
| `client_name`  | `String(255)`                         |                                       | No       |         |
| `email_name`   | `String(255)`                         |                                       | Yes      |         |
| `plan_id`      | `Integer`                             | Foreign Key (`plans.id`)              | No       |         |
| `expires_at`   | `DateTime`                            |                                       | No       |         |
| `traffic_limit`| `Integer`                             |                                       | No       |         |
| `traffic_used` | `Integer`                             |                                       | No       |         |
| `status`       | `Enum(ACTIVE, EXPIRED, DISABLED, SWITCHED)` |                                       | No       |         |
| `config_url`   | `Text`                                |                                       | Yes      |         |
| `qr_code_path` | `String(255)`                         |                                       | Yes      |         |
| `created_at`   | `DateTime`                            |                                       | No       |         |

## Table: `test_account_log`

| Column Name  | Data Type    | Constraints                | Nullable | Comment |
| ------------ | ------------ | -------------------------- | -------- | ------- |
| `id`         | `Integer`    | Primary Key, Autoincrement | No       |         |
| `user_id`    | `BigInteger` | Foreign Key (`users.id`)   | No       |         |
| `plan_id`    | `Integer`    | Foreign Key (`plans.id`)   | No       |         |
| `created_at` | `DateTime`   |                            | No       |         |

## Table: `account_transfers`

| Column Name      | Data Type    | Constraints                                  | Nullable | Comment |
| ---------------- | ------------ | -------------------------------------------- | -------- | ------- |
| `id`             | `Integer`    | Primary Key                                  | No       |         |
| `old_account_id` | `Integer`    | Foreign Key (`client_accounts.id`)           | No       |         |
| `new_account_id` | `Integer`    | Foreign Key (`client_accounts.id`)           | No       |         |
| `from_panel_id`  | `Integer`    | Foreign Key (`panels.id`)                    | No       |         |
| `to_panel_id`    | `Integer`    | Foreign Key (`panels.id`)                    | No       |         |
| `created_at`     | `DateTime`   |                                              | No       |         |

## Table: `client_renewal_logs`

| Column Name  | Data Type          | Constraints                                  | Nullable | Comment |
| ------------ | ------------------ | -------------------------------------------- | -------- | ------- |
| `id`         | `Integer`          | Primary Key                                  | No       |         |
| `user_id`    | `BigInteger`       | Foreign Key (`users.id`), Index              | No       |         |
| `client_id`  | `Integer`          | Foreign Key (`client_accounts.id`), Index    | No       |         |
| `time_added` | `Integer`          |                                              | Yes      |         |
| `data_added` | `Float`            |                                              | Yes      |         |
| `created_at` | `DateTime(True)`   | Server Default (`now()`), Index              | Yes      |         |

## Table: `orders`

| Column Name         | Data Type                                        | Constraints                        | Nullable | Comment |
| ------------------- | ------------------------------------------------ | ---------------------------------- | -------- | ------- |
| `id`                | `BigInteger`                                     | Primary Key, Autoincrement         | No       |         |
| `user_id`           | `BigInteger`                                     | Foreign Key (`users.id`)           | No       |         |
| `plan_id`           | `Integer`                                        | Foreign Key (`plans.id`)           | No       |         |
| `location_name`     | `String(100)`                                    |                                    | No       |         |
| `client_account_id` | `Integer`                                        | Foreign Key (`client_accounts.id`) | Yes      |         |
| `amount`            | `DECIMAL(10, 2)`                                 |                                    | No       |         |
| `final_amount`      | `DECIMAL(10, 2)`                                 |                                    | Yes      |         |
| `discount_code_id`  | `Integer`                                        | Foreign Key (`discount_codes.id`)  | Yes      |         |
| `status`            | `Enum(PENDING, PAID, COMPLETED, FAILED, EXPIRED)` |                                    | No       |         |
| `receipt_required`  | `Boolean`                                        |                                    | No       |         |
| `created_at`        | `DateTime`                                       |                                    | No       |         |
| `updated_at`        | `DateTime`                                       |                                    | No       |         |
| `fulfilled_at`      | `DateTime`                                       |                                    | Yes      |         |

## Table: `transactions`

| Column Name        | Data Type                        | Constraints                           | Nullable | Comment |
| ------------------ | -------------------------------- | ------------------------------------- | -------- | ------- |
| `id`               | `BigInteger`                     | Primary Key, Autoincrement, Index     | No       |         |
| `user_id`          | `BigInteger`                     | Foreign Key (`users.id`), Index       | No       |         |
| `related_order_id` | `BigInteger`                     | Foreign Key (`orders.id`), Index      | Yes      |         |
| `amount`           | `DECIMAL(10, 2)`                 |                                       | No       |         |
| `type`             | `Enum(DEPOSIT, PURCHASE, REFUND)` |                                       | No       |         |
| `status`           | `Enum(PENDING, SUCCESS, FAILED)` |                                       | No       |         |
| `gateway`          | `String(100)`                    |                                       | Yes      |         |
| `reference`        | `String(255)`                    |                                       | Yes      |         |
| `tracking_code`    | `String(50)`                     | Unique                                | Yes      |         |
| `created_at`       | `DateTime`                       |                                       | No       |         |

## Table: `receipt_log`

| Column Name           | Data Type                              | Constraints                        | Nullable | Comment |
| --------------------- | -------------------------------------- | ---------------------------------- | -------- | ------- |
| `id`                  | `BigInteger`                           | Primary Key, Autoincrement         | No       |         |
| `amount`              | `DECIMAL(10, 2)`                       |                                    | No       |         |
| `text_reference`      | `Text`                                 |                                    | Yes      |         |
| `photo_file_id`       | `String(255)`                          |                                    | Yes      |         |
| `status`              | `Enum(PENDING, APPROVED, REJECTED, EXPIRED)` |                                    | No       |         |
| `notes`               | `Text`                                 |                                    | Yes      |         |
| `rejection_reason`    | `Text`                                 |                                    | Yes      |         |
| `is_flagged`          | `Boolean`                              |                                    | No       |         |
| `tracking_code`       | `String(50)`                           | Unique                             | No       |         |
| `auto_detected_amount`| `DECIMAL(10, 2)`                       |                                    | Yes      |         |
| `auto_validated`      | `Boolean`                              |                                    | No       |         |
| `submitted_at`        | `DateTime`                             |                                    | No       |         |
| `responded_at`        | `DateTime`                             |                                    | Yes      |         |
| `telegram_message_id` | `BigInteger`                           |                                    | Yes      |         |
| `telegram_channel_id` | `BigInteger`                           |                                    | Yes      |         |
| `user_id`             | `BigInteger`                           | Foreign Key (`users.id`)           | No       |         |
| `order_id`            | `BigInteger`                           | Foreign Key (`orders.id`)          | Yes      |         |
| `transaction_id`      | `BigInteger`                           | Foreign Key (`transactions.id`)    | Yes      |         |
| `card_id`             | `BigInteger`                           | Foreign Key (`bank_cards.id`)      | No       |         |
| `admin_id`            | `BigInteger`                           | Foreign Key (`users.id`)           | Yes      |         |

