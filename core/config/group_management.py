"""
Admin group management handler for MoonVPN Telegram Bot.

This module handles commands for managing admin groups and their members.
"""

from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackContext
from sqlalchemy.orm import Session

from app.core.database.models.admin import AdminGroupType, NotificationLevel
from app.bot.services.admin_group_service import AdminGroupService
from app.bot.utils.decorators import admin_required
from app.bot.utils.helpers import get_user_info

class AdminGroupHandler:
    """Handler for admin group management commands."""
    
    def __init__(self, db: Session):
        """Initialize the admin group handler.
        
        Args:
            db: Database session
        """
        self.service = AdminGroupService(db)
    
    async def handle_create_group(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /create_admin_group command.
        
        Usage: /create_admin_group <name> <chat_id> <type> [description]
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "❌ Usage: /create_admin_group <name> <chat_id> <type> [description]\n\n"
                "Types: manage, reports, logs, transactions, outages, sellers, backups"
            )
            return
        
        try:
            name = context.args[0]
            chat_id = int(context.args[1])
            group_type = AdminGroupType(context.args[2].lower())
            description = " ".join(context.args[3:]) if len(context.args) > 3 else None
            
            # Get user info for added_by
            user_info = await get_user_info(update.effective_user)
            
            # Create the group
            group = self.service.create_group(
                name=name,
                chat_id=chat_id,
                group_type=group_type,
                description=description,
                added_by=user_info
            )
            
            await update.message.reply_text(
                f"✅ Admin group created successfully!\n\n"
                f"Name: {group.name}\n"
                f"Type: {group.type.value}\n"
                f"Chat ID: {group.chat_id}\n"
                f"Description: {group.description or 'None'}"
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid chat ID or group type. Please check your input."
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to create admin group: {str(e)}")
    
    async def handle_list_groups(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /list_admin_groups command.
        
        Usage: /list_admin_groups [type]
        
        Args:
            update: Telegram update
            context: Callback context
        """
        try:
            group_type = None
            if context.args:
                group_type = AdminGroupType(context.args[0].lower())
            
            if group_type:
                groups = self.service.get_groups_by_type(group_type)
                title = f"📊 Admin Groups - {group_type.value.title()}"
            else:
                groups = self.service.db.query(AdminGroup).all()
                title = "📊 All Admin Groups"
            
            if not groups:
                await update.message.reply_text(f"❌ No admin groups found{f' of type {group_type.value}' if group_type else ''}.")
                return
            
            message = f"{title}\n\n"
            for group in groups:
                message += (
                    f"{group.icon} {group.name}\n"
                    f"Type: {group.type.value}\n"
                    f"Chat ID: {group.chat_id}\n"
                    f"Status: {'✅ Active' if group.is_active else '❌ Inactive'}\n"
                    f"Description: {group.description or 'None'}\n\n"
                )
            
            await update.message.reply_text(message)
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid group type. Available types: manage, reports, logs, transactions, outages, sellers, backups"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to list admin groups: {str(e)}")
    
    async def handle_update_group(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /update_admin_group command.
        
        Usage: /update_admin_group <chat_id> <field> <value>
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "❌ Usage: /update_admin_group <chat_id> <field> <value>\n\n"
                "Fields: name, description, icon, notification_level, is_active\n"
                "Example: /update_admin_group 123456789 name New Name"
            )
            return
        
        try:
            chat_id = int(context.args[0])
            field = context.args[1].lower()
            value = " ".join(context.args[2:])
            
            # Convert value based on field type
            if field == "notification_level":
                value = NotificationLevel(value.lower())
            elif field == "is_active":
                value = value.lower() == "true"
            
            # Update the group
            group = self.service.update_group(
                chat_id=chat_id,
                **{field: value}
            )
            
            await update.message.reply_text(
                f"✅ Admin group updated successfully!\n\n"
                f"Name: {group.name}\n"
                f"Type: {group.type.value}\n"
                f"Chat ID: {group.chat_id}\n"
                f"Status: {'✅ Active' if group.is_active else '❌ Inactive'}\n"
                f"Description: {group.description or 'None'}"
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid input. Please check your values."
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to update admin group: {str(e)}")
    
    async def handle_delete_group(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /delete_admin_group command.
        
        Usage: /delete_admin_group <chat_id>
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ Usage: /delete_admin_group <chat_id>"
            )
            return
        
        try:
            chat_id = int(context.args[0])
            
            if self.service.delete_group(chat_id):
                await update.message.reply_text(
                    f"✅ Admin group with chat ID {chat_id} deleted successfully!"
                )
            else:
                await update.message.reply_text(
                    f"❌ Admin group with chat ID {chat_id} not found."
                )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to delete admin group: {str(e)}")
    
    async def handle_add_member(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /add_admin_member command.
        
        Usage: /add_admin_member <group_chat_id> <user_id> [role]
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Usage: /add_admin_member <group_chat_id> <user_id> [role]\n\n"
                "Roles: admin, moderator, member"
            )
            return
        
        try:
            group_chat_id = int(context.args[0])
            user_id = int(context.args[1])
            role = context.args[2] if len(context.args) > 2 else "member"
            
            # Get user info for added_by
            user_info = await get_user_info(update.effective_user)
            
            # Add the member
            member = self.service.add_member(
                group_chat_id=group_chat_id,
                user_id=user_id,
                role=role,
                added_by=user_info
            )
            
            await update.message.reply_text(
                f"✅ Member added successfully!\n\n"
                f"Group: {member.group.name}\n"
                f"User ID: {member.user_id}\n"
                f"Role: {member.role}"
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID or user ID.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to add member: {str(e)}")
    
    async def handle_remove_member(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /remove_admin_member command.
        
        Usage: /remove_admin_member <group_chat_id> <user_id>
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) != 2:
            await update.message.reply_text(
                "❌ Usage: /remove_admin_member <group_chat_id> <user_id>"
            )
            return
        
        try:
            group_chat_id = int(context.args[0])
            user_id = int(context.args[1])
            
            if self.service.remove_member(group_chat_id, user_id):
                await update.message.reply_text(
                    f"✅ Member removed successfully!"
                )
            else:
                await update.message.reply_text(
                    f"❌ Member not found in the specified group."
                )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID or user ID.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to remove member: {str(e)}")
    
    async def handle_list_members(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /list_admin_members command.
        
        Usage: /list_admin_members <group_chat_id>
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ Usage: /list_admin_members <group_chat_id>"
            )
            return
        
        try:
            group_chat_id = int(context.args[0])
            members = self.service.get_group_members(group_chat_id)
            
            if not members:
                await update.message.reply_text(
                    f"❌ No members found in the specified group."
                )
                return
            
            message = f"👥 Members of {members[0].group.name}\n\n"
            for member in members:
                message += f"User ID: {member.user_id}\nRole: {member.role}\n\n"
            
            await update.message.reply_text(message)
            
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to list members: {str(e)}")
    
    def get_handlers(self) -> list:
        """Get the command handlers for admin group management.
        
        Returns:
            List of command handlers
        """
        return [
            CommandHandler("create_admin_group", self.handle_create_group),
            CommandHandler("list_admin_groups", self.handle_list_groups),
            CommandHandler("update_admin_group", self.handle_update_group),
            CommandHandler("delete_admin_group", self.handle_delete_group),
            CommandHandler("add_admin_member", self.handle_add_member),
            CommandHandler("remove_admin_member", self.handle_remove_member),
            CommandHandler("list_admin_members", self.handle_list_members)
        ] 