from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from points.services import PointsService
from points.models import PointsRedemptionRule

# Conversation states
SELECTING_REWARD = 1

async def check_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /points command - show current points balance and available rewards."""
    user = update.effective_user
    try:
        # Get user's points balance
        points = PointsService.get_user_points(user)
        
        # Get available rewards
        rewards = PointsService.get_available_rewards(user)
        
        # Get recent transactions
        transactions = PointsService.get_user_transactions(user, limit=5)
        
        # Format message
        message = _("""🌟 *Your Points Balance*: {points} points

🔄 *Recent Transactions*:
{transactions}

✨ *Available Rewards*:
{rewards}

Use /redeem to redeem your points for rewards!""").format(
            points=points,
            transactions="\n".join([
                f"• {t.description}: {t.points:+d} points"
                for t in transactions
            ]) or "No recent transactions",
            rewards="\n".join([
                f"• {r.name} ({r.points_required} points) - {r.description}"
                for r in rewards
            ]) or "No rewards available yet"
        )
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(
            _("❌ Error checking points: {}").format(str(e))
        )

async def redeem_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /redeem command - show available rewards for redemption."""
    user = update.effective_user
    try:
        # Get available rewards
        rewards = PointsService.get_available_rewards(user)
        
        if not rewards:
            await update.message.reply_text(
                _("😔 No rewards available for redemption at this time.")
            )
            return ConversationHandler.END
        
        # Create keyboard with rewards
        keyboard = [
            [InlineKeyboardButton(
                f"{r.name} ({r.points_required} points)",
                callback_data=f"redeem_{r.id}"
            )]
            for r in rewards
        ]
        keyboard.append([InlineKeyboardButton(_("❌ Cancel"), callback_data="cancel_redeem")])
        
        await update.message.reply_text(
            _("🎁 Select a reward to redeem:"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return SELECTING_REWARD
        
    except Exception as e:
        await update.message.reply_text(
            _("❌ Error listing rewards: {}").format(str(e))
        )
        return ConversationHandler.END

async def handle_reward_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle reward selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_redeem":
        await query.edit_message_text(_("🚫 Redemption cancelled."))
        return ConversationHandler.END
    
    try:
        # Extract reward ID from callback data
        reward_id = int(query.data.split("_")[1])
        
        # Attempt to redeem points
        redemption = PointsService.redeem_points(query.from_user, reward_id)
        
        # Format success message based on reward type
        if redemption.rule.reward_type == PointsRedemptionRule.RewardType.DISCOUNT:
            message = _("🎉 Success! You've received a {value}% discount!")
        elif redemption.rule.reward_type == PointsRedemptionRule.RewardType.VIP:
            message = _("🌟 Success! You've received {value} days of VIP status!")
        elif redemption.rule.reward_type == PointsRedemptionRule.RewardType.TRAFFIC:
            message = _("📈 Success! You've received {value}GB extra traffic!")
        else:
            message = _("🎁 Success! You've received your reward!")
            
        await query.edit_message_text(
            message.format(value=redemption.reward_value)
        )
        
    except ValidationError as e:
        await query.edit_message_text(
            _("❌ Error: {}").format(str(e))
        )
    except Exception as e:
        await query.edit_message_text(
            _("❌ An unexpected error occurred.")
        )
    
    return ConversationHandler.END

# Create handlers
points_handler = CommandHandler("points", check_points)
redeem_conversation = ConversationHandler(
    entry_points=[CommandHandler("redeem", redeem_points)],
    states={
        SELECTING_REWARD: [CallbackQueryHandler(handle_reward_selection)],
    },
    fallbacks=[],
) 