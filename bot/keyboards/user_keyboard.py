"""
کیبوردهای مختص کاربران در ربات
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# def get_main_keyboard() -> ReplyKeyboardMarkup:
#     """کیبورد اصلی برای منوی ربات"""
    
#     # دکمه‌های ردیف اول
#     btn_plans = KeyboardButton(text="📱 پلن‌های VPN")
#     btn_profile = KeyboardButton(text="👤 حساب کاربری")
    
#     # دکمه‌های ردیف دوم
#     btn_accounts = KeyboardButton(text="🔑 سرویس‌های من")
#     btn_wallet = KeyboardButton(text="💰 کیف پول")
    
#     # دکمه‌های ردیف سوم
#     btn_help = KeyboardButton(text="🆘 راهنما")
#     btn_contact = KeyboardButton(text="📞 پشتیبانی")
    
#     # ایجاد کیبورد با استفاده از ساختار صحیح برای aiogram v3
#     keyboard = ReplyKeyboardMarkup(
#         keyboard=[
#             [btn_plans, btn_profile],
#             [btn_accounts, btn_wallet],
#             [btn_help, btn_contact]
#         ],
#         resize_keyboard=True,
#         type="reply" # This seems incorrect/deprecated in v3
#     )
    
#     return keyboard

def get_main_keyboard(role: str = "user") -> ReplyKeyboardMarkup:
    """Generate main menu reply keyboard based on user role.
    
    Defaults to 'user' role if not provided.
    
    Args:
        role: User role (user, admin, superadmin, seller)
        
    Returns:
        ReplyKeyboardMarkup with appropriate buttons
    """
    kb = ReplyKeyboardBuilder()
    
    # Common buttons for all users
    kb.button(text="🛒 خرید سرویس")
    kb.button(text="💳 کیف پول")
    kb.button(text="📊 اشتراک‌های من")
    kb.button(text="❓ راهنما")
    kb.button(text="💬 پشتیبانی")
    kb.button(text="👤 حساب کاربری") # Added Profile button based on old version
    
    # Admin-specific buttons
    if role in ["admin", "superadmin"]:
        kb.button(text="⚙️ پنل مدیریت")
        kb.button(text="📈 آمار و گزارشات")
        kb.button(text="🔄 همگام‌سازی پنل‌ها")
        kb.button(text="👥 کاربران")
        kb.button(text="💰 تراکنش‌ها")
        kb.button(text="⚡️ وضعیت سرورها")
    
    # Seller-specific buttons (Example, adjust if needed)
    # if role == "seller":
    #     kb.button(text="💼 فروش‌های من")
    #     kb.button(text="🎯 پلن‌های من")
    #     kb.button(text="👥 مشتریان من")
    #     kb.button(text="💰 درآمد من")
    #     kb.button(text="📊 گزارش عملکرد")
    
    # Adjust layout - 2 buttons per row generally
    kb.adjust(2) 
    
    return kb.as_markup(
        resize_keyboard=True,
        input_field_placeholder="گزینه مورد نظر را انتخاب کنید..."
    )

def remove_keyboard() -> ReplyKeyboardRemove:
    """Removes the reply keyboard."""
    return ReplyKeyboardRemove()
