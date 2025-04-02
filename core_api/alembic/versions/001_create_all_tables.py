"""Create all initial tables with correct dependency order

Revision ID: 001
Revises: 
Create Date: 2025-04-02 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Create tables in order of dependency ###

    # --- Base Tables (no or few dependencies) ---
    op.create_table('locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        # ... other location columns ...
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for locations ...

    op.create_table('permissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        # ... other permission columns ...
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for permissions ...

    op.create_table('plan_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        # ... other plan_category columns ...
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for plan_categories ...

    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        # ... other role columns ...
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for roles ...

    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=True), # Made nullable based on later migration
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, server_default='0'),
        # ... other user columns ...
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        # sa.ForeignKeyConstraint(['referrer_user_id'], ['users.id'], ), # Avoid self-reference for simplicity now
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for users ...
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table('servers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        # ... other server columns ...
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for servers ...

    op.create_table('panels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=True),
        # ... other panel columns ...
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for panels ...

    op.create_table('plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('seller_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        # ... other plan columns ...
        sa.ForeignKeyConstraint(['category_id'], ['plan_categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for plans ...

    op.create_table('bank_cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('card_number', sa.String(length=20), nullable=False),
        # ... other bank_card columns ...
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for bank_cards ...

    # --- Association Tables ---
    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # --- Dependent Tables ---
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('panel_id', sa.Integer(), nullable=True),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('payment_authority', sa.String(length=50), nullable=True),
        sa.Column('payment_proof_img_url', sa.String(length=512), nullable=True),
        sa.Column('payment_proof_submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_verified_at', sa.DateTime(), nullable=True),
        sa.Column('payment_verification_admin_id', sa.Integer(), nullable=True),
        sa.Column('admin_note', sa.Text(), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['panel_id'], ['panels.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['payment_verification_admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for orders ...

    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('panel_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['panel_id'], ['panels.id'], ),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for subscriptions ...

    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('admin_note', sa.Text(), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for transactions ...

    op.create_table('payment_admin_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bank_card_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bank_card_id'], ['bank_cards.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for payment_admin_assignments ...

    op.create_table('payment_admin_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # ... indexes for payment_admin_metrics ...

    # --- Add Foreign Key Constraints Separately ---
    # Orders FKs
    op.create_foreign_key('fk_orders_admin_id', 'orders', 'users', ['admin_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_orders_panel_id', 'orders', 'panels', ['panel_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_orders_payment_verification_admin_id', 'orders', 'users', ['payment_verification_admin_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_orders_plan_id', 'orders', 'plans', ['plan_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_orders_user_id', 'orders', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_orders_subscription_id', 'orders', 'subscriptions', ['subscription_id'], ['id'], ondelete='SET NULL')
    
    # Subscriptions FKs
    op.create_foreign_key('fk_subscriptions_order_id', 'subscriptions', 'orders', ['order_id'], ['id'])
    op.create_foreign_key('fk_subscriptions_panel_id', 'subscriptions', 'panels', ['panel_id'], ['id'])
    op.create_foreign_key('fk_subscriptions_plan_id', 'subscriptions', 'plans', ['plan_id'], ['id'])
    op.create_foreign_key('fk_subscriptions_user_id', 'subscriptions', 'users', ['user_id'], ['id'])
    
    # Transactions FKs
    op.create_foreign_key('fk_transactions_admin_id', 'transactions', 'users', ['admin_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_transactions_order_id', 'transactions', 'orders', ['order_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_transactions_user_id', 'transactions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    
    # Payment Admin Assignments FKs
    op.create_foreign_key('fk_payment_admin_assignments_user_id', 'payment_admin_assignments', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_payment_admin_assignments_bank_card_id', 'payment_admin_assignments', 'bank_cards', ['bank_card_id'], ['id'], ondelete='SET NULL')
    
    # Payment Admin Metrics FKs
    op.create_foreign_key('fk_payment_admin_metrics_user_id', 'payment_admin_metrics', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###

def downgrade() -> None:
    # ### Drop constraints and tables in reverse order ###
    # Drop FKs first
    op.drop_constraint('fk_payment_admin_metrics_user_id', 'payment_admin_metrics', type_='foreignkey')
    op.drop_constraint('fk_payment_admin_assignments_bank_card_id', 'payment_admin_assignments', type_='foreignkey')
    op.drop_constraint('fk_payment_admin_assignments_user_id', 'payment_admin_assignments', type_='foreignkey')
    op.drop_constraint('fk_transactions_user_id', 'transactions', type_='foreignkey')
    op.drop_constraint('fk_transactions_order_id', 'transactions', type_='foreignkey')
    op.drop_constraint('fk_transactions_admin_id', 'transactions', type_='foreignkey')
    op.drop_constraint('fk_subscriptions_user_id', 'subscriptions', type_='foreignkey')
    op.drop_constraint('fk_subscriptions_plan_id', 'subscriptions', type_='foreignkey')
    op.drop_constraint('fk_subscriptions_panel_id', 'subscriptions', type_='foreignkey')
    op.drop_constraint('fk_subscriptions_order_id', 'subscriptions', type_='foreignkey')
    op.drop_constraint('fk_orders_subscription_id', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_user_id', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_plan_id', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_payment_verification_admin_id', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_panel_id', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_admin_id', 'orders', type_='foreignkey')
    
    # Drop tables (same order as before, but now FKs are gone)
    # ... drop indexes for payment_admin_metrics ...
    op.drop_table('payment_admin_metrics')
    # ... drop indexes for payment_admin_assignments ...
    op.drop_table('payment_admin_assignments')
    # ... drop indexes for transactions ...
    op.drop_table('transactions')
    # ... drop indexes for subscriptions ...
    op.drop_table('subscriptions')
    # ... drop indexes for orders ...
    op.drop_table('orders')
    op.drop_table('role_permissions')
    # ... drop indexes for bank_cards ...
    op.drop_table('bank_cards')
    # ... drop indexes for plans ...
    op.drop_table('plans')
    # ... drop indexes for panels ...
    op.drop_table('panels')
    # ... drop indexes for servers ...
    op.drop_table('servers')
    # ... drop indexes for users ...
    op.drop_table('users')
    # ... drop indexes for roles ...
    op.drop_table('roles')
    # ... drop indexes for plan_categories ...
    op.drop_table('plan_categories')
    # ... drop indexes for permissions ...
    op.drop_table('permissions')
    # ... drop indexes for locations ...
    op.drop_table('locations')
    # ### end Alembic commands ### 