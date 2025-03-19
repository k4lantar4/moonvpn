from typing import List, Optional
from decimal import Decimal
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from django.db.models import Q
from django.utils import timezone
from ...models import User, Transaction
from ...services.payment_manager import PaymentManager
from ..keyboards import (
    get_wallet_keyboard,
    get_payment_methods_keyboard,
    get_transaction_details_keyboard
)
from ..utils import format_transaction_text
from ..constants import (
    MENU_WALLET,
    ACTION_SELECT,
    ACTION_BACK,
    get_message
)
from .menu_base import MenuHandler

class WalletHandler(MenuHandler):
    """Handler for wallet menu"""
    
    MENU_TYPE = MENU_WALLET
    
    @classmethod
    async def show_menu(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Show wallet menu"""
        if not update.effective_message:
            return
            
        # Get recent transactions
        transactions = Transaction.objects.filter(
            user=user
        ).order_by('-created_at')[:5]  # Show last 5 transactions
        
        # Format wallet text
        if user.language == 'fa':
            text = (
                f"👛 کیف پول شما\n\n"
                f"💰 موجودی: {user.wallet_balance:,} تومان\n\n"
                "🔄 تراکنش‌های اخیر:\n"
            )
            
            if transactions:
                for tx in transactions:
                    text += f"• {format_transaction_text(tx, 'fa')}\n"
            else:
                text += "• هیچ تراکنشی ثبت نشده است\n"
                
        else:
            text = (
                f"👛 Your Wallet\n\n"
                f"💰 Balance: ${user.wallet_balance:,.2f}\n\n"
                "🔄 Recent Transactions:\n"
            )
            
            if transactions:
                for tx in transactions:
                    text += f"• {format_transaction_text(tx, 'en')}\n"
            else:
                text += "• No transactions recorded\n"
        
        # Get keyboard
        keyboard = get_wallet_keyboard(
            transactions=list(transactions),
            language=user.language
        )
        
        await update.effective_message.reply_text(
            text,
            reply_markup=keyboard
        )
    
    @classmethod
    async def show_transaction_details(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        tx_id: int
    ) -> None:
        """Show transaction details"""
        try:
            transaction = Transaction.objects.get(
                id=tx_id,
                user=user
            )
        except Transaction.DoesNotExist:
            await cls.answer_callback_error(
                query,
                "Transaction not found",
                user.language
            )
            return
        
        text = format_transaction_text(transaction, user.language, detailed=True)
        keyboard = get_transaction_details_keyboard(transaction, user.language)
        
        await cls.update_menu(query, text, keyboard)
    
    @classmethod
    async def request_deposit_amount(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Request deposit amount from user"""
        # Set state
        context.user_data['awaiting_deposit_amount'] = True
        
        await cls.update_menu(
            query,
            get_message('enter_amount', user.language)
        )
    
    @classmethod
    async def show_payment_methods(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        amount: Decimal
    ) -> None:
        """Show payment methods for deposit"""
        keyboard = get_payment_methods_keyboard(
            amount=amount,
            language=user.language
        )
        
        if user.language == 'fa':
            text = (
                f"💳 انتخاب روش پرداخت\n\n"
                f"💰 مبلغ: {amount:,} تومان\n\n"
                "لطفاً روش پرداخت را انتخاب کنید:"
            )
        else:
            text = (
                f"💳 Select Payment Method\n\n"
                f"💰 Amount: ${amount:,.2f}\n\n"
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
        """Handle wallet callback queries"""
        action = data[1] if len(data) > 1 else None
        
        if action == ACTION_SELECT:
            # Show transaction details
            tx_id = int(data[2])
            await cls.show_transaction_details(query, context, user, tx_id)
            
        elif action == "deposit":
            # Request deposit amount
            await cls.request_deposit_amount(query, context, user)
            
        elif action == ACTION_BACK:
            # Show wallet menu
            await cls.show_menu(query, context, user)
            
        else:
            await cls.answer_callback_error(
                query,
                "Invalid action",
                user.language
            )
    
    @classmethod
    async def handle_deposit_message(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Handle deposit amount message"""
        if not update.message or not update.message.text:
            return
            
        text = update.message.text.strip()
        
        # Handle cancel command
        if text == '/cancel':
            context.user_data.clear()
            await cls.show_menu(update, context, user)
            return
        
        # Validate amount
        try:
            amount = Decimal(text.replace(',', ''))
            if amount <= 0:
                raise ValueError
        except (ValueError, decimal.InvalidOperation):
            await update.message.reply_text(
                get_message('invalid_amount', user.language)
            )
            return
        
        # Show payment methods
        keyboard = get_payment_methods_keyboard(
            amount=amount,
            language=user.language
        )
        
        if user.language == 'fa':
            text = (
                f"💳 انتخاب روش پرداخت\n\n"
                f"💰 مبلغ: {amount:,} تومان\n\n"
                "لطفاً روش پرداخت را انتخاب کنید:"
            )
        else:
            text = (
                f"💳 Select Payment Method\n\n"
                f"💰 Amount: ${amount:,.2f}\n\n"
                "Please select a payment method:"
            )
        
        context.user_data.clear()
        await update.message.reply_text(
            text,
            reply_markup=keyboard
        ) 