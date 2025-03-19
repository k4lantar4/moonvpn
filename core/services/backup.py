import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import telegram
from celery import shared_task
from django.conf import settings
from django.core.management import call_command

class BackupManager:
    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.admin_group_id = settings.TELEGRAM_ADMIN_GROUP_ID
        
    def _create_backup_name(self):
        """Create a unique backup name with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}"
        
    def _create_db_backup(self, backup_path: Path):
        """Create database backup"""
        db_file = backup_path / "database.json"
        call_command("dumpdata", output=str(db_file))
        
    def _backup_config_files(self, backup_path: Path):
        """Backup configuration files"""
        config_dir = backup_path / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Backup .env file
        if os.path.exists(".env"):
            shutil.copy2(".env", config_dir / ".env")
            
        # Backup nginx configs
        nginx_dir = config_dir / "nginx"
        nginx_dir.mkdir(exist_ok=True)
        if os.path.exists("nginx"):
            shutil.copytree("nginx", nginx_dir, dirs_exist_ok=True)
    
    def _backup_user_data(self, backup_path: Path):
        """Backup user uploaded files"""
        media_dir = backup_path / "media"
        if os.path.exists(settings.MEDIA_ROOT):
            shutil.copytree(settings.MEDIA_ROOT, media_dir, dirs_exist_ok=True)
    
    def _create_archive(self, backup_path: Path) -> Path:
        """Create compressed archive of backup"""
        archive_name = f"{backup_path.name}.tar.gz"
        archive_path = self.backup_dir / archive_name
        
        subprocess.run([
            "tar", 
            "-czf", 
            str(archive_path),
            "-C", 
            str(self.backup_dir),
            backup_path.name
        ])
        
        return archive_path
    
    def _cleanup_old_backups(self, keep_last: int = 48):  # Keep last 24 hours (48 backups)
        """Remove old backups to save space"""
        backups = sorted(self.backup_dir.glob("backup_*.tar.gz"))
        if len(backups) > keep_last:
            for backup in backups[:-keep_last]:
                backup.unlink()
    
    def _notify_telegram(self, success: bool, backup_path: Path = None, error: str = None):
        """Send backup status notification to Telegram admin group"""
        if success:
            message = f"✅ بکاپ با موفقیت انجام شد!\n\n"
            message += f"📁 نام فایل: {backup_path.name}\n"
            message += f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            message = f"❌ خطا در تهیه بکاپ!\n\n"
            message += f"⚠️ علت: {error}\n"
            message += f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        self.bot.send_message(chat_id=self.admin_group_id, text=message)

    async def create_backup(self):
        """Create a complete system backup"""
        try:
            backup_name = self._create_backup_name()
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir()
            
            # Create backups
            self._create_db_backup(backup_path)
            self._backup_config_files(backup_path)
            self._backup_user_data(backup_path)
            
            # Create archive
            archive_path = self._create_archive(backup_path)
            
            # Cleanup
            shutil.rmtree(backup_path)
            self._cleanup_old_backups()
            
            # Notify success
            self._notify_telegram(True, archive_path)
            
            return str(archive_path)
            
        except Exception as e:
            # Notify error
            self._notify_telegram(False, error=str(e))
            raise

@shared_task
def backup_system():
    """Celery task for automated backup"""
    backup_manager = BackupManager()
    return backup_manager.create_backup() 