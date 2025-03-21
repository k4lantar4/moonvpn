"""
Legacy code management service.
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from core.config import settings
from core.database.models import LegacyCode, LegacyMigration
from core.services.notification import NotificationService

logger = logging.getLogger(__name__)

class LegacyCodeService:
    """Service for managing legacy code and migrations."""

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.legacy_dir = Path(settings.LEGACY_CODE_DIR)
        self.legacy_dir.mkdir(parents=True, exist_ok=True)

    async def archive_legacy_code(self, code_path: str, description: str) -> LegacyCode:
        """Archive legacy code with documentation."""
        try:
            # Create unique archive directory
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            archive_dir = self.legacy_dir / f"archive_{timestamp}"
            archive_dir.mkdir(parents=True)
            
            # Copy code to archive
            source_path = Path(code_path)
            if source_path.is_file():
                shutil.copy2(source_path, archive_dir)
            else:
                shutil.copytree(source_path, archive_dir / source_path.name)
            
            # Create legacy code record
            legacy_code = LegacyCode(
                original_path=str(source_path),
                archive_path=str(archive_dir),
                description=description,
                archived_at=datetime.utcnow()
            )
            
            self.db.add(legacy_code)
            self.db.commit()
            
            # Send notification
            await self.notification_service.send_admin_notification(
                "Legacy Code Archived",
                f"Path: {code_path}\nDescription: {description}"
            )
            
            return legacy_code
            
        except Exception as e:
            logger.error(f"Error archiving legacy code: {str(e)}")
            raise

    async def create_migration_plan(
        self,
        legacy_code_id: int,
        new_implementation: str,
        steps: List[Dict[str, Any]]
    ) -> LegacyMigration:
        """Create a migration plan for legacy code."""
        try:
            legacy_code = self.db.query(LegacyCode).get(legacy_code_id)
            if not legacy_code:
                raise ValueError(f"Legacy code {legacy_code_id} not found")
            
            migration = LegacyMigration(
                legacy_code_id=legacy_code_id,
                new_implementation=new_implementation,
                steps=steps,
                status="planned",
                created_at=datetime.utcnow()
            )
            
            self.db.add(migration)
            self.db.commit()
            
            # Send notification
            await self.notification_service.send_admin_notification(
                "Legacy Migration Plan Created",
                f"Legacy Code: {legacy_code.original_path}\n"
                f"Steps: {len(steps)}"
            )
            
            return migration
            
        except Exception as e:
            logger.error(f"Error creating migration plan: {str(e)}")
            raise

    async def execute_migration(self, migration_id: int) -> Dict[str, Any]:
        """Execute a legacy code migration plan."""
        try:
            migration = self.db.query(LegacyMigration).get(migration_id)
            if not migration:
                raise ValueError(f"Migration {migration_id} not found")
            
            migration.status = "in_progress"
            migration.started_at = datetime.utcnow()
            self.db.commit()
            
            results = []
            for step in migration.steps:
                try:
                    # Execute migration step
                    # This is a placeholder - actual implementation would depend
                    # on the type of migration steps
                    result = await self._execute_migration_step(step)
                    results.append({
                        "step": step,
                        "status": "completed",
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "step": step,
                        "status": "failed",
                        "error": str(e)
                    })
                    raise
            
            migration.status = "completed"
            migration.completed_at = datetime.utcnow()
            migration.results = results
            self.db.commit()
            
            # Send notification
            await self.notification_service.send_admin_notification(
                "Legacy Migration Completed",
                f"Migration ID: {migration_id}\n"
                f"Results: {results}"
            )
            
            return {
                "migration_id": migration_id,
                "status": "completed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error executing migration: {str(e)}")
            if migration:
                migration.status = "failed"
                migration.error_message = str(e)
                self.db.commit()
            raise

    async def rollback_migration(self, migration_id: int) -> Dict[str, Any]:
        """Rollback a legacy code migration."""
        try:
            migration = self.db.query(LegacyMigration).get(migration_id)
            if not migration:
                raise ValueError(f"Migration {migration_id} not found")
            
            # Reverse the steps and execute rollback
            reversed_steps = list(reversed(migration.steps))
            results = []
            
            for step in reversed_steps:
                try:
                    # Execute rollback step
                    result = await self._rollback_migration_step(step)
                    results.append({
                        "step": step,
                        "status": "rolled_back",
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "step": step,
                        "status": "rollback_failed",
                        "error": str(e)
                    })
                    raise
            
            migration.status = "rolled_back"
            migration.rollback_at = datetime.utcnow()
            migration.rollback_results = results
            self.db.commit()
            
            # Send notification
            await self.notification_service.send_admin_notification(
                "Legacy Migration Rolled Back",
                f"Migration ID: {migration_id}\n"
                f"Results: {results}"
            )
            
            return {
                "migration_id": migration_id,
                "status": "rolled_back",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error rolling back migration: {str(e)}")
            if migration:
                migration.status = "rollback_failed"
                migration.error_message = str(e)
                self.db.commit()
            raise

    async def get_legacy_code_status(self) -> Dict[str, Any]:
        """Get status of all legacy code and migrations."""
        try:
            legacy_codes = self.db.query(LegacyCode).all()
            migrations = self.db.query(LegacyMigration).all()
            
            return {
                "total_legacy_codes": len(legacy_codes),
                "total_migrations": len(migrations),
                "migrations_by_status": {
                    "planned": len([m for m in migrations if m.status == "planned"]),
                    "in_progress": len([m for m in migrations if m.status == "in_progress"]),
                    "completed": len([m for m in migrations if m.status == "completed"]),
                    "failed": len([m for m in migrations if m.status == "failed"]),
                    "rolled_back": len([m for m in migrations if m.status == "rolled_back"])
                },
                "latest_activities": [
                    {
                        "type": "migration",
                        "id": m.id,
                        "status": m.status,
                        "timestamp": m.created_at
                    }
                    for m in sorted(migrations, key=lambda x: x.created_at, reverse=True)[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting legacy code status: {str(e)}")
            raise

    async def _execute_migration_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single migration step."""
        # This is a placeholder - actual implementation would depend
        # on the type of migration steps
        return {"status": "completed"}

    async def _rollback_migration_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback a single migration step."""
        # This is a placeholder - actual implementation would depend
        # on the type of migration steps
        return {"status": "rolled_back"} 