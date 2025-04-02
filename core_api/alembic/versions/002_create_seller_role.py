"""Add seller role and migrate eligible users

Revision ID: 002
Revises: 001
Create Date: 2024-04-02 14:00:00.000000

"""
from typing import Sequence, Union
from decimal import Decimal
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import select, update, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

Base = declarative_base()

class Role(Base):
    __tablename__ = "roles"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True)
    role_id = sa.Column(sa.Integer, sa.ForeignKey("roles.id"), nullable=False)
    wallet_balance = sa.Column(sa.DECIMAL(10, 2), nullable=False, default=0.00)


def upgrade() -> None:
    # Connect to database
    conn = op.get_bind()
    session = Session(bind=conn)
    
    # Check if seller role already exists
    seller_role = session.query(Role).filter(Role.name == 'seller').first()
    
    # If seller role doesn't exist, create it
    if not seller_role:
        seller_role = Role(
            name='seller',
            description='Seller role with special pricing and permissions',
            created_at=datetime.utcnow()
        )
        session.add(seller_role)
        session.flush() # Make sure to get the ID
        seller_role_id = seller_role.id
        
        print(f"Created seller role with ID: {seller_role_id}")
    else:
        seller_role_id = seller_role.id
        print(f"Seller role already exists with ID: {seller_role_id}")
    
    # Create the trigger for automatic upgrading users to seller role when they reach the threshold
    # This is SQL that runs directly against the database
    trigger_sql = """
    CREATE TRIGGER after_wallet_update
    AFTER UPDATE ON users
    FOR EACH ROW
    BEGIN
        DECLARE seller_role_id INT;
        DECLARE threshold DECIMAL(10,2);
        
        -- Set threshold from environment or use default
        SET threshold = 1000000.00;
        
        -- Find seller role ID
        SELECT id INTO seller_role_id FROM roles WHERE name = 'seller' LIMIT 1;
        
        -- If wallet balance increased and now meets threshold, and user isn't already a seller
        IF NEW.wallet_balance >= threshold AND OLD.wallet_balance < threshold 
           AND NEW.role_id != seller_role_id THEN
            -- Update user to seller role
            UPDATE users SET role_id = seller_role_id WHERE id = NEW.id;
        END IF;
    END;
    """
    
    # Try to create the trigger, but don't stop migration if it fails
    try:
        conn.execute(text(trigger_sql))
        print("Created trigger for automatic user role upgrade")
    except Exception as e:
        print(f"Warning: Could not create trigger: {e}")
    
    # Migrate eligible users to seller role
    # Get threshold from environment vars or use default
    threshold = Decimal('1000000.00')  # 1M Toman default
    
    # Get user IDs who have high balance but aren't sellers yet
    eligible_users = session.query(User).filter(
        User.wallet_balance >= threshold,
        User.role_id != seller_role_id
    ).all()
    
    # Update their role
    for user in eligible_users:
        user.role_id = seller_role_id
        print(f"Upgrading user ID {user.id} to seller role (balance: {user.wallet_balance})")
    
    session.commit()
    print(f"Migration complete. Total users upgraded: {len(eligible_users)}")


def downgrade() -> None:
    """
    This downgrade doesn't remove the seller role since it might be in use.
    It only removes the automatic trigger.
    """
    conn = op.get_bind()
    
    # Try to drop the trigger
    try:
        conn.execute(text("DROP TRIGGER IF EXISTS after_wallet_update"))
        print("Removed trigger for automatic user role upgrade")
    except Exception as e:
        print(f"Warning: Could not drop trigger: {e}") 