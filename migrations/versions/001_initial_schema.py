"""Initial database schema

Revision ID: 001_initial_schema
Create Date: 2025-04-07 09:35:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # --- Users and Roles ---
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Enum('ADMIN', 'SELLER', 'USER', name='rolename'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('can_manage_panels', sa.Boolean(), default=False),
        sa.Column('can_manage_users', sa.Boolean(), default=False),
        sa.Column('can_manage_plans', sa.Boolean(), default=False),
        sa.Column('can_approve_payments', sa.Boolean(), default=False),
        sa.Column('can_broadcast', sa.Boolean(), default=False),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('is_seller', sa.Boolean(), default=False),
        sa.Column('discount_percent', sa.Integer(), default=0),
        sa.Column('commission_percent', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.DECIMAL(10, 2), nullable=False, default=0.00),
        sa.Column('is_banned', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('referral_code', sa.String(20), nullable=True),
        sa.Column('referred_by_id', sa.Integer(), nullable=True),
        sa.Column('lang', sa.String(10), default='fa'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('login_ip', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('phone'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('referral_code'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.ForeignKeyConstraint(['referred_by_id'], ['users.id'])
    )

    # --- Locations and Panels ---
    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('flag', sa.String(10), nullable=True),
        sa.Column('country_code', sa.String(2), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_inbound_id', sa.Integer(), nullable=True),
        sa.Column('protocols_supported', sa.String(100), nullable=True),
        sa.Column('inbound_tag_pattern', sa.String(100), nullable=True),
        sa.Column('default_remark_prefix', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'panels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('url', sa.String(255), nullable=False),
        sa.Column('api_path', sa.String(100), default='/panel/api/'),
        sa.Column('login_path', sa.String(50), default='/login'),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('panel_type', sa.Enum('3X-UI', 'MARZBAN', 'SANAEI', 'ALIREZA', 'VAXILU', 'XRAY', name='paneltype'), default='3X-UI'),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('server_ip', sa.String(45), nullable=True),
        sa.Column('server_type', sa.String(50), default='vps'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_healthy', sa.Boolean(), default=False),
        sa.Column('last_check', sa.DateTime(), nullable=True),
        sa.Column('status_message', sa.String(255), nullable=True),
        sa.Column('max_clients', sa.Integer(), default=500),
        sa.Column('current_clients', sa.Integer(), default=0),
        sa.Column('traffic_limit', sa.BigInteger(), nullable=True),
        sa.Column('traffic_used', sa.BigInteger(), default=0),
        sa.Column('api_token', sa.String(255), nullable=True),
        sa.Column('api_token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'])
    )
    
    # --- Panel Inbounds ---
    op.create_table(
        'panel_inbounds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('panel_id', sa.Integer(), nullable=False),
        sa.Column('inbound_id', sa.Integer(), nullable=False),
        sa.Column('tag', sa.String(100), nullable=True),
        sa.Column('protocol', sa.Enum('VMESS', 'VLESS', 'TROJAN', 'SHADOWSOCKS', name='protocoltype'), nullable=False),
        sa.Column('network', sa.String(50), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('tls', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('remark', sa.String(255), nullable=True),
        sa.Column('client_stats', sa.Text(), nullable=True),
        sa.Column('settings', sa.Text(), nullable=True),
        sa.Column('stream_settings', sa.Text(), nullable=True),
        sa.Column('sniffing', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('panel_id', 'inbound_id'),
        sa.ForeignKeyConstraint(['panel_id'], ['panels.id'])
    )

    # --- Plans and Categories ---
    op.create_table(
        'plan_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sorting_order', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('traffic', sa.BigInteger(), nullable=False),
        sa.Column('days', sa.Integer(), nullable=False),
        sa.Column('price', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('features', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('max_clients', sa.Integer(), nullable=True),
        sa.Column('protocols', sa.String(255), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('sorting_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['category_id'], ['plan_categories.id'])
    )

    # --- Orders and Payments ---
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('discount_amount', sa.DECIMAL(10, 2), default=0),
        sa.Column('final_amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', 'CANCELLED', name='orderstatus'), default='PENDING'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'])
    )

    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('payment_gateway_id', sa.String(100), nullable=True),
        sa.Column('card_number', sa.String(20), nullable=True),
        sa.Column('tracking_code', sa.String(100), nullable=True),
        sa.Column('receipt_image', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'VERIFIED', 'REJECTED', name='paymentstatus'), default='PENDING'),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'])
    )

    # --- Discounts ---
    op.create_table(
        'discount_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('discount_type', sa.Enum('FIXED', 'PERCENTAGE', name='discounttype'), default='PERCENTAGE'),
        sa.Column('discount_value', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), default=0),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'])
    )

    # --- Clients and Related Tables ---
    op.create_table(
        'client_id_sequences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('last_id', sa.Integer(), default=0),
        sa.Column('prefix', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'])
    )

    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('panel_id', sa.Integer(), nullable=False),
        sa.Column('panel_inbound_id', sa.Integer(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('client_uuid', sa.String(36), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('remark', sa.String(255), nullable=False),
        sa.Column('expire_date', sa.DateTime(), nullable=False),
        sa.Column('traffic', sa.BigInteger(), nullable=False),
        sa.Column('used_traffic', sa.BigInteger(), default=0),
        sa.Column('status', sa.Enum('ACTIVE', 'EXPIRED', 'DISABLED', 'FROZEN', name='clientstatus'), default='ACTIVE'),
        sa.Column('protocol', sa.Enum('VMESS', 'VLESS', 'TROJAN', 'SHADOWSOCKS', name='protocoltype'), nullable=False),
        sa.Column('network', sa.String(20), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('tls', sa.Boolean(), default=False),
        sa.Column('security', sa.String(20), nullable=True),
        sa.Column('config_json', sa.Text(), nullable=True),
        sa.Column('subscription_url', sa.String(255), nullable=True),
        sa.Column('qrcode_url', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('freeze_start', sa.DateTime(), nullable=True),
        sa.Column('freeze_end', sa.DateTime(), nullable=True),
        sa.Column('is_trial', sa.Boolean(), default=False),
        sa.Column('auto_renew', sa.Boolean(), default=False),
        sa.Column('last_online', sa.DateTime(), nullable=True),
        sa.Column('last_notified', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['panel_id'], ['panels.id']),
        sa.ForeignKeyConstraint(['panel_inbound_id'], ['panel_inbounds.id']),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'])
    )

    # --- Other Tables ---
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('type', sa.Enum('DEPOSIT', 'WITHDRAW', 'PURCHASE', 'REFUND', 'COMMISSION', name='transactiontype'), nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('balance_after', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'])
    )

    op.create_table(
        'bank_cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bank_name', sa.String(100), nullable=False),
        sa.Column('card_number', sa.String(20), nullable=False),
        sa.Column('account_number', sa.String(30), nullable=True),
        sa.Column('owner_name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('rotation_priority', sa.Integer(), default=0),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('daily_limit', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('monthly_limit', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'notification_channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('channel_id', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('notification_types', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('group', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )

    op.create_table(
        'panel_health_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('panel_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('checked_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['panel_id'], ['panels.id'])
    )

def downgrade():
    # Drop tables in reverse order to handle dependencies
    op.drop_table('panel_health_checks')
    op.drop_table('settings')
    op.drop_table('notification_channels')
    op.drop_table('bank_cards')
    op.drop_table('transactions')
    op.drop_table('clients')
    op.drop_table('client_id_sequences')
    op.drop_table('discount_codes')
    op.drop_table('payments')
    op.drop_table('orders')
    op.drop_table('plans')
    op.drop_table('plan_categories')
    op.drop_table('panel_inbounds')
    op.drop_table('panels')
    op.drop_table('locations')
    op.drop_table('users')
    op.drop_table('roles')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS rolename')
    op.execute('DROP TYPE IF EXISTS paneltype')
    op.execute('DROP TYPE IF EXISTS protocoltype')
    op.execute('DROP TYPE IF EXISTS orderstatus')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS discounttype')
    op.execute('DROP TYPE IF EXISTS clientstatus')
    op.execute('DROP TYPE IF EXISTS transactiontype') 