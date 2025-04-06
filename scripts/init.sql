-- Initialize MoonVPN Database / راه‌اندازی پایگاه داده مون‌وی‌پی‌ان

-- Set character set and time zone / تنظیم کاراکترست و منطقه زمانی
SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- Create database if not exists / ایجاد پایگاه داده در صورت عدم وجود
CREATE DATABASE IF NOT EXISTS moonvpn_db
    CHARACTER SET = utf8mb4
    COLLATE = utf8mb4_unicode_ci;

USE moonvpn_db;

-- Create users table / ایجاد جدول کاربران
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(32),
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64),
    phone_number VARCHAR(15),
    language_code CHAR(2) DEFAULT 'fa',
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create panels table / ایجاد جدول پنل‌ها
CREATE TABLE IF NOT EXISTS panels (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(64) NOT NULL,
    url VARCHAR(255) NOT NULL,
    username VARCHAR(64) NOT NULL,
    password VARCHAR(255) NOT NULL,
    location VARCHAR(64) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    max_clients INT DEFAULT 500,
    current_clients INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_location (location),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create plans table / ایجاد جدول پلن‌ها
CREATE TABLE IF NOT EXISTS plans (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(64) NOT NULL,
    description TEXT,
    duration_days INT NOT NULL,
    traffic_gb INT NOT NULL,
    price_irr BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create clients table / ایجاد جدول مشتریان
CREATE TABLE IF NOT EXISTS clients (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    panel_id BIGINT NOT NULL,
    plan_id BIGINT NOT NULL,
    uuid VARCHAR(36) NOT NULL,
    email VARCHAR(255) NOT NULL,
    traffic_used_gb INT DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (panel_id) REFERENCES panels(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_panel_id (panel_id),
    INDEX idx_plan_id (plan_id),
    INDEX idx_uuid (uuid),
    INDEX idx_expires_at (expires_at),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create transactions table / ایجاد جدول تراکنش‌ها
CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    plan_id BIGINT NOT NULL,
    amount_irr BIGINT NOT NULL,
    payment_id VARCHAR(64),
    status VARCHAR(16) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_plan_id (plan_id),
    INDEX idx_payment_id (payment_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create notifications table / ایجاد جدول اعلان‌ها
CREATE TABLE IF NOT EXISTS notifications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    type VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_type (type),
    INDEX idx_is_read (is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create settings table / ایجاد جدول تنظیمات
CREATE TABLE IF NOT EXISTS settings (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    `key` VARCHAR(64) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user / درج کاربر ادمین پیش‌فرض
INSERT INTO users (telegram_id, first_name, is_admin)
VALUES (1713374557, 'Admin', TRUE)
ON DUPLICATE KEY UPDATE is_admin = TRUE;

-- Insert default settings / درج تنظیمات پیش‌فرض
INSERT INTO settings (`key`, value, description) VALUES
('TRIAL_ENABLED', 'true', 'Whether trial accounts are enabled'),
('TRIAL_DURATION_HOURS', '24', 'Duration of trial accounts in hours'),
('TRIAL_TRAFFIC_GB', '2', 'Traffic limit for trial accounts in GB'),
('MAX_DAILY_TRIALS', '50', 'Maximum number of trial accounts per day'),
('MAINTENANCE_MODE', 'false', 'Whether the system is in maintenance mode'),
('PAYMENT_ENABLED', 'true', 'Whether payment system is enabled'),
('REGISTRATION_ENABLED', 'true', 'Whether new user registration is enabled'),
('WELCOME_MESSAGE', '🌙 به مون وی‌پی‌ان خوش آمدید!\n\nبرای شروع، یکی از گزینه‌های زیر را انتخاب کنید.', 'Welcome message for new users')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP; 