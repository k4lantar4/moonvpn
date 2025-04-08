"""panel_server_migration_support

Revision ID: 413447bb0285
Revises: 5dd52fd73f6a
Create Date: 2025-04-07 10:48:31.389177

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '413447bb0285'
down_revision = '5dd52fd73f6a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. اضافه کردن فیلدهای جدید به جدول panels برای پشتیبانی از مهاجرت فیزیکی سرور
    op.add_column('panels', sa.Column('previous_server_ip', sa.String(45), nullable=True))
    op.add_column('panels', sa.Column('previous_url', sa.String(255), nullable=True))
    op.add_column('panels', sa.Column('migration_date', sa.DateTime(), nullable=True))
    op.add_column('panels', sa.Column('migration_notes', sa.Text(), nullable=True))
    op.add_column('panels', sa.Column('is_migrated', sa.Boolean(), default=False))
    
    # 2. ایجاد جدول تاریخچه مهاجرت پنل
    op.create_table(
        'panel_server_migrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('panel_id', sa.Integer(), nullable=False),
        sa.Column('old_server_ip', sa.String(45), nullable=False),
        sa.Column('new_server_ip', sa.String(45), nullable=False),
        sa.Column('old_url', sa.String(255), nullable=False),
        sa.Column('new_url', sa.String(255), nullable=False),
        sa.Column('old_geo_location', sa.String(100), nullable=True),
        sa.Column('new_geo_location', sa.String(100), nullable=True),
        sa.Column('old_country_code', sa.String(2), nullable=True),
        sa.Column('new_country_code', sa.String(2), nullable=True),
        sa.Column('backup_file', sa.String(255), nullable=True),
        sa.Column('migration_status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', name='migrationstatus'), default='PENDING'),
        sa.Column('affected_clients_count', sa.Integer(), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['panel_id'], ['panels.id']),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'])
    )
    
    # 3. ایجاد یک جدول نگاشت دامنه برای پنل‌ها
    op.create_table(
        'panel_domains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('panel_id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('panel_id', 'domain'),
        sa.ForeignKeyConstraint(['panel_id'], ['panels.id'])
    )
    
    # 4. اضافه کردن تنظیمات مربوط به مهاجرت پنل
    op.execute(text("INSERT INTO settings (`key`, value, description, is_public, `group`) VALUES ('PANEL_MIGRATION_NOTIFICATION', 'true', 'Notify users when panel is migrated to a new server', 1, 'system')"))
    op.execute(text("INSERT INTO settings (`key`, value, description, is_public, `group`) VALUES ('AUTO_UPDATE_CLIENT_CONFIGS', 'true', 'Automatically update client configs after panel migration', 0, 'system')"))
    op.execute(text("INSERT INTO settings (`key`, value, description, is_public, `group`) VALUES ('PANEL_BACKUP_RETENTION_DAYS', '30', 'Number of days to keep panel backups', 0, 'system')"))


def downgrade() -> None:
    # حذف تنظیمات اضافه شده
    op.execute(text("DELETE FROM settings WHERE `key` IN ('PANEL_MIGRATION_NOTIFICATION', 'AUTO_UPDATE_CLIENT_CONFIGS', 'PANEL_BACKUP_RETENTION_DAYS')"))
    
    # حذف جدول نگاشت دامنه
    op.drop_table('panel_domains')
    
    # حذف جدول تاریخچه مهاجرت پنل
    op.drop_table('panel_server_migrations')
    
    # حذف فیلدهای اضافه شده به جدول panels
    op.drop_column('panels', 'is_migrated')
    op.drop_column('panels', 'migration_notes')
    op.drop_column('panels', 'migration_date')
    op.drop_column('panels', 'previous_url')
    op.drop_column('panels', 'previous_server_ip')
