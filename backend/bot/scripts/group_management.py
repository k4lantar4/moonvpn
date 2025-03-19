#!/usr/bin/env python3
"""
Group Management Script for MoonVPN

This script provides command-line utilities for managing Telegram groups
that the bot is allowed to operate in.
"""

import os
import sys
import argparse
import logging
import django
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("group_management")

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

# Now import Django models
try:
    from main.models import AllowedGroup
    logger.info("Django models imported successfully")
except ImportError as e:
    logger.error(f"Failed to import Django models: {e}")
    sys.exit(1)

def list_groups():
    """List all groups in the database."""
    print("\n🔍 Listing all groups:")
    print("=" * 60)
    print(f"{'ID':<12} {'Status':<10} {'Title':<25} {'Added By':<15} {'Date Added'}")
    print("-" * 60)
    
    groups = AllowedGroup.objects.all().order_by('-is_active', 'title')
    
    for group in groups:
        status = "🟢 Active" if group.is_active else "🔴 Inactive"
        added_date = group.joined_at.strftime("%Y-%m-%d") if group.joined_at else "N/A"
        
        print(f"{group.group_id:<12} {status:<10} {group.title[:25]:<25} {group.added_by:<15} {added_date}")
    
    print("=" * 60)
    print(f"Total: {groups.count()} groups ({AllowedGroup.objects.filter(is_active=True).count()} active)\n")

def add_group(group_id, title=None, added_by=None):
    """Add a new group to the database."""
    try:
        # Check if group already exists
        existing = AllowedGroup.objects.filter(group_id=group_id).first()
        
        if existing:
            if existing.is_active:
                print(f"⚠️ Group {group_id} already exists and is active.")
                return
            else:
                # Reactivate existing group
                existing.is_active = True
                existing.updated_at = datetime.now()
                if title:
                    existing.title = title
                if added_by:
                    existing.added_by = added_by
                existing.save()
                print(f"✅ Group {group_id} ({existing.title}) has been reactivated.")
                return
        
        # Create new group
        if not title:
            title = f"Group {group_id}"
        
        if not added_by:
            added_by = 0  # Default value when added via script
            
        AllowedGroup.objects.create(
            group_id=group_id,
            title=title,
            added_by=added_by,
            is_active=True
        )
        
        print(f"✅ Group {group_id} ({title}) has been added to the database.")
        
    except Exception as e:
        print(f"❌ Error adding group: {e}")

def remove_group(group_id):
    """Remove a group from the active list."""
    try:
        group = AllowedGroup.objects.filter(group_id=group_id).first()
        
        if not group:
            print(f"⚠️ Group {group_id} not found in the database.")
            return
            
        if not group.is_active:
            print(f"⚠️ Group {group_id} ({group.title}) is already inactive.")
            return
            
        # Deactivate group
        group.is_active = False
        group.updated_at = datetime.now()
        group.save()
        
        print(f"✅ Group {group_id} ({group.title}) has been deactivated.")
        
    except Exception as e:
        print(f"❌ Error removing group: {e}")

def purge_group(group_id):
    """Completely remove a group from the database."""
    try:
        group = AllowedGroup.objects.filter(group_id=group_id).first()
        
        if not group:
            print(f"⚠️ Group {group_id} not found in the database.")
            return
            
        # Ask for confirmation
        confirm = input(f"Are you sure you want to permanently delete group {group_id} ({group.title})? [y/N] ")
        
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
            
        # Delete group
        group.delete()
        
        print(f"✅ Group {group_id} ({group.title}) has been permanently deleted from the database.")
        
    except Exception as e:
        print(f"❌ Error purging group: {e}")

def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description="Manage MoonVPN Telegram groups")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all groups")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new group")
    add_parser.add_argument("group_id", type=int, help="Telegram group ID")
    add_parser.add_argument("--title", type=str, help="Group title")
    add_parser.add_argument("--added-by", type=int, help="Telegram ID of user who added the group")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a group (set inactive)")
    remove_parser.add_argument("group_id", type=int, help="Telegram group ID")
    
    # Purge command
    purge_parser = subparsers.add_parser("purge", help="Permanently delete a group")
    purge_parser.add_argument("group_id", type=int, help="Telegram group ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "list":
        list_groups()
    elif args.command == "add":
        add_group(args.group_id, args.title, args.added_by)
    elif args.command == "remove":
        remove_group(args.group_id)
    elif args.command == "purge":
        purge_group(args.group_id)

if __name__ == "__main__":
    main() 