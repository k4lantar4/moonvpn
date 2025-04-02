import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union
from sqlalchemy.orm import Session
import uuid
from decimal import Decimal

from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.panel import Panel
from app.models.plan import Plan
from app.utils.sync_panel_client import SyncPanelClient, PanelClientError
from app import crud
from app.services.subscription_service import SubscriptionService

# Configure logger
logger = logging.getLogger(__name__)


class OrderProcessingError(Exception):
    """Custom exception for order processing errors."""
    pass


class OrderService:
    """
    Service for managing orders and related operations.
    """
    
    @staticmethod
    def create_order(
        db: Session,
        user_id: int,
        plan_id: int,
        amount: Decimal,
        discount_amount: Decimal = Decimal('0.00'),
        discount_code: Optional[str] = None,
        panel_id: Optional[int] = None,
        config_protocol: Optional[str] = None,
        config_days: Optional[int] = None,
        config_traffic_gb: Optional[int] = None,
        config_details: Optional[Dict[str, Any]] = None,
        admin_note: Optional[str] = None,
    ) -> Order:
        """
        Create a new order for a user.
        
        Args:
            db: Database session
            user_id: ID of the user placing the order
            plan_id: ID of the plan being ordered
            amount: Original price (determined by endpoint based on role)
            discount_amount: Discount amount (determined by endpoint)
            discount_code: Discount code used
            panel_id: Optional panel ID for this order
            config_protocol: Optional protocol override
            config_days: Optional duration override
            config_traffic_gb: Optional traffic limit override
            config_details: Optional additional configuration
            admin_note: Optional note from admin
            
        Returns:
            Created Order object
            
        Raises:
            ValueError: If invalid parameters are provided
        """
        # Get the plan
        plan = crud.plan.get(db, id=plan_id)
        if not plan:
            raise ValueError(f"Plan with ID {plan_id} not found")
        
        # Validate and use plan values as defaults if not provided
        if config_days is None:
            config_days = plan.duration_days
        
        if config_traffic_gb is None:
            config_traffic_gb = plan.traffic_limit_gb
            
        # Calculate final amount (using Decimal directly)
        final_amount = amount - discount_amount
        if final_amount < Decimal('0.00'):
            final_amount = Decimal('0.00')
            
        # Create order using CRUD
        order_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "panel_id": panel_id,
            "amount": amount,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
            "discount_code": discount_code,
            "config_protocol": config_protocol,
            "config_days": config_days,
            "config_traffic_gb": config_traffic_gb,
            "config_details": config_details,
            "admin_note": admin_note,
            "status": OrderStatus.PENDING
        }
        
        # Create the order
        return crud.order.create(db, obj_in=order_data)
    
    @staticmethod
    def process_payment(
        db: Session,
        order_id: int,
        payment_method: str,
        payment_reference: str,
        admin_id: Optional[int] = None,
        admin_note: Optional[str] = None
    ) -> Order:
        """
        Process payment for an order.
        
        Args:
            db: Database session
            order_id: ID of the order to process
            payment_method: Payment method used
            payment_reference: Payment reference or transaction ID
            admin_id: ID of admin processing the payment
            admin_note: Optional note from admin
            
        Returns:
            Updated Order object
            
        Raises:
            OrderProcessingError: If order cannot be processed
        """
        # Get the order
        order = crud.order.get(db, id=order_id)
        if not order:
            raise OrderProcessingError(f"Order with ID {order_id} not found")
        
        # Check if order can be processed
        if order.status != OrderStatus.PENDING:
            raise OrderProcessingError(
                f"Order is in state {order.status.value}, cannot process payment"
            )
        
        # Mark as paid
        return crud.order.process_payment(
            db,
            order_id=order_id,
            payment_method=payment_method,
            payment_reference=payment_reference,
            admin_id=admin_id,
            admin_note=admin_note
        )
    
    @staticmethod
    def create_client_on_panel(
        db: Session,
        order_id: int,
        admin_id: Optional[int] = None,
        admin_note: Optional[str] = None,
        client_uuid: Optional[str] = None,  # If None, will be generated
        panel_id: Optional[int] = None  # If None, will use order's panel_id or auto-select
    ) -> Tuple[Order, Dict[str, Any]]:
        """
        Create a client on the panel for a paid order.
        
        Args:
            db: Database session
            order_id: ID of the order to process
            admin_id: ID of admin confirming the order
            admin_note: Optional note from admin
            client_uuid: Optional predefined UUID for client
            panel_id: Optional panel ID override
            
        Returns:
            Tuple of (updated Order, client_info)
            
        Raises:
            OrderProcessingError: If client creation fails
        """
        # Get the order
        order = crud.order.get(db, id=order_id)
        if not order:
            raise OrderProcessingError(f"Order with ID {order_id} not found")
        
        # Check if order can be processed
        if order.status != OrderStatus.PAID:
            raise OrderProcessingError(
                f"Order is in state {order.status.value}, expected PAID"
            )
        
        # Get the panel
        if panel_id is None:
            if order.panel_id:
                panel_id = order.panel_id
            else:
                # Auto-select a panel
                panels = crud.panel.get_active_panels(db)
                if not panels:
                    raise OrderProcessingError("No active panels available")
                # TODO: Implement more sophisticated panel selection logic
                panel_id = panels[0].id
        
        panel = crud.panel.get(db, id=panel_id)
        if not panel:
            raise OrderProcessingError(f"Panel with ID {panel_id} not found")
        
        # Get the user
        user = crud.user.get(db, id=order.user_id)
        if not user:
            raise OrderProcessingError(f"User with ID {order.user_id} not found")
        
        # Get the plan
        plan = crud.plan.get(db, id=order.plan_id)
        if not plan:
            raise OrderProcessingError(f"Plan with ID {order.plan_id} not found")
        
        # Generate client UUID if not provided
        if not client_uuid:
            client_uuid = str(uuid.uuid4())
        
        # Generate client email/remark from username or email + random suffix
        # This should be a unique identifier for the client on the panel
        client_email = ""
        if user.email:
            client_email = user.email
        elif user.username:
            client_email = f"{user.username}@moonvpn.local"
        else:
            # Use user ID if neither email nor username are available
            client_email = f"user{user.id}@moonvpn.local"
        
        # Add order ID and timestamp to make it unique
        timestamp = int(datetime.utcnow().timestamp())
        client_email = f"{client_email.split('@')[0]}_{order_id}_{timestamp}@{client_email.split('@')[1]}"
        
        # Get configuration from order or fall back to plan defaults
        traffic_gb = order.config_traffic_gb if order.config_traffic_gb else plan.traffic_limit_gb
        expire_days = order.config_days if order.config_days else plan.duration_days
        
        # Calculate expiry date
        expires_at = datetime.utcnow() + timedelta(days=expire_days)
        
        try:
            # Connect to panel and add client
            with SyncPanelClient(panel.url, panel.admin_username, panel.admin_password) as client:
                # Get inbounds
                inbounds = client.get_inbounds()
                if not inbounds:
                    raise OrderProcessingError("No inbounds available on the panel")
                
                # Select inbound based on protocol or other criteria
                # TODO: Implement more sophisticated inbound selection logic
                selected_inbound = inbounds[0]
                inbound_id = selected_inbound.get('id')
                
                # Add client to inbound
                client_info = client.add_client_to_inbound(
                    inbound_id=inbound_id,
                    remark=client_email,
                    total_gb=traffic_gb,
                    expire_days=expire_days,
                    limit_ip=0,  # No IP limit for now
                    flow="xtls-rprx-vision",  # Default flow
                    client_uuid=client_uuid
                )
                
                # Create a subscription for this order
                try:
                    # Create a new subscription record to track this service
                    subscription = SubscriptionService.create_subscription(
                        db=db,
                        user_id=order.user_id,
                        plan_id=order.plan_id,
                        start_date=datetime.utcnow(),
                        end_date=expires_at,
                        auto_renew=False  # Default to no auto-renewal for new subscriptions
                    )
                    
                    # Update the subscription with client details 
                    # This ensures we can link the subscription to the panel client
                    subscription.client_email = client_email
                    subscription.client_uuid = client_uuid
                    subscription.panel_id = panel_id
                    subscription.inbound_id = inbound_id
                    
                    # Add any order-specific details that might be useful
                    subscription.config_traffic_gb = traffic_gb
                    
                    # Add a reference to the originating order
                    subscription.order_id = order_id
                    
                    # Save the updated subscription
                    db.commit()
                    db.refresh(subscription)
                    
                    # Add subscription ID to order for reference
                    # We need to update the order with the subscription ID
                    order = crud.order.confirm_order(
                        db,
                        order_id=order_id,
                        panel_id=panel_id,
                        inbound_id=inbound_id,
                        client_uuid=client_uuid,
                        client_email=client_email,
                        expires_at=expires_at,
                        admin_id=admin_id,
                        admin_note=admin_note,
                        subscription_id=subscription.id
                    )
                    
                    logger.info(f"Created subscription {subscription.id} for order {order_id}")
                    
                except Exception as e:
                    # Don't fail the entire operation if subscription creation fails
                    # The client is already created on the panel and the order is confirmed
                    logger.error(f"Failed to create subscription for order {order_id}: {e}")
                    # Update order with a note about the failure
                    order.admin_note = f"{order.admin_note or ''}\nWarning: Subscription creation failed: {str(e)}"
                    db.commit()
                
                return order, client_info
                
        except PanelClientError as e:
            # Mark order as failed
            crud.order.fail_order(
                db,
                order_id=order_id,
                admin_id=admin_id,
                admin_note=f"Panel client error: {str(e)}"
            )
            raise OrderProcessingError(f"Failed to create client on panel: {str(e)}")
        except Exception as e:
            # Mark order as failed
            crud.order.fail_order(
                db,
                order_id=order_id,
                admin_id=admin_id,
                admin_note=f"Unexpected error: {str(e)}"
            )
            logger.exception("Unexpected error creating client")
            raise OrderProcessingError(f"Unexpected error: {str(e)}")
    
    @staticmethod
    def get_client_config(
        db: Session,
        order_id: int
    ) -> Dict[str, Any]:
        """
        Get the client configuration for a confirmed order.
        
        Args:
            db: Database session
            order_id: ID of the order
            
        Returns:
            Client configuration information
            
        Raises:
            OrderProcessingError: If configuration cannot be retrieved
        """
        # Get the order
        order = crud.order.get(db, id=order_id)
        if not order:
            raise OrderProcessingError(f"Order with ID {order_id} not found")
        
        # Check if order is confirmed
        if order.status != OrderStatus.CONFIRMED:
            raise OrderProcessingError(
                f"Order is in state {order.status.value}, expected CONFIRMED"
            )
        
        # Get the panel
        if not order.panel_id:
            raise OrderProcessingError("Order doesn't have a panel assigned")
            
        panel = crud.panel.get(db, id=order.panel_id)
        if not panel:
            raise OrderProcessingError(f"Panel with ID {order.panel_id} not found")
        
        # Get client configuration from panel
        try:
            with SyncPanelClient(panel.url, panel.admin_username, panel.admin_password) as client:
                if not order.client_uuid:
                    raise OrderProcessingError("Order doesn't have a client UUID assigned")
                    
                # Get client info
                client_info = client.get_client(order.client_uuid)
                if not client_info:
                    raise OrderProcessingError(f"Client with UUID {order.client_uuid} not found on panel")
                
                # Get subscription link
                sub_link = client.get_subscription_link(order.client_uuid)
                if not sub_link:
                    raise OrderProcessingError("Failed to get subscription link")
                
                # Get client config
                config = client.get_client_config(order.client_uuid)
                if not config:
                    raise OrderProcessingError("Failed to get client configuration")
                
                return {
                    "subscription_link": sub_link,
                    "client_info": client_info,
                    "config": config
                }
        except PanelClientError as e:
            raise OrderProcessingError(f"Failed to get client configuration: {str(e)}")

    @staticmethod
    def submit_payment_proof(
        db: Session,
        order_id: int,
        payment_proof_img_url: str,
        payment_reference: str,
        payment_method: PaymentMethod,
        notes: Optional[str] = None
    ) -> Order:
        """
        Submit payment proof for an order.
        
        Args:
            db: Database session
            order_id: ID of the order
            payment_proof_img_url: URL to the uploaded proof image
            payment_reference: Payment reference number or transaction ID
            payment_method: Payment method used
            notes: Additional notes from the user
            
        Returns:
            Updated Order object
            
        Raises:
            OrderProcessingError: If submission fails
        """
        # Get the order
        order = crud.order.get(db, id=order_id)
        if not order:
            raise OrderProcessingError(f"Order with ID {order_id} not found")
        
        # Check if order can be updated with payment proof
        valid_statuses = [OrderStatus.PENDING, OrderStatus.REJECTED]
        if order.status not in valid_statuses:
            raise OrderProcessingError(
                f"Order is in state {order.status.value}, cannot submit payment proof"
            )
        
        # Update order with payment proof details
        update_data = {
            "status": OrderStatus.VERIFICATION_PENDING,
            "payment_proof_img_url": payment_proof_img_url,
            "payment_proof_submitted_at": datetime.utcnow(),
            "payment_reference": payment_reference,
            "payment_method": payment_method,
            "admin_note": notes if notes else order.admin_note
        }
        
        # Update the order
        updated_order = crud.order.update(db, db_obj=order, obj_in=update_data)
        
        return updated_order

    @staticmethod
    def verify_payment_proof(
        db: Session,
        order_id: int,
        admin_id: int,
        is_approved: bool,
        rejection_reason: Optional[str] = None,
        admin_note: Optional[str] = None
    ) -> Order:
        """
        Verify a payment proof for an order.
        
        Args:
            db: Database session
            order_id: The ID of the order to verify
            admin_id: The ID of the admin who is verifying the proof
            is_approved: Whether the payment is approved or rejected
            rejection_reason: The reason for rejection (required if not approved)
            admin_note: Optional note from the admin
            
        Returns:
            The updated Order object
            
        Raises:
            ValueError: If the order is not found or if the verification parameters are invalid
        """
        # Get the order
        order = crud.order.get(db, id=order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
        
        # Check if the order is in a state that can be verified
        if order.status != OrderStatus.VERIFICATION_PENDING:
            raise ValueError(f"Order with ID {order_id} is not pending verification")
        
        # Check if a rejection reason is provided for rejected payments
        if not is_approved and not rejection_reason:
            raise ValueError("A rejection reason is required when rejecting a payment")
        
        # Get the admin
        admin = crud.user.get(db, id=admin_id)
        if not admin:
            raise ValueError(f"Admin with ID {admin_id} not found")
        
        # Update the order
        if is_approved:
            order.status = OrderStatus.CONFIRMED
        else:
            order.status = OrderStatus.REJECTED
            order.payment_rejection_reason = rejection_reason
        
        order.payment_verified_at = datetime.now()
        order.payment_verification_admin_id = admin_id
        
        if admin_note:
            # Append to existing notes or create new if None
            if order.admin_note:
                order.admin_note += f"\nAdmin note ({admin.email}): {admin_note}"
            else:
                order.admin_note = f"Admin note ({admin.email}): {admin_note}"
        
        try:
            # Track admin metrics
            payment_admin_service = PaymentAdminService(db)
            payment_admin_service.record_processed_payment(
                admin_id=admin_id,
                is_approved=is_approved,
                response_time_seconds=(datetime.now() - order.payment_proof_submitted_at).total_seconds() 
                if order.payment_proof_submitted_at else 0
            )
        except Exception as e:
            # Don't fail the verification if metrics tracking fails
            logger.error(f"Failed to track payment admin metrics: {str(e)}")
        
        # If the payment is approved, create the client on the panel
        if is_approved:
            try:
                # This will also create a subscription
                OrderService.create_client_on_panel(
                    db=db,
                    order_id=order_id,
                    admin_id=admin_id,
                    admin_note=admin_note
                )
            except Exception as e:
                # Log the error but don't fail the verification
                logger.error(f"Failed to create client on panel: {str(e)}")
                # Add a note about the failure
                if order.admin_note:
                    order.admin_note += f"\nFailed to create client on panel: {str(e)}"
                else:
                    order.admin_note = f"Failed to create client on panel: {str(e)}"
        
        # Commit the changes
        crud.order.update(db, db_obj=order, obj_in=order)
        db.commit()
        db.refresh(order)
        
        return order

    @staticmethod
    def mark_expired_orders(db: Session, days: int = 7) -> int:
        """
        Mark expired orders that haven't been paid within the given time period.
        
        Args:
            db: Database session
            days: Number of days after which unpaid orders are considered expired
            
        Returns:
            Number of orders marked as expired
        """
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find orders that are still pending and older than cutoff_date
        query = db.query(Order).filter(
            Order.status.in_([OrderStatus.PENDING, OrderStatus.VERIFICATION_PENDING]),
            Order.created_at < cutoff_date
        )
        
        # Count orders to expire
        count = query.count()
        
        # Update orders to expired status
        if count > 0:
            query.update(
                {"status": OrderStatus.EXPIRED},
                synchronize_session=False
            )
            db.commit()
        
        return count

    def update_telegram_message_info(
        self,
        order_id: int,
        telegram_msg_id: int,
        telegram_group_id: str
    ) -> Order:
        """
        Update Telegram message information for an order.
        
        Args:
            order_id: The ID of the order to update
            telegram_msg_id: The Telegram message ID
            telegram_group_id: The Telegram group ID
            
        Returns:
            The updated Order object
            
        Raises:
            ValueError: If the order is not found
        """
        # Get the order
        order = crud.order.get(self.db, id=order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
        
        # Update Telegram message information
        order.payment_proof_telegram_msg_id = telegram_msg_id
        order.payment_proof_telegram_group_id = telegram_group_id
        
        # Commit the changes
        crud.order.update(self.db, db_obj=order, obj_in=order)
        self.db.commit()
        self.db.refresh(order)
        
        return order


# Create a singleton instance
order_service = OrderService() 