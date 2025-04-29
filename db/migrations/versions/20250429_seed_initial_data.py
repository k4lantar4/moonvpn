"""seed_initial_data

Revision ID: 20250429_seed_initial_data
Revises: 394eae8c93d8
Create Date: 2025-04-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime, timedelta
from decimal import Decimal

# revision identifiers, used by Alembic.
revision = '20250429_seed_initial_data'
down_revision = '394eae8c93d8'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create tables references
    settings = table('settings',
        column('key', sa.String),
        column('value', sa.Text),
        column('type', sa.String),
        column('scope', sa.String),
        column('description', sa.Text)
    )

    plans = table('plans',
        column('id', sa.Integer),
        column('name', sa.String),
        column('description', sa.Text),
        column('traffic_gb', sa.Integer),
        column('duration_days', sa.Integer),
        column('price', sa.DECIMAL),
        column('available_locations', sa.JSON),
        column('status', sa.String),
        column('created_at', sa.DateTime)
    )

    panels = table('panels',
        column('id', sa.Integer),
        column('name', sa.String),
        column('location_name', sa.String),
        column('url', sa.Text),
        column('username', sa.String),
        column('password', sa.String),
        column('type', sa.String),
        column('status', sa.String)
    )

    # Insert initial settings
    op.bulk_insert(settings, [
        {
            'key': 'maintenance_mode',
            'value': 'false',
            'type': 'boolean',
            'scope': 'system',
            'description': 'Whether the system is in maintenance mode'
        },
        {
            'key': 'test_account_duration',
            'value': '1',
            'type': 'integer',
            'scope': 'system',
            'description': 'Duration of test accounts in days'
        },
        {
            'key': 'test_account_traffic',
            'value': '1',
            'type': 'integer',
            'scope': 'system',
            'description': 'Traffic limit for test accounts in GB'
        }
    ])

    # Insert initial plans
    op.bulk_insert(plans, [
        {
            'id': 1,
            'name': 'پلن برنزی',
            'description': 'پلن مناسب برای استفاده روزانه',
            'traffic_gb': 30,
            'duration_days': 30,
            'price': Decimal('150000.00'),
            'available_locations': ['germany', 'netherlands'],
            'status': 'ACTIVE',
            'created_at': datetime.utcnow()
        },
        {
            'id': 2,
            'name': 'پلن نقره‌ای',
            'description': 'پلن مناسب برای استفاده خانواده',
            'traffic_gb': 60,
            'duration_days': 30,
            'price': Decimal('250000.00'),
            'available_locations': ['germany', 'netherlands', 'france'],
            'status': 'ACTIVE',
            'created_at': datetime.utcnow()
        },
        {
            'id': 3,
            'name': 'پلن طلایی',
            'description': 'پلن نامحدود برای استفاده حرفه‌ای',
            'traffic_gb': 100,
            'duration_days': 30,
            'price': Decimal('350000.00'),
            'available_locations': ['germany', 'netherlands', 'france', 'united_states'],
            'status': 'ACTIVE',
            'created_at': datetime.utcnow()
        }
    ])

    # Insert sample panels
    op.bulk_insert(panels, [
        {
            'id': 1,
            'name': 'Panel DE-1',
            'location_name': 'germany',
            'url': 'https://de1.example.com:8443',
            'username': 'admin',
            'password': 'changeme123',
            'type': 'XUI',
            'status': 'ACTIVE'
        },
        {
            'id': 2,
            'name': 'Panel NL-1',
            'location_name': 'netherlands',
            'url': 'https://nl1.example.com:8443',
            'username': 'admin',
            'password': 'changeme123',
            'type': 'XUI',
            'status': 'ACTIVE'
        },
        {
            'id': 3,
            'name': 'Panel FR-1',
            'location_name': 'france',
            'url': 'https://fr1.example.com:8443',
            'username': 'admin',
            'password': 'changeme123',
            'type': 'XUI',
            'status': 'ACTIVE'
        }
    ])

def downgrade() -> None:
    # Remove data in reverse order
    op.execute("DELETE FROM panels WHERE id IN (1, 2, 3)")
    op.execute("DELETE FROM plans WHERE id IN (1, 2, 3)")
    op.execute("DELETE FROM settings WHERE key IN ('maintenance_mode', 'test_account_duration', 'test_account_traffic')") 