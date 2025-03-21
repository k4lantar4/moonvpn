#!/usr/bin/env python3
"""
Script to run settings migration.
"""

import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)

from migrate_settings import migrate_settings

def main():
    """Run the migration process."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting settings migration...")
        migrate_settings()
        logger.info("Settings migration completed successfully!")
    except Exception as e:
        logger.error(f"Error during settings migration: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 