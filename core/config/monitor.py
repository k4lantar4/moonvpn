import logging
import argparse
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout

from .connection import get_db_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()


class DatabaseMonitor:
    """Database monitoring and performance analysis."""
    
    def __init__(self, refresh_interval: int = 5):
        """Initialize database monitor."""
        self.refresh_interval = refresh_interval
    
    def get_connection_stats(self, db: Session) -> Dict:
        """Get database connection statistics."""
        stats = db.execute(text("""
            SELECT
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections,
                count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
                count(*) FILTER (WHERE state = 'waiting') as waiting_connections
            FROM pg_stat_activity
            WHERE datname = current_database()
        """)).first()
        
        return {
            "total": stats.total_connections,
            "active": stats.active_connections,
            "idle": stats.idle_connections,
            "idle_in_transaction": stats.idle_in_transaction,
            "waiting": stats.waiting_connections
        }
    
    def get_table_stats(self, db: Session) -> List[Dict]:
        """Get table statistics."""
        stats = db.execute(text("""
            SELECT
                relname as table_name,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples,
                last_vacuum as last_vacuum,
                last_autovacuum as last_autovacuum,
                last_analyze as last_analyze,
                last_autoanalyze as last_autoanalyze
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
        """)).fetchall()
        
        return [
            {
                "table": row.table_name,
                "live_tuples": row.live_tuples,
                "dead_tuples": row.dead_tuples,
                "last_vacuum": row.last_vacuum,
                "last_autovacuum": row.last_autovacuum,
                "last_analyze": row.last_analyze,
                "last_autoanalyze": row.last_autoanalyze
            }
            for row in stats
        ]
    
    def get_index_stats(self, db: Session) -> List[Dict]:
        """Get index statistics."""
        stats = db.execute(text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan as index_scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC
        """)).fetchall()
        
        return [
            {
                "schema": row.schemaname,
                "table": row.tablename,
                "index": row.indexname,
                "scans": row.index_scans,
                "tuples_read": row.tuples_read,
                "tuples_fetched": row.tuples_fetched
            }
            for row in stats
        ]
    
    def get_query_stats(self, db: Session) -> List[Dict]:
        """Get query statistics."""
        stats = db.execute(text("""
            SELECT
                query,
                calls,
                total_time,
                mean_time,
                rows,
                shared_blks_hit,
                shared_blks_read,
                shared_blks_dirtied,
                shared_blks_written
            FROM pg_stat_statements
            ORDER BY total_time DESC
            LIMIT 10
        """)).fetchall()
        
        return [
            {
                "query": row.query,
                "calls": row.calls,
                "total_time": row.total_time,
                "mean_time": row.mean_time,
                "rows": row.rows,
                "shared_blks_hit": row.shared_blks_hit,
                "shared_blks_read": row.shared_blks_read,
                "shared_blks_dirtied": row.shared_blks_dirtied,
                "shared_blks_written": row.shared_blks_written
            }
            for row in stats
        ]
    
    def create_layout(self) -> Layout:
        """Create the monitoring layout."""
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        return layout
    
    def generate_tables(self, db: Session) -> None:
        """Generate monitoring tables."""
        # Connection stats
        conn_stats = self.get_connection_stats(db)
        conn_table = Table(title="Connection Statistics")
        conn_table.add_column("Metric", style="cyan")
        conn_table.add_column("Value", style="green")
        for key, value in conn_stats.items():
            conn_table.add_row(key.replace("_", " ").title(), str(value))
        
        # Table stats
        table_stats = self.get_table_stats(db)
        table_table = Table(title="Table Statistics")
        table_table.add_column("Table", style="cyan")
        table_table.add_column("Live Tuples", style="green")
        table_table.add_column("Dead Tuples", style="red")
        for stat in table_stats:
            table_table.add_row(
                stat["table"],
                str(stat["live_tuples"]),
                str(stat["dead_tuples"])
            )
        
        # Index stats
        index_stats = self.get_index_stats(db)
        index_table = Table(title="Index Statistics")
        index_table.add_column("Index", style="cyan")
        index_table.add_column("Scans", style="green")
        index_table.add_column("Tuples Read", style="blue")
        for stat in index_stats:
            index_table.add_row(
                stat["index"],
                str(stat["scans"]),
                str(stat["tuples_read"])
            )
        
        # Query stats
        query_stats = self.get_query_stats(db)
        query_table = Table(title="Top Queries")
        query_table.add_column("Query", style="cyan")
        query_table.add_column("Calls", style="green")
        query_table.add_column("Mean Time (ms)", style="blue")
        for stat in query_stats:
            query_table.add_row(
                stat["query"][:50] + "...",
                str(stat["calls"]),
                f"{stat['mean_time']:.2f}"
            )
        
        return {
            "connection": conn_table,
            "tables": table_table,
            "indexes": index_table,
            "queries": query_table
        }
    
    def monitor(self, duration: Optional[int] = None) -> None:
        """Monitor database performance."""
        start_time = datetime.now()
        layout = self.create_layout()
        
        with Live(layout, refresh_per_second=1) as live:
            while True:
                try:
                    with get_db_context() as db:
                        # Update layout
                        layout["header"].update(
                            Panel(f"Database Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        )
                        
                        # Generate tables
                        tables = self.generate_tables(db)
                        
                        # Update body layout
                        layout["left"].update(tables["connection"])
                        layout["right"].update(tables["tables"])
                        
                        # Update footer
                        layout["footer"].update(
                            Panel("Press Ctrl+C to exit")
                        )
                        
                        # Check duration
                        if duration and (datetime.now() - start_time).seconds >= duration:
                            break
                        
                        time.sleep(self.refresh_interval)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Monitoring error: {str(e)}")
                    break


def main() -> None:
    """Main function to run database monitoring."""
    parser = argparse.ArgumentParser(description="Database monitoring tools")
    parser.add_argument(
        "--refresh",
        type=int,
        default=5,
        help="Refresh interval in seconds"
    )
    parser.add_argument(
        "--duration",
        type=int,
        help="Monitoring duration in seconds"
    )
    
    args = parser.parse_args()
    
    try:
        monitor = DatabaseMonitor(args.refresh)
        monitor.monitor(args.duration)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Monitoring failed: {str(e)}[/red]")


if __name__ == "__main__":
    main() 