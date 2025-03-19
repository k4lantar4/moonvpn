from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from django.utils.translation import gettext as _
from points.models import PointsRedemptionRule, PointsRedemption
from main.models import Subscription
from ..services.points import PointsService
from .base import BaseCommand

class PointsCommand(BaseCommand):
    """Command for managing points and redemptions."""
    
    async def points_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show points menu."""
        user = update.effective_user
        db_user = await self.get_user(user.id)
        
        if not db_user:
            await update.message.reply_text(_("Please start the bot first with /start"))
            return
        
        keyboard = [
            [
                InlineKeyboardButton(_("💎 Points Balance"), callback_data="points_balance"),
                InlineKeyboardButton(_("📊 Points History"), callback_data="points_history")
            ],
            [
                InlineKeyboardButton(_("🎁 Redeem Points"), callback_data="points_redeem"),
                InlineKeyboardButton(_("❓ How to Earn"), callback_data="points_earn")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            _("🎯 *Points Menu*\n\n"
              "Your current points: *{points}*\n\n"
              "Choose an option below:").format(points=db_user.points),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def points_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show points balance."""
        query = update.callback_query
        user = query.from_user
        db_user = await self.get_user(user.id)
        
        if not db_user:
            await query.answer(_("Please start the bot first with /start"))
            return
        
        await query.answer()
        await query.edit_message_text(
            _("💎 *Your Points Balance*\n\n"
              "Current Points: *{points}*\n\n"
              "Use /points to see all points options.").format(points=db_user.points),
            parse_mode='Markdown'
        )
    
    async def points_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show points transaction history."""
        query = update.callback_query
        user = query.from_user
        db_user = await self.get_user(user.id)
        
        if not db_user:
            await query.answer(_("Please start the bot first with /start"))
            return
        
        await query.answer()
        
        transactions = db_user.get_points_history()[:10]  # Last 10 transactions
        if not transactions:
            await query.edit_message_text(
                _("📊 *Points History*\n\n"
                  "No transactions found.\n\n"
                  "Use /points to see all points options."),
                parse_mode='Markdown'
            )
            return
        
        history_text = _("📊 *Points History*\n\n")
        for tx in transactions:
            emoji = "➕" if tx.type == 'earn' else "➖" if tx.type == 'spend' else "⚡️"
            history_text += f"{emoji} *{tx.type.title()}*: {abs(tx.points)} points\n"
            history_text += f"   _{tx.description}_\n"
            history_text += f"   {tx.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        history_text += _("\nUse /points to see all points options.")
        
        await query.edit_message_text(history_text, parse_mode='Markdown')
    
    async def points_redeem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available redemption options."""
        query = update.callback_query
        user = query.from_user
        db_user = await self.get_user(user.id)
        
        if not db_user:
            await query.answer(_("Please start the bot first with /start"))
            return
        
        await query.answer()
        
        rules = PointsRedemptionRule.objects.filter(is_active=True)
        if not rules:
            await query.edit_message_text(
                _("🎁 *Points Redemption*\n\n"
                  "No redemption options available at the moment.\n\n"
                  "Use /points to see all points options."),
                parse_mode='Markdown'
            )
            return
        
        keyboard = []
        for rule in rules:
            keyboard.append([
                InlineKeyboardButton(
                    f"{rule.name} ({rule.points_cost} points)",
                    callback_data=f"redeem_{rule.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton(_("🔙 Back"), callback_data="points_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            _("🎁 *Points Redemption*\n\n"
              "Your points: *{points}*\n\n"
              "Choose a reward to redeem:").format(points=db_user.points),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def redeem_rule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle rule redemption."""
        query = update.callback_query
        user = query.from_user
        db_user = await self.get_user(user.id)
        rule_id = int(query.data.split('_')[1])
        
        if not db_user:
            await query.answer(_("Please start the bot first with /start"))
            return
        
        try:
            rule = PointsRedemptionRule.objects.get(id=rule_id, is_active=True)
            
            # Check if user has enough points
            if db_user.points < rule.points_cost:
                await query.answer(_("Insufficient points!"))
                return
            
            # Get active subscription if needed
            applied_to = None
            if rule.reward_type in ['data', 'days']:
                applied_to = Subscription.objects.filter(
                    user=db_user,
                    status='active'
                ).first()
                
                if not applied_to:
                    await query.answer(_("No active subscription found!"))
                    return
            
            # Create redemption
            redemption = PointsRedemption.objects.create(
                user=db_user,
                rule=rule,
                points_spent=rule.points_cost,
                reward_value=rule.reward_value,
                applied_to=applied_to
            )
            
            # Apply reward
            if redemption.apply_reward():
                await query.answer(_("Reward redeemed successfully!"))
                
                # Send success message
                reward_text = _("🎉 *Reward Redeemed Successfully!*\n\n")
                reward_text += _("Points spent: *{points}*\n").format(points=rule.points_cost)
                reward_text += _("Reward: *{reward}*\n").format(reward=rule.name)
                
                if rule.reward_type == 'discount':
                    reward_text += _("\nYour discount code: *{code}*").format(
                        code=f"POINTS_{redemption.id}"
                    )
                
                await query.edit_message_text(
                    reward_text,
                    parse_mode='Markdown'
                )
            else:
                await query.answer(_("Failed to apply reward!"))
                
        except PointsRedemptionRule.DoesNotExist:
            await query.answer(_("Invalid redemption option!"))
    
    async def points_earn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show how to earn points."""
        query = update.callback_query
        
        await query.answer()
        await query.edit_message_text(
            _("❓ *How to Earn Points*\n\n"
              "You can earn points through:\n\n"
              "• Purchasing subscriptions\n"
              "• Referring new users\n"
              "• Participating in promotions\n"
              "• Special events and contests\n\n"
              "Use /points to see all points options."),
            parse_mode='Markdown'
        )
    
    def get_handlers(self):
        """Get command handlers."""
        return [
            (self.points_menu, "points"),
            (self.points_balance, "points_balance"),
            (self.points_history, "points_history"),
            (self.points_redeem, "points_redeem"),
            (self.redeem_rule, "redeem_"),
            (self.points_earn, "points_earn")
        ] 