#!/usr/bin/env python
"""
Script to test the OrderService and PaymentService refactoring.
"""

import asyncio
import logging
import sys
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("test_order_service")

# Create a test async database session
async def get_test_session():
    from db.connection import DATABASE_URL
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

async def test_order_purchase():
    """Test the order purchase process."""
    # Get a database session
    session_gen = get_test_session()
    session = await session_gen.__anext__()
    
    try:
        from core.services.order_service import OrderService
        
        # Initialize order service
        order_service = OrderService(session)
        
        # Test parameters
        user_id = 1  # Make sure this user exists and has sufficient wallet balance
        plan_id = 1  # Make sure this plan exists
        location_name = "هلند"  # Make sure this location exists and has available panels
        
        logger.info(f"Testing order purchase for user {user_id}, plan {plan_id}, location {location_name}")
        
        # Process order purchase with wallet payment
        success, message, result_data = await order_service.process_order_purchase(
            user_id=user_id,
            plan_id=plan_id,
            location_name=location_name,
            payment_method="wallet",
            discount_code=None,
            send_notifications=True
        )
        
        logger.info(f"Order purchase result: {success}")
        logger.info(f"Message: {message}")
        
        if success:
            logger.info(f"Order ID: {result_data['order'].id}")
            if result_data['transaction']:
                logger.info(f"Transaction ID: {result_data['transaction'].id}")
            if result_data['account']:
                logger.info(f"Account ID: {result_data['account'].id}")
        else:
            logger.error(f"Order purchase failed: {message}")
            
        # Commit the transaction if successful
        if success:
            await session.commit()
            logger.info("Transaction committed successfully")
        else:
            await session.rollback()
            logger.info("Transaction rolled back")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in test_order_purchase: {e}", exc_info=True)
        await session.rollback()
        logger.info("Transaction rolled back due to exception")
        return False
    finally:
        await session.close()

async def test_receipt_approval():
    """Test the receipt approval process."""
    # Get a database session
    session_gen = get_test_session()
    session = await session_gen.__anext__()
    
    try:
        from core.services.order_service import OrderService
        from db.models.enums import OrderStatus
        
        # Initialize order service
        order_service = OrderService(session)
        
        # Create a test order with PENDING_RECEIPT status
        user_id = 1  # Make sure this user exists
        plan_id = 1  # Make sure this plan exists
        location_name = "هلند"  # Make sure this location exists
        amount = Decimal("50000")
        admin_id = 1  # Admin user ID for approval
        
        logger.info(f"Creating test order for receipt approval...")
        
        order = await order_service.create_order(
            user_id=user_id,
            plan_id=plan_id,
            location_name=location_name,
            amount=amount,
            status=OrderStatus.PENDING_RECEIPT
        )
        
        if not order:
            logger.error("Failed to create test order")
            await session.rollback()
            return False
        
        logger.info(f"Created test order ID: {order.id}")
        
        # Process receipt approval
        success, message, account = await order_service.process_receipt_approval(
            order_id=order.id,
            approved_by_user_id=admin_id
        )
        
        logger.info(f"Receipt approval result: {success}")
        logger.info(f"Message: {message}")
        
        if success and account:
            logger.info(f"Account ID: {account.id}")
        else:
            logger.error(f"Receipt approval failed: {message}")
        
        # Commit the transaction if successful
        if success:
            await session.commit()
            logger.info("Transaction committed successfully")
        else:
            await session.rollback()
            logger.info("Transaction rolled back")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in test_receipt_approval: {e}", exc_info=True)
        await session.rollback()
        logger.info("Transaction rolled back due to exception")
        return False
    finally:
        await session.close()

async def main():
    """Run the tests."""
    logger.info("Starting OrderService tests...")
    
    # Test the wallet payment process
    wallet_result = await test_order_purchase()
    logger.info(f"Wallet payment test: {'✅ PASSED' if wallet_result else '❌ FAILED'}")
    
    # Test the receipt approval process
    receipt_result = await test_receipt_approval()
    logger.info(f"Receipt approval test: {'✅ PASSED' if receipt_result else '❌ FAILED'}")
    
    logger.info("All tests completed.")
    
if __name__ == "__main__":
    asyncio.run(main()) 