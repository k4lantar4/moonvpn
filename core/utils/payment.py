"""
Payment utilities for MoonVPN.

This module contains utility functions for payment-related operations
including validation, formatting, and helper functions.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import json
from decimal import Decimal, ROUND_DOWN

from app.core.config import settings

logger = logging.getLogger(__name__)

def format_amount(amount: float, currency: str = settings.DEFAULT_CURRENCY) -> str:
    """Format amount with currency symbol."""
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "IRR": "ریال"
    }
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"

def validate_amount(amount: float) -> bool:
    """Validate payment amount."""
    try:
        amount = Decimal(str(amount))
        if amount <= 0:
            return False
        if amount > settings.MAX_WALLET_BALANCE:
            return False
        return True
    except (ValueError, TypeError):
        return False

def generate_order_id(prefix: str = "ORD") -> str:
    """Generate a unique order ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random = hashlib.md5(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:8]
    return f"{prefix}{timestamp}{random}"

def generate_transaction_id(prefix: str = "TRX") -> str:
    """Generate a unique transaction ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random = hashlib.md5(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:8]
    return f"{prefix}{timestamp}{random}"

def calculate_tax(amount: float, tax_rate: float = 0.09) -> float:
    """Calculate tax amount."""
    try:
        amount = Decimal(str(amount))
        tax_rate = Decimal(str(tax_rate))
        tax = amount * tax_rate
        return float(tax.quantize(Decimal("0.01"), rounding=ROUND_DOWN))
    except (ValueError, TypeError):
        return 0.0

def calculate_total(amount: float, tax_rate: float = 0.09) -> float:
    """Calculate total amount including tax."""
    try:
        amount = Decimal(str(amount))
        tax = calculate_tax(float(amount), tax_rate)
        total = amount + Decimal(str(tax))
        return float(total.quantize(Decimal("0.01"), rounding=ROUND_DOWN))
    except (ValueError, TypeError):
        return amount

def format_bank_details(
    account_number: str,
    bank_name: str,
    account_holder: str,
    amount: float,
    reference: str
) -> Dict[str, Any]:
    """Format bank transfer details."""
    return {
        "account_number": account_number,
        "bank_name": bank_name,
        "account_holder": account_holder,
        "amount": format_amount(amount),
        "reference": reference,
        "iban": settings.BANK_IBAN if settings.BANK_IBAN else None
    }

def log_payment_event(
    event_type: str,
    data: Dict[str, Any],
    level: str = "INFO"
) -> None:
    """Log payment-related events."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data
    }
    
    if level.upper() == "ERROR":
        logger.error(json.dumps(log_data))
    elif level.upper() == "WARNING":
        logger.warning(json.dumps(log_data))
    else:
        logger.info(json.dumps(log_data))

def validate_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str = settings.WEBHOOK_SECRET
) -> bool:
    """Validate webhook signature."""
    try:
        expected_signature = hashlib.sha256(
            payload + secret.encode()
        ).hexdigest()
        return signature == expected_signature
    except Exception:
        return False

def format_payment_response(
    success: bool,
    message: str,
    transaction_id: Optional[int] = None,
    payment_url: Optional[str] = None,
    authority: Optional[str] = None,
    transaction_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format payment response."""
    response = {
        "success": success,
        "message": message
    }
    
    if transaction_id:
        response["transaction_id"] = transaction_id
    if payment_url:
        response["payment_url"] = payment_url
    if authority:
        response["authority"] = authority
    if transaction_data:
        response["transaction_data"] = transaction_data
        
    return response 