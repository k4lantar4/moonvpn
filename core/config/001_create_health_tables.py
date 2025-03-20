"""create health tables

Revision ID: 001
Revises: 
Create Date: 2024-03-19 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create health_checks table
    op.create_table(
        'health_checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('overall_status', sa.String(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('warning_count', sa.Integer(), nullable=False, default=0),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_health_checks_id'), 'health_checks', ['id'], unique=False)
    op.create_index(op.f('ix_health_checks_timestamp'), 'health_checks', ['timestamp'], unique=False)

    # Create health_status table
    op.create_table(
        'health_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('component', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('check_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['check_id'], ['health_checks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_health_status_id'), 'health_status', ['id'], unique=False)
    op.create_index(op.f('ix_health_status_component'), 'health_status', ['component'], unique=False)
    op.create_index(op.f('ix_health_status_timestamp'), 'health_status', ['timestamp'], unique=False)

    # Create recovery_actions table
    op.create_table(
        'recovery_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('component', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('health_status_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['health_status_id'], ['health_status.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_actions_id'), 'recovery_actions', ['id'], unique=False)
    op.create_index(op.f('ix_recovery_actions_component'), 'recovery_actions', ['component'], unique=False)
    op.create_index(op.f('ix_recovery_actions_timestamp'), 'recovery_actions', ['timestamp'], unique=False)
    op.create_index(op.f('ix_recovery_actions_status'), 'recovery_actions', ['status'], unique=False)

def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_recovery_actions_status'), table_name='recovery_actions')
    op.drop_index(op.f('ix_recovery_actions_timestamp'), table_name='recovery_actions')
    op.drop_index(op.f('ix_recovery_actions_component'), table_name='recovery_actions')
    op.drop_index(op.f('ix_recovery_actions_id'), table_name='recovery_actions')
    op.drop_index(op.f('ix_health_status_timestamp'), table_name='health_status')
    op.drop_index(op.f('ix_health_status_component'), table_name='health_status')
    op.drop_index(op.f('ix_health_status_id'), table_name='health_status')
    op.drop_index(op.f('ix_health_checks_timestamp'), table_name='health_checks')
    op.drop_index(op.f('ix_health_checks_id'), table_name='health_checks')

    # Drop tables
    op.drop_table('recovery_actions')
    op.drop_table('health_status')
    op.drop_table('health_checks') 