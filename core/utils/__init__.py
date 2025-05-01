# This file makes the 'utils' directory a Python package 

"""
Utility functions for the application.
"""

from decimal import Decimal
from typing import Union, Optional

def format_currency(amount: Union[float, Decimal, int], 
                   currency_symbol: str = "تومان", 
                   with_commas: bool = True, 
                   decimal_places: Optional[int] = None) -> str:
    """
    Format a currency amount with options for symbols, commas and decimals.
    
    Args:
        amount: The amount to format
        currency_symbol: Symbol or code to append (default: تومان)
        with_commas: Whether to add thousand separators
        decimal_places: Number of decimal places (None = keep as is)
    
    Returns:
        Formatted currency string
    """
    # Convert to Decimal for consistent handling
    amount_decimal = Decimal(str(amount))
    
    # Round if decimal places specified
    if decimal_places is not None:
        amount_decimal = amount_decimal.quantize(Decimal(10) ** -decimal_places)
    
    # Format with or without commas
    if with_commas:
        # Split into integer and decimal parts
        int_part, *dec_part = str(amount_decimal).split('.')
        
        # Add commas to integer part
        int_part_with_commas = ""
        for i, digit in enumerate(reversed(int_part)):
            if i > 0 and i % 3 == 0:
                int_part_with_commas = ',' + int_part_with_commas
            int_part_with_commas = digit + int_part_with_commas
        
        # Reconstruct with decimal part if it exists
        if dec_part:
            formatted = f"{int_part_with_commas}.{dec_part[0]}"
        else:
            formatted = int_part_with_commas
    else:
        formatted = str(amount_decimal)
    
    # Add currency symbol with space
    formatted = f"{formatted} {currency_symbol}"
    
    return formatted 