"""
Simplified models for subscription plans and user wallet management.
These are placeholder models for the bot to use until proper API integration is implemented.
"""

class UserSubscription:
    """Simplified model for user subscriptions."""
    
    def __init__(self, user_id, plan_name, status="active", traffic_used_bytes=0):
        self.user_id = user_id
        self.plan_name = plan_name
        self.status = status
        self.traffic_used_bytes = traffic_used_bytes
        self.traffic_limit_gb = 100  # Default value
        
    @property
    def traffic_remaining_gb(self):
        """Calculate remaining traffic in GB."""
        used_gb = self.traffic_used_bytes / (1024 * 1024 * 1024)
        return max(0, self.traffic_limit_gb - used_gb)
        
    @property
    def is_expired(self):
        """Check if subscription is expired."""
        return self.status == "expired"


class UserWallet:
    """Simplified model for user wallet."""
    
    def __init__(self, user_id, balance=0, points=0, referral_code=None, referred_by=None):
        self.user_id = user_id
        self.balance = balance
        self.points = points
        self.referral_code = referral_code
        self.referred_by = referred_by
        self.total_referral_earnings = 0


class WalletTransaction:
    """Simplified model for wallet transactions."""
    
    def __init__(self, wallet_id, transaction_type, amount, status="completed", description=""):
        self.wallet_id = wallet_id
        self.transaction_type = transaction_type
        self.amount = amount
        self.status = status
        self.description = description
        self.points = 0
        self.created_at = None  # Would be datetime.now() in a real implementation


# Mock data access functions
def get_user_subscription(user_id):
    """Get a user's subscription."""
    # This would normally query a database
    return UserSubscription(user_id, "Basic Plan")
    
def get_user_wallet(user_id):
    """Get a user's wallet."""
    # This would normally query a database
    return UserWallet(user_id, balance=0, points=0)
    
def get_wallet_transactions(wallet_id, limit=10):
    """Get a wallet's transactions."""
    # This would normally query a database
    return [] 