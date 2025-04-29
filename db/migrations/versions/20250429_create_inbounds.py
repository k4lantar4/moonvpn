"""create_inbounds

Revision ID: 20250429_create_inbounds
Revises: 20250429_create_admin_user
Create Date: 2025-04-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime
import json

# revision identifiers, used by Alembic.
revision = '20250429_create_inbounds'
down_revision = '20250429_create_admin_user'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create tables references
    inbound = table('inbound',
        column('id', sa.Integer),
        column('panel_id', sa.Integer),
        column('remote_id', sa.Integer),
        column('protocol', sa.String),
        column('tag', sa.String),
        column('port', sa.Integer),
        column('settings_json', sa.JSON),
        column('sniffing', sa.JSON),
        column('status', sa.String),
        column('max_clients', sa.Integer),
        column('last_synced', sa.DateTime),
        column('listen', sa.String),
        column('stream_settings', sa.JSON),
        column('allocate_settings', sa.JSON),
        column('receive_original_dest', sa.Boolean),
        column('allow_transparent', sa.Boolean),
        column('security_settings', sa.JSON),
        column('remark', sa.String)
    )

    # Common settings for all inbounds
    base_settings = {
        'clients': [],
        'decryption': 'none',
        'fallbacks': []
    }

    base_sniffing = {
        'enabled': True,
        'destOverride': ['http', 'tls', 'quic']
    }

    base_stream_settings = {
        'network': 'tcp',
        'security': 'tls',
        'tlsSettings': {
            'alpn': ['http/1.1'],
            'certificates': [{
                'certificateFile': '/root/cert.crt',
                'keyFile': '/root/private.key'
            }]
        }
    }

    # Insert inbounds for each panel
    inbounds_data = [
        # Panel DE-1 (Germany)
        {
            'id': 1,
            'panel_id': 1,
            'remote_id': 1,
            'protocol': 'vless',
            'tag': 'vless-tcp-tls',
            'port': 443,
            'settings_json': base_settings,
            'sniffing': base_sniffing,
            'status': 'ACTIVE',
            'max_clients': 1000,
            'last_synced': datetime.utcnow(),
            'listen': '0.0.0.0',
            'stream_settings': base_stream_settings,
            'allocate_settings': None,
            'receive_original_dest': False,
            'allow_transparent': False,
            'security_settings': None,
            'remark': 'Germany VLESS TCP'
        },
        # Panel NL-1 (Netherlands)
        {
            'id': 2,
            'panel_id': 2,
            'remote_id': 1,
            'protocol': 'vless',
            'tag': 'vless-tcp-tls',
            'port': 443,
            'settings_json': base_settings,
            'sniffing': base_sniffing,
            'status': 'ACTIVE',
            'max_clients': 1000,
            'last_synced': datetime.utcnow(),
            'listen': '0.0.0.0',
            'stream_settings': base_stream_settings,
            'allocate_settings': None,
            'receive_original_dest': False,
            'allow_transparent': False,
            'security_settings': None,
            'remark': 'Netherlands VLESS TCP'
        },
        # Panel FR-1 (France)
        {
            'id': 3,
            'panel_id': 3,
            'remote_id': 1,
            'protocol': 'vless',
            'tag': 'vless-tcp-tls',
            'port': 443,
            'settings_json': base_settings,
            'sniffing': base_sniffing,
            'status': 'ACTIVE',
            'max_clients': 1000,
            'last_synced': datetime.utcnow(),
            'listen': '0.0.0.0',
            'stream_settings': base_stream_settings,
            'allocate_settings': None,
            'receive_original_dest': False,
            'allow_transparent': False,
            'security_settings': None,
            'remark': 'France VLESS TCP'
        }
    ]

    op.bulk_insert(inbound, inbounds_data)

def downgrade() -> None:
    # Remove inbounds
    op.execute("DELETE FROM inbound WHERE id IN (1, 2, 3)") 