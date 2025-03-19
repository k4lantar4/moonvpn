"""
MoonVPN Telegram Bot - Transaction Model

This module provides the Transaction model for managing transactions.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class Transaction:
    """Transaction model for managing financial transactions."""
    
    # Transaction types
    TYPE_DEPOSIT = 'deposit'
    TYPE_WITHDRAWAL = 'withdrawal'
    TYPE_PURCHASE = 'purchase'
    TYPE_REFUND = 'refund'
    TYPE_ADJUSTMENT = 'adjustment'
    
    # Transaction status
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize a transaction object."""
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.transaction_type = data.get('transaction_type')
        self.amount = float(data.get('amount', 0))
        self.description = data.get('description', '')
        self.reference_id = data.get('reference_id')
        self.status = data.get('status', self.STATUS_PENDING)
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        self.extra_data = data.get('extra_data', {})
        
        # Fields from joined tables
        self.username = data.get('username')
        
    @staticmethod
    def get_by_id(transaction_id: int) -> Optional['Transaction']:
        """Get transaction by ID."""
        query = """
            SELECT t.*, u.username
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.id
            WHERE t.id = %s
        """
        result = execute_query(query, (transaction_id,), fetch="one")
        
        if result:
            return Transaction(result)
        return None
    
    @staticmethod
    def get_by_user_id(user_id: int, limit: int = 10, offset: int = 0) -> List['Transaction']:
        """Get transactions by user ID."""
        query = """
            SELECT t.*, u.username
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.id
            WHERE t.user_id = %s
            ORDER BY t.created_at DESC
            LIMIT %s OFFSET %s
        """
        results = execute_query(query, (user_id, limit, offset))
        
        return [Transaction(result) for result in results]
    
    @staticmethod
    def get_by_reference_id(reference_id: str) -> Optional['Transaction']:
        """Get transaction by reference ID."""
        query = """
            SELECT t.*, u.username
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.id
            WHERE t.reference_id = %s
        """
        result = execute_query(query, (reference_id,), fetch="one")
        
        if result:
            return Transaction(result)
        return None
    
    @staticmethod
    def create(user_id: int, transaction_type: str, amount: float, description: str, 
              reference_id: Optional[str] = None, status: str = 'pending',
              extra_data: Optional[Dict] = None) -> Optional['Transaction']:
        """Create a new transaction."""
        # Generate reference ID if not provided
        if not reference_id:
            reference_id = str(uuid.uuid4())
        
        # Convert extra_data to JSON string if provided
        extra_data_json = None
        if extra_data:
            import json
            extra_data_json = json.dumps(extra_data)
        
        query = """
            INSERT INTO transactions (
                user_id, transaction_type, amount, description, 
                reference_id, status, extra_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        transaction_id = execute_insert(query, (
            user_id, transaction_type, amount, description,
            reference_id, status, extra_data_json
        ))
        
        if transaction_id:
            return Transaction.get_by_id(transaction_id)
        return None
    
    def save(self) -> bool:
        """Save changes to the database."""
        if not self.id:
            return False
        
        # Convert extra_data to JSON string if it's a dict
        extra_data_json = None
        if self.extra_data:
            import json
            if isinstance(self.extra_data, dict):
                extra_data_json = json.dumps(self.extra_data)
            else:
                extra_data_json = self.extra_data
        
        query = """
            UPDATE transactions
            SET user_id = %s, transaction_type = %s, amount = %s,
                description = %s, reference_id = %s, status = %s,
                extra_data = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        return execute_update(query, (
            self.user_id, self.transaction_type, self.amount,
            self.description, self.reference_id, self.status,
            extra_data_json, self.id
        ))
    
    def complete(self) -> bool:
        """Mark transaction as completed."""
        self.status = self.STATUS_COMPLETED
        return self.save()
    
    def fail(self) -> bool:
        """Mark transaction as failed."""
        self.status = self.STATUS_FAILED
        return self.save()
    
    def cancel(self) -> bool:
        """Mark transaction as cancelled."""
        self.status = self.STATUS_CANCELLED
        return self.save()
    
    def get_user(self):
        """Get user associated with this transaction."""
        from models.user import User
        return User.get_by_id(self.user_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'description': self.description,
            'reference_id': self.reference_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'extra_data': self.extra_data,
            'username': self.username
        } 