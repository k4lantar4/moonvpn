import os
import sys

# مسیر فایل‌هایی که می‌خواهیم بررسی کنیم
paths_to_check = [
    "/app/bot/commands/plans.py",
    "/app/bot/main.py",
    "/app/bot/callbacks/common.py",
    "/app/bot/buttons/plan_buttons.py",
    "/app/core/services/plan_service.py"
]

# نمایش معلومات درباره سیستم
print(f"سیستم عامل: {sys.platform}")
print(f"نسخه پایتون: {sys.version}")
print(f"مسیر اجرا: {os.getcwd()}")
print(f"متغیرهای محیطی: {list(os.environ.keys())}")

# بررسی محتوای فایل‌ها
for path in paths_to_check:
    print(f"\nبررسی فایل: {path}")
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
                # نمایش بخشی از محتوای فایل
                preview = content[:100].replace('\n', ' ') + '...'
                print(f"محتوا: {preview}")
                print(f"اندازه فایل: {len(content)} بایت")
                
                # بررسی کلمات کلیدی مهم
                keywords = [
                    "register_plans_command", 
                    "Command(\"plans\")", 
                    "get_plans_keyboard",
                    "get_all_active_plans"
                ]
                for kw in keywords:
                    if kw in content:
                        print(f"✅ کلمه کلیدی '{kw}' پیدا شد")
                    else:
                        print(f"❌ کلمه کلیدی '{kw}' پیدا نشد")
        else:
            print(f"❌ فایل وجود ندارد!")
    except Exception as e:
        print(f"خطا در خواندن فایل: {e}")

print("\nعملیات بررسی به پایان رسید") 