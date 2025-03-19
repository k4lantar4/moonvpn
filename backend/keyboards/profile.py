"""
Keyboard layouts for profile-related menus.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from django.utils.translation import gettext as _

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for the main profile menu."""
    keyboard = [
        [
            InlineKeyboardButton(_("💰 Wallet"), callback_data="wallet"),
            InlineKeyboardButton(_("📱 Subscriptions"), callback_data="subscriptions")
        ],
        [
            InlineKeyboardButton(_("👥 Referrals"), callback_data="referrals"),
            InlineKeyboardButton(_("⚙️ Settings"), callback_data="settings")
        ],
        [
            InlineKeyboardButton(_("🏠 Main Menu"), callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_wallet_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for the wallet menu."""
    keyboard = [
        [
            InlineKeyboardButton(_("💳 Add Funds"), callback_data="add_funds"),
            InlineKeyboardButton(_("🔄 Transfer"), callback_data="transfer")
        ],
        [
            InlineKeyboardButton(_("📊 Statistics"), callback_data="wallet_stats"),
            InlineKeyboardButton(_("📜 History"), callback_data="wallet_history")
        ],
        [
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for the subscription menu."""
    keyboard = [
        [
            InlineKeyboardButton(_("🛒 Buy Plan"), callback_data="buy_plan"),
            InlineKeyboardButton(_("🔄 Renew"), callback_data="renew_plan")
        ],
        [
            InlineKeyboardButton(_("📊 Usage"), callback_data="usage_stats"),
            InlineKeyboardButton(_("📜 History"), callback_data="sub_history")
        ],
        [
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_referral_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for the referral menu."""
    keyboard = [
        [
            InlineKeyboardButton(_("📊 Statistics"), callback_data="ref_stats"),
            InlineKeyboardButton(_("📜 History"), callback_data="ref_history")
        ],
        [
            InlineKeyboardButton(_("🎁 Rewards"), callback_data="ref_rewards"),
            InlineKeyboardButton(_("📢 Share"), callback_data="ref_share")
        ],
        [
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard) 