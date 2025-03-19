import os
import logging
import argparse
import subprocess
from datetime import datetime
from typing import Optional
from pathlib import Path

from .config import db_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Database backup and restore operations."""
    
    def __init__(self, backup_dir: str = "backups"):
        """Initialize backup manager."""
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Database connection parameters
        self.db_name = db_settings.DB_NAME
        self.db_user = db_settings.DB_USER
        self.db_host = db_settings.DB_HOST
        self.db_port = db_settings.DB_PORT
    
    def _get_backup_filename(self, timestamp: Optional[datetime] = None) -> str:
        """Generate backup filename with timestamp."""
        if timestamp is None:
            timestamp = datetime.now()
        return f"moonvpn_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.sql"
    
    def create_backup(self, compress: bool = True) -> str:
        """Create a database backup."""
        try:
            # Generate backup filename
            backup_file = self.backup_dir / self._get_backup_filename()
            
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", self.db_name,
                "-F", "c" if compress else "p",
                "-f", str(backup_file)
            ]
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_settings.DB_PASSWORD
            
            # Execute backup command
            subprocess.run(cmd, env=env, check=True)
            
            logger.info(f"Database backup created successfully: {backup_file}")
            return str(backup_file)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create database backup: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during backup: {str(e)}")
            raise
    
    def restore_backup(self, backup_file: str) -> None:
        """Restore database from backup."""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            # Build pg_restore command
            cmd = [
                "pg_restore",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", self.db_name,
                "-c",  # Clean (drop) database objects before recreating
                "-1",  # Process everything in a single transaction
                str(backup_path)
            ]
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_settings.DB_PASSWORD
            
            # Execute restore command
            subprocess.run(cmd, env=env, check=True)
            
            logger.info(f"Database restored successfully from: {backup_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restore database backup: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during restore: {str(e)}")
            raise
    
    def list_backups(self) -> list[str]:
        """List available database backups."""
        try:
            backups = []
            for file in self.backup_dir.glob("moonvpn_backup_*.sql"):
                backups.append(str(file))
            return sorted(backups, reverse=True)
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            raise
    
    def cleanup_old_backups(self, days: int = 30) -> None:
        """Remove backups older than specified days."""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            removed = 0
            
            for file in self.backup_dir.glob("moonvpn_backup_*.sql"):
                if file.stat().st_mtime < cutoff_date:
                    file.unlink()
                    removed += 1
            
            logger.info(f"Removed {removed} old backup files")
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")
            raise


def main() -> None:
    """Main function to run backup operations."""
    parser = argparse.ArgumentParser(description="Database backup and restore tools")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a new database backup"
    )
    parser.add_argument(
        "--restore",
        type=str,
        help="Restore database from backup file"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups"
    )
    parser.add_argument(
        "--cleanup",
        type=int,
        default=30,
        help="Remove backups older than specified days"
    )
    parser.add_argument(
        "--backup-dir",
        type=str,
        default="backups",
        help="Directory to store backups"
    )
    
    args = parser.parse_args()
    
    try:
        backup_manager = DatabaseBackup(args.backup_dir)
        
        if args.backup:
            backup_manager.create_backup()
        
        if args.restore:
            backup_manager.restore_backup(args.restore)
        
        if args.list:
            backups = backup_manager.list_backups()
            if backups:
                print("\nAvailable backups:")
                for backup in backups:
                    print(f"- {backup}")
            else:
                print("No backups found")
        
        if args.cleanup:
            backup_manager.cleanup_old_backups(args.cleanup)
        
        if not any([args.backup, args.restore, args.list, args.cleanup]):
            parser.print_help()
    except KeyboardInterrupt:
        logger.info("Backup operation interrupted by user")
    except Exception as e:
        logger.error(f"Backup operation failed: {str(e)}")
        raise


if __name__ == "__main__":
    main() 