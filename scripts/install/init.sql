-- MySQL initialization script for MoonVPN
-- This script is run when the MySQL container starts for the first time

-- Set default character set and collation
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_server = utf8mb4;
SET collation_server = utf8mb4_unicode_ci;

-- Set timezone to UTC
SET GLOBAL time_zone = '+00:00';
SET time_zone = '+00:00';

-- Enable MySQL strict mode
SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS `moonvpn_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `moonvpn_db`;

-- Log initialization
SELECT 'Database initialization complete. Tables will be created by the application.' AS 'Info'; 