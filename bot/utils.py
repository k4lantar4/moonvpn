def format_currency(amount: float) -> str:
    """تبدیل عدد به رشتهٔ زیبا با کاما و واحد تومان"""
    # Ensure amount is treated as float for formatting, then handle potential .0
    try:
        # Format with commas, remove trailing .0 if it exists for whole numbers
        formatted_amount = f'{amount:,.0f}' if amount == int(amount) else f'{amount:,.2f}'
    except (ValueError, TypeError):
        formatted_amount = str(amount) # Fallback if formatting fails
    return f'{formatted_amount} تومان' 