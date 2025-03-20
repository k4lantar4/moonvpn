"""
Payment service manager implementation.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from app.core.managers.base import ResourceManager
from app.core.exceptions import PaymentError, ResourceError
from app.core.models.payment import Transaction, Wallet, PaymentMethod
from app.core.schemas.payment import TransactionCreate, TransactionUpdate, WalletCreate, WalletUpdate

class PaymentManager(ResourceManager):
    """Manager for payment operations."""
    
    def __init__(self):
        super().__init__()
        self.resource_type = "payment"
        
    async def _create_resource(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment transaction or wallet."""
        try:
            if "type" not in data:
                raise ValidationError("Resource type not specified")
                
            if data["type"] == "transaction":
                transaction = TransactionCreate(**data)
                payment_transaction = await Transaction.create(transaction)
                await self.metrics.record_resource_operation(
                    resource_type="payment_transaction",
                    operation="create",
                    success=True
                )
                return payment_transaction.dict()
                
            elif data["type"] == "wallet":
                wallet = WalletCreate(**data)
                payment_wallet = await Wallet.create(wallet)
                await self.metrics.record_resource_operation(
                    resource_type="payment_wallet",
                    operation="create",
                    success=True
                )
                return payment_wallet.dict()
                
            else:
                raise ValidationError(f"Invalid resource type: {data['type']}")
                
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="create",
                success=False
            )
            raise ResourceError(f"Failed to create {self.resource_type}: {str(e)}")
            
    async def _get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get payment transaction or wallet by ID."""
        try:
            # Try to get from cache first
            cache_key = f"payment:{resource_id}"
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return cached_data
                
            # Get from database
            resource = await Transaction.get_by_id(resource_id) or await Wallet.get_by_id(resource_id)
            if not resource:
                return None
                
            # Cache the result
            await self.cache.set(cache_key, resource.dict(), ttl=300)
            return resource.dict()
            
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="get",
                success=False
            )
            raise ResourceError(f"Failed to get {self.resource_type}: {str(e)}")
            
    async def _update_resource(
        self,
        resource_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update payment transaction or wallet."""
        try:
            # Get existing resource
            resource = await Transaction.get_by_id(resource_id) or await Wallet.get_by_id(resource_id)
            if not resource:
                raise ResourceError(f"{self.resource_type} not found: {resource_id}")
                
            # Update based on type
            if isinstance(resource, Transaction):
                update_data = TransactionUpdate(**data)
                updated = await Transaction.update(resource_id, update_data)
            else:
                update_data = WalletUpdate(**data)
                updated = await Wallet.update(resource_id, update_data)
                
            # Invalidate cache
            await self.cache.delete(f"payment:{resource_id}")
            
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="update",
                success=True
            )
            return updated.dict()
            
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="update",
                success=False
            )
            raise ResourceError(f"Failed to update {self.resource_type}: {str(e)}")
            
    async def _delete_resource(self, resource_id: str) -> None:
        """Delete payment transaction or wallet."""
        try:
            # Get resource type
            resource = await Transaction.get_by_id(resource_id) or await Wallet.get_by_id(resource_id)
            if not resource:
                raise ResourceError(f"{self.resource_type} not found: {resource_id}")
                
            # Delete based on type
            if isinstance(resource, Transaction):
                await Transaction.delete(resource_id)
            else:
                await Wallet.delete(resource_id)
                
            # Invalidate cache
            await self.cache.delete(f"payment:{resource_id}")
            
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="delete",
                success=True
            )
            
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="delete",
                success=False
            )
            raise ResourceError(f"Failed to delete {self.resource_type}: {str(e)}")
            
    async def process_payment(
        self,
        user_id: int,
        amount: float,
        method: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process payment transaction."""
        try:
            # Create transaction
            transaction = await Transaction.create({
                "user_id": user_id,
                "amount": amount,
                "method": method,
                "status": "pending",
                "metadata": metadata
            })
            
            # Process based on method
            if method == "wallet":
                result = await self._process_wallet_payment(transaction)
            elif method == "zarinpal":
                result = await self._process_zarinpal_payment(transaction)
            else:
                raise ValidationError(f"Unsupported payment method: {method}")
                
            # Update transaction
            await Transaction.update_status(
                transaction_id=transaction.id,
                status=result["status"],
                details=result
            )
            
            await self.metrics.record_payment(
                method=method,
                amount=amount,
                status=result["status"]
            )
            
            return {
                "status": "success",
                "transaction": transaction.dict(),
                "result": result
            }
            
        except Exception as e:
            await self.metrics.record_error("process_payment", str(e))
            raise PaymentError(f"Payment processing failed: {str(e)}")
            
    async def _process_wallet_payment(self, transaction: Transaction) -> Dict[str, Any]:
        """Process wallet payment."""
        try:
            # Get user wallet
            wallet = await Wallet.get_by_user_id(transaction.user_id)
            if not wallet:
                raise ResourceError(f"Wallet not found for user: {transaction.user_id}")
                
            # Check balance
            if wallet.balance < transaction.amount:
                return {
                    "status": "failed",
                    "error": "Insufficient balance"
                }
                
            # Update wallet balance
            await Wallet.update_balance(
                wallet_id=wallet.id,
                amount=-transaction.amount
            )
            
            return {
                "status": "success",
                "balance": wallet.balance - transaction.amount
            }
            
        except Exception as e:
            raise PaymentError(f"Wallet payment failed: {str(e)}")
            
    async def _process_zarinpal_payment(self, transaction: Transaction) -> Dict[str, Any]:
        """Process Zarinpal payment."""
        # Implementation depends on Zarinpal API
        pass
        
    async def get_wallet_balance(self, user_id: int) -> Dict[str, Any]:
        """Get user wallet balance."""
        try:
            wallet = await Wallet.get_by_user_id(user_id)
            if not wallet:
                raise ResourceError(f"Wallet not found for user: {user_id}")
                
            return {
                "balance": wallet.balance,
                "currency": wallet.currency,
                "last_updated": wallet.updated_at
            }
            
        except Exception as e:
            await self.metrics.record_error("get_wallet_balance", str(e))
            raise PaymentError(f"Failed to get wallet balance: {str(e)}")
            
    async def add_wallet_balance(
        self,
        user_id: int,
        amount: float,
        source: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Add balance to user wallet."""
        try:
            wallet = await Wallet.get_by_user_id(user_id)
            if not wallet:
                raise ResourceError(f"Wallet not found for user: {user_id}")
                
            # Update balance
            updated = await Wallet.update_balance(
                wallet_id=wallet.id,
                amount=amount
            )
            
            # Record transaction
            await Transaction.create({
                "user_id": user_id,
                "amount": amount,
                "method": "wallet",
                "status": "success",
                "type": "deposit",
                "source": source,
                "metadata": metadata
            })
            
            return {
                "status": "success",
                "balance": updated.balance,
                "currency": updated.currency
            }
            
        except Exception as e:
            await self.metrics.record_error("add_wallet_balance", str(e))
            raise PaymentError(f"Failed to add wallet balance: {str(e)}")
            
    async def get_transaction_history(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user transaction history."""
        try:
            transactions = await Transaction.get_by_user_id(
                user_id=user_id,
                limit=limit,
                offset=offset
            )
            
            return [t.dict() for t in transactions]
            
        except Exception as e:
            await self.metrics.record_error("get_transaction_history", str(e))
            raise PaymentError(f"Failed to get transaction history: {str(e)}")
            
    async def get_available_payment_methods(self) -> List[Dict[str, Any]]:
        """Get available payment methods."""
        try:
            # Try to get from cache first
            cache_key = "payment:methods"
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return cached_data
                
            # Get from database
            methods = await PaymentMethod.get_all_active()
            
            # Cache the result
            await self.cache.set(cache_key, [m.dict() for m in methods], ttl=3600)
            return [m.dict() for m in methods]
            
        except Exception as e:
            await self.metrics.record_error("get_payment_methods", str(e))
            raise PaymentError(f"Failed to get payment methods: {str(e)}")
            
    async def validate_payment(
        self,
        transaction_id: str,
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate payment transaction."""
        try:
            transaction = await Transaction.get_by_id(transaction_id)
            if not transaction:
                raise ResourceError(f"Transaction not found: {transaction_id}")
                
            # Validate based on method
            if transaction.method == "zarinpal":
                result = await self._validate_zarinpal_payment(transaction, validation_data)
            else:
                raise ValidationError(f"Unsupported payment method: {transaction.method}")
                
            # Update transaction
            await Transaction.update_status(
                transaction_id=transaction.id,
                status=result["status"],
                details=result
            )
            
            return result
            
        except Exception as e:
            await self.metrics.record_error("validate_payment", str(e))
            raise PaymentError(f"Payment validation failed: {str(e)}")
            
    async def _validate_zarinpal_payment(
        self,
        transaction: Transaction,
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate Zarinpal payment."""
        # Implementation depends on Zarinpal API
        pass 