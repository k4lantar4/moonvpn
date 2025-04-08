"""add_panel_additional_fields

Revision ID: 5dd52fd73f6a
Revises: 16548e252372
Create Date: 2025-04-07 10:45:38.129315

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '5dd52fd73f6a'
down_revision = '16548e252372'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # افزودن فیلدهای اضافی به جدول panels برای مدیریت بهتر پنل‌ها
    op.add_column('panels', sa.Column('geo_location', sa.String(100), nullable=True))
    op.add_column('panels', sa.Column('provider', sa.String(100), nullable=True))
    op.add_column('panels', sa.Column('datacenter', sa.String(100), nullable=True))
    op.add_column('panels', sa.Column('alternate_domain', sa.String(255), nullable=True))
    op.add_column('panels', sa.Column('is_premium', sa.Boolean(), default=False))
    op.add_column('panels', sa.Column('network_speed', sa.String(50), nullable=True))
    op.add_column('panels', sa.Column('server_specs', sa.Text(), nullable=True))
    
    # به‌روزرسانی اطلاعات پنل‌های موجود
    op.execute(text("UPDATE panels SET geo_location = 'Frankfurt, Germany', provider = 'Hetzner', datacenter = 'Frankfurt DC1', network_speed = '1 Gbps' WHERE name = 'DE-1'"))
    op.execute(text("UPDATE panels SET geo_location = 'Amsterdam, Netherlands', provider = 'OVH', datacenter = 'Amsterdam DC2', network_speed = '1 Gbps' WHERE name = 'NL-1'"))
    
    # اضافه کردن یک تنظیم سیستمی برای ماکزیمم تعداد تغییر لوکیشن در روز
    op.execute(text("INSERT INTO settings (`key`, value, description, is_public, `group`) VALUES ('MAX_LOCATION_CHANGES_PER_DAY', '2', 'Maximum allowed location changes per day per user', 0, 'system')"))


def downgrade() -> None:
    # حذف فیلدهای اضافه شده از جدول panels
    op.drop_column('panels', 'server_specs')
    op.drop_column('panels', 'network_speed')
    op.drop_column('panels', 'is_premium')
    op.drop_column('panels', 'alternate_domain')
    op.drop_column('panels', 'datacenter')
    op.drop_column('panels', 'provider')
    op.drop_column('panels', 'geo_location')
