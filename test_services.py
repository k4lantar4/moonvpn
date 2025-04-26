#!/usr/bin/env python3
"""
Simple test script to verify the refactored order and payment services.
"""
import asyncio
import logging
import sys
import os

# Add app directory to path to find modules
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test")

# Database URL - same as in the application
DATABASE_URL = "postgresql+asyncpg://moonvpn:moonvpn@db/moonvpn"

async def test_payment_service():
    """Test the payment service individually"""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from decimal import Decimal
    
    try:
        # Create engine and session
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Import service here to avoid circular imports
            from core.services.payment_service import PaymentService
            
            logger.info("Testing payment service...")
            payment_service = PaymentService(session)
            
            # Test wallet balance
            user_id = 1  # Ensure this user exists
            balance = await payment_service.get_user_balance(user_id)
            logger.info(f"✅ User {user_id} wallet balance: {balance}")
            
            # Test discount code validation (with a dummy code)
            discount_result = await payment_service.validate_and_apply_discount(
                code="TESTCODE",
                user_id=user_id,
                plan_id=1,
                original_amount=Decimal("100000")
            )
            logger.info(f"✅ Discount validation result: {discount_result[0]}, message: {discount_result[1]}")
            
            logger.info("✅ Payment service tests completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error testing payment service: {e}")
        return False

async def test_order_service():
    """Test the order service individually"""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from decimal import Decimal
    
    try:
        # Create engine and session
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Import here to avoid circular imports
            from core.services.order_service import OrderService
            from db.models.enums import OrderStatus
            
            logger.info("Testing order service...")
            order_service = OrderService(session)
            
            # Create a test order
            user_id = 1  # Ensure this user exists
            order = await order_service.create_order(
                user_id=user_id,
                plan_id=1,  # Ensure this plan exists
                location_name="هلند",
                amount=Decimal("50000"),
                status=OrderStatus.PENDING_RECEIPT
            )
            
            if order:
                logger.info(f"✅ Created test order with ID: {order.id}")
                
                # Get order by ID
                retrieved_order = await order_service.get_order_by_id(order.id)
                logger.info(f"✅ Retrieved order status: {retrieved_order.status}")
                
                # Get user orders
                user_orders = await order_service.get_user_orders(user_id, limit=5)
                logger.info(f"✅ Retrieved {len(user_orders)} orders for user {user_id}")
                
                # Rollback test changes
                await session.rollback()
                logger.info("✅ Test changes rolled back")
                return True
            else:
                logger.error("❌ Failed to create test order")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error testing order service: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting services tests...")
    
    # Test payment service
    payment_result = await test_payment_service()
    
    # Test order service
    order_result = await test_order_service()
    
    # Summary
    if payment_result and order_result:
        logger.info("🎉 All tests passed successfully!")
    else:
        logger.error("❌ Some tests failed.")

if __name__ == "__main__":
    asyncio.run(main())
