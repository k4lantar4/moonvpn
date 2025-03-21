from typing import List, Optional
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from django.db.models import Q
from ...models import User, Plan
from ..keyboards import (
    get_plans_keyboard,
    get_plan_details_keyboard,
    get_payment_methods_keyboard
)
from ..utils import get_plan_details_text
from ..constants import (
    MENU_PLANS,
    ACTION_SELECT,
    ACTION_PURCHASE,
    ACTION_PAGE,
    get_message
)
from .menu_base import MenuHandler

class PlansHandler(MenuHandler):
    """Handler for plans menu"""
    
    MENU_TYPE = MENU_PLANS
    
    @classmethod
    async def show_menu(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Show plans menu"""
        if not update.effective_message:
            return
            
        # Get available plans
        plans = Plan.objects.filter(
            Q(status='active') &
            Q(is_public=True)
        ).order_by('price')
        
        if not plans:
            await update.effective_message.reply_text(
                get_message('no_plans', user.language)
            )
            return
        
        # Show plans keyboard
        keyboard = get_plans_keyboard(
            plans=list(plans),
            language=user.language
        )
        
        await update.effective_message.reply_text(
            get_message('select_plan', user.language),
            reply_markup=keyboard
        )
    
    @classmethod
    async def show_plan_details(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        plan_id: int
    ) -> None:
        """Show plan details"""
        try:
            plan = Plan.objects.get(id=plan_id, status='active')
        except Plan.DoesNotExist:
            await cls.answer_callback_error(
                query,
                "This plan is no longer available.",
                user.language
            )
            return
        
        text = get_plan_details_text(plan, user.language)
        keyboard = get_plan_details_keyboard(plan, user.language)
        
        await cls.update_menu(query, text, keyboard)
    
    @classmethod
    async def show_payment_methods(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        plan_id: int
    ) -> None:
        """Show payment methods for plan"""
        try:
            plan = Plan.objects.get(id=plan_id, status='active')
        except Plan.DoesNotExist:
            await cls.answer_callback_error(
                query,
                "This plan is no longer available.",
                user.language
            )
            return
        
        keyboard = get_payment_methods_keyboard(
            plan_id=plan.id,
            language=user.language
        )
        
        if user.language == 'fa':
            text = (
                f"💰 قیمت پلن: {plan.price:,} تومان\n\n"
                f"👛 موجودی کیف پول: {user.wallet_balance:,} تومان\n\n"
                "لطفاً روش پرداخت را انتخاب کنید:"
            )
        else:
            text = (
                f"💰 Plan Price: ${plan.price:,.2f}\n\n"
                f"👛 Wallet Balance: ${user.wallet_balance:,.2f}\n\n"
                "Please select a payment method:"
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
        """Handle plans callback queries"""
        action = data[1] if len(data) > 1 else None
        
        if action == ACTION_SELECT:
            # Show plan details
            plan_id = int(data[2])
            await cls.show_plan_details(query, context, user, plan_id)
            
        elif action == ACTION_PURCHASE:
            # Show payment methods
            plan_id = int(data[2])
            await cls.show_payment_methods(query, context, user, plan_id)
            
        elif action == ACTION_PAGE:
            # Show plans page
            page = int(data[2])
            plans = Plan.objects.filter(
                Q(status='active') &
                Q(is_public=True)
            ).order_by('price')
            
            keyboard = get_plans_keyboard(
                plans=list(plans),
                language=user.language,
                page=page
            )
            
            await cls.update_menu(
                query,
                get_message('select_plan', user.language),
                keyboard
            )
            
        else:
            await cls.answer_callback_error(
                query,
                "Invalid action",
                user.language
            ) 