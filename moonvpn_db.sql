-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: db:3306
-- Generation Time: Apr 09, 2025 at 03:44 AM
-- Server version: 8.0.41
-- PHP Version: 8.2.27

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `moonvpn_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `alembic_version`
--

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `alembic_version`
--

INSERT INTO `alembic_version` (`version_num`) VALUES
('b14731ed37cd');

-- --------------------------------------------------------

--
-- Table structure for table `bank_cards`
--

CREATE TABLE `bank_cards` (
  `id` int NOT NULL,
  `bank_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `card_number` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `account_number` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `owner_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `rotation_priority` int DEFAULT NULL,
  `last_used` datetime DEFAULT NULL,
  `daily_limit` decimal(15,2) DEFAULT NULL,
  `monthly_limit` decimal(15,2) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `clients`
--

CREATE TABLE `clients` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `panel_id` int NOT NULL,
  `panel_inbound_id` int DEFAULT NULL,
  `location_id` int NOT NULL,
  `plan_id` int NOT NULL,
  `order_id` int DEFAULT NULL,
  `client_uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `remark` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime NOT NULL,
  `traffic` bigint NOT NULL,
  `used_traffic` bigint DEFAULT NULL,
  `status` enum('ACTIVE','EXPIRED','DISABLED','FROZEN') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `protocol` enum('VMESS','VLESS','TROJAN','SHADOWSOCKS') COLLATE utf8mb4_unicode_ci NOT NULL,
  `network` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `port` int DEFAULT NULL,
  `tls` tinyint(1) DEFAULT NULL,
  `security` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `config_json` text COLLATE utf8mb4_unicode_ci,
  `subscription_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `qrcode_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `freeze_start` datetime DEFAULT NULL,
  `freeze_end` datetime DEFAULT NULL,
  `is_trial` tinyint(1) DEFAULT NULL,
  `auto_renew` tinyint(1) DEFAULT NULL,
  `last_online` datetime DEFAULT NULL,
  `last_notified` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `original_client_uuid` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `original_remark` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `custom_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `migration_count` int DEFAULT NULL,
  `previous_panel_id` int DEFAULT NULL,
  `migration_history` text COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `client_id_sequences`
--

CREATE TABLE `client_id_sequences` (
  `id` int NOT NULL,
  `location_id` int NOT NULL,
  `last_id` int DEFAULT NULL,
  `prefix` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `client_migrations`
--

CREATE TABLE `client_migrations` (
  `id` int NOT NULL,
  `client_id` int NOT NULL,
  `from_panel_id` int NOT NULL,
  `to_panel_id` int NOT NULL,
  `old_client_uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `new_client_uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `old_remark` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `new_remark` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `traffic_remaining` bigint NOT NULL,
  `time_remaining_days` int NOT NULL,
  `reason` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `migrated_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `discount_codes`
--

CREATE TABLE `discount_codes` (
  `id` int NOT NULL,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `discount_type` enum('FIXED','PERCENTAGE') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `discount_value` decimal(10,2) NOT NULL,
  `max_uses` int DEFAULT NULL,
  `used_count` int DEFAULT NULL,
  `expires_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `created_by` int DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `locations`
--

CREATE TABLE `locations` (
  `id` int NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `flag` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `country_code` varchar(2) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `protocols_supported` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `inbound_tag_pattern` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `default_remark_prefix` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `remark_pattern` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '{prefix}-{id}-{custom}',
  `migration_remark_pattern` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '{original}-M{count}'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `locations`
--

INSERT INTO `locations` (`id`, `name`, `flag`, `country_code`, `is_active`, `description`, `protocols_supported`, `inbound_tag_pattern`, `default_remark_prefix`, `created_at`, `updated_at`, `remark_pattern`, `migration_remark_pattern`) VALUES
(1, 'Default Location 🇮🇷', '🇮🇷', NULL, 1, NULL, NULL, NULL, NULL, '2025-04-09 02:58:21', NULL, '{prefix}-{id}-{custom}', '{original}-M{count}');

-- --------------------------------------------------------

--
-- Table structure for table `notification_channels`
--

CREATE TABLE `notification_channels` (
  `id` int NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `channel_id` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `notification_types` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `notification_channels`
--

INSERT INTO `notification_channels` (`id`, `name`, `channel_id`, `description`, `notification_types`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'ADMIN', '-1002542112596', 'Admin general notifications', NULL, 1, '2025-04-09 03:14:28', '2025-04-09 03:14:28'),
(2, 'PAYMENT', '-1002542112596', 'Payment verification requests', NULL, 1, '2025-04-09 03:14:28', '2025-04-09 03:14:28'),
(3, 'BACKUP', '-1002542112596', 'Database backup status', NULL, 1, '2025-04-09 03:14:28', '2025-04-09 03:14:28'),
(4, 'CRITICAL', '-1002542112596', 'Critical system errors', NULL, 1, '2025-04-09 03:14:28', '2025-04-09 03:14:28'),
(5, 'USER_REGISTRATION', '-1002542112596', 'New user registrations', NULL, 1, '2025-04-09 03:14:28', '2025-04-09 03:14:28');

-- --------------------------------------------------------

--
-- Table structure for table `orders`
--

CREATE TABLE `orders` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `plan_id` int NOT NULL,
  `payment_method` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `discount_amount` decimal(10,2) DEFAULT NULL,
  `final_amount` decimal(10,2) NOT NULL,
  `status` enum('PENDING','COMPLETED','FAILED','CANCELLED') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `discount_code_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `panels`
--

CREATE TABLE `panels` (
  `id` int NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `url` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `api_path` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `login_path` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `username` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `panel_type` enum('XUI','MARZBAN','SANAEI','ALIREZA','VAXILU','XRAY') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `location_id` int NOT NULL,
  `server_ip` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `server_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_healthy` tinyint(1) DEFAULT NULL,
  `last_check` datetime DEFAULT NULL,
  `status_message` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `max_clients` int DEFAULT NULL,
  `current_clients` int DEFAULT NULL,
  `traffic_limit` bigint DEFAULT NULL,
  `traffic_used` bigint DEFAULT NULL,
  `api_token` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `api_token_expires_at` datetime DEFAULT NULL,
  `priority` int DEFAULT NULL,
  `created_by` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `geo_location` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `provider` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `datacenter` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `alternate_domain` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_premium` tinyint(1) DEFAULT NULL,
  `network_speed` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `server_specs` text COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `panels`
--

INSERT INTO `panels` (`id`, `name`, `url`, `api_path`, `login_path`, `username`, `password`, `panel_type`, `location_id`, `server_ip`, `server_type`, `is_active`, `is_healthy`, `last_check`, `status_message`, `max_clients`, `current_clients`, `traffic_limit`, `traffic_used`, `api_token`, `api_token_expires_at`, `priority`, `created_by`, `created_at`, `updated_at`, `geo_location`, `provider`, `datacenter`, `alternate_domain`, `is_premium`, `network_speed`, `server_specs`) VALUES
(2, 'Initial 3x-UI Panel', 'http://65.109.189.171:30335/k2WVbEsXaJPx11U', NULL, NULL, 'gAAAAABn9eJOn4eBruQgFy9ZIllyPm7D6cAeLGZyG7lrtBq1dFrGhfYujrGYAHjidAaa1JS9ROjj4fr0ja6tQcs8ExuwdLjj_A==', 'gAAAAABn9eJO4H8oPOsXTYPNeUVd-iTHmmTZaPOk7LFQ9fO0R82erAJ4I4QlGjnqHy-Jl5s5XwoH7rleHtX8RTtxWWtxeAZJag==', 'XUI', 1, NULL, NULL, 1, 1, NULL, NULL, NULL, 0, NULL, 0, NULL, NULL, 1, NULL, '2025-04-09 02:58:22', NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `panel_health_checks`
--

CREATE TABLE `panel_health_checks` (
  `id` int NOT NULL,
  `panel_id` int NOT NULL,
  `status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `response_time_ms` int DEFAULT NULL,
  `details` text COLLATE utf8mb4_unicode_ci,
  `checked_at` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `panel_inbounds`
--

CREATE TABLE `panel_inbounds` (
  `id` int NOT NULL,
  `panel_id` int NOT NULL,
  `inbound_id` int NOT NULL,
  `tag` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `protocol` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `network` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `port` int NOT NULL,
  `tls` tinyint(1) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `remark` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `client_stats` text COLLATE utf8mb4_unicode_ci,
  `settings` json DEFAULT NULL,
  `stream_settings` json DEFAULT NULL,
  `sniffing` json DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `panel_inbound_id` int DEFAULT NULL,
  `listen` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `panel_enabled` tinyint(1) DEFAULT NULL,
  `last_synced_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `payments`
--

CREATE TABLE `payments` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `order_id` int DEFAULT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_method` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payment_gateway_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `card_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tracking_code` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `receipt_image` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` enum('PENDING','VERIFIED','REJECTED') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `admin_id` int DEFAULT NULL,
  `verification_notes` text COLLATE utf8mb4_unicode_ci,
  `verified_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL,
  `transaction_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `plans`
--

CREATE TABLE `plans` (
  `id` int NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `traffic` bigint NOT NULL,
  `days` int NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `features` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_featured` tinyint(1) DEFAULT NULL,
  `max_clients` int DEFAULT NULL,
  `protocols` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category_id` int NOT NULL,
  `sorting_order` int DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `plans`
--

INSERT INTO `plans` (`id`, `name`, `traffic`, `days`, `price`, `description`, `features`, `is_active`, `is_featured`, `max_clients`, `protocols`, `category_id`, `sorting_order`, `created_at`, `updated_at`) VALUES
(1, 'برنزی ۱ ماهه ۵۰ گیگ ✨', 53687091200, 30, 50000.00, 'پلان برنزی اقتصادی یک ماهه با ۵۰ گیگابایت ترافیک.', NULL, 1, 0, 1, 'vless,vmess', 1, 0, '2025-04-09 03:14:28', '2025-04-09 03:14:28');

-- --------------------------------------------------------

--
-- Table structure for table `plan_categories`
--

CREATE TABLE `plan_categories` (
  `id` int NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `sorting_order` int DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `plan_categories`
--

INSERT INTO `plan_categories` (`id`, `name`, `description`, `sorting_order`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'عمومی Bronze 🥉', 'دسته‌بندی پلان‌های عمومی برنزی', 0, 1, '2025-04-09 03:14:28', '2025-04-09 03:14:28'),
(2, 'عمومی Silver 🥈', 'دسته‌بندی پلان‌های عمومی نقره ای', 0, 1, '2025-04-09 03:14:28', '2025-04-09 03:14:28'),
(3, 'عمومی Gold 🥇', 'دسته‌بندی پلان‌های عمومی طلایی', 0, 1, '2025-04-09 03:14:28', '2025-04-09 03:14:28');

-- --------------------------------------------------------

--
-- Table structure for table `roles`
--

CREATE TABLE `roles` (
  `id` int NOT NULL,
  `name` enum('ADMIN','SELLER','USER') COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `can_manage_panels` tinyint(1) DEFAULT NULL,
  `can_manage_users` tinyint(1) DEFAULT NULL,
  `can_manage_plans` tinyint(1) DEFAULT NULL,
  `can_approve_payments` tinyint(1) DEFAULT NULL,
  `can_broadcast` tinyint(1) DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT NULL,
  `is_seller` tinyint(1) DEFAULT NULL,
  `discount_percent` int DEFAULT NULL,
  `commission_percent` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `roles`
--

INSERT INTO `roles` (`id`, `name`, `description`, `can_manage_panels`, `can_manage_users`, `can_manage_plans`, `can_approve_payments`, `can_broadcast`, `is_admin`, `is_seller`, `discount_percent`, `commission_percent`, `created_at`, `updated_at`) VALUES
(1, 'ADMIN', 'Administrator with full access', 0, 0, 0, 0, 0, 0, 0, 0, 0, '2025-04-09 03:05:28', NULL),
(2, 'SELLER', 'Seller/Reseller', 0, 0, 0, 0, 0, 0, 0, 0, 0, '2025-04-09 03:05:28', NULL),
(3, 'USER', 'Regular end-user', 0, 0, 0, 0, 0, 0, 0, 0, 0, '2025-04-09 03:05:28', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `settings`
--

CREATE TABLE `settings` (
  `id` int NOT NULL,
  `key` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_public` tinyint(1) DEFAULT NULL,
  `group` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `settings`
--

INSERT INTO `settings` (`id`, `key`, `value`, `description`, `is_public`, `group`) VALUES
(1, 'DEFAULT_REMARK_PATTERN', '{prefix}-{id}-{custom}', 'Default pattern for new client remarks', 0, 'system'),
(2, 'MIGRATION_REMARK_PATTERN', '{original}-M{count}', 'Pattern for migrated client remarks', 0, 'system'),
(3, 'ALLOW_CUSTOM_REMARKS', 'true', 'Allow users to set custom remark names', 1, 'system'),
(4, 'MAX_MIGRATIONS_PER_DAY', '3', 'Maximum allowed migrations per day per user', 0, 'system');

-- --------------------------------------------------------

--
-- Table structure for table `transactions`
--

CREATE TABLE `transactions` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `type` enum('DEPOSIT','WITHDRAW','PURCHASE','REFUND','COMMISSION') COLLATE utf8mb4_unicode_ci NOT NULL,
  `reference_id` int DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `balance_after` decimal(10,2) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `telegram_id` bigint NOT NULL,
  `username` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `full_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role_id` int NOT NULL,
  `balance` decimal(10,2) NOT NULL,
  `is_banned` tinyint(1) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `referral_code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `referred_by_id` int DEFAULT NULL,
  `lang` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  `login_ip` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `telegram_id`, `username`, `full_name`, `phone`, `email`, `role_id`, `balance`, `is_banned`, `is_active`, `referral_code`, `referred_by_id`, `lang`, `last_login`, `login_ip`, `created_at`, `updated_at`) VALUES
(3, 1713374557, 'initial_admin', 'Initial Admin', NULL, NULL, 1, 0.00, 0, 1, NULL, NULL, 'fa', NULL, NULL, '2025-04-09 03:14:28', NULL);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `alembic_version`
--
ALTER TABLE `alembic_version`
  ADD PRIMARY KEY (`version_num`);

--
-- Indexes for table `bank_cards`
--
ALTER TABLE `bank_cards`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `clients`
--
ALTER TABLE `clients`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `panel_id` (`panel_id`),
  ADD KEY `panel_inbound_id` (`panel_inbound_id`),
  ADD KEY `location_id` (`location_id`),
  ADD KEY `plan_id` (`plan_id`),
  ADD KEY `order_id` (`order_id`),
  ADD KEY `fk_clients_previous_panel` (`previous_panel_id`);

--
-- Indexes for table `client_id_sequences`
--
ALTER TABLE `client_id_sequences`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `location_id` (`location_id`),
  ADD UNIQUE KEY `location_id_2` (`location_id`),
  ADD UNIQUE KEY `location_id_3` (`location_id`);

--
-- Indexes for table `client_migrations`
--
ALTER TABLE `client_migrations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `client_id` (`client_id`),
  ADD KEY `from_panel_id` (`from_panel_id`),
  ADD KEY `to_panel_id` (`to_panel_id`);

--
-- Indexes for table `discount_codes`
--
ALTER TABLE `discount_codes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `code` (`code`),
  ADD KEY `created_by` (`created_by`);

--
-- Indexes for table `locations`
--
ALTER TABLE `locations`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `notification_channels`
--
ALTER TABLE `notification_channels`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD UNIQUE KEY `name_2` (`name`),
  ADD UNIQUE KEY `name_3` (`name`);

--
-- Indexes for table `orders`
--
ALTER TABLE `orders`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `plan_id` (`plan_id`),
  ADD KEY `discount_code_id` (`discount_code_id`);

--
-- Indexes for table `panels`
--
ALTER TABLE `panels`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `url` (`url`),
  ADD KEY `location_id` (`location_id`),
  ADD KEY `created_by` (`created_by`);

--
-- Indexes for table `panel_health_checks`
--
ALTER TABLE `panel_health_checks`
  ADD PRIMARY KEY (`id`),
  ADD KEY `panel_id` (`panel_id`);

--
-- Indexes for table `panel_inbounds`
--
ALTER TABLE `panel_inbounds`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_panel_inbound_id` (`panel_id`,`inbound_id`);

--
-- Indexes for table `payments`
--
ALTER TABLE `payments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `order_id` (`order_id`),
  ADD KEY `admin_id` (`admin_id`);

--
-- Indexes for table `plans`
--
ALTER TABLE `plans`
  ADD PRIMARY KEY (`id`),
  ADD KEY `category_id` (`category_id`);

--
-- Indexes for table `plan_categories`
--
ALTER TABLE `plan_categories`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `settings`
--
ALTER TABLE `settings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `key` (`key`);

--
-- Indexes for table `transactions`
--
ALTER TABLE `transactions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_users_telegram_id` (`telegram_id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `phone` (`phone`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `referral_code` (`referral_code`),
  ADD KEY `role_id` (`role_id`),
  ADD KEY `referred_by_id` (`referred_by_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bank_cards`
--
ALTER TABLE `bank_cards`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `clients`
--
ALTER TABLE `clients`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `client_id_sequences`
--
ALTER TABLE `client_id_sequences`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `client_migrations`
--
ALTER TABLE `client_migrations`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `discount_codes`
--
ALTER TABLE `discount_codes`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `locations`
--
ALTER TABLE `locations`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `notification_channels`
--
ALTER TABLE `notification_channels`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `orders`
--
ALTER TABLE `orders`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `panels`
--
ALTER TABLE `panels`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `panel_health_checks`
--
ALTER TABLE `panel_health_checks`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `panel_inbounds`
--
ALTER TABLE `panel_inbounds`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `payments`
--
ALTER TABLE `payments`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `plans`
--
ALTER TABLE `plans`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `plan_categories`
--
ALTER TABLE `plan_categories`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `roles`
--
ALTER TABLE `roles`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `settings`
--
ALTER TABLE `settings`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `transactions`
--
ALTER TABLE `transactions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `clients`
--
ALTER TABLE `clients`
  ADD CONSTRAINT `clients_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `clients_ibfk_2` FOREIGN KEY (`panel_id`) REFERENCES `panels` (`id`),
  ADD CONSTRAINT `clients_ibfk_3` FOREIGN KEY (`panel_inbound_id`) REFERENCES `panel_inbounds` (`id`),
  ADD CONSTRAINT `clients_ibfk_4` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`),
  ADD CONSTRAINT `clients_ibfk_5` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`),
  ADD CONSTRAINT `clients_ibfk_6` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  ADD CONSTRAINT `fk_clients_previous_panel` FOREIGN KEY (`previous_panel_id`) REFERENCES `panels` (`id`);

--
-- Constraints for table `client_id_sequences`
--
ALTER TABLE `client_id_sequences`
  ADD CONSTRAINT `client_id_sequences_ibfk_1` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`);

--
-- Constraints for table `client_migrations`
--
ALTER TABLE `client_migrations`
  ADD CONSTRAINT `client_migrations_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`),
  ADD CONSTRAINT `client_migrations_ibfk_2` FOREIGN KEY (`from_panel_id`) REFERENCES `panels` (`id`),
  ADD CONSTRAINT `client_migrations_ibfk_3` FOREIGN KEY (`to_panel_id`) REFERENCES `panels` (`id`);

--
-- Constraints for table `discount_codes`
--
ALTER TABLE `discount_codes`
  ADD CONSTRAINT `discount_codes_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`);

--
-- Constraints for table `orders`
--
ALTER TABLE `orders`
  ADD CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`),
  ADD CONSTRAINT `orders_ibfk_3` FOREIGN KEY (`discount_code_id`) REFERENCES `discount_codes` (`id`),
  ADD CONSTRAINT `orders_ibfk_4` FOREIGN KEY (`discount_code_id`) REFERENCES `discount_codes` (`id`);

--
-- Constraints for table `panels`
--
ALTER TABLE `panels`
  ADD CONSTRAINT `panels_ibfk_1` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`),
  ADD CONSTRAINT `panels_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`);

--
-- Constraints for table `panel_health_checks`
--
ALTER TABLE `panel_health_checks`
  ADD CONSTRAINT `panel_health_checks_ibfk_1` FOREIGN KEY (`panel_id`) REFERENCES `panels` (`id`);

--
-- Constraints for table `panel_inbounds`
--
ALTER TABLE `panel_inbounds`
  ADD CONSTRAINT `panel_inbounds_ibfk_1` FOREIGN KEY (`panel_id`) REFERENCES `panels` (`id`);

--
-- Constraints for table `payments`
--
ALTER TABLE `payments`
  ADD CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `payments_ibfk_2` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  ADD CONSTRAINT `payments_ibfk_3` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `plans`
--
ALTER TABLE `plans`
  ADD CONSTRAINT `plans_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `plan_categories` (`id`);

--
-- Constraints for table `transactions`
--
ALTER TABLE `transactions`
  ADD CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`),
  ADD CONSTRAINT `users_ibfk_2` FOREIGN KEY (`referred_by_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
