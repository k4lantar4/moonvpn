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
        amount: float,
        discount_amount: float = 0.0,
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
            amount: Original price
            discount_amount: Discount amount
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
            
        # Calculate final amount
        final_amount = amount - discount_amount
        if final_amount < 0:
            final_amount = 0
            
        # Create order using CRUD
        order_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "panel_id": panel_id,
            "amount": Decimal(str(amount)),
            "discount_amount": Decimal(str(discount_amount)),
            "final_amount": Decimal(str(final_amount)),
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
        Get client configuration for a confirmed order.
        
        Args:
            db: Database session
            order_id: ID of the order to get config for
            
        Returns:
            Dictionary with client configuration
            
        Raises:
            OrderProcessingError: If config cannot be retrieved
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
        panel = crud.panel.get(db, id=order.panel_id)
        if not panel:
            raise OrderProcessingError(f"Panel with ID {order.panel_id} not found")
        
        # Build configuration
        # TODO: Implement actual config generation based on the panel's protocol
        
        config = {
            "client_uuid": order.client_uuid,
            "panel_url": panel.url,
            "inbound_id": order.inbound_id,
            "email": order.client_email,
            "expires_at": order.expires_at.isoformat() if order.expires_at else None,
            # Additional config details would be added here
        }
        
        # Check if there's a subscription for this order
        if hasattr(order, 'subscription_id') and order.subscription_id:
            # Add subscription ID to the config
            config["subscription_id"] = order.subscription_id
            
            # We could potentially redirect to the subscription endpoints for full config
            config["config_url"] = f"/api/v1/subscriptions/{order.subscription_id}/config"
            config["qrcode_url"] = f"/api/v1/subscriptions/{order.subscription_id}/qrcode"
        
        return config
    
    @staticmethod
    def mark_expired_orders(db: Session, days: int = 7) -> int:
        """
        Mark pending orders older than X days as expired.
        
        Args:
            db: Database session
            days: Number of days after which to mark orders as expired
            
        Returns:
            Number of orders marked as expired
        """
        return crud.order.mark_expired_orders(db, days=days)


# Create a singleton instance
order_service = OrderService() 