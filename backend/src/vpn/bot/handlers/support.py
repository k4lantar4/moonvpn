from typing import List, Optional
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from django.conf import settings
from django.utils import timezone
from ...models import User, SupportTicket
from ..keyboards import get_support_keyboard
from ..constants import (
    MENU_SUPPORT,
    MENU_MAIN,
    ACTION_SELECT,
    ACTION_BACK,
    get_message
)
from .menu_base import MenuHandler

class SupportHandler(MenuHandler):
    """Handler for support menu"""
    
    MENU_TYPE = MENU_SUPPORT
    
    @classmethod
    async def show_menu(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Show support menu"""
        if not update.effective_message:
            return
            
        # Get active tickets
        active_tickets = SupportTicket.objects.filter(
            user=user,
            status='open'
        ).order_by('-created_at')
        
        # Format support text
        text = get_message('support_menu', user.language)
        
        if active_tickets:
            text += get_message('active_tickets', user.language)
            for ticket in active_tickets:
                text += (
                    f"• {'شماره تیکت' if user.language == 'fa' else 'Ticket #'}: {ticket.id}\n"
                    f"  {'موضوع' if user.language == 'fa' else 'Subject'}: {ticket.subject}\n"
                    f"  {'تاریخ' if user.language == 'fa' else 'Date'}: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                )
        else:
            text += get_message('no_tickets', user.language)
        
        # Get keyboard
        keyboard = get_support_keyboard(
            active_tickets=list(active_tickets),
            language=user.language
        )
        
        await update.effective_message.reply_text(
            text,
            reply_markup=keyboard
        )
        
        # Set state for message handling
        context.user_data['awaiting_support'] = True
    
    @classmethod
    async def show_ticket_details(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        ticket_id: int
    ) -> None:
        """Show ticket details"""
        try:
            ticket = SupportTicket.objects.get(
                id=ticket_id,
                user=user
            )
        except SupportTicket.DoesNotExist:
            await cls.answer_callback_error(
                query,
                get_message('ticket_not_found', user.language),
                user.language
            )
            return
        
        status = 'باز' if ticket.status == 'open' else 'بسته' if user.language == 'fa' else 'Open' if ticket.status == 'open' else 'Closed'
        
        response = ""
        if ticket.response:
            response = get_message('ticket_response', user.language).format(
                response=ticket.response,
                response_date=ticket.response_date.strftime('%Y-%m-%d %H:%M')
            )
            
        text = get_message('ticket_details', user.language).format(
            ticket_id=ticket.id,
            subject=ticket.subject,
            created_at=ticket.created_at.strftime('%Y-%m-%d %H:%M'),
            status=status,
            message=ticket.message,
            response=response
        )
        
        await cls.update_menu(query, text)
    
    @classmethod
    async def handle_callback(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        data: List[str]
    ) -> None:
        """Handle support callback queries"""
        action = data[1] if len(data) > 1 else None
        
        if action == ACTION_SELECT:
            # Show ticket details
            ticket_id = int(data[2])
            await cls.show_ticket_details(query, context, user, ticket_id)
            
        elif action == ACTION_BACK:
            # Show support menu
            await cls.show_menu(query, context, user)
            
        else:
            await cls.answer_callback_error(
                query,
                get_message('invalid_action', user.language),
                user.language
            )
    
    @classmethod
    async def handle_message(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Handle support messages"""
        if not update.message or not update.message.text:
            return
            
        text = update.message.text.strip()
        
        # Handle cancel command
        if text == '/cancel':
            context.user_data.clear()
            await cls.show_menu(update, context, user)
            return
        
        # Create support ticket
        ticket = SupportTicket.objects.create(
            user=user,
            message=text,
            subject=text[:50] + "..." if len(text) > 50 else text
        )
        
        # Send confirmation to user
        reply = get_message('ticket_created', user.language).format(
            ticket_id=ticket.id
        )
        
        await update.message.reply_text(reply)
        
        # Forward to admin group if configured
        if settings.TELEGRAM_ADMIN_GROUP_ID:
            admin_text = (
                f"📨 New Support Ticket\n\n"
                f"🆔 User: {user.username} (ID: {user.telegram_id})\n"
                f"🎫 Ticket #{ticket.id}\n"
                f"📅 Date: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"💬 Message:\n{text}"
            )
            
            try:
                await context.bot.send_message(
                    chat_id=settings.TELEGRAM_ADMIN_GROUP_ID,
                    text=admin_text
                )
            except Exception as e:
                # Log error but don't notify user
                print(f"Error forwarding to admin group: {e}")
        
        # Clear state
        context.user_data.clear() 