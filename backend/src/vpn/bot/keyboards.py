from typing import List, Dict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from ..models import Plan, Subscription, SupportTicket

def get_main_menu_keyboard(language: str = 'en') -> ReplyKeyboardMarkup:
    """Get main menu keyboard"""
    if language == 'fa':
        keyboard = [
            ['📱 پروفایل', '💰 کیف پول'],
            ['🌐 پلن‌ها', '⚙️ تنظیمات'],
            ['📞 پشتیبانی', '❓ راهنما']
        ]
    else:
        keyboard = [
            ['📱 Profile', '💰 Wallet'],
            ['🌐 Plans', '⚙️ Settings'],
            ['📞 Support', '❓ Help']
        ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

def get_plans_keyboard(
    plans: List[Plan],
    language: str = 'en',
    page: int = 0,
    items_per_page: int = 5
) -> InlineKeyboardMarkup:
    """Get plans selection keyboard"""
    keyboard = []
    start = page * items_per_page
    end = start + items_per_page
    current_plans = plans[start:end]
    
    # Add plan buttons
    for plan in current_plans:
        if language == 'fa':
            button_text = (
                f"{plan.name} - {plan.price:,} تومان\n"
                f"({plan.duration_days} روز)"
            )
        else:
            button_text = (
                f"{plan.name} - ${plan.price:,.2f}\n"
                f"({plan.duration_days} days)"
            )
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"plans:select:{plan.id}"
            )
        ])
    
    # Add navigation buttons if needed
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                "⬅️" if language == 'en' else "قبلی ⬅️",
                callback_data=f"plans:page:{page-1}"
            )
        )
    
    if end < len(plans):
        nav_buttons.append(
            InlineKeyboardButton(
                "➡️" if language == 'en' else "➡️ بعدی",
                callback_data=f"plans:page:{page+1}"
            )
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(keyboard)

def get_plan_details_keyboard(
    plan: Plan,
    language: str = 'en'
) -> InlineKeyboardMarkup:
    """Get keyboard for plan details"""
    if language == 'fa':
        keyboard = [
            [
                InlineKeyboardButton(
                    "🛒 خرید",
                    callback_data=f"plans:purchase:{plan.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت به لیست پلن‌ها",
                    callback_data="plans:list:0"
                )
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🛒 Purchase",
                    callback_data=f"plans:purchase:{plan.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back to Plans",
                    callback_data="plans:list:0"
                )
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_payment_methods_keyboard(
    plan_id: int,
    language: str = 'en'
) -> InlineKeyboardMarkup:
    """Get keyboard for payment methods"""
    if language == 'fa':
        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 درگاه پرداخت",
                    callback_data=f"payment:gateway:{plan_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "👛 پرداخت با کیف پول",
                    callback_data=f"payment:wallet:{plan_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data=f"plans:details:{plan_id}"
                )
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 Payment Gateway",
                    callback_data=f"payment:gateway:{plan_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "👛 Pay with Wallet",
                    callback_data=f"payment:wallet:{plan_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data=f"plans:details:{plan_id}"
                )
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_subscription_keyboard(
    subscription: Subscription,
    language: str = 'en'
) -> InlineKeyboardMarkup:
    """Get keyboard for subscription management"""
    if language == 'fa':
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 تمدید",
                    callback_data=f"subscription:renew:{subscription.id}"
                ),
                InlineKeyboardButton(
                    "❌ لغو",
                    callback_data=f"subscription:cancel:{subscription.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 آمار مصرف",
                    callback_data=f"subscription:stats:{subscription.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📱 دانلود کانفیگ",
                    callback_data=f"subscription:config:{subscription.id}"
                )
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Renew",
                    callback_data=f"subscription:renew:{subscription.id}"
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=f"subscription:cancel:{subscription.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Usage Stats",
                    callback_data=f"subscription:stats:{subscription.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📱 Download Config",
                    callback_data=f"subscription:config:{subscription.id}"
                )
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_wallet_keyboard(language: str = 'en') -> InlineKeyboardMarkup:
    """Get wallet management keyboard"""
    if language == 'fa':
        keyboard = [
            [
                InlineKeyboardButton(
                    "💰 افزایش موجودی",
                    callback_data="wallet:deposit"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 تراکنش‌ها",
                    callback_data="wallet:transactions:0"
                )
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "💰 Add Funds",
                    callback_data="wallet:deposit"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Transactions",
                    callback_data="wallet:transactions:0"
                )
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard(language: str = 'en') -> InlineKeyboardMarkup:
    """Get settings keyboard"""
    if language == 'fa':
        keyboard = [
            [
                InlineKeyboardButton(
                    "🌐 زبان",
                    callback_data="settings:language"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔔 اعلان‌ها",
                    callback_data="settings:notifications"
                )
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🌐 Language",
                    callback_data="settings:language"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔔 Notifications",
                    callback_data="settings:notifications"
                )
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Get language selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                "English 🇺🇸",
                callback_data="settings:language:en"
            ),
            InlineKeyboardButton(
                "فارسی 🇮🇷",
                callback_data="settings:language:fa"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back",
                callback_data="settings:main"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_notifications_keyboard(
    language: str = 'en'
) -> InlineKeyboardMarkup:
    """Get notifications settings keyboard"""
    if language == 'fa':
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ فعال",
                    callback_data="settings:notifications:on"
                ),
                InlineKeyboardButton(
                    "❌ غیرفعال",
                    callback_data="settings:notifications:off"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="settings:main"
                )
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Enable",
                    callback_data="settings:notifications:on"
                ),
                InlineKeyboardButton(
                    "❌ Disable",
                    callback_data="settings:notifications:off"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="settings:main"
                )
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard(language: str = 'en') -> InlineKeyboardMarkup:
    """Get admin panel keyboard"""
    if language == 'fa':
        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 کاربران",
                    callback_data="admin:users:0"
                ),
                InlineKeyboardButton(
                    "📊 آمار",
                    callback_data="admin:stats"
                )
            ],
            [
                InlineKeyboardButton(
                    "🌐 پلن‌ها",
                    callback_data="admin:plans"
                ),
                InlineKeyboardButton(
                    "💰 تراکنش‌ها",
                    callback_data="admin:transactions:0"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚙️ تنظیمات",
                    callback_data="admin:settings"
                )
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 Users",
                    callback_data="admin:users:0"
                ),
                InlineKeyboardButton(
                    "📊 Stats",
                    callback_data="admin:stats"
                )
            ],
            [
                InlineKeyboardButton(
                    "🌐 Plans",
                    callback_data="admin:plans"
                ),
                InlineKeyboardButton(
                    "💰 Transactions",
                    callback_data="admin:transactions:0"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚙️ Settings",
                    callback_data="admin:settings"
                )
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_reseller_keyboard(language: str = 'en') -> InlineKeyboardMarkup:
    """Get reseller panel keyboard"""
    if language == 'fa':
        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 مشتریان",
                    callback_data="reseller:customers:0"
                ),
                InlineKeyboardButton(
                    "📊 آمار",
                    callback_data="reseller:stats"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 کد تخفیف",
                    callback_data="reseller:referral"
                ),
                InlineKeyboardButton(
                    "💰 درآمد",
                    callback_data="reseller:earnings:0"
                )
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 Customers",
                    callback_data="reseller:customers:0"
                ),
                InlineKeyboardButton(
                    "📊 Stats",
                    callback_data="reseller:stats"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 Referral",
                    callback_data="reseller:referral"
                ),
                InlineKeyboardButton(
                    "💰 Earnings",
                    callback_data="reseller:earnings:0"
                )
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_support_keyboard(active_tickets: List[SupportTicket], language: str) -> InlineKeyboardMarkup:
    """Get support menu keyboard"""
    keyboard = []
    
    # Add active tickets
    for ticket in active_tickets:
        if language == 'fa':
            text = f"🎫 تیکت #{ticket.id} - {ticket.subject}"
        else:
            text = f"🎫 Ticket #{ticket.id} - {ticket.subject}"
            
        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"{MENU_SUPPORT}:{ACTION_SELECT}:{ticket.id}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 بازگشت" if language == 'fa' else "🔙 Back",
            callback_data=f"{MENU_MAIN}:{ACTION_BACK}"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard) 