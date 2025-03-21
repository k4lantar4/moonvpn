from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from django.utils.translation import gettext as _
from django.db.models import Avg
from points.services import PointsService
from v2ray.models import Subscription, Server
from datetime import datetime, timedelta

async def suggest_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /suggest command - provide smart plan suggestions."""
    user = update.effective_user
    try:
        # Get user's points and current subscription
        points = PointsService.get_user_points(user)
        current_sub = Subscription.objects.filter(
            user=user,
            is_active=True
        ).first()
        
        # Calculate usage patterns
        usage_data = None
        if current_sub:
            usage_data = current_sub.usage_records.filter(
                timestamp__gte=datetime.now() - timedelta(days=30)
            ).aggregate(
                avg_daily_usage=Avg('daily_usage')
            )
        
        # Get available servers with capacity
        available_servers = Server.objects.filter(
            is_active=True,
            current_load__lt=0.8  # Less than 80% load
        ).order_by('current_load')
        
        # Build suggestions based on usage and points
        suggestions = []
        
        if usage_data and usage_data['avg_daily_usage']:
            avg_daily = usage_data['avg_daily_usage']
            
            if avg_daily < 1:  # Light user (< 1GB/day)
                suggestions.append({
                    'name': 'MoonVpn-Light-30',
                    'traffic': '30GB',
                    'duration': 30,
                    'description': _('Perfect for light browsing and messaging'),
                    'server': next((s for s in available_servers if s.location == 'NL'), None)
                })
            elif avg_daily < 3:  # Medium user (1-3GB/day)
                suggestions.append({
                    'name': 'MoonVpn-Standard-50',
                    'traffic': '50GB',
                    'duration': 30,
                    'description': _('Ideal for regular streaming and downloads'),
                    'server': next((s for s in available_servers if s.location == 'DE'), None)
                })
            else:  # Heavy user (>3GB/day)
                suggestions.append({
                    'name': 'MoonVpn-Pro-100',
                    'traffic': '100GB',
                    'duration': 30,
                    'description': _('Best for heavy streaming and gaming'),
                    'server': next((s for s in available_servers if s.location == 'FR'), None)
                })
        else:
            # Default suggestions for new users
            suggestions.append({
                'name': 'MoonVpn-Starter-20',
                'traffic': '20GB',
                'duration': 30,
                'description': _('Great starter package for new users'),
                'server': next((s for s in available_servers if s.location == 'NL'), None)
            })
        
        # Add VIP suggestions if user has enough points
        if points >= 100:
            suggestions.append({
                'name': 'MoonVpn-VIP-150',
                'traffic': '150GB',
                'duration': 30,
                'description': _('VIP package with priority support (Redeem with points!)'),
                'server': next((s for s in available_servers if s.location == 'FR'), None)
            })
        
        # Format message
        message = _("""🎯 *Smart Plan Suggestions*

Based on your usage patterns and points, here are some personalized recommendations:

{suggestions}

💫 You have {points} points available for discounts!
Use /points to check available rewards.""").format(
            suggestions="\n\n".join([
                f"🔹 *{s['name']}*\n"
                f"📊 Traffic: {s['traffic']}\n"
                f"⏱️ Duration: {s['duration']} days\n"
                f"🌍 Server: {s['server'].name if s['server'] else 'Auto-select'}\n"
                f"ℹ️ {s['description']}"
                for s in suggestions
            ]),
            points=points
        )
        
        # Create keyboard for purchasing
        keyboard = [
            [InlineKeyboardButton(
                f"Get {s['name']} ({s['traffic']})",
                callback_data=f"purchase_{s['name']}"
            )]
            for s in suggestions
        ]
        
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(
            _("❌ Error getting suggestions: {}").format(str(e))
        )

# Create handler
suggestions_handler = CommandHandler("suggest", suggest_plans) 