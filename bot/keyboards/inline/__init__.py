"""Inline keyboard module."""

from bot.keyboards.inline.purchase import (
    get_plan_categories_keyboard,
    get_plans_keyboard,
    get_locations_keyboard,
    get_order_confirmation_keyboard
)

__all__ = [
    'get_plan_categories_keyboard',
    'get_plans_keyboard',
    'get_locations_keyboard',
    'get_order_confirmation_keyboard',
]
