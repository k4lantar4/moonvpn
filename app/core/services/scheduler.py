"""
Scheduler Service for System Health Monitoring.

This module provides scheduling functionality for automated recovery actions
and system maintenance tasks.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.core.models.recovery import RecoveryAction, RecoveryStatus
from app.core.services.recovery import RecoveryService
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

class SchedulerService:
    """Service for managing scheduled recovery actions and maintenance tasks."""

    def __init__(self, db: Session):
        """Initialize the scheduler service.
        
        Args:
            db: Database session for persistence operations
        """
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.recovery_service = RecoveryService(db)
        self.scheduled_jobs: Dict[str, str] = {}  # job_id -> action_id mapping

    async def start(self):
        """Start the scheduler service."""
        try:
            self.scheduler.start()
            logger.info("Scheduler service started successfully")
        except Exception as e:
            logger.error(f"Error starting scheduler service: {str(e)}")
            raise

    async def stop(self):
        """Stop the scheduler service."""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler service: {str(e)}")
            raise

    async def schedule_recovery_action(
        self,
        action_id: int,
        schedule_type: str,
        schedule_params: Dict[str, Any]
    ) -> str:
        """Schedule a recovery action.
        
        Args:
            action_id: ID of the recovery action to schedule
            schedule_type: Type of schedule (cron, interval, date)
            schedule_params: Schedule parameters
            
        Returns:
            str: Job ID of the scheduled task
        """
        action = self.recovery_service.get_recovery_action(action_id)
        if not action:
            raise ValueError(f"Recovery action {action_id} not found")

        try:
            # Create trigger based on schedule type
            trigger = self._create_trigger(schedule_type, schedule_params)
            
            # Schedule the job
            job = self.scheduler.add_job(
                self._execute_scheduled_action,
                trigger=trigger,
                args=[action_id],
                id=f"recovery_{action_id}_{datetime.utcnow().timestamp()}",
                replace_existing=True
            )
            
            # Store job mapping
            self.scheduled_jobs[job.id] = str(action_id)
            
            logger.info(f"Scheduled recovery action {action_id} with job ID {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Error scheduling recovery action {action_id}: {str(e)}")
            raise

    def _create_trigger(
        self,
        schedule_type: str,
        schedule_params: Dict[str, Any]
    ) -> Any:
        """Create an APScheduler trigger.
        
        Args:
            schedule_type: Type of schedule
            schedule_params: Schedule parameters
            
        Returns:
            Any: APScheduler trigger instance
        """
        if schedule_type == "cron":
            return CronTrigger(**schedule_params)
        elif schedule_type == "interval":
            return IntervalTrigger(**schedule_params)
        elif schedule_type == "date":
            return schedule_params.get("date")
        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")

    async def _execute_scheduled_action(self, action_id: int):
        """Execute a scheduled recovery action.
        
        Args:
            action_id: ID of the recovery action to execute
        """
        try:
            await self.recovery_service.execute_recovery_action(action_id)
            logger.info(f"Successfully executed scheduled recovery action {action_id}")
        except Exception as e:
            logger.error(f"Error executing scheduled recovery action {action_id}: {str(e)}")

    async def cancel_scheduled_action(self, job_id: str) -> bool:
        """Cancel a scheduled recovery action.
        
        Args:
            job_id: ID of the scheduled job
            
        Returns:
            bool: True if job was cancelled successfully
        """
        try:
            if job_id in self.scheduled_jobs:
                self.scheduler.remove_job(job_id)
                del self.scheduled_jobs[job_id]
                logger.info(f"Cancelled scheduled job {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling scheduled job {job_id}: {str(e)}")
            return False

    async def get_scheduled_actions(self) -> List[Dict[str, Any]]:
        """Get all scheduled recovery actions.
        
        Returns:
            List[Dict[str, Any]]: List of scheduled actions with their details
        """
        try:
            scheduled_jobs = []
            for job_id, action_id in self.scheduled_jobs.items():
                job = self.scheduler.get_job(job_id)
                if job:
                    action = self.recovery_service.get_recovery_action(int(action_id))
                    if action:
                        scheduled_jobs.append({
                            "job_id": job_id,
                            "action_id": action_id,
                            "next_run_time": job.next_run_time,
                            "trigger": str(job.trigger),
                            "action": action.to_dict()
                        })
            return scheduled_jobs
        except Exception as e:
            logger.error(f"Error getting scheduled actions: {str(e)}")
            return []

    async def reschedule_action(
        self,
        job_id: str,
        schedule_type: str,
        schedule_params: Dict[str, Any]
    ) -> bool:
        """Reschedule a recovery action.
        
        Args:
            job_id: ID of the scheduled job
            schedule_type: New schedule type
            schedule_params: New schedule parameters
            
        Returns:
            bool: True if job was rescheduled successfully
        """
        try:
            if job_id in self.scheduled_jobs:
                action_id = self.scheduled_jobs[job_id]
                await self.cancel_scheduled_action(job_id)
                await self.schedule_recovery_action(
                    int(action_id),
                    schedule_type,
                    schedule_params
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error rescheduling job {job_id}: {str(e)}")
            return False 