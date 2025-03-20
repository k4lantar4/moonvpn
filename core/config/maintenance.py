import logging
import argparse
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from .connection import get_db_context
from .models.payments import Transaction, Payment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cleanup_expired_transactions(days: int = 30) -> None:
    """Clean up expired transactions older than specified days."""
    try:
        with get_db_context() as db:
            # Delete expired transactions
            expired_date = datetime.utcnow() - timedelta(days=days)
            deleted = db.query(Transaction).filter(
                Transaction.created_at < expired_date,
                Transaction.status.in_(['pending', 'failed'])
            ).delete()
            
            db.commit()
            logger.info(f"Cleaned up {deleted} expired transactions")
    except Exception as e:
        logger.error(f"Failed to cleanup expired transactions: {str(e)}")
        raise


def cleanup_failed_payments(days: int = 30) -> None:
    """Clean up failed payments older than specified days."""
    try:
        with get_db_context() as db:
            # Delete failed payments
            expired_date = datetime.utcnow() - timedelta(days=days)
            deleted = db.query(Payment).filter(
                Payment.created_at < expired_date,
                Payment.status == 'failed'
            ).delete()
            
            db.commit()
            logger.info(f"Cleaned up {deleted} failed payments")
    except Exception as e:
        logger.error(f"Failed to cleanup failed payments: {str(e)}")
        raise


def vacuum_database() -> None:
    """Vacuum the database to reclaim space."""
    try:
        with get_db_context() as db:
            # Run VACUUM ANALYZE
            db.execute(text("VACUUM ANALYZE"))
            db.commit()
            logger.info("Database vacuum completed successfully")
    except Exception as e:
        logger.error(f"Failed to vacuum database: {str(e)}")
        raise


def reindex_database() -> None:
    """Reindex the database tables."""
    try:
        with get_db_context() as db:
            # Reindex all tables
            db.execute(text("REINDEX DATABASE moonvpn"))
            db.commit()
            logger.info("Database reindex completed successfully")
    except Exception as e:
        logger.error(f"Failed to reindex database: {str(e)}")
        raise


def check_database_health() -> None:
    """Check database health and report issues."""
    try:
        with get_db_context() as db:
            # Check for dead tuples
            dead_tuples = db.execute(text("""
                SELECT relname, n_dead_tup
                FROM pg_stat_user_tables
                WHERE n_dead_tup > 1000
            """)).fetchall()
            
            if dead_tuples:
                logger.warning("Found tables with dead tuples:")
                for table, count in dead_tuples:
                    logger.warning(f"- {table}: {count} dead tuples")
            
            # Check for long-running transactions
            long_transactions = db.execute(text("""
                SELECT pid, query, age(clock_timestamp(), query_start) as duration
                FROM pg_stat_activity
                WHERE state = 'active'
                AND query NOT ILIKE '%pg_stat_activity%'
                AND age(clock_timestamp(), query_start) > interval '1 hour'
            """)).fetchall()
            
            if long_transactions:
                logger.warning("Found long-running transactions:")
                for pid, query, duration in long_transactions:
                    logger.warning(f"- PID {pid}: {duration} ({query})")
            
            logger.info("Database health check completed")
    except Exception as e:
        logger.error(f"Failed to check database health: {str(e)}")
        raise


def main() -> None:
    """Main function to run database maintenance tasks."""
    parser = argparse.ArgumentParser(description="Database maintenance tools")
    parser.add_argument(
        "--cleanup-transactions",
        type=int,
        default=30,
        help="Clean up expired transactions older than specified days"
    )
    parser.add_argument(
        "--cleanup-payments",
        type=int,
        default=30,
        help="Clean up failed payments older than specified days"
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Vacuum the database"
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Reindex the database"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Check database health"
    )
    
    args = parser.parse_args()
    
    try:
        if args.cleanup_transactions:
            cleanup_expired_transactions(args.cleanup_transactions)
        
        if args.cleanup_payments:
            cleanup_failed_payments(args.cleanup_payments)
        
        if args.vacuum:
            vacuum_database()
        
        if args.reindex:
            reindex_database()
        
        if args.health_check:
            check_database_health()
        
        if not any([args.cleanup_transactions, args.cleanup_payments, args.vacuum, args.reindex, args.health_check]):
            parser.print_help()
    except KeyboardInterrupt:
        logger.info("Database maintenance interrupted by user")
    except Exception as e:
        logger.error(f"Database maintenance failed: {str(e)}")
        raise


if __name__ == "__main__":
    main() 