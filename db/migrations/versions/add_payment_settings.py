"""
Add payment settings to settings table

Revision ID: add_payment_settings
Revises: 20240630wallet
Create Date: 2025-04-27 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_payment_settings'
down_revision = '20240630wallet'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add payment_settings
    op.execute(
        "INSERT INTO settings (`key`, `value`, `type`, `scope`, `description`) VALUES "
        "('bank_cards', '[]', 'json', 'payment', 'کارت‌های بانکی فعال برای پرداخت') "
        "ON DUPLICATE KEY UPDATE `value`='[]', `type`='json', `scope`='payment'"
    )
    
    op.execute(
        "INSERT INTO settings (`key`, `value`, `type`, `scope`, `description`) VALUES "
        "('receipt_channel_id', '-1001234567890', 'str', 'payment', 'آیدی کانال دریافت رسید') "
        "ON DUPLICATE KEY UPDATE `type`='str', `scope`='payment'"
    )
    
    op.execute(
        "INSERT INTO settings (`key`, `value`, `type`, `scope`, `description`) VALUES "
        "('admin_id', '0', 'int', 'system', 'آیدی ادمین اصلی') "
        "ON DUPLICATE KEY UPDATE `type`='int', `scope`='system'"
    )


def downgrade() -> None:
    # Remove payment_settings if needed
    op.execute("DELETE FROM settings WHERE `key`='bank_cards' AND `scope`='payment'")
    op.execute("DELETE FROM settings WHERE `key`='receipt_channel_id' AND `scope`='payment'")
    op.execute("DELETE FROM settings WHERE `key`='admin_id' AND `scope`='system'") 