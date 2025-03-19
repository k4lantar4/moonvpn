from typing import List, Optional
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from django.db.models import Q
from django.utils import timezone
from ...models import User, Subscription
from ..keyboards import (
    get_profile_keyboard,
    get_subscription_details_keyboard,
    get_subscription_actions_keyboard
)
from ..utils import (
    format_bytes,
    get_subscription_details_text,
    get_subscription_status_text
)
from ..constants import (
    MENU_PROFILE,
    ACTION_SELECT,
    ACTION_BACK,
    get_message
)
from .menu_base import MenuHandler

class ProfileHandler(MenuHandler):
    """Handler for profile menu"""
    
    MENU_TYPE = MENU_PROFILE
    
    @classmethod
    async def show_menu(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Show profile menu"""
        if not update.effective_message:
            return
            
        # Get active subscriptions
        active_subs = Subscription.objects.filter(
            Q(user=user) &
            Q(status='active') &
            Q(end_date__gt=timezone.now())
        ).order_by('-end_date')
        
        # Get expired subscriptions
        expired_subs = Subscription.objects.filter(
            Q(user=user) &
            (Q(status='expired') | Q(end_date__lte=timezone.now()))
        ).order_by('-end_date')[:5]  # Show last 5 expired
        
        # Format profile text
        if user.language == 'fa':
            text = (
                f"👤 پروفایل شما\n\n"
                f"🆔 نام کاربری: {user.username}\n"
                f"💰 موجودی کیف پول: {user.wallet_balance:,} تومان\n"
                f"📊 مجموع ترافیک: {format_bytes(user.total_traffic_used)}\n\n"
            )
            
            if user.is_reseller:
                text += (
                    f"🎯 وضعیت: فروشنده\n"
                    f"💎 نرخ کمیسیون: {user.commission_rate}%\n"
                    f"💵 درآمد کل: {user.total_earnings:,} تومان\n\n"
                )
            
            text += "📱 اشتراک‌های فعال:\n"
            if active_subs:
                for sub in active_subs:
                    text += f"• {sub.plan.name}: {get_subscription_status_text(sub, 'fa')}\n"
            else:
                text += "• هیچ اشتراک فعالی ندارید\n"
                
        else:
            text = (
                f"👤 Your Profile\n\n"
                f"🆔 Username: {user.username}\n"
                f"💰 Wallet Balance: ${user.wallet_balance:,.2f}\n"
                f"📊 Total Traffic: {format_bytes(user.total_traffic_used)}\n\n"
            )
            
            if user.is_reseller:
                text += (
                    f"🎯 Status: Reseller\n"
                    f"💎 Commission Rate: {user.commission_rate}%\n"
                    f"💵 Total Earnings: ${user.total_earnings:,.2f}\n\n"
                )
            
            text += "📱 Active Subscriptions:\n"
            if active_subs:
                for sub in active_subs:
                    text += f"• {sub.plan.name}: {get_subscription_status_text(sub, 'en')}\n"
            else:
                text += "• No active subscriptions\n"
        
        # Get keyboard
        keyboard = get_profile_keyboard(
            active_subs=list(active_subs),
            expired_subs=list(expired_subs),
            language=user.language
        )
        
        await update.effective_message.reply_text(
            text,
            reply_markup=keyboard
        )
    
    @classmethod
    async def show_subscription_details(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        sub_id: int
    ) -> None:
        """Show subscription details"""
        try:
            subscription = Subscription.objects.get(
                id=sub_id,
                user=user
            )
        except Subscription.DoesNotExist:
            await cls.answer_callback_error(
                query,
                "Subscription not found",
                user.language
            )
            return
        
        text = get_subscription_details_text(subscription, user.language)
        keyboard = get_subscription_details_keyboard(subscription, user.language)
        
        await cls.update_menu(query, text, keyboard)
    
    @classmethod
    async def show_subscription_actions(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        sub_id: int
    ) -> None:
        """Show subscription actions"""
        try:
            subscription = Subscription.objects.get(
                id=sub_id,
                user=user
            )
        except Subscription.DoesNotExist:
            await cls.answer_callback_error(
                query,
                "Subscription not found",
                user.language
            )
            return
        
        keyboard = get_subscription_actions_keyboard(subscription, user.language)
        
        if user.language == 'fa':
            text = (
                f"🔧 مدیریت اشتراک\n\n"
                f"📱 پلن: {subscription.plan.name}\n"
                f"⏱ وضعیت: {get_subscription_status_text(subscription, 'fa')}\n\n"
                "لطفاً عملیات مورد نظر را انتخاب کنید:"
            )
        else:
            text = (
                f"🔧 Subscription Management\n\n"
                f"📱 Plan: {subscription.plan.name}\n"
                f"⏱ Status: {get_subscription_status_text(subscription, 'en')}\n\n"
                "Please select an action:"
            )
        
        await cls.update_menu(query, text, keyboard)
    
    @classmethod
    async def handle_callback(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        data: List[str]
    ) -> None:
        """Handle profile callback queries"""
        action = data[1] if len(data) > 1 else None
        
        if action == ACTION_SELECT:
            # Show subscription details
            sub_id = int(data[2])
            await cls.show_subscription_details(query, context, user, sub_id)
            
        elif action == "actions":
            # Show subscription actions
            sub_id = int(data[2])
            await cls.show_subscription_actions(query, context, user, sub_id)
            
        elif action == ACTION_BACK:
            # Show profile menu
            await cls.show_menu(query, context, user)
            
        else:
            await cls.answer_callback_error(
                query,
                "Invalid action",
                user.language
            ) 