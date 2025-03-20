#!/usr/bin/env python3
"""
System cleanup script for MoonVPN.
"""

import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from core.config import settings
from core.database import get_db
from core.services.cleanup import CleanupService

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_cleanup(args: argparse.Namespace) -> None:
    """Run cleanup operations based on arguments."""
    try:
        db = next(get_db())
        cleanup_service = CleanupService(db)
        
        if args.all:
            results = await cleanup_service.cleanup_all()
            logger.info("Completed all cleanup operations:")
            for operation, result in results.items():
                logger.info(f"{operation}: {result}")
        else:
            if args.backups:
                result = await cleanup_service.cleanup_old_backups(args.backup_days)
                logger.info(f"Backup cleanup result: {result}")
            
            if args.metrics:
                result = await cleanup_service.cleanup_old_metrics(args.metrics_days)
                logger.info(f"Metrics cleanup result: {result}")
            
            if args.logs:
                result = await cleanup_service.cleanup_old_logs(args.logs_days)
                logger.info(f"Logs cleanup result: {result}")
            
            if args.temp:
                result = await cleanup_service.cleanup_temp_files()
                logger.info(f"Temporary files cleanup result: {result}")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="MoonVPN System Cleanup Tool")
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all cleanup operations"
    )
    parser.add_argument(
        "--backups",
        action="store_true",
        help="Clean up old backups"
    )
    parser.add_argument(
        "--backup-days",
        type=int,
        default=30,
        help="Number of days to retain backups"
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Clean up old metrics"
    )
    parser.add_argument(
        "--metrics-days",
        type=int,
        default=7,
        help="Number of days to retain metrics"
    )
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Clean up old logs"
    )
    parser.add_argument(
        "--logs-days",
        type=int,
        default=30,
        help="Number of days to retain logs"
    )
    parser.add_argument(
        "--temp",
        action="store_true",
        help="Clean up temporary files"
    )
    
    args = parser.parse_args()
    
    # If no specific operation is selected, show help
    if not any([args.all, args.backups, args.metrics, args.logs, args.temp]):
        parser.print_help()
        return
    
    try:
        asyncio.run(run_cleanup(args))
    except KeyboardInterrupt:
        logger.info("Cleanup interrupted by user")
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 