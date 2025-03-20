from typing import List, Optional
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from sqlalchemy.orm import Session

from app.core.database.models.admin_group import AdminGroup, AdminGroupMember
from app.core.schemas.admin_group import AdminGroupCreate, AdminGroupUpdate, AdminGroupMemberCreate
from app.bot.services.admin_group_service import AdminGroupService
from app.bot.utils.decorators import admin_required
from app.bot.utils.messages import format_admin_group_info, format_admin_group_list, format_admin_group_member_list

# Conversation states
NAME, DESCRIPTION, ICON, NOTIFICATION_LEVEL, NOTIFICATION_TYPES = range(5)

class AdminGroupHandlers:
    """Handlers for admin group management commands."""
    
    def __init__(self, db: Session):
        self.db = db
        self.service = AdminGroupService(db)
    
    def get_handlers(self) -> List[CommandHandler]:
        """Get all command handlers for admin group management."""
        return [
            # Group creation conversation
            ConversationHandler(
                entry_points=[CommandHandler('create_admin_group', self.handle_create_group)],
                states={
                    NAME: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_group_name)
                    ],
                    DESCRIPTION: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_group_description)
                    ],
                    ICON: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_group_icon)
                    ],
                    NOTIFICATION_LEVEL: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_notification_level)
                    ],
                    NOTIFICATION_TYPES: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_notification_types)
                    ]
                },
                fallbacks=[CommandHandler('cancel', self.handle_cancel)]
            ),
            # Other group management commands
            CommandHandler('list_admin_groups', self.handle_list_groups),
            CommandHandler('group_info', self.handle_group_info),
            CommandHandler('add_admin_member', self.handle_add_member),
            CommandHandler('remove_admin_member', self.handle_remove_member),
            CommandHandler('list_admin_members', self.handle_list_members),
            CommandHandler('update_admin_group', self.handle_update_group),
            CommandHandler('delete_admin_group', self.handle_delete_group)
        ]
    
    @admin_required
    async def handle_create_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the group creation process."""
        await update.message.reply_text(
            "🔧 لطفاً نام گروه ادمین را وارد کنید:\n"
            "Please enter the admin group name:"
        )
        return NAME
    
    @admin_required
    async def handle_group_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group name input."""
        context.user_data['group_name'] = update.message.text
        await update.message.reply_text(
            "📝 لطفاً توضیحات گروه را وارد کنید:\n"
            "Please enter the group description:"
        )
        return DESCRIPTION
    
    @admin_required
    async def handle_group_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group description input."""
        context.user_data['group_description'] = update.message.text
        await update.message.reply_text(
            "🎨 لطفاً آیکون گروه را وارد کنید (یک ایموجی):\n"
            "Please enter the group icon (an emoji):"
        )
        return ICON
    
    @admin_required
    async def handle_group_icon(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle group icon input."""
        context.user_data['group_icon'] = update.message.text
        await update.message.reply_text(
            "⚙️ لطفاً سطح اعلان را انتخاب کنید (normal/high/critical):\n"
            "Please select notification level (normal/high/critical):"
        )
        return NOTIFICATION_LEVEL
    
    @admin_required
    async def handle_notification_level(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle notification level input."""
        context.user_data['notification_level'] = update.message.text
        await update.message.reply_text(
            "🔔 لطفاً انواع اعلان‌ها را وارد کنید (با کاما جدا کنید):\n"
            "Please enter notification types (comma-separated):"
        )
        return NOTIFICATION_TYPES
    
    @admin_required
    async def handle_notification_types(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle notification types input and create the group."""
        try:
            notification_types = [t.strip() for t in update.message.text.split(',')]
            group_data = AdminGroupCreate(
                name=context.user_data['group_name'],
                description=context.user_data['group_description'],
                icon=context.user_data['group_icon'],
                notification_level=context.user_data['notification_level'],
                notification_types=notification_types,
                added_by={"user_id": update.effective_user.id}
            )
            
            group = self.service.create_group(group_data)
            await update.message.reply_text(
                f"✅ گروه ادمین با موفقیت ایجاد شد!\n"
                f"Admin group created successfully!\n\n"
                f"{format_admin_group_info(group)}"
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در ایجاد گروه ادمین:\n"
                f"Error creating admin group:\n{str(e)}"
            )
        finally:
            context.user_data.clear()
            return ConversationHandler.END
    
    @admin_required
    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the current operation."""
        context.user_data.clear()
        await update.message.reply_text(
            "❌ عملیات لغو شد.\n"
            "Operation cancelled."
        )
        return ConversationHandler.END
    
    @admin_required
    async def handle_list_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all admin groups or groups of a specific type."""
        try:
            args = context.args
            group_type = args[0] if args else None
            groups = self.service.get_groups_by_type(group_type) if group_type else self.service.get_all_groups()
            
            if not groups:
                await update.message.reply_text(
                    "❌ هیچ گروه ادمینی یافت نشد.\n"
                    "No admin groups found."
                )
                return
            
            await update.message.reply_text(format_admin_group_list(groups))
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در دریافت لیست گروه‌ها:\n"
                f"Error getting groups list:\n{str(e)}"
            )
    
    @admin_required
    async def handle_group_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get information about a specific admin group."""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ لطفاً شناسه گروه را وارد کنید.\n"
                    "Please provide the group ID."
                )
                return
            
            chat_id = int(context.args[0])
            group = self.service.get_group_by_chat_id(chat_id)
            
            if not group:
                await update.message.reply_text(
                    "❌ گروه مورد نظر یافت نشد.\n"
                    "Group not found."
                )
                return
            
            await update.message.reply_text(format_admin_group_info(group))
        except ValueError:
            await update.message.reply_text(
                "❌ شناسه گروه نامعتبر است.\n"
                "Invalid group ID."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در دریافت اطلاعات گروه:\n"
                f"Error getting group info:\n{str(e)}"
            )
    
    @admin_required
    async def handle_add_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a member to an admin group."""
        try:
            if len(context.args) < 2:
                await update.message.reply_text(
                    "❌ لطفاً شناسه گروه و شناسه کاربر را وارد کنید.\n"
                    "Please provide group ID and user ID."
                )
                return
            
            chat_id = int(context.args[0])
            user_id = int(context.args[1])
            role = context.args[2] if len(context.args) > 2 else "member"
            
            member_data = AdminGroupMemberCreate(
                group_id=chat_id,
                user_id=user_id,
                role=role,
                added_by={"user_id": update.effective_user.id}
            )
            
            member = self.service.add_member(member_data)
            await update.message.reply_text(
                f"✅ کاربر با موفقیت به گروه اضافه شد!\n"
                f"User added to group successfully!"
            )
        except ValueError:
            await update.message.reply_text(
                "❌ شناسه‌های وارد شده نامعتبر هستند.\n"
                "Invalid IDs provided."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در اضافه کردن کاربر به گروه:\n"
                f"Error adding user to group:\n{str(e)}"
            )
    
    @admin_required
    async def handle_remove_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a member from an admin group."""
        try:
            if len(context.args) < 2:
                await update.message.reply_text(
                    "❌ لطفاً شناسه گروه و شناسه کاربر را وارد کنید.\n"
                    "Please provide group ID and user ID."
                )
                return
            
            chat_id = int(context.args[0])
            user_id = int(context.args[1])
            
            self.service.remove_member(chat_id, user_id)
            await update.message.reply_text(
                f"✅ کاربر با موفقیت از گروه حذف شد!\n"
                f"User removed from group successfully!"
            )
        except ValueError:
            await update.message.reply_text(
                "❌ شناسه‌های وارد شده نامعتبر هستند.\n"
                "Invalid IDs provided."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در حذف کاربر از گروه:\n"
                f"Error removing user from group:\n{str(e)}"
            )
    
    @admin_required
    async def handle_list_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all members of an admin group."""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ لطفاً شناسه گروه را وارد کنید.\n"
                    "Please provide the group ID."
                )
                return
            
            chat_id = int(context.args[0])
            members = self.service.get_group_members(chat_id)
            
            if not members:
                await update.message.reply_text(
                    "❌ هیچ عضوی در این گروه یافت نشد.\n"
                    "No members found in this group."
                )
                return
            
            await update.message.reply_text(format_admin_group_member_list(members))
        except ValueError:
            await update.message.reply_text(
                "❌ شناسه گروه نامعتبر است.\n"
                "Invalid group ID."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در دریافت لیست اعضا:\n"
                f"Error getting members list:\n{str(e)}"
            )
    
    @admin_required
    async def handle_update_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Update an admin group's information."""
        try:
            if len(context.args) < 3:
                await update.message.reply_text(
                    "❌ لطفاً شناسه گروه، فیلد و مقدار را وارد کنید.\n"
                    "Please provide group ID, field, and value."
                )
                return
            
            chat_id = int(context.args[0])
            field = context.args[1]
            value = context.args[2]
            
            update_data = AdminGroupUpdate(**{field: value})
            group = self.service.update_group(chat_id, update_data)
            
            await update.message.reply_text(
                f"✅ اطلاعات گروه با موفقیت بروزرسانی شد!\n"
                f"Group information updated successfully!\n\n"
                f"{format_admin_group_info(group)}"
            )
        except ValueError:
            await update.message.reply_text(
                "❌ شناسه گروه نامعتبر است.\n"
                "Invalid group ID."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در بروزرسانی اطلاعات گروه:\n"
                f"Error updating group information:\n{str(e)}"
            )
    
    @admin_required
    async def handle_delete_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete an admin group."""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ لطفاً شناسه گروه را وارد کنید.\n"
                    "Please provide the group ID."
                )
                return
            
            chat_id = int(context.args[0])
            self.service.delete_group(chat_id)
            
            await update.message.reply_text(
                f"✅ گروه با موفقیت حذف شد!\n"
                f"Group deleted successfully!"
            )
        except ValueError:
            await update.message.reply_text(
                "❌ شناسه گروه نامعتبر است.\n"
                "Invalid group ID."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا در حذف گروه:\n"
                f"Error deleting group:\n{str(e)}"
            ) 