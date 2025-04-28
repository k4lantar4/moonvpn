#!/usr/bin/env python
"""
Test script for receipt approval system.
This script tests the receipt approval functionality by:
1. Creating a test receipt in PENDING status
2. Approving the receipt using ReceiptService
3. Verifying the status change in the database
"""

import asyncio
import logging
import sys
import datetime
import random
import string
from decimal import Decimal

# Add the project root directory to Python path
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from db.models import Base
from db.models.receipt_log import ReceiptLog, ReceiptStatus
from db.models.transaction import Transaction, TransactionStatus, TransactionType
from db.models.user import User, UserRole, UserStatus
from db.models.bank_card import BankCard
from db.repositories.receipt_log_repository import ReceiptLogRepository
from db.repositories.transaction_repo import TransactionRepository
from core.services.user_service import UserService
from core.services.receipt_service import ReceiptService
import core.settings as settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Generate random tracking code for receipt
def generate_tracking_code(length=8):
    """Generate a random tracking code for the test receipt."""
    letters = string.ascii_uppercase
    return 'TEST-' + ''.join(random.choice(letters) for _ in range(length))

async def init_db():
    """Initialize database connection."""
    database_url = settings.DATABASE_URL
    
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    return async_session

async def get_first_bank_card(session):
    """Get the first available bank card for testing."""
    query = select(BankCard).limit(1)
    result = await session.execute(query)
    return result.scalar_one_or_none()

async def test_receipt_approval():
    """
    Test the receipt approval system.
    
    1. Create a test user if doesn't exist
    2. Create a test bank card ID
    3. Create a pending receipt
    4. Approve the receipt
    5. Verify the receipt status changed to APPROVED
    """
    logger.info("Starting receipt approval test...")
    
    # Initialize database session
    session_factory = await init_db()
    
    async with session_factory() as session:
        # Step 1: Create a test admin user
        user_service = UserService(session)
        test_user_id = 12345  # Example user ID
        admin_user_id = 54321  # Example admin ID
        
        # Check if test user exists
        test_user = await user_service.get_user_by_telegram_id(test_user_id)
        if not test_user:
            logger.info(f"Creating test user with ID {test_user_id}")
            test_user = await user_service.create_user(
                telegram_id=test_user_id,
                username="test_user",
                first_name="Test",
                last_name="User",
                role=UserRole.USER
            )
        
        # Check if admin user exists
        admin_user = await user_service.get_user_by_telegram_id(admin_user_id)
        if not admin_user:
            logger.info(f"Creating test admin with ID {admin_user_id}")
            admin_user = await user_service.create_user(
                telegram_id=admin_user_id,
                username="test_admin",
                first_name="Test",
                last_name="Admin",
                role=UserRole.ADMIN
            )
            
        # Get a bank card for testing
        bank_card = await get_first_bank_card(session)
        if not bank_card:
            logger.error("No bank card found for testing. Please create at least one bank card in the database.")
            logger.info("Creating a test bank card...")
            
            # Create a test bank card
            bank_card = BankCard(
                card_number="6037991234567890",
                holder_name="Test Card",
                bank_name="Test Bank",
                is_active=True,
                rotation_policy="MANUAL",
                admin_user_id=admin_user.id,
                created_at=datetime.datetime.now(datetime.UTC)
            )
            session.add(bank_card)
            await session.flush()
            
        logger.info(f"Using bank card ID {bank_card.id} for testing.")
        
        # Step 2: Create a test transaction
        transaction_repo = TransactionRepository(session)
        
        # Create a unique tracking code for transaction
        transaction_tracking_code = f"TEST-TRX-{random.randint(10000, 99999)}"
        
        # Create a new transaction
        test_transaction = Transaction(
            user_id=test_user.id,
            amount=Decimal('100000.00'),  # 100,000 تومان
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            gateway="CARD_TO_CARD",
            tracking_code=transaction_tracking_code,
            created_at=datetime.datetime.now(datetime.UTC)
        )
        session.add(test_transaction)
        await session.flush()
        logger.info(f"Created test transaction with ID {test_transaction.id}")
        
        # Step 3: Create a test receipt
        receipt_repo = ReceiptLogRepository(session)
        
        # Create a unique tracking code for receipt
        receipt_tracking_code = generate_tracking_code()
        
        # Create the test receipt
        test_receipt = await receipt_repo.create_receipt_log(
            user_id=test_user.id,
            card_id=bank_card.id,
            amount=Decimal('100000.00'),
            status=ReceiptStatus.PENDING,
            text_reference="این یک رسید تست است برای آزمایش سیستم تایید رسید",
            photo_file_id=None,  # No photo for test
            transaction_id=test_transaction.id,
            tracking_code=receipt_tracking_code,
            submitted_at=datetime.datetime.now(datetime.UTC)
        )
        await session.commit()
        
        logger.info(f"Created test receipt with ID {test_receipt.id} and tracking code {receipt_tracking_code}")
        
        # Step 4: Approve the receipt using ReceiptService in a new session
        async with session_factory() as approval_session:
            receipt_service = ReceiptService(approval_session)
            
            try:
                logger.info(f"Approving receipt {test_receipt.id}...")
                approved_receipt = await receipt_service.approve_receipt(
                    receipt_id=test_receipt.id,
                    admin_id=admin_user.id
                )
                
                if approved_receipt:
                    logger.info(f"✅ Receipt successfully approved. New status: {approved_receipt.status}")
                    
                    # Fetch the transaction to verify it was updated too
                    updated_transaction = await transaction_repo.get_by_id(test_transaction.id)
                    logger.info(f"Transaction status: {updated_transaction.status}")
                    
                    # Provide test results
                    logger.info("🧪 Test Results:")
                    logger.info(f"  - Receipt ID: {approved_receipt.id}")
                    logger.info(f"  - Receipt Status: {approved_receipt.status}")
                    logger.info(f"  - Transaction Status: {updated_transaction.status}")
                    logger.info(f"  - Admin ID: {approved_receipt.admin_id}")
                    logger.info(f"  - Response Time: {approved_receipt.responded_at}")
                    
                    if approved_receipt.status == ReceiptStatus.APPROVED and updated_transaction.status == TransactionStatus.SUCCESS:
                        logger.info("✅ TEST PASSED: Receipt approval workflow works correctly!")
                    else:
                        logger.error("❌ TEST FAILED: Receipt/transaction status not updated correctly!")
                else:
                    logger.error("❌ Failed to approve receipt. Receipt service returned None.")
            except Exception as e:
                logger.error(f"Error during approval process: {e}", exc_info=True)
    
    logger.info("Receipt approval test completed.")

if __name__ == "__main__":
    asyncio.run(test_receipt_approval())