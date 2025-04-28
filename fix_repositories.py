#!/usr/bin/env python
"""
اسکریپت اصلاح ریپوزیتوری‌ها 

این اسکریپت تمام ریپوزیتوری‌های موجود در پروژه را اصلاح می‌کند تا از
کلاس BaseRepository به درستی ارث‌بری کنند و تعامل صحیح با دیتابیس داشته باشند.
"""

import os
import re
import glob
from typing import List, Dict, Tuple

# مسیر پایه ریپوزیتوری‌ها
REPO_DIR = "db/repositories"
# الگوی فایل‌های ریپوزیتوری
REPO_PATTERNS = ["*_repo.py", "*_repository.py"]
# فایل‌هایی که باید نادیده گرفته شوند
IGNORE_FILES = ["base_repository.py", "__init__.py"]

# نگاشت نام کلاس ریپوزیتوری به نام کلاس مدل
REPO_TO_MODEL_MAP = {
    "UserRepository": "User",
    "PanelRepository": "Panel",
    "InboundRepository": "Inbound",
    "ClientRepository": "ClientAccount",
    "AccountRepository": "AccountLog",
    "PlanRepository": "Plan",
    "SettingRepository": "Setting",
    "TransactionRepository": "Transaction",
    "OrderRepository": "Order",
    "WalletRepository": "Wallet",
    "BankCardRepository": "BankCard",
    "DiscountCodeRepository": "DiscountCode",
    "ReceiptLogRepository": "ReceiptLog"
}

def find_repository_files() -> List[str]:
    """یافتن تمام فایل‌های ریپوزیتوری"""
    repo_files = []
    for pattern in REPO_PATTERNS:
        repo_files.extend(glob.glob(os.path.join(REPO_DIR, pattern)))
    
    # حذف فایل‌های نادیده گرفته شده
    repo_files = [f for f in repo_files if os.path.basename(f) not in IGNORE_FILES]
    return repo_files

def extract_repo_class_name(file_content: str) -> str:
    """استخراج نام کلاس ریپوزیتوری از محتوای فایل"""
    match = re.search(r"class\s+(\w+)\s*(?:\(([^)]+)\))?:", file_content)
    if match:
        return match.group(1)
    return ""

def extract_model_name(file_content: str) -> str:
    """استخراج نام کلاس مدل از محتوای فایل"""
    # Import statements for models
    model_imports = re.findall(r"from\s+db\.models\.\w+\s+import\s+([^,]+)", file_content)
    if model_imports:
        # First imported model is usually the main model
        return model_imports[0].strip()
    return ""

def needs_init_correction(file_content: str, repo_class: str) -> bool:
    """بررسی نیاز به اصلاح متد سازنده"""
    # Check if the repository inherits from BaseRepository
    inherits_base = re.search(fr"class\s+{repo_class}\s*\(\s*BaseRepository", file_content)
    if not inherits_base:
        return False
    
    # Check if __init__ method properly calls super().__init__(session, Model)
    init_correct = re.search(r"super\(\)\.__init__\(session,\s+\w+\)", file_content)
    return not bool(init_correct)

def fix_repository_file(file_path: str) -> Tuple[bool, str]:
    """اصلاح یک فایل ریپوزیتوری"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # اگر فایل از قبل اصلاح شده است، نیازی به اصلاح نیست
    if "super().__init__(session," in content:
        return False, "فایل از قبل اصلاح شده است"
    
    # استخراج نام کلاس ریپوزیتوری
    repo_class = extract_repo_class_name(content)
    if not repo_class:
        return False, "کلاس ریپوزیتوری یافت نشد"
    
    # استخراج نام کلاس مدل
    model_class = REPO_TO_MODEL_MAP.get(repo_class, None)
    if not model_class:
        model_class = extract_model_name(content)
    
    if not model_class:
        return False, "کلاس مدل یافت نشد"
    
    # بررسی نیاز به اصلاح
    if not needs_init_correction(content, repo_class):
        return False, "نیازی به اصلاح ندارد"
    
    # الگوی جایگزینی برای کلاس ریپوزیتوری
    class_pattern = fr"class\s+{repo_class}\s*\(\s*BaseRepository\s*\):(?:[^\n]*\n)(?:\s+[^\n]*\n)*"
    class_with_init = fr"class {repo_class}(BaseRepository):\n    def __init__(self, session: AsyncSession):\n        super().__init__(session, {model_class})\n"
    
    # اصلاح کلاس ریپوزیتوری
    corrected_content = re.sub(class_pattern, class_with_init, content)
    
    # ذخیره فایل اصلاح شده
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(corrected_content)
    
    return True, f"فایل {file_path} با موفقیت اصلاح شد"

def main():
    """
    تابع اصلی اجرای اسکریپت
    """
    repo_files = find_repository_files()
    print(f"تعداد {len(repo_files)} فایل ریپوزیتوری یافت شد")
    
    for file_path in repo_files:
        success, message = fix_repository_file(file_path)
        status = "✅" if success else "❌"
        print(f"{status} {file_path}: {message}")

if __name__ == "__main__":
    main() 