"""client_location_change_history

Revision ID: 4f5a7b23e1c9
Revises: 413447bb0285
Create Date: 2025-04-07 11:26:32.481234

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect


# revision identifiers, used by Alembic.
revision = '4f5a7b23e1c9'
down_revision = '413447bb0285'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. اضافه کردن فیلدهای جدید به جدول clients برای پشتیبانی از تغییر لوکیشن و تاریخچه
    # ابتدا بررسی می‌کنیم کدام ستون‌ها قبلاً اضافه شده‌اند
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('clients')]
    
    # اضافه کردن ستون‌ها فقط اگر وجود نداشته باشند
    if 'original_location_id' not in columns:
        op.add_column('clients', sa.Column('original_location_id', sa.Integer(), sa.ForeignKey('locations.id'), nullable=True))
    if 'original_remark' not in columns:
        op.add_column('clients', sa.Column('original_remark', sa.String(255), nullable=True))
    if 'custom_name' not in columns:
        op.add_column('clients', sa.Column('custom_name', sa.String(100), nullable=True))
    if 'previous_panel_id' not in columns:
        op.add_column('clients', sa.Column('previous_panel_id', sa.Integer(), sa.ForeignKey('panels.id'), nullable=True))
    if 'migration_count' not in columns:
        op.add_column('clients', sa.Column('migration_count', sa.Integer(), default=0))
    if 'last_location_change' not in columns:
        op.add_column('clients', sa.Column('last_location_change', sa.DateTime(), nullable=True))
    if 'location_changes_today' not in columns:
        op.add_column('clients', sa.Column('location_changes_today', sa.Integer(), default=0))
    if 'location_changes_reset_date' not in columns:
        op.add_column('clients', sa.Column('location_changes_reset_date', sa.DateTime(), nullable=True))
    if 'migration_history' not in columns:
        op.add_column('clients', sa.Column('migration_history', sa.Text(), nullable=True))
    
    # 2. ایجاد جدول client_migrations برای ثبت تاریخچه مهاجرت بین لوکیشن‌ها
    # بررسی می‌کنیم آیا جدول قبلاً ساخته شده است
    tables = inspector.get_table_names()
    if 'client_migrations' not in tables:
        op.create_table(
            'client_migrations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('client_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('old_location_id', sa.Integer(), nullable=False),
            sa.Column('new_location_id', sa.Integer(), nullable=False),
            sa.Column('old_panel_id', sa.Integer(), nullable=False),
            sa.Column('new_panel_id', sa.Integer(), nullable=False),
            sa.Column('old_remark', sa.String(255), nullable=False),
            sa.Column('new_remark', sa.String(255), nullable=False),
            sa.Column('old_uuid', sa.String(36), nullable=True),
            sa.Column('new_uuid', sa.String(36), nullable=True),
            sa.Column('reason', sa.String(255), nullable=True),
            sa.Column('transferred_traffic', sa.BigInteger(), default=0),
            sa.Column('transferred_expiry', sa.Boolean(), default=True),
            sa.Column('performed_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['old_location_id'], ['locations.id']),
            sa.ForeignKeyConstraint(['new_location_id'], ['locations.id']),
            sa.ForeignKeyConstraint(['old_panel_id'], ['panels.id']),
            sa.ForeignKeyConstraint(['new_panel_id'], ['panels.id']),
            sa.ForeignKeyConstraint(['performed_by'], ['users.id']),
        )
    
    # 3. اضافه کردن فیلدهای جدید به جدول locations برای کنترل الگوی ریمارک
    location_columns = [column['name'] for column in inspector.get_columns('locations')]
    if 'default_remark_prefix' not in location_columns:
        op.add_column('locations', sa.Column('default_remark_prefix', sa.String(10), nullable=True))
    if 'remark_pattern' not in location_columns:
        op.add_column('locations', sa.Column('remark_pattern', sa.String(100), nullable=True))
    if 'migration_remark_pattern' not in location_columns:
        op.add_column('locations', sa.Column('migration_remark_pattern', sa.String(100), nullable=True))
    
    # 4. اضافه کردن تنظیمات مربوط به تغییر لوکیشن و ریمارک
    # بررسی می‌کنیم که آیا تنظیمات قبلاً اضافه شده است
    result = conn.execute(text("SELECT COUNT(*) FROM settings WHERE `key` = 'MAX_LOCATION_CHANGES_PER_DAY'"))
    count = result.scalar()
    if count == 0:
        op.execute(text("INSERT INTO settings (`key`, value, description, is_public, `group`) VALUES ('MAX_LOCATION_CHANGES_PER_DAY', '3', 'Maximum allowed location changes per day per user', 0, 'system')"))


def downgrade() -> None:
    # حذف تنظیمات اضافه شده
    op.execute(text("DELETE FROM settings WHERE `key` = 'MAX_LOCATION_CHANGES_PER_DAY'"))
    
    # حذف فیلدهای اضافه شده به جدول locations
    op.drop_column('locations', 'migration_remark_pattern')
    op.drop_column('locations', 'remark_pattern')
    op.drop_column('locations', 'default_remark_prefix')
    
    # حذف جدول client_migrations
    op.drop_table('client_migrations')
    
    # حذف فیلدهای اضافه شده به جدول clients
    op.drop_column('clients', 'migration_history')
    op.drop_column('clients', 'location_changes_reset_date')
    op.drop_column('clients', 'location_changes_today')
    op.drop_column('clients', 'last_location_change')
    op.drop_column('clients', 'migration_count')
    op.drop_column('clients', 'previous_panel_id')
    op.drop_column('clients', 'custom_name')
    op.drop_column('clients', 'original_remark')
    op.drop_column('clients', 'original_location_id') 