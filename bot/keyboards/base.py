from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    """کیبورد اصلی ربات"""
    keyboard = [
        [KeyboardButton("🚀 نمایش سرویس‌ها"), KeyboardButton("💼 حساب کاربری من")],
        [KeyboardButton("💰 کیف پول"), KeyboardButton("🧑‍💻 پشتیبانی")],
        [KeyboardButton("⚙️ تنظیمات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_plans_keyboard(categories):
    """کیبورد دسته‌بندی طرح‌ها"""
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(f"📱 {category.name}", callback_data=f"category_{category.id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def get_plan_list_keyboard(plans, category_id):
    """کیبورد انتخاب طرح از یک دسته بندی"""
    keyboard = []
    for plan in plans:
        # اضافه کردن ستارها برای طرح‌های ویژه
        star = "⭐ " if plan.is_featured else ""
        # نمایش نام طرح و قیمت آن
        plan_text = f"{star}{plan.name} - {format_price(plan.price)} تومان"
        keyboard.append([InlineKeyboardButton(plan_text, callback_data=f"plan_{plan.id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به دسته‌بندی‌ها", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(keyboard)

def get_locations_keyboard(locations):
    """کیبورد انتخاب موقعیت جغرافیایی"""
    keyboard = []
    for location in locations:
        # نمایش نام موقعیت و پرچم آن
        location_text = f"{location.flag} {location.name}"
        keyboard.append([InlineKeyboardButton(location_text, callback_data=f"location_{location.id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به طرح‌ها", callback_data="back_to_plans")])
    return InlineKeyboardMarkup(keyboard)

def get_protocols_keyboard(protocols):
    """کیبورد انتخاب پروتکل"""
    keyboard = []
    
    # پشتیبانی از هر دو حالت آرایه‌ای از آبجکت‌ها یا رشته جدا شده با کاما
    if isinstance(protocols, str):
        protocol_list = protocols.split(",")
        for protocol in protocol_list:
            keyboard.append([InlineKeyboardButton(f"🔐 {protocol}", callback_data=f"protocol_{protocol}")])
    else:
        for protocol in protocols:
            keyboard.append([InlineKeyboardButton(f"🔐 {protocol.name}", callback_data=f"protocol_{protocol.id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به موقعیت‌ها", callback_data="back_to_locations")])
    return InlineKeyboardMarkup(keyboard)

def get_payment_methods_keyboard():
    """کیبورد انتخاب روش پرداخت"""
    keyboard = [
        [InlineKeyboardButton("💳 کارت به کارت", callback_data="payment_card")],
        [InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data="payment_wallet")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_confirm")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirm_purchase_keyboard():
    """کیبورد تأیید خرید"""
    keyboard = [
        [InlineKeyboardButton("✅ تأیید و پرداخت", callback_data="confirm_purchase")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_protocols")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """کیبورد لغو عملیات"""
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="cancel")]]
    return InlineKeyboardMarkup(keyboard)

def get_my_services_keyboard(services):
    """کیبورد نمایش سرویس‌های کاربر"""
    keyboard = []
    for service in services:
        keyboard.append([InlineKeyboardButton(f"🌐 {service.remark}", callback_data=f"service_{service.id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def get_service_actions_keyboard(service_id):
    """کیبورد عملیات‌های قابل انجام روی یک سرویس"""
    keyboard = [
        [InlineKeyboardButton("🔄 تمدید سرویس", callback_data=f"renew_{service_id}")],
        [InlineKeyboardButton("🌍 تغییر موقعیت", callback_data=f"change_location_{service_id}")],
        [InlineKeyboardButton("🔐 تغییر پروتکل", callback_data=f"change_protocol_{service_id}")],
        [InlineKeyboardButton("❄️ توقف موقت سرویس", callback_data=f"freeze_{service_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_services")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_wallet_amounts_keyboard():
    """کیبورد انتخاب مبلغ شارژ کیف پول"""
    keyboard = [
        [InlineKeyboardButton("💰 100,000 تومان", callback_data="amount_100000")],
        [InlineKeyboardButton("💰 200,000 تومان", callback_data="amount_200000")],
        [InlineKeyboardButton("💰 500,000 تومان", callback_data="amount_500000")],
        [InlineKeyboardButton("💰 1,000,000 تومان", callback_data="amount_1000000")],
        [InlineKeyboardButton("💰 مبلغ دلخواه", callback_data="amount_custom")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- توابع کمکی ---
def format_price(price):
    """قالب‌بندی قیمت به صورت خوانا"""
    return "{:,}".format(int(price))
