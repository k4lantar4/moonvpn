#!/usr/bin/env python
"""
اسکریپت اصلاح سرویس‌ها

این اسکریپت تمام سرویس‌های موجود در پروژه را اصلاح می‌کند تا
ریپوزیتوری‌ها را با ارسال جلسه دیتابیس ایجاد کنند و پارامتر session را
در فراخوانی متدهای ریپوزیتوری حذف کنند.
"""

import os
import re
import glob
from typing import List, Dict, Tuple

# مسیر پایه سرویس‌ها
SERVICE_DIR = "core/services"
# الگوی فایل‌های سرویس
SERVICE_PATTERNS = ["*_service.py"]

# نگاشت نام ریپوزیتوری به نام متغیر ریپوزیتوری در کلاس سرویس
REPO_VAR_MAP = {
    "UserRepository": "user_repo",
    "PanelRepository": "panel_repo",
    "InboundRepository": "inbound_repo",
    "ClientRepository": "client_repo",
    "AccountRepository": "account_repo",
    "PlanRepository": "plan_repo",
    "SettingRepository": "setting_repo",
    "TransactionRepository": "transaction_repo",
    "OrderRepository": "order_repo",
    "WalletRepository": "wallet_repo",
    "BankCardRepository": "repository",
    "DiscountCodeRepository": "discount_repo",
    "ReceiptLogRepository": "receipt_repo"
}

def find_service_files() -> List[str]:
    """یافتن تمام فایل‌های سرویس"""
    service_files = []
    for pattern in SERVICE_PATTERNS:
        service_files.extend(glob.glob(os.path.join(SERVICE_DIR, pattern)))
    return service_files

def extract_repo_initializations(file_content: str) -> List[Tuple[str, str]]:
    """استخراج نام‌های ریپوزیتوری‌ها و نحوه ایجاد آنها"""
    # Finding all repository class imports
    repo_imports = re.findall(r"from\s+db\.repositories\.\w+\s+import\s+(\w+Repository)", file_content)
    
    # Finding repository initializations in __init__ methods
    # Pattern: self.repo_name = RepoClass()
    repo_inits = []
    for repo_class in repo_imports:
        # Find variable names for repositories
        repo_var = REPO_VAR_MAP.get(repo_class, "repository")
        # Look for initialization patterns
        init_patterns = [
            fr"self\.{repo_var}\s*=\s*{repo_class}\(\)",  # No params
            fr"self\.{repo_var}\s*=\s*{repo_class}\([^)]*\)",  # With params
        ]
        
        for pattern in init_patterns:
            match = re.search(pattern, file_content)
            if match:
                repo_inits.append((repo_class, match.group(0)))
                break
    
    return repo_inits

def fix_repo_initialization(file_content: str, repo_class: str, init_line: str) -> str:
    """اصلاح نحوه ایجاد ریپوزیتوری‌ها"""
    # Check if already fixed
    if f"{repo_class}(self.session)" in init_line or f"{repo_class}(session)" in init_line:
        return file_content  # Already fixed
    
    # Replace with proper initialization with session parameter
    repo_var = REPO_VAR_MAP.get(repo_class, "repository")
    old_pattern = fr"self\.{repo_var}\s*=\s*{repo_class}\([^)]*\)"
    new_init = f"self.{repo_var} = {repo_class}(self.session)"
    
    return re.sub(old_pattern, new_init, file_content)

def remove_session_params(file_content: str, repo_class: str) -> str:
    """حذف پارامتر session از فراخوانی‌های متدهای ریپوزیتوری"""
    repo_var = REPO_VAR_MAP.get(repo_class, "repository")
    
    # Pattern for repository method calls with session parameter
    # self.repo.method(self.session, other_params)
    method_call_pattern = fr"(self\.{repo_var}\.[\w_]+)\(self\.session,?\s*([^)]*)\)"
    
    # Replace with calls without session parameter
    # self.repo.method(other_params)
    fixed_content = re.sub(method_call_pattern, r"\1(\2)", file_content)
    
    return fixed_content

def fix_service_file(file_path: str) -> Tuple[bool, str]:
    """اصلاح یک فایل سرویس"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # استخراج نحوه ایجاد ریپوزیتوری‌ها
    repo_inits = extract_repo_initializations(content)
    if not repo_inits:
        return False, "ریپوزیتوری یافت نشد"
    
    modified = False
    modified_content = content
    
    # اصلاح نحوه ایجاد ریپوزیتوری‌ها
    for repo_class, init_line in repo_inits:
        new_content = fix_repo_initialization(modified_content, repo_class, init_line)
        if new_content != modified_content:
            modified = True
            modified_content = new_content
    
        # حذف پارامتر session از فراخوانی‌های متدهای ریپوزیتوری
        new_content = remove_session_params(modified_content, repo_class)
        if new_content != modified_content:
            modified = True
            modified_content = new_content
    
    if not modified:
        return False, "نیازی به اصلاح ندارد"
    
    # ذخیره فایل اصلاح شده
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    return True, f"فایل {file_path} با موفقیت اصلاح شد"

def main():
    """
    تابع اصلی اجرای اسکریپت
    """
    service_files = find_service_files()
    print(f"تعداد {len(service_files)} فایل سرویس یافت شد")
    
    for file_path in service_files:
        success, message = fix_service_file(file_path)
        status = "✅" if success else "❌"
        print(f"{status} {file_path}: {message}")

if __name__ == "__main__":
    main() 