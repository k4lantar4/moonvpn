#!/usr/bin/env python
"""
اسکریپت انتظار برای آماده شدن پایگاه داده
این اسکریپت تلاش می‌کند به پایگاه داده متصل شود و تا زمانی که اتصال موفقیت‌آمیز نباشد، منتظر می‌ماند
"""

import os
import time
import psycopg2
import logging

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# پارامترهای اتصال به پایگاه داده
db_host = os.environ.get('DB_HOST', 'postgres')
db_port = os.environ.get('DB_PORT', '5432')
db_name = os.environ.get('DB_NAME', 'moonvpn')
db_user = os.environ.get('DB_USER', 'moonvpn')
db_password = os.environ.get('DB_PASSWORD', 'moonvpn')

# حداکثر تعداد تلاش‌ها
max_attempts = 60
attempts = 0

logger.info(f"Waiting for database {db_host}:{db_port} to be ready...")

while attempts < max_attempts:
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        conn.close()
        logger.info("Database connection successful!")
        break
    except psycopg2.OperationalError as e:
        attempts += 1
        logger.warning(f"Database connection attempt {attempts}/{max_attempts} failed: {e}")
        time.sleep(1)
        
if attempts >= max_attempts:
    logger.error("Could not connect to database after maximum attempts. Exiting.")
    exit(1)
    
logger.info("Database is ready!") 