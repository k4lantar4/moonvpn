"""enhance_remark_and_migration_system

Revision ID: 16548e252372
Revises: 001_initial_schema
Create Date: 2025-04-07 10:43:20.639862

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '16548e252372'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. تغییر جدول clients برای پشتیبانی از تاریخچه مهاجرت و ریمارک
    op.add_column('clients', sa.Column('original_client_uuid', sa.String(36), nullable=True))
    op.add_column('clients', sa.Column('original_remark', sa.String(255), nullable=True))
    op.add_column('clients', sa.Column('custom_name', sa.String(100), nullable=True))
    op.add_column('clients', sa.Column('migration_count', sa.Integer(), default=0))
    op.add_column('clients', sa.Column('previous_panel_id', sa.Integer(), nullable=True))
    op.add_column('clients', sa.Column('migration_history', sa.Text(), nullable=True))
    
    # 2. ایجاد جدول تاریخچه مهاجرت
    op.create_table(
        'client_migrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('from_panel_id', sa.Integer(), nullable=False),
        sa.Column('to_panel_id', sa.Integer(), nullable=False),
        sa.Column('old_client_uuid', sa.String(36), nullable=False),
        sa.Column('new_client_uuid', sa.String(36), nullable=False),
        sa.Column('old_remark', sa.String(255), nullable=False),
        sa.Column('new_remark', sa.String(255), nullable=False),
        sa.Column('traffic_remaining', sa.BigInteger(), nullable=False),
        sa.Column('time_remaining_days', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('migrated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['from_panel_id'], ['panels.id']),
        sa.ForeignKeyConstraint(['to_panel_id'], ['panels.id'])
    )
    
    # 3. اضافه کردن فیلدهای جدید به جدول locations برای مدیریت بهتر الگوی ریمارک
    op.add_column('locations', sa.Column('remark_pattern', sa.String(255), nullable=True, 
                                         server_default="{prefix}-{id}-{custom}"))
    op.add_column('locations', sa.Column('migration_remark_pattern', sa.String(255), nullable=True, 
                                         server_default="{original}-M{count}"))
    
    # 4. تنظیمات جدید برای سیستم
    op.execute(text("INSERT INTO settings (`key`, value, description, is_public, `group`) VALUES ('DEFAULT_REMARK_PATTERN', '{prefix}-{id}-{custom}', 'Default pattern for new client remarks', 0, 'system')"))
    op.execute(text("INSERT INTO settings (`key`, value, description, is_public, `group`) VALUES ('MIGRATION_REMARK_PATTERN', '{original}-M{count}', 'Pattern for migrated client remarks', 0, 'system')"))
    op.execute(text("INSERT INTO settings (`key`, value, description, is_public, `group`) VALUES ('ALLOW_CUSTOM_REMARKS', 'true', 'Allow users to set custom remark names', 1, 'system')"))
    op.execute(text("INSERT INTO settings (`key`, value, description, is_public, `group`) VALUES ('MAX_MIGRATIONS_PER_DAY', '3', 'Maximum allowed migrations per day per user', 0, 'system')"))
    
    # 5. افزودن فیلدهای اضافی به جدول panels برای مدیریت بهتر پنل‌ها
    op.add_column('panels', sa.Column('geo_location', sa.String(100), nullable=True))
    op.add_column('panels', sa.Column('provider', sa.String(100), nullable=True))
    op.add_column('panels', sa.Column('datacenter', sa.String(100), nullable=True))
    op.add_column('panels', sa.Column('alternate_domain', sa.String(255), nullable=True))
    op.add_column('panels', sa.Column('is_premium', sa.Boolean(), default=False))
    op.add_column('panels', sa.Column('network_speed', sa.String(50), nullable=True))
    op.add_column('panels', sa.Column('server_specs', sa.Text(), nullable=True))
    
    # 6. ارتباط خارجی برای previous_panel_id
    op.create_foreign_key(
        'fk_clients_previous_panel',
        'clients', 'panels',
        ['previous_panel_id'], ['id']
    )


def downgrade() -> None:
    # حذف ارتباط خارجی
    op.drop_constraint('fk_clients_previous_panel', 'clients', type_='foreignkey')
    
    # حذف فیلدهای اضافه شده به جدول panels
    op.drop_column('panels', 'server_specs')
    op.drop_column('panels', 'network_speed')
    op.drop_column('panels', 'is_premium')
    op.drop_column('panels', 'alternate_domain')
    op.drop_column('panels', 'datacenter')
    op.drop_column('panels', 'provider')
    op.drop_column('panels', 'geo_location')
    
    # حذف فیلدهای اضافه شده به جدول locations
    op.drop_column('locations', 'migration_remark_pattern')
    op.drop_column('locations', 'remark_pattern')
    
    # حذف جدول تاریخچه مهاجرت
    op.drop_table('client_migrations')
    
    # حذف فیلدهای اضافه شده به جدول clients
    op.drop_column('clients', 'migration_history')
    op.drop_column('clients', 'previous_panel_id')
    op.drop_column('clients', 'migration_count')
    op.drop_column('clients', 'custom_name')
    op.drop_column('clients', 'original_remark')
    op.drop_column('clients', 'original_client_uuid')
