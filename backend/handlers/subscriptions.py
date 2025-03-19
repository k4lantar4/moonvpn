"""
Subscription management handlers for the Telegram bot.
"""

from typing import List, Dict, Any
from decimal import Decimal

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from django.utils import timezone
from django.utils.translation import gettext as _
from django.db import transaction

from subscriptions.models import SubscriptionPlan, UserSubscription, WalletTransaction
from ..utils.formatting import format_bytes, format_currency, format_number
from ..decorators import authenticated_user

async def buy_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available subscription plans."""
    query = update.callback_query
    await query.answer()
    
    # Get active plans
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    
    message = _("🛒 *Available Plans*\n\n")
    
    keyboard = []
    for plan in plans:
        # Format plan details
        message += _(
            "*{name}*\n"
            "• Duration: {duration} days\n"
            "• Traffic: {traffic} GB\n"
            "• Connections: {connections}\n"
            "• Price: {price}\n"
            "• Points Reward: {points}\n"
        ).format(
            name=plan.name,
            duration=plan.duration_days,
            traffic=plan.traffic_limit_gb,
            connections=plan.max_connections,
            price=format_currency(plan.price, "IRR"),
            points=format_number(plan.points_reward)
        )
        
        if plan.has_priority_support:
            message += _("• ✅ Priority Support\n")
        if plan.has_dedicated_ip:
            message += _("• ✅ Dedicated IP\n")
        if plan.has_renewal_discount:
            message += _("• 🔄 {discount}% Renewal Discount\n").format(
                discount=plan.renewal_discount_percent
            )
            
        message += "\n"
        
        # Add button for this plan
        keyboard.append([
            InlineKeyboardButton(
                _("Select {name}").format(name=plan.name),
                callback_data=f"select_plan_{plan.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(_("⬅️ Back"), callback_data="back")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return BUYING_PLAN

async def process_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process plan selection and handle payment."""
    query = update.callback_query
    await query.answer()
    
    # Get selected plan
    plan_id = int(query.data.split("_")[2])
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        await query.edit_message_text(_("❌ Plan not found or no longer available."))
        return SUBSCRIPTION_MENU
    
    user = context.user_data["db_user"]
    wallet = user.wallet
    
    # Check if user has active subscription
    active_sub = user.subscriptions.filter(status="active").first()
    if active_sub:
        message = _(
            "⚠️ *Warning*\n\n"
            "You already have an active subscription that expires on {expires}.\n"
            "Are you sure you want to purchase a new plan?"
        ).format(expires=active_sub.end_date.strftime("%Y-%m-%d"))
        
        keyboard = [
            [
                InlineKeyboardButton(_("✅ Continue"), callback_data=f"confirm_plan_{plan.id}"),
                InlineKeyboardButton(_("❌ Cancel"), callback_data="back")
            ]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return BUYING_PLAN
    
    # Calculate final price
    price = plan.price
    
    # Check wallet balance
    if wallet.balance < price:
        message = _(
            "❌ *Insufficient Balance*\n\n"
            "Plan Price: {price}\n"
            "Your Balance: {balance}\n\n"
            "Please add funds to your wallet first."
        ).format(
            price=format_currency(price, "IRR"),
            balance=format_currency(wallet.balance, "IRR")
        )
        
        keyboard = [
            [
                InlineKeyboardButton(_("💰 Add Funds"), callback_data="add_funds"),
                InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
            ]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return SUBSCRIPTION_MENU
    
    # Create subscription
    try:
        with transaction.atomic():
            # Create subscription
            now = timezone.now()
            subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                status="active",
                start_date=now,
                end_date=now + timezone.timedelta(days=plan.duration_days),
                amount_paid=price
            )
            
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type="subscription",
                amount=-price,
                points=plan.points_reward,
                status="completed",
                description=_("Subscription purchase: {plan}").format(plan=plan.name),
                reference_id=str(subscription.id)
            )
            
            # Update wallet
            wallet.balance -= price
            wallet.points += plan.points_reward
            wallet.save()
            
            # Handle referral bonus if applicable
            if wallet.referred_by:
                referrer = wallet.referred_by
                referrer_wallet = referrer.wallet
                
                bonus_amount = (price * Decimal(str(plan.referral_bonus_percent))) / Decimal('100')
                
                WalletTransaction.objects.create(
                    wallet=referrer_wallet,
                    transaction_type="referral",
                    amount=bonus_amount,
                    status="completed",
                    description=_("Referral bonus from {user}'s subscription").format(
                        user=user.username
                    ),
                    reference_id=str(subscription.id)
                )
                
                referrer_wallet.balance += bonus_amount
                referrer_wallet.total_referral_earnings += bonus_amount
                referrer_wallet.save()
            
            message = _(
                "✅ *Subscription Activated*\n\n"
                "*Plan Details:*\n"
                "• Name: {name}\n"
                "• Duration: {duration} days\n"
                "• Traffic: {traffic} GB\n"
                "• Connections: {connections}\n"
                "• Expires: {expires}\n\n"
                "*Payment Details:*\n"
                "• Amount Paid: {price}\n"
                "• Points Earned: {points}\n"
                "• New Balance: {balance}"
            ).format(
                name=plan.name,
                duration=plan.duration_days,
                traffic=plan.traffic_limit_gb,
                connections=plan.max_connections,
                expires=subscription.end_date.strftime("%Y-%m-%d"),
                price=format_currency(price, "IRR"),
                points=format_number(plan.points_reward),
                balance=format_currency(wallet.balance, "IRR")
            )
            
    except Exception as e:
        message = _("❌ Failed to process subscription. Please try again later.")
        
    keyboard = [
        [
            InlineKeyboardButton(_("📱 My Subscriptions"), callback_data="subscriptions"),
            InlineKeyboardButton(_("🏠 Main Menu"), callback_data="main_menu")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SUBSCRIPTION_MENU

async def renew_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle plan renewal."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    active_sub = user.subscriptions.filter(status="active").first()
    
    if not active_sub:
        message = _(
            "❌ *No Active Subscription*\n\n"
            "You don't have any active subscription to renew.\n"
            "Please purchase a new plan."
        )
        
        keyboard = [
            [
                InlineKeyboardButton(_("🛒 Buy Plan"), callback_data="buy_plan"),
                InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
            ]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return SUBSCRIPTION_MENU
    
    plan = active_sub.plan
    
    # Calculate renewal price
    base_price = plan.price
    if plan.has_renewal_discount:
        discount = (base_price * Decimal(str(plan.renewal_discount_percent))) / Decimal('100')
        final_price = base_price - discount
    else:
        final_price = base_price
        discount = Decimal('0')
    
    message = _(
        "🔄 *Renew Subscription*\n\n"
        "*Current Plan:*\n"
        "• Name: {name}\n"
        "• Duration: {duration} days\n"
        "• Traffic: {traffic} GB\n"
        "• Connections: {connections}\n"
        "• Expires: {expires}\n\n"
        "*Renewal Details:*\n"
        "• Base Price: {base_price}\n"
        "• Discount: {discount}\n"
        "• Final Price: {final_price}\n"
        "• Points Reward: {points}\n\n"
        "Your Balance: {balance}"
    ).format(
        name=plan.name,
        duration=plan.duration_days,
        traffic=plan.traffic_limit_gb,
        connections=plan.max_connections,
        expires=active_sub.end_date.strftime("%Y-%m-%d"),
        base_price=format_currency(base_price, "IRR"),
        discount=format_currency(discount, "IRR"),
        final_price=format_currency(final_price, "IRR"),
        points=format_number(plan.points_reward),
        balance=format_currency(user.wallet.balance, "IRR")
    )
    
    keyboard = [
        [
            InlineKeyboardButton(_("✅ Confirm Renewal"), callback_data=f"confirm_renewal_{active_sub.id}"),
            InlineKeyboardButton(_("❌ Cancel"), callback_data="back")
        ]
    ]
    
    if user.wallet.balance < final_price:
        keyboard = [
            [
                InlineKeyboardButton(_("💰 Add Funds"), callback_data="add_funds"),
                InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
            ]
        ]
        message += _("\n\n❌ Insufficient balance. Please add funds first.")
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SUBSCRIPTION_MENU

async def usage_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show subscription usage statistics."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    active_sub = user.subscriptions.filter(status="active").first()
    
    if not active_sub:
        message = _("❌ No active subscription found.")
        keyboard = [
            [
                InlineKeyboardButton(_("🛒 Buy Plan"), callback_data="buy_plan"),
                InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
            ]
        ]
    else:
        # Calculate usage percentages
        traffic_used_gb = active_sub.traffic_used_bytes / (1024 * 1024 * 1024)
        traffic_percent = (traffic_used_gb / active_sub.plan.traffic_limit_gb) * 100
        
        connections_percent = (active_sub.connections_count / active_sub.plan.max_connections) * 100
        
        days_left = (active_sub.end_date - timezone.now()).days
        total_days = active_sub.plan.duration_days
        days_percent = ((total_days - days_left) / total_days) * 100
        
        message = _(
            "📊 *Subscription Usage*\n\n"
            "*Traffic Usage:*\n"
            "• Used: {used_gb:.1f} GB\n"
            "• Total: {total_gb} GB\n"
            "• Remaining: {remaining_gb:.1f} GB\n"
            "• Usage: {traffic_percent:.1f}%\n\n"
            "*Connections:*\n"
            "• Active: {active_conn}\n"
            "• Maximum: {max_conn}\n"
            "• Usage: {conn_percent:.1f}%\n\n"
            "*Time:*\n"
            "• Days Left: {days_left}\n"
            "• Total Days: {total_days}\n"
            "• Progress: {days_percent:.1f}%"
        ).format(
            used_gb=traffic_used_gb,
            total_gb=active_sub.plan.traffic_limit_gb,
            remaining_gb=active_sub.traffic_remaining_gb,
            traffic_percent=traffic_percent,
            active_conn=active_sub.connections_count,
            max_conn=active_sub.plan.max_connections,
            conn_percent=connections_percent,
            days_left=days_left,
            total_days=total_days,
            days_percent=days_percent
        )
        
        keyboard = [
            [
                InlineKeyboardButton(_("🔄 Refresh"), callback_data="usage_stats"),
                InlineKeyboardButton(_("📜 History"), callback_data="sub_history")
            ],
            [
                InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
            ]
        ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SUBSCRIPTION_MENU

async def sub_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show subscription history."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    
    # Get paginated subscription history
    page = context.user_data.get("sub_history_page", 1)
    per_page = 5
    
    subscriptions = user.subscriptions.all().order_by("-created_at")
    total_pages = (subscriptions.count() + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    page_subscriptions = subscriptions[start:end]
    
    message = _(
        "📜 *Subscription History*\n\n"
        "Page {page} of {total_pages}\n\n"
    ).format(page=page, total_pages=total_pages)
    
    for sub in page_subscriptions:
        message += _(
            "*{plan}*\n"
            "Status: {status}\n"
            "Start Date: {start}\n"
            "End Date: {end}\n"
            "Traffic Used: {traffic}\n"
            "Amount Paid: {amount}\n\n"
        ).format(
            plan=sub.plan.name,
            status=sub.get_status_display(),
            start=sub.start_date.strftime("%Y-%m-%d") if sub.start_date else "N/A",
            end=sub.end_date.strftime("%Y-%m-%d") if sub.end_date else "N/A",
            traffic=format_bytes(sub.traffic_used_bytes),
            amount=format_currency(sub.amount_paid, "IRR") if sub.amount_paid else "N/A"
        )
    
    # Create pagination keyboard
    keyboard = []
    
    if total_pages > 1:
        row = []
        if page > 1:
            row.append(InlineKeyboardButton("◀️", callback_data=f"sub_history_{page-1}"))
        row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            row.append(InlineKeyboardButton("▶️", callback_data=f"sub_history_{page+1}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(_("⬅️ Back"), callback_data="back")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SUBSCRIPTION_MENU 