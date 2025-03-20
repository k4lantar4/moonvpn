"""
Default messages for the Telegram bot.
These will be used if the messages are not found in the database.
"""

default_messages = {
    # Welcome and language
    'welcome': {
        'fa': "به ربات V2Ray خوش آمدید! 👋\nلطفا زبان خود را انتخاب کنید:",
        'en': "Welcome to V2Ray Bot! 👋\nPlease select your language:"
    },
    
    # Main menu
    'main_menu': {
        'fa': "🏠 منوی اصلی\nاز دکمه‌های زیر می‌توانید استفاده کنید:",
        'en': "🏠 Main Menu\nYou can use the buttons below:"
    },
    
    # Buttons
    'btn_my_accounts': {
        'fa': "🔑 اکانت‌های من",
        'en': "🔑 My Accounts"
    },
    'btn_buy_subscription': {
        'fa': "🛒 خرید اشتراک",
        'en': "🛒 Buy Subscription"
    },
    'btn_payment': {
        'fa': "💰 پرداخت",
        'en': "💰 Payment"
    },
    'btn_support': {
        'fa': "📞 پشتیبانی",
        'en': "📞 Support"
    },
    'btn_profile': {
        'fa': "👤 پروفایل من",
        'en': "👤 My Profile"
    },
    'btn_admin': {
        'fa': "⚙️ پنل مدیریت",
        'en': "⚙️ Admin Panel"
    },
    'btn_language': {
        'fa': "🌐 تغییر زبان",
        'en': "🌐 Change Language"
    },
    'btn_back_main': {
        'fa': "🔙 بازگشت به منوی اصلی",
        'en': "🔙 Back to Main Menu"
    },
    'btn_back_accounts': {
        'fa': "🔙 بازگشت به لیست اکانت‌ها",
        'en': "🔙 Back to Accounts List"
    },
    
    # Account related
    'no_active_accounts': {
        'fa': "❌ شما هیچ اکانت فعالی ندارید.\nبرای خرید اشتراک از دکمه زیر استفاده کنید:",
        'en': "❌ You don't have any active accounts.\nUse the button below to buy a subscription:"
    },
    'accounts_list': {
        'fa': "📋 لیست اکانت‌های شما:\nبرای مشاهده جزئیات روی هر اکانت کلیک کنید:",
        'en': "📋 Your accounts list:\nClick on each account to see details:"
    },
    'account_details': {
        'fa': """
📊 *جزئیات اکانت*

🔰 *پلن*: {plan_name}
🖥 *سرور*: {server_name}
⏱ *روزهای باقیمانده*: {remaining_days} روز
📅 *تاریخ انقضا*: {expiry_date}
📊 *میزان مصرف*: {data_usage} از {data_limit}
📉 *درصد مصرف*: {usage_percentage}

برای دریافت لینک اتصال، از دکمه‌های زیر استفاده کنید:
""",
        'en': """
📊 *Account Details*

🔰 *Plan*: {plan_name}
🖥 *Server*: {server_name}
⏱ *Remaining Days*: {remaining_days} days
📅 *Expiry Date*: {expiry_date}
📊 *Data Usage*: {data_usage} of {data_limit}
📉 *Usage Percentage*: {usage_percentage}

To get connection links, use the buttons below:
"""
    },
    'config_not_found': {
        'fa': "❌ تنظیمات اکانت شما یافت نشد! لطفاً با پشتیبانی تماس بگیرید.",
        'en': "❌ Your account configuration was not found! Please contact support."
    },
    'config_not_available': {
        'fa': "❌ این نوع کانفیگ برای اکانت شما در دسترس نیست.",
        'en': "❌ This config type is not available for your account."
    },
    'config_link': {
        'fa': "🔗 لینک اتصال {config_type} برای پلن {plan_name} در سرور {server_name}:",
        'en': "🔗 {config_type} connection link for {plan_name} plan on {server_name} server:"
    },
    'qrcode_coming_soon': {
        'fa': "🔜 امکان ارسال QR Code به زودی اضافه خواهد شد.",
        'en': "🔜 QR Code feature will be added soon."
    },
    'btn_vmess_config': {
        'fa': "📲 دریافت کانفیگ VMess",
        'en': "📲 Get VMess Config"
    },
    'btn_vless_config': {
        'fa': "📲 دریافت کانفیگ VLess",
        'en': "📲 Get VLess Config"
    },
    'btn_trojan_config': {
        'fa': "📲 دریافت کانفیگ Trojan",
        'en': "📲 Get Trojan Config"
    },
    'btn_shadowsocks_config': {
        'fa': "📲 دریافت کانفیگ ShadowSocks",
        'en': "📲 Get ShadowSocks Config"
    },
    'btn_subscription_url': {
        'fa': "🔄 دریافت لینک اشتراک",
        'en': "🔄 Get Subscription URL"
    },
    'btn_qrcode': {
        'fa': "📱 دریافت QR Code",
        'en': "📱 Get QR Code"
    },
    
    # Plan related
    'plans_list': {
        'fa': "📋 لیست پلن‌های موجود:\nبرای خرید هر پلن روی آن کلیک کنید:",
        'en': "📋 Available plans:\nClick on each plan to purchase:"
    },
    'no_active_plans': {
        'fa': "❌ در حال حاضر هیچ پلن فعالی وجود ندارد. لطفاً بعداً دوباره تلاش کنید.",
        'en': "❌ No active plans are available at the moment. Please try again later."
    },
    'unlimited_traffic': {
        'fa': "ترافیک نامحدود",
        'en': "Unlimited Traffic"
    },
    'days': {
        'fa': "روز",
        'en': "days"
    },
    'unlimited': {
        'fa': "نامحدود",
        'en': "Unlimited"
    },
    'currency': {
        'fa': "تومان",
        'en': "Toman"
    },
    
    # Payment related
    'payment_menu': {
        'fa': "💰 منوی پرداخت\nاز این قسمت می‌توانید حساب خود را شارژ کنید یا وضعیت پرداخت‌های قبلی را ببینید:",
        'en': "💰 Payment Menu\nYou can recharge your account or check previous payments:"
    },
    'btn_recharge_wallet': {
        'fa': "💸 شارژ کیف پول",
        'en': "💸 Recharge Wallet"
    },
    'btn_payment_history': {
        'fa': "📃 تاریخچه پرداخت‌ها",
        'en': "📃 Payment History"
    },
    'btn_check_payment': {
        'fa': "🔍 پیگیری پرداخت",
        'en': "🔍 Check Payment Status"
    },
    'btn_back_payment': {
        'fa': "🔙 بازگشت به منوی پرداخت",
        'en': "🔙 Back to Payment Menu"
    },
    'no_payment_methods': {
        'fa': "❌ در حال حاضر هیچ روش پرداختی فعال نیست. لطفاً بعداً مجدد تلاش کنید.",
        'en': "❌ No payment methods are currently active. Please try again later."
    },
    'select_payment_method': {
        'fa': "💳 لطفاً روش پرداخت را انتخاب کنید:",
        'en': "💳 Please select a payment method:"
    },
    'enter_payment_amount': {
        'fa': "💲 لطفاً مبلغ مورد نظر برای شارژ کیف پول را به تومان وارد کنید:",
        'en': "💲 Please enter the amount (in Toman) you want to charge your wallet:"
    },
    'invalid_amount': {
        'fa': "❌ مبلغ وارد شده نامعتبر است. لطفاً یک عدد مثبت وارد کنید.",
        'en': "❌ Invalid amount. Please enter a positive number."
    },
    'card_payment_info': {
        'fa': """
💳 *اطلاعات پرداخت کارت به کارت*

💰 *مبلغ*: {amount} تومان
💳 *شماره کارت*: `{card_number}`
👤 *به نام*: {card_holder}

لطفاً مبلغ را به کارت فوق واریز کرده و سپس اطلاعات زیر را وارد کنید:
""",
        'en': """
💳 *Card Payment Information*

💰 *Amount*: {amount} Toman
💳 *Card Number*: `{card_number}`
👤 *Card Holder*: {card_holder}

Please transfer the amount to the above card and then enter the following information:
"""
    },
    'enter_card_number': {
        'fa': "🔢 لطفاً شماره کارت خود را وارد کنید (۱۶ رقم بدون فاصله یا خط تیره):",
        'en': "🔢 Please enter your card number (16 digits without spaces or dashes):"
    },
    'invalid_card_number': {
        'fa': "❌ شماره کارت نامعتبر است. لطفاً یک شماره کارت ۱۶ رقمی وارد کنید.",
        'en': "❌ Invalid card number. Please enter a 16-digit card number."
    },
    'enter_reference_number': {
        'fa': "🧾 لطفاً شماره پیگیری یا شناسه مرجع تراکنش را وارد کنید:",
        'en': "🧾 Please enter the transaction reference or tracking number:"
    },
    'invalid_reference': {
        'fa': "❌ شماره پیگیری نامعتبر است. لطفاً شماره پیگیری تراکنش خود را وارد کنید.",
        'en': "❌ Invalid reference number. Please enter your transaction reference number."
    },
    'enter_transfer_time': {
        'fa': "🕒 لطفاً تاریخ و زمان تراکنش را به صورت YYYY-MM-DD HH:MM وارد کنید (مثال: 1402-05-15 14:30):",
        'en': "🕒 Please enter the transaction date and time in format YYYY-MM-DD HH:MM (example: 2023-08-06 14:30):"
    },
    'invalid_date_format': {
        'fa': "❌ فرمت تاریخ نامعتبر است. لطفاً به صورت YYYY-MM-DD HH:MM وارد کنید (مثال: 1402-05-15 14:30).",
        'en': "❌ Invalid date format. Please enter in format YYYY-MM-DD HH:MM (example: 2023-08-06 14:30)."
    },
    'payment_creation_failed': {
        'fa': "❌ خطا در ثبت پرداخت. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
        'en': "❌ Failed to create payment. Please try again or contact support."
    },
    'payment_created': {
        'fa': """
✅ *پرداخت شما با موفقیت ثبت شد*

💰 *مبلغ*: {amount} تومان
🔑 *کد پیگیری*: `{verification_code}`

این پرداخت در انتظار تایید ادمین است و پس از تایید، به کیف پول شما اضافه خواهد شد.
برای پیگیری وضعیت پرداخت، می‌توانید از بخش "پیگیری پرداخت" استفاده کنید.
""",
        'en': """
✅ *Your payment was successfully registered*

💰 *Amount*: {amount} Toman
🔑 *Verification Code*: `{verification_code}`

This payment is waiting for admin verification and after confirmation, it will be added to your wallet.
You can check the payment status using the "Check Payment Status" option.
"""
    },
    'zarinpal_coming_soon': {
        'fa': "🔜 پرداخت از طریق زرین‌پال به زودی اضافه خواهد شد.",
        'en': "🔜 Zarinpal payment will be added soon."
    },
    'enter_verification_code': {
        'fa': "🔑 لطفاً کد پیگیری پرداخت خود را وارد کنید:",
        'en': "🔑 Please enter your payment verification code:"
    },
    'payment_not_found': {
        'fa': "❌ پرداختی با این کد پیگیری یافت نشد. لطفاً کد را بررسی کرده و دوباره وارد کنید.",
        'en': "❌ No payment found with this verification code. Please check the code and try again."
    },
    'payment_info': {
        'fa': """
📋 *اطلاعات پرداخت*

💰 *مبلغ*: {amount} تومان
📊 *وضعیت تراکنش*: {status}
📊 *وضعیت پرداخت کارتی*: {card_status}
📅 *تاریخ ثبت*: {date}
💳 *شماره کارت*: {card_number}
🧾 *شماره پیگیری*: {reference}

اگر پرداخت شما هنوز تایید نشده است، لطفاً منتظر بمانید. تایید پرداخت ممکن است تا ۲۴ ساعت زمان ببرد.
""",
        'en': """
📋 *Payment Information*

💰 *Amount*: {amount} Toman
📊 *Transaction Status*: {status}
📊 *Card Payment Status*: {card_status}
📅 *Date*: {date}
💳 *Card Number*: {card_number}
🧾 *Reference Number*: {reference}

If your payment is not yet verified, please wait. Payment verification may take up to 24 hours.
"""
    },
    'no_payment_history': {
        'fa': "❌ شما هیچ تراکنش مالی ندارید.",
        'en': "❌ You don't have any transaction history."
    },
    'payment_history': {
        'fa': "📃 تاریخچه پرداخت‌های شما:",
        'en': "📃 Your payment history:"
    },
    'payment_history_item': {
        'fa': "🧾 *شناسه*: {id}\n💰 *مبلغ*: {amount} تومان\n📊 *وضعیت*: {status}\n📋 *نوع*: {type}\n📅 *تاریخ*: {date}",
        'en': "🧾 *ID*: {id}\n💰 *Amount*: {amount} Toman\n📊 *Status*: {status}\n📋 *Type*: {type}\n📅 *Date*: {date}"
    },
    
    # Transaction status
    'status_pending': {
        'fa': "⏳ در انتظار",
        'en': "⏳ Pending"
    },
    'status_completed': {
        'fa': "✅ تکمیل شده",
        'en': "✅ Completed"
    },
    'status_failed': {
        'fa': "❌ ناموفق",
        'en': "❌ Failed"
    },
    'status_expired': {
        'fa': "⌛ منقضی شده",
        'en': "⌛ Expired"
    },
    'status_refunded': {
        'fa': "↩️ بازگشت وجه",
        'en': "↩️ Refunded"
    },
    'status_verified': {
        'fa': "✅ تایید شده",
        'en': "✅ Verified"
    },
    'status_rejected': {
        'fa': "❌ رد شده",
        'en': "❌ Rejected"
    },
    
    # Transaction types
    'type_deposit': {
        'fa': "💰 شارژ کیف پول",
        'en': "💰 Wallet Deposit"
    },
    'type_purchase': {
        'fa': "🛒 خرید",
        'en': "🛒 Purchase"
    },
    'type_refund': {
        'fa': "↩️ بازگشت وجه",
        'en': "↩️ Refund"
    },
    'type_admin': {
        'fa': "⚙️ تنظیم ادمین",
        'en': "⚙️ Admin Adjustment"
    },
    
    # Support related
    'support_message': {
        'fa': "📞 پشتیبانی\nپیام خود را ارسال کنید تا به زودی پاسخ داده شود:",
        'en': "📞 Support\nSend your message and we'll respond shortly:"
    },
    'support_sent': {
        'fa': "✅ پیام شما با موفقیت ارسال شد. به زودی با شما تماس خواهیم گرفت.",
        'en': "✅ Your message was sent successfully. We'll contact you shortly."
    },
    
    # Profile related
    'profile_info': {
        'fa': """
👤 *اطلاعات کاربری*

🆔 *نام کاربری*: {username}
💰 *موجودی کیف پول*: {wallet_balance} تومان
📅 *تاریخ عضویت*: {date_joined}
🌐 *زبان*: {language}
""",
        'en': """
👤 *User Profile*

🆔 *Username*: {username}
💰 *Wallet Balance*: {wallet_balance} Toman
📅 *Join Date*: {date_joined}
🌐 *Language*: {language}
"""
    },
    
    # Admin related
    'admin_menu': {
        'fa': "⚙️ پنل مدیریت\nاز این بخش می‌توانید به عنوان مدیر سیستم به تنظیمات دسترسی داشته باشید:",
        'en': "⚙️ Admin Panel\nFrom this section, you can access system settings as an administrator:"
    },
    'btn_admin_servers': {
        'fa': "🖥 مدیریت سرورها",
        'en': "🖥 Manage Servers"
    },
    'btn_admin_users': {
        'fa': "👥 مدیریت کاربران",
        'en': "👥 Manage Users"
    },
    'btn_admin_plans': {
        'fa': "📋 مدیریت پلن‌ها",
        'en': "📋 Manage Plans"
    },
    'btn_admin_payments': {
        'fa': "💰 مدیریت پرداخت‌ها",
        'en': "💰 Manage Payments"
    },
    'btn_admin_discounts': {
        'fa': "🎁 مدیریت تخفیف‌ها",
        'en': "🎁 Manage Discounts"
    },
    'btn_admin_broadcast': {
        'fa': "📢 ارسال پیام گروهی",
        'en': "📢 Broadcast Message"
    },
    'btn_admin_settings': {
        'fa': "⚙️ تنظیمات ربات",
        'en': "⚙️ Bot Settings"
    },
    
    # Help message
    'help': {
        'fa': """
*راهنمای استفاده از ربات*

/start - شروع مجدد ربات
/help - نمایش این راهنما
/language - تغییر زبان
/cancel - لغو عملیات جاری

برای خرید اشتراک و مدیریت اکانت‌های خود، از منوی اصلی استفاده کنید.
در صورت نیاز به راهنمایی بیشتر، با پشتیبانی تماس بگیرید.
""",
        'en': """
*Bot Help Guide*

/start - Restart the bot
/help - Show this help
/language - Change language
/cancel - Cancel current operation

To purchase a subscription and manage your accounts, use the main menu.
If you need further assistance, contact support.
"""
    },
    
    # Error messages
    'error_general': {
        'fa': "❌ خطایی رخ داده است. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
        'en': "❌ An error has occurred. Please try again or contact support."
    },
    'error_user_not_found': {
        'fa': "❌ کاربر یافت نشد. لطفاً دوباره با /start شروع کنید.",
        'en': "❌ User not found. Please start again with /start."
    },
    
    # FAQ related
    'faq_menu': {
        'fa': """
📚 *سوالات متداول*

از این بخش می‌توانید پاسخ سوالات رایج را مشاهده کنید.
برای مشاهده پاسخ هر سوال، روی آن کلیک کنید:
""",
        'en': """
📚 *Frequently Asked Questions*

Here you can find answers to common questions.
Click on any question to see its answer:
"""
    },

    'btn_faq': {
        'fa': "📚 سوالات متداول",
        'en': "📚 FAQ"
    },

    'btn_back_faq': {
        'fa': "🔙 بازگشت به سوالات متداول",
        'en': "🔙 Back to FAQ"
    },

    # Tutorial related
    'tutorial_menu': {
        'fa': """
📖 *آموزش‌های نصب و راه‌اندازی*

لطفاً پلتفرم مورد نظر خود را انتخاب کنید:
""",
        'en': """
📖 *Setup Tutorials*

Please select your platform:
"""
    },

    'btn_tutorials': {
        'fa': "📖 آموزش‌ها",
        'en': "📖 Tutorials"
    },

    'btn_back_tutorials': {
        'fa': "🔙 بازگشت به آموزش‌ها",
        'en': "🔙 Back to Tutorials"
    },

    'platform_android': {
        'fa': "📱 اندروید",
        'en': "📱 Android"
    },

    'platform_ios': {
        'fa': "📱 آیفون",
        'en': "📱 iPhone"
    },

    'platform_windows': {
        'fa': "💻 ویندوز",
        'en': "💻 Windows"
    },

    'platform_macos': {
        'fa': "💻 مک",
        'en': "💻 Mac"
    },

    'platform_linux': {
        'fa': "💻 لینوکس",
        'en': "💻 Linux"
    },

    # Referral system
    'referral_menu': {
        'fa': """
🎁 *سیستم دعوت از دوستان*

کد دعوت شما: `{code}`
تعداد دعوت‌های موفق: {count}
مجموع پاداش دریافتی: {total_bonus} تومان

با دعوت از دوستان خود، هر دو نفر شما {bonus_amount} تومان پاداش دریافت می‌کنید!
""",
        'en': """
🎁 *Referral System*

Your referral code: `{code}`
Successful referrals: {count}
Total bonus earned: {total_bonus} Toman

Invite your friends and both of you will receive {bonus_amount} Toman bonus!
"""
    },

    'btn_referral': {
        'fa': "🎁 دعوت از دوستان",
        'en': "🎁 Refer Friends"
    },

    'referral_code_used': {
        'fa': """
✅ *تبریک!*
کد دعوت با موفقیت ثبت شد.
{bonus_amount} تومان به کیف پول شما اضافه شد.
""",
        'en': """
✅ *Congratulations!*
Referral code successfully applied.
{bonus_amount} Toman has been added to your wallet.
"""
    },

    'enter_referral_code': {
        'fa': "🎁 اگر کد دعوت دارید، آن را وارد کنید:",
        'en': "🎁 If you have a referral code, enter it:"
    },

    'invalid_referral_code': {
        'fa': "❌ کد دعوت نامعتبر است. لطفاً دوباره تلاش کنید یا /skip را بزنید.",
        'en': "❌ Invalid referral code. Please try again or type /skip."
    },

    # Server status
    'server_status': {
        'fa': """
📊 *وضعیت سرور {server_name}*

🟢 وضعیت: {status}
⏱ پینگ: {ping} ms
💻 CPU: {cpu}%
💾 RAM: {memory}%
💿 دیسک: {disk}%
🕒 آخرین بررسی: {last_check}
""",
        'en': """
📊 *Server Status: {server_name}*

🟢 Status: {status}
⏱ Ping: {ping} ms
💻 CPU: {cpu}%
💾 RAM: {memory}%
💿 Disk: {disk}%
🕒 Last Check: {last_check}
"""
    },

    'btn_server_status': {
        'fa': "📊 وضعیت سرورها",
        'en': "📊 Server Status"
    },

    # User preferences
    'preferences_menu': {
        'fa': """
⚙️ *تنظیمات شخصی*

🔔 اعلان انقضای اشتراک: {notify_expiration}
⏰ اعلان {expiration_days} روز قبل از انقضا
📊 اعلان مصرف حجم: {notify_data_usage}
📈 اعلان در {data_threshold}% مصرف
🔄 تمدید خودکار: {auto_renewal}
""",
        'en': """
⚙️ *User Preferences*

🔔 Subscription expiry notification: {notify_expiration}
⏰ Notify {expiration_days} days before expiry
📊 Data usage notification: {notify_data_usage}
📈 Notify at {data_threshold}% usage
🔄 Auto renewal: {auto_renewal}
"""
    },

    'btn_preferences': {
        'fa': "⚙️ تنظیمات",
        'en': "⚙️ Preferences"
    },

    'btn_toggle_expiry_notify': {
        'fa': "🔔 تغییر وضعیت اعلان انقضا",
        'en': "🔔 Toggle Expiry Notification"
    },

    'btn_set_expiry_days': {
        'fa': "⏰ تنظیم روزهای اعلان",
        'en': "⏰ Set Notification Days"
    },

    'btn_toggle_usage_notify': {
        'fa': "📊 تغییر وضعیت اعلان مصرف",
        'en': "📊 Toggle Usage Notification"
    },

    'btn_set_usage_threshold': {
        'fa': "📈 تنظیم آستانه مصرف",
        'en': "📈 Set Usage Threshold"
    },

    'btn_toggle_auto_renewal': {
        'fa': "🔄 تغییر وضعیت تمدید خودکار",
        'en': "🔄 Toggle Auto Renewal"
    },

    'enter_expiry_days': {
        'fa': "⏰ لطفاً تعداد روزهای قبل از انقضا برای دریافت اعلان را وارد کنید (1-30):",
        'en': "⏰ Please enter how many days before expiry you want to be notified (1-30):"
    },

    'enter_usage_threshold': {
        'fa': "📈 لطفاً درصد مصرف برای دریافت اعلان را وارد کنید (1-100):",
        'en': "📈 Please enter at what percentage of usage you want to be notified (1-100):"
    },

    'invalid_number': {
        'fa': "❌ عدد وارد شده نامعتبر است. لطفاً دوباره تلاش کنید.",
        'en': "❌ Invalid number. Please try again."
    },

    'preferences_updated': {
        'fa': "✅ تنظیمات شما با موفقیت به‌روزرسانی شد.",
        'en': "✅ Your preferences have been successfully updated."
    },

    # Usage statistics
    'usage_stats': {
        'fa': """
📊 *آمار مصرف {plan_name}*

📅 دوره: {period}
📈 مصرف: {usage} از {total}
📉 درصد مصرف: {percentage}%
📊 میانگین روزانه: {daily_avg}
⏳ روزهای باقیمانده: {days_left}
""",
        'en': """
📊 *Usage Statistics for {plan_name}*

📅 Period: {period}
📈 Usage: {usage} of {total}
📉 Usage percentage: {percentage}%
📊 Daily average: {daily_avg}
⏳ Days remaining: {days_left}
"""
    },

    'btn_usage_stats': {
        'fa': "📊 آمار مصرف",
        'en': "📊 Usage Stats"
    },

    # Speed test
    'speed_test': {
        'fa': """
🚀 *نتایج تست سرعت*

📥 دانلود: {download} Mbps
📤 آپلود: {upload} Mbps
⏱ پینگ: {ping} ms
🌍 سرور: {server}
""",
        'en': """
🚀 *Speed Test Results*

📥 Download: {download} Mbps
📤 Upload: {upload} Mbps
⏱ Ping: {ping} ms
🌍 Server: {server}
"""
    },

    'btn_speed_test': {
        'fa': "🚀 تست سرعت",
        'en': "🚀 Speed Test"
    },

    'speed_test_running': {
        'fa': "🔄 در حال انجام تست سرعت...",
        'en': "🔄 Running speed test..."
    },

    # Points related
    'points_menu': {
        'fa': "💎 منوی امتیازات\n\nامتیازات فعلی شما: {points}\n\nچه کاری می‌خواهید انجام دهید؟",
        'en': "💎 Points Menu\n\nYour current points: {points}\n\nWhat would you like to do?"
    },
    'points_balance': {
        'fa': "💰 موجودی امتیازات\n\nامتیازات فعلی شما: {points}\n\nبه جمع‌آوری امتیازات ادامه دهید تا جوایز عالی دریافت کنید!",
        'en': "💰 Points Balance\n\nYour current points: {points}\n\nKeep earning points to unlock amazing rewards!"
    },
    'points_history': {
        'fa': "📊 تاریخچه امتیازات\n\n۱۰ تراکنش آخر شما:\n\n{transactions}",
        'en': "📊 Points History\n\nHere are your last 10 transactions:\n\n{transactions}"
    },
    'points_history_empty': {
        'fa': "📊 تاریخچه امتیازات\n\nشما هنوز هیچ تراکنشی انجام نداده‌اید.\n\nشروع به کسب امتیازات کنید تا تاریخچه شما اینجا نمایش داده شود!",
        'en': "📊 Points History\n\nYou haven't made any transactions yet.\n\nStart earning points to see your history here!"
    },
    'points_redemption': {
        'fa': "🎁 تبدیل امتیازات\n\nجوایز موجود:\n\n{rewards}\n\nیک جایزه را انتخاب کنید تا امتیازات خود را تبدیل کنید!",
        'en': "🎁 Points Redemption\n\nAvailable rewards:\n\n{rewards}\n\nSelect a reward to redeem your points!"
    },
    'points_redemption_empty': {
        'fa': "🎁 تبدیل امتیازات\n\nدر حال حاضر هیچ جایزه‌ای موجود نیست.\n\nبعداً دوباره بررسی کنید تا جوایز جدید را ببینید!",
        'en': "🎁 Points Redemption\n\nNo rewards available at the moment.\n\nCheck back later for new rewards!"
    },
    'points_redemption_success': {
        'fa': "🎉 تبریک می‌گوییم!\n\nشما با موفقیت {points} امتیاز را برای {reward} تبدیل کردید!\n\nموجودی جدید شما: {new_balance} امتیاز",
        'en': "🎉 Congratulations!\n\nYou have successfully redeemed {points} points for {reward}!\n\nYour new balance: {new_balance} points"
    },
    'points_redemption_failed': {
        'fa': "❌ تبدیل ناموفق\n\n{error_message}\n\nلطفاً دوباره تلاش کنید یا جایزه دیگری را انتخاب کنید.",
        'en': "❌ Redemption Failed\n\n{error_message}\n\nPlease try again or select a different reward."
    },
    'points_earn': {
        'fa': "💫 کسب امتیازات\n\nراه‌های کسب امتیازات:\n\n1. 🛍️ خرید محصولات\n2. 👥 معرفی دوستان\n3. 📱 ورود روزانه\n4. 🎮 انجام وظایف\n\nاز امروز شروع به کسب امتیازات کنید!",
        'en': "💫 Earn Points\n\nHere's how you can earn points:\n\n1. 🛍️ Make purchases\n2. 👥 Refer friends\n3. 📱 Daily check-ins\n4. 🎮 Complete tasks\n\nStart earning points today!"
    },
    'btn_points': {
        'fa': "💎 امتیازات",
        'en': "💎 Points"
    },
    'btn_points_balance': {
        'fa': "💰 موجودی",
        'en': "💰 Balance"
    },
    'btn_points_history': {
        'fa': "📊 تاریخچه",
        'en': "📊 History"
    },
    'btn_points_redeem': {
        'fa': "🎁 تبدیل",
        'en': "🎁 Redeem"
    },
    'btn_points_earn': {
        'fa': "💫 کسب امتیازات",
        'en': "💫 Earn Points"
    },
    'btn_back_points': {
        'fa': "⬅️ بازگشت به امتیازات",
        'en': "⬅️ Back to Points"
    },
}

def get_default_message(name, lang='fa'):
    """Get default message by name and language"""
    messages = {
        'fa': {
            # ... existing messages ...
            
            # Points menu
            'btn_points': '💎 امتیازات',
            'points_menu': '🎯 *منوی امتیازات*\n\nامتیازات شما: *{points}*\n\nگزینه مورد نظر را انتخاب کنید:',
            'btn_points_balance': '💎 موجودی امتیازات',
            'btn_points_history': '📊 تاریخچه امتیازات',
            'btn_points_redeem': '🎁 استفاده از امتیازات',
            'btn_points_earn': '❓ نحوه کسب امتیاز',
            
            # Points balance
            'points_balance': '💎 *موجودی امتیازات*\n\nامتیازات شما: *{points}*\n\nاز منوی امتیازات برای مشاهده گزینه‌های دیگر استفاده کنید.',
            
            # Points history
            'points_history': '📊 *تاریخچه امتیازات*\n\n',
            'points_history_empty': '📊 *تاریخچه امتیازات*\n\nهیچ تراکنشی یافت نشد.\n\nاز منوی امتیازات برای مشاهده گزینه‌های دیگر استفاده کنید.',
            
            # Points redemption
            'points_redemption': '🎁 *استفاده از امتیازات*\n\nامتیازات شما: *{points}*\n\nگزینه مورد نظر را برای استفاده انتخاب کنید:',
            'points_redemption_empty': '🎁 *استفاده از امتیازات*\n\nدر حال حاضر هیچ گزینه‌ای برای استفاده از امتیازات موجود نیست.\n\nاز منوی امتیازات برای مشاهده گزینه‌های دیگر استفاده کنید.',
            'points_insufficient': '❌ امتیازات شما کافی نیست!',
            'points_no_subscription': '❌ اشتراک فعالی یافت نشد!',
            'points_redeem_success': '✅ امتیازات با موفقیت استفاده شد!',
            'points_reward_success': '🎉 *استفاده از امتیازات موفقیت‌آمیز بود!*\n\nامتیازات استفاده شده: *{points}*\nپاداش: *{reward}*',
            'points_discount_code': '\n\nکد تخفیف شما: *{code}*',
            'points_redeem_failed': '❌ خطا در استفاده از امتیازات!',
            'points_invalid_rule': '❌ گزینه نامعتبر است!',
            
            # Points earn info
            'points_earn_info': '❓ *نحوه کسب امتیاز*\n\nشما می‌توانید از طریق موارد زیر امتیاز کسب کنید:\n\n'
                                  '• خرید اشتراک\n'
                                  '• معرفی کاربران جدید\n'
                                  '• شرکت در مسابقات و رویدادها\n'
                                  '• استفاده از کدهای تخفیف\n\n'
                                  'از منوی امتیازات برای مشاهده گزینه‌های دیگر استفاده کنید.',
        },
        'en': {
            # ... existing messages ...
            
            # Points menu
            'btn_points': '💎 Points',
            'points_menu': '🎯 *Points Menu*\n\nYour points: *{points}*\n\nChoose an option:',
            'btn_points_balance': '💎 Points Balance',
            'btn_points_history': '📊 Points History',
            'btn_points_redeem': '🎁 Redeem Points',
            'btn_points_earn': '❓ How to Earn',
            
            # Points balance
            'points_balance': '💎 *Points Balance*\n\nYour points: *{points}*\n\nUse the points menu to see other options.',
            
            # Points history
            'points_history': '📊 *Points History*\n\n',
            'points_history_empty': '📊 *Points History*\n\nNo transactions found.\n\nUse the points menu to see other options.',
            
            # Points redemption
            'points_redemption': '🎁 *Redeem Points*\n\nYour points: *{points}*\n\nChoose a reward to redeem:',
            'points_redemption_empty': '🎁 *Redeem Points*\n\nNo redemption options available at the moment.\n\nUse the points menu to see other options.',
            'points_insufficient': '❌ Insufficient points!',
            'points_no_subscription': '❌ No active subscription found!',
            'points_redeem_success': '✅ Points redeemed successfully!',
            'points_reward_success': '🎉 *Points Redemption Successful!*\n\nPoints spent: *{points}*\nReward: *{reward}*',
            'points_discount_code': '\n\nYour discount code: *{code}*',
            'points_redeem_failed': '❌ Failed to redeem points!',
            'points_invalid_rule': '❌ Invalid redemption option!',
            
            # Points earn info
            'points_earn_info': '❓ *How to Earn Points*\n\nYou can earn points through:\n\n'
                                  '• Purchasing subscriptions\n'
                                  '• Referring new users\n'
                                  '• Participating in contests and events\n'
                                  '• Using discount codes\n\n'
                                  'Use the points menu to see other options.',
        }
    }
    
    return messages.get(lang, messages['en']).get(name, f"Message not found: {name}") 