from decimal import Decimal
from typing import Union

def format_decimal(value: Union[str, int, float, Decimal], decimal_places: int = 2) -> str:
    """
    Format a decimal number for display in messages.
    
    Args:
        value: The value to format
        decimal_places: Number of decimal places to display
    
    Returns:
        The formatted string
    """
    try:
        # Convert to Decimal if not already
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        # Format the value with the specified decimal places
        return f"{value:.{decimal_places}f}".rstrip('0').rstrip('.') if '.' in f"{value:.{decimal_places}f}" else f"{value:.{decimal_places}f}"
    except (ValueError, TypeError):
        return "0" 