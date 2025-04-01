import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.models.user import User
from app.models.plan import Plan
from app.models.client import Client
from app.services.panel_service import PanelService, PanelClientNotFoundError

# Configure logging
logger = logging.getLogger(__name__)

class SubscriptionException(Exception):
    """Base exception for subscription service errors."""
    pass

class SubscriptionNotFoundError(SubscriptionException):
    """Exception raised when a subscription cannot be found."""
    pass

class SubscriptionService:
    """
    Service for managing user subscriptions.
    Handles operations like freeze/unfreeze, adding notes, and auto-renew settings.
    """
    
    @staticmethod
    def get_subscription(db: Session, subscription_id: int) -> Subscription:
        """
        Get a subscription by ID.
        
        Args:
            db: Database session
            subscription_id: ID of the subscription
            
        Returns:
            Subscription object
            
        Raises:
            SubscriptionNotFoundError: If subscription not found
        """
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise SubscriptionNotFoundError(f"Subscription with ID {subscription_id} not found")
            
        return subscription
    
    @staticmethod
    def get_user_subscriptions(db: Session, user_id: int) -> List[Subscription]:
        """
        Get all subscriptions for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            List of Subscription objects
        """
        return db.query(Subscription).filter(Subscription.user_id == user_id).all()
    
    @staticmethod
    def create_subscription(
        db: Session,
        user_id: int,
        plan_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        auto_renew: bool = False
    ) -> Subscription:
        """
        Create a new subscription.
        
        Args:
            db: Database session
            user_id: ID of the user
            plan_id: ID of the plan
            start_date: Start date of the subscription (defaults to now)
            end_date: End date of the subscription (calculated from plan if not provided)
            auto_renew: Whether to automatically renew the subscription
            
        Returns:
            Created Subscription object
        """
        # Check if user and plan exist
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise SubscriptionException(f"User with ID {user_id} not found")
            
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise SubscriptionException(f"Plan with ID {plan_id} not found")
            
        # Set start date to now if not provided
        if not start_date:
            start_date = datetime.utcnow()
            
        # Calculate end date from plan duration if not provided
        if not end_date and plan.duration_days:
            end_date = start_date + timedelta(days=plan.duration_days)
            
        # Create new subscription
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status="active",
            is_frozen=False,
            auto_renew=auto_renew,
            start_date=start_date,
            end_date=end_date
        )
        
        # Add to database
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def freeze_subscription(
        db: Session,
        subscription_id: int,
        freeze_end_date: Optional[datetime] = None,
        freeze_reason: Optional[str] = None,
        sync_with_panel: bool = True
    ) -> Subscription:
        """
        Freeze a subscription.
        
        Args:
            db: Database session
            subscription_id: ID of the subscription to freeze
            freeze_end_date: Date when the freeze should end (optional)
            freeze_reason: Reason for freezing (optional)
            sync_with_panel: Whether to sync with the VPN panel
            
        Returns:
            Updated Subscription object
            
        Raises:
            SubscriptionNotFoundError: If subscription not found
            SubscriptionException: If subscription cannot be frozen
        """
        # Get subscription
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Check if subscription is already frozen
        if subscription.is_frozen:
            raise SubscriptionException(f"Subscription with ID {subscription_id} is already frozen")
            
        # Freeze the subscription
        subscription.freeze(end_date=freeze_end_date, reason=freeze_reason)
        
        # If sync_with_panel is True, disable the client on the panel
        if sync_with_panel:
            try:
                # Get the client associated with this subscription
                client = db.query(Client).filter(Client.subscription_id == subscription_id).first()
                if client:
                    with PanelService() as panel_service:
                        # Disable the client on the panel
                        panel_service.disable_client(email=client.email)
            except PanelClientNotFoundError:
                # Client might not exist on panel yet, log but continue
                logger.warning(f"Client for subscription ID {subscription_id} not found on panel")
            except Exception as e:
                # Log any other errors but don't raise (we still want to freeze the subscription in DB)
                logger.error(f"Error disabling client on panel for subscription ID {subscription_id}: {str(e)}")
        
        # Save changes
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def unfreeze_subscription(
        db: Session,
        subscription_id: int,
        sync_with_panel: bool = True
    ) -> Subscription:
        """
        Unfreeze a subscription.
        
        Args:
            db: Database session
            subscription_id: ID of the subscription to unfreeze
            sync_with_panel: Whether to sync with the VPN panel
            
        Returns:
            Updated Subscription object
            
        Raises:
            SubscriptionNotFoundError: If subscription not found
            SubscriptionException: If subscription cannot be unfrozen
        """
        # Get subscription
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Check if subscription is frozen
        if not subscription.is_frozen:
            raise SubscriptionException(f"Subscription with ID {subscription_id} is not frozen")
            
        # Unfreeze the subscription
        subscription.unfreeze()
        
        # If sync_with_panel is True, enable the client on the panel
        if sync_with_panel:
            try:
                # Get the client associated with this subscription
                client = db.query(Client).filter(Client.subscription_id == subscription_id).first()
                if client:
                    with PanelService() as panel_service:
                        # Enable the client on the panel
                        panel_service.enable_client(email=client.email)
            except PanelClientNotFoundError:
                # Client might not exist on panel yet, log but continue
                logger.warning(f"Client for subscription ID {subscription_id} not found on panel")
            except Exception as e:
                # Log any other errors but don't raise (we still want to unfreeze the subscription in DB)
                logger.error(f"Error enabling client on panel for subscription ID {subscription_id}: {str(e)}")
        
        # Save changes
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def add_note(
        db: Session,
        subscription_id: int,
        note: str
    ) -> Subscription:
        """
        Add a note to a subscription.
        
        Args:
            db: Database session
            subscription_id: ID of the subscription
            note: Text of the note to add
            
        Returns:
            Updated Subscription object
            
        Raises:
            SubscriptionNotFoundError: If subscription not found
        """
        # Get subscription
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Add note
        subscription.add_note(note)
        
        # Save changes
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def toggle_auto_renew(
        db: Session,
        subscription_id: int,
        enabled: bool,
        payment_method: Optional[str] = None
    ) -> Subscription:
        """
        Toggle auto-renew setting for a subscription.
        
        Args:
            db: Database session
            subscription_id: ID of the subscription
            enabled: Whether auto-renew should be enabled
            payment_method: Payment method to use for auto-renewal (optional)
            
        Returns:
            Updated Subscription object
            
        Raises:
            SubscriptionNotFoundError: If subscription not found
        """
        # Get subscription
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Toggle auto-renew
        subscription.toggle_auto_renew(enabled, payment_method)
        
        # Save changes
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def check_expired_subscriptions(db: Session) -> List[Subscription]:
        """
        Check for expired subscriptions and update their status.
        This would typically be called by a scheduler.
        
        Args:
            db: Database session
            
        Returns:
            List of expired subscriptions
        """
        now = datetime.utcnow()
        
        # Find active subscriptions that have passed their end date
        expired_subscriptions = db.query(Subscription).filter(
            Subscription.status == "active",
            Subscription.end_date < now,
            Subscription.is_frozen == False  # Ignore frozen subscriptions
        ).all()
        
        for subscription in expired_subscriptions:
            # If auto-renew is enabled, we would handle renewal here
            if subscription.auto_renew:
                # TODO: Implement renewal logic
                pass
            else:
                # Update status to expired
                subscription.status = "expired"
                
                # Disable the associated client
                try:
                    client = db.query(Client).filter(Client.subscription_id == subscription.id).first()
                    if client:
                        with PanelService() as panel_service:
                            panel_service.disable_client(email=client.email)
                except Exception as e:
                    logger.error(f"Error disabling client for expired subscription {subscription.id}: {str(e)}")
        
        # Save changes
        if expired_subscriptions:
            db.commit()
            
        return expired_subscriptions
    
    @staticmethod
    def change_protocol_or_location(
        db: Session,
        subscription_id: int,
        new_inbound_id: Optional[int] = None,
        new_panel_id: Optional[int] = None,
        sync_with_panel: bool = True
    ) -> Subscription:
        """
        Change the protocol or location for a subscription by moving the client to a different inbound or panel.
        
        Args:
            db: Database session
            subscription_id: ID of the subscription to modify
            new_inbound_id: ID of the new inbound (protocol) to use
            new_panel_id: ID of the new panel (location) to use
            sync_with_panel: Whether to sync changes with the VPN panel
            
        Returns:
            Updated Subscription object
            
        Raises:
            SubscriptionNotFoundError: If subscription not found
            SubscriptionException: If changes cannot be applied
            PanelException: If there are issues with the panel operations
        """
        # Get subscription
        subscription = SubscriptionService.get_subscription(db, subscription_id)
        
        # Check if subscription is active
        if subscription.status != "active":
            raise SubscriptionException(f"Cannot change protocol/location for inactive subscription with ID {subscription_id}")
            
        # Check if subscription is frozen
        if subscription.is_frozen:
            raise SubscriptionException(f"Cannot change protocol/location for frozen subscription with ID {subscription_id}")
        
        # Store original values for rollback if needed
        original_inbound_id = subscription.inbound_id
        original_panel_id = subscription.panel_id
        original_client_uuid = subscription.client_uuid
        original_client_email = subscription.client_email
        
        # Track whether we've made panel changes that need to be rolled back on failure
        panel_changes_made = False
        
        try:
            # If sync_with_panel is True, update the client on the panel
            if sync_with_panel:
                # Check if we have client details
                if not subscription.client_email:
                    raise SubscriptionException("Cannot update panel: missing client email")
                
                # First, retrieve client details to get current settings
                with PanelService(panel_id=original_panel_id) as panel_service:
                    try:
                        client = panel_service.get_client(email=subscription.client_email, inbound_id=original_inbound_id)
                        
                        # Extract current settings
                        current_total_gb = client.get('totalGB', 1)
                        current_expire_time = client.get('expiryTime', None)
                        
                        # Calculate expire_days based on current time and expiry time
                        expire_days = 30  # Default
                        if current_expire_time:
                            # Convert timestamp to datetime
                            expire_date = datetime.fromtimestamp(current_expire_time / 1000)  # Convert ms to seconds
                            days_left = (expire_date - datetime.utcnow()).days
                            expire_days = max(1, days_left)  # At least 1 day
                    except PanelClientNotFoundError:
                        # If client not found, use defaults
                        logger.warning(f"Client for subscription ID {subscription_id} not found on panel, using defaults")
                        current_total_gb = 1
                        expire_days = 30
                        
                # If changing panel (location)
                if new_panel_id and new_panel_id != original_panel_id:
                    # Remove client from old panel
                    with PanelService(panel_id=original_panel_id) as panel_service:
                        try:
                            panel_service.remove_client(email=subscription.client_email, inbound_id=original_inbound_id)
                        except Exception as e:
                            logger.warning(f"Error removing client from old panel: {str(e)}")
                    
                    # Add client to new panel
                    with PanelService(panel_id=new_panel_id) as panel_service:
                        # Use same client UUID if possible
                        new_client = panel_service.add_client(
                            email=subscription.client_email,
                            total_gb=current_total_gb,
                            expire_days=expire_days,
                            inbound_id=new_inbound_id if new_inbound_id else None,
                            client_uuid=subscription.client_uuid
                        )
                        
                        # Update subscription with new panel details
                        subscription.panel_id = new_panel_id
                        subscription.inbound_id = new_client.get('inbound_id')
                        subscription.client_uuid = new_client.get('uuid')
                        
                        panel_changes_made = True
                
                # If only changing inbound (protocol) within same panel
                elif new_inbound_id and new_inbound_id != original_inbound_id:
                    with PanelService(panel_id=subscription.panel_id) as panel_service:
                        # Remove from current inbound
                        try:
                            panel_service.remove_client(email=subscription.client_email, inbound_id=original_inbound_id)
                        except Exception as e:
                            logger.warning(f"Error removing client from old inbound: {str(e)}")
                        
                        # Add to new inbound
                        new_client = panel_service.add_client(
                            email=subscription.client_email,
                            total_gb=current_total_gb,
                            expire_days=expire_days,
                            inbound_id=new_inbound_id,
                            client_uuid=subscription.client_uuid
                        )
                        
                        # Update subscription with new inbound details
                        subscription.inbound_id = new_inbound_id
                        subscription.client_uuid = new_client.get('uuid')
                        
                        panel_changes_made = True
            
            # Save changes to the database
            subscription.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(subscription)
            
            return subscription
            
        except Exception as e:
            # Rollback database changes
            db.rollback()
            
            # If we made panel changes but the overall operation failed, try to restore the original state
            if panel_changes_made:
                try:
                    logger.info(f"Rolling back panel changes for subscription {subscription_id}")
                    
                    # If we changed panels (location)
                    if new_panel_id and new_panel_id != original_panel_id:
                        # Remove from new panel
                        with PanelService(panel_id=new_panel_id) as panel_service:
                            try:
                                panel_service.remove_client(email=subscription.client_email)
                            except:
                                pass
                        
                        # Restore on original panel
                        with PanelService(panel_id=original_panel_id) as panel_service:
                            try:
                                panel_service.add_client(
                                    email=original_client_email,
                                    inbound_id=original_inbound_id,
                                    client_uuid=original_client_uuid
                                )
                            except:
                                pass
                    # If we only changed inbound (protocol)
                    elif new_inbound_id and new_inbound_id != original_inbound_id:
                        with PanelService(panel_id=original_panel_id) as panel_service:
                            # Remove from new inbound
                            try:
                                panel_service.remove_client(email=subscription.client_email, inbound_id=new_inbound_id)
                            except:
                                pass
                            
                            # Restore to original inbound
                            try:
                                panel_service.add_client(
                                    email=original_client_email,
                                    inbound_id=original_inbound_id,
                                    client_uuid=original_client_uuid
                                )
                            except:
                                pass
                except Exception as rollback_error:
                    logger.error(f"Error during rollback for subscription {subscription_id}: {str(rollback_error)}")
            
            # Re-raise the original exception
            if isinstance(e, SubscriptionException):
                raise
            elif isinstance(e, PanelException):
                raise
            else:
                logger.error(f"Error changing protocol/location for subscription {subscription_id}: {str(e)}")
                raise SubscriptionException(f"Failed to change protocol/location: {str(e)}") 