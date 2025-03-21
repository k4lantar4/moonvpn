"""
Analytics handler for MoonVPN Telegram Bot.

This module handles commands for admin group analytics and reporting.
"""

from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from sqlalchemy.orm import Session

from app.bot.services.admin_analytics_service import AdminAnalyticsService
from app.bot.utils.decorators import admin_required

class AnalyticsHandler:
    """Handler for analytics commands."""
    
    def __init__(self, db: Session):
        """Initialize the analytics handler.
        
        Args:
            db: Database session
        """
        self.service = AdminAnalyticsService(db)
    
    @admin_required
    async def handle_group_stats(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /group_stats command.
        
        Usage: /group_stats <group_chat_id>
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ Usage: /group_stats <group_chat_id>"
            )
            return
        
        try:
            group_chat_id = int(context.args[0])
            stats = self.service.get_group_statistics(group_chat_id)
            
            message = (
                f"📊 <b>Group Statistics</b>\n\n"
                f"Name: {stats['group_name']}\n"
                f"Type: {stats['group_type']}\n"
                f"Total Members: {stats['total_members']}\n\n"
                f"<b>Role Distribution:</b>\n"
            )
            
            for role, count in stats['role_distribution'].items():
                message += f"• {role.title()}: {count}\n"
            
            message += (
                f"\nStatus: {'✅ Active' if stats['is_active'] else '❌ Inactive'}\n"
                f"Notification Level: {stats['notification_level'].upper()}\n"
                f"Notification Types: {', '.join(stats['notification_types']) or 'None'}"
            )
            
            await update.message.reply_text(
                text=message,
                parse_mode='HTML'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to get group statistics: {str(e)}")
    
    @admin_required
    async def handle_member_activity(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /member_activity command.
        
        Usage: /member_activity <group_chat_id> [days]
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "❌ Usage: /member_activity <group_chat_id> [days]"
            )
            return
        
        try:
            group_chat_id = int(context.args[0])
            days = int(context.args[1]) if len(context.args) > 1 else 30
            
            activity = self.service.get_member_activity(group_chat_id, days)
            
            if not activity:
                await update.message.reply_text(
                    f"❌ No member activity found for the last {days} days."
                )
                return
            
            message = f"👥 <b>Member Activity (Last {days} days)</b>\n\n"
            
            for member in activity:
                message += (
                    f"User ID: {member['user_id']}\n"
                    f"Role: {member['role']}\n"
                    f"Actions: {member['action_count']}\n\n"
                )
            
            await update.message.reply_text(
                text=message,
                parse_mode='HTML'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID or days value.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to get member activity: {str(e)}")
    
    @admin_required
    async def handle_group_health(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /group_health command.
        
        Usage: /group_health <group_chat_id>
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ Usage: /group_health <group_chat_id>"
            )
            return
        
        try:
            group_chat_id = int(context.args[0])
            health = self.service.get_group_health(group_chat_id)
            
            # Get status emoji
            status_emoji = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '❌'
            }.get(health['status'], '❓')
            
            message = (
                f"🏥 <b>Group Health Check</b>\n\n"
                f"Health Score: {health['health_score']}%\n"
                f"Status: {status_emoji} {health['status'].upper()}\n\n"
            )
            
            if health['factors']:
                message += "<b>Health Factors:</b>\n"
                for factor in health['factors']:
                    message += f"• {factor}\n"
                message += "\n"
            
            message += (
                f"Active Members: {health['active_members']}\n"
                f"Admin Members: {health['admin_members']}\n"
                f"Status: {'✅ Active' if health['is_active'] else '❌ Inactive'}\n"
                f"Notifications: {'✅ Configured' if health['has_notifications'] else '❌ Not configured'}"
            )
            
            await update.message.reply_text(
                text=message,
                parse_mode='HTML'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to get group health: {str(e)}")
    
    @admin_required
    async def handle_group_recommendations(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /group_recommendations command.
        
        Usage: /group_recommendations <group_chat_id>
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ Usage: /group_recommendations <group_chat_id>"
            )
            return
        
        try:
            group_chat_id = int(context.args[0])
            recommendations = self.service.get_group_recommendations(group_chat_id)
            
            if not recommendations:
                await update.message.reply_text(
                    "✅ No recommendations found. Group is well configured!"
                )
                return
            
            message = "💡 <b>Group Recommendations</b>\n\n"
            
            # Group recommendations by priority
            priorities = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }
            
            for priority in ['high', 'medium', 'low']:
                priority_recs = [r for r in recommendations if r['priority'] == priority]
                if priority_recs:
                    message += f"<b>{priorities[priority]} {priority.upper()} Priority:</b>\n"
                    for rec in priority_recs:
                        message += (
                            f"• {rec['message']}\n"
                            f"  {rec['details']}\n\n"
                        )
            
            await update.message.reply_text(
                text=message,
                parse_mode='HTML'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to get recommendations: {str(e)}")
    
    @admin_required
    async def handle_activity_report(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /activity_report command.
        
        Usage: /activity_report <group_chat_id> [days]
        
        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "❌ Usage: /activity_report <group_chat_id> [days]"
            )
            return
        
        try:
            group_chat_id = int(context.args[0])
            days = int(context.args[1]) if len(context.args) > 1 else 30
            
            report = self.service.generate_activity_report(group_chat_id, days)
            
            message = (
                f"📋 <b>Activity Report</b>\n"
                f"Generated: {report['report_date']}\n"
                f"Period: {report['time_period']}\n\n"
                
                f"<b>Group Information:</b>\n"
                f"Name: {report['group_info']['group_name']}\n"
                f"Type: {report['group_info']['group_type']}\n"
                f"Members: {report['group_info']['total_members']}\n\n"
                
                f"<b>Member Activity:</b>\n"
            )
            
            for member in report['member_activity']:
                message += (
                    f"• User {member['user_id']} ({member['role']}): "
                    f"{member['action_count']} actions\n"
                )
            
            message += (
                f"\n<b>Notifications:</b>\n"
                f"Total Types: {report['notifications']['total_notifications']}\n"
                f"Level: {report['notifications']['notification_level']}\n\n"
                
                f"<b>Health Status:</b>\n"
                f"Score: {report['health_metrics']['health_score']}%\n"
                f"Status: {report['health_metrics']['status'].upper()}\n"
            )
            
            if report['health_metrics']['factors']:
                message += "Factors:\n"
                for factor in report['health_metrics']['factors']:
                    message += f"• {factor}\n"
            
            if report['recommendations']:
                message += "\n<b>Recommendations:</b>\n"
                for rec in report['recommendations']:
                    message += (
                        f"• [{rec['priority'].upper()}] {rec['message']}\n"
                        f"  {rec['details']}\n"
                    )
            
            await update.message.reply_text(
                text=message,
                parse_mode='HTML'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID or days value.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to generate activity report: {str(e)}")
    
    def get_handlers(self) -> list:
        """Get the command handlers for analytics.
        
        Returns:
            List of command handlers
        """
        return [
            CommandHandler("group_stats", self.handle_group_stats),
            CommandHandler("member_activity", self.handle_member_activity),
            CommandHandler("group_health", self.handle_group_health),
            CommandHandler("group_recommendations", self.handle_group_recommendations),
            CommandHandler("activity_report", self.handle_activity_report)
        ] 