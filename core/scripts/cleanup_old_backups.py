"""
Cleanup script for old backup records.

This script removes old backup records and their associated files based on retention policies.
It also performs database maintenance tasks like vacuuming and analyzing tables.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models.backup import SystemBackup, BackupSchedule, BackupStatus
from app.core.services.storage_service import StorageService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_backups(db: Session):
    """Clean up old backup records based on retention policies."""
    try:
        # Get all backup schedules
        schedules = db.query(BackupSchedule).filter(BackupSchedule.is_active == True).all()
        storage_service = StorageService()
        
        for schedule in schedules:
            logger.info(f"Processing schedule: {schedule.name}")
            
            # Calculate retention date
            retention_date = datetime.utcnow() - timedelta(days=schedule.retention_days)
            
            # Get backups to delete
            old_backups = (
                db.query(SystemBackup)
                .filter(
                    SystemBackup.schedule_id == schedule.id,
                    SystemBackup.created_at < retention_date,
                    SystemBackup.status.in_([
                        BackupStatus.COMPLETED,
                        BackupStatus.VERIFIED,
                        BackupStatus.FAILED
                    ])
                )
                .order_by(SystemBackup.created_at)
                .limit(1000)  # Process in batches
                .all()
            )
            
            for backup in old_backups:
                try:
                    # Delete backup file
                    if backup.status in [BackupStatus.COMPLETED, BackupStatus.VERIFIED]:
                        storage_service.delete_file(
                            backup.storage_provider,
                            backup.storage_path
                        )
                    
                    # Update backup status
                    backup.status = BackupStatus.DELETED
                    db.add(backup)
                    
                    logger.info(f"Deleted backup: {backup.name} (ID: {backup.id})")
                except Exception as e:
                    logger.error(f"Error deleting backup {backup.id}: {str(e)}")
                    continue
            
            # Commit changes for this schedule
            db.commit()
            
            # Keep only the maximum number of backups
            if schedule.max_backups > 0:
                excess_backups = (
                    db.query(SystemBackup)
                    .filter(
                        SystemBackup.schedule_id == schedule.id,
                        SystemBackup.status.in_([
                            BackupStatus.COMPLETED,
                            BackupStatus.VERIFIED
                        ])
                    )
                    .order_by(SystemBackup.created_at.desc())
                    .offset(schedule.max_backups)
                    .limit(1000)
                    .all()
                )
                
                for backup in excess_backups:
                    try:
                        # Delete backup file
                        storage_service.delete_file(
                            backup.storage_provider,
                            backup.storage_path
                        )
                        
                        # Update backup status
                        backup.status = BackupStatus.DELETED
                        db.add(backup)
                        
                        logger.info(f"Deleted excess backup: {backup.name} (ID: {backup.id})")
                    except Exception as e:
                        logger.error(f"Error deleting excess backup {backup.id}: {str(e)}")
                        continue
                
                # Commit changes for excess backups
                db.commit()
        
        # Perform database maintenance
        logger.info("Performing database maintenance...")
        
        # Vacuum analyze tables
        db.execute(text("VACUUM ANALYZE system_backups"))
        db.execute(text("VACUUM ANALYZE backup_schedules"))
        
        logger.info("Cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise

def main():
    """Main entry point for the cleanup script."""
    logger.info("Starting backup cleanup process...")
    
    try:
        db = next(get_db())
        cleanup_old_backups(db)
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    main() 