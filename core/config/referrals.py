"""
Referral system handlers for the Telegram bot.
"""

from typing import List, Dict, Any
from decimal import Decimal

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from django.utils import timezone
from django.utils.translation import gettext as _
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth

from subscriptions.models import UserWallet, WalletTransaction
from ..utils.formatting import format_currency, format_number, format_percentage
from ..decorators import authenticated_user

async def ref_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show referral statistics."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    wallet = user.wallet
    
    # Get referral statistics
    referrals = user.referrals.all()
    total_referrals = referrals.count()
    
    # Get active referrals (with active subscriptions)
    active_referrals = referrals.filter(
        subscriptions__status="active"
    ).distinct().count()
    
    # Get monthly earnings
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_earnings = WalletTransaction.objects.filter(
        wallet=wallet,
        transaction_type="referral",
        created_at__gte=start_of_month
    ).aggregate(total=Sum("amount"))["total"] or 0
    
    # Get earnings by month
    monthly_stats = WalletTransaction.objects.filter(
        wallet=wallet,
        transaction_type="referral"
    ).annotate(
        month=TruncMonth("created_at")
    ).values("month").annotate(
        earnings=Sum("amount"),
        count=Count("id")
    ).order_by("-month")[:3]
    
    message = _(
        "📊 *Referral Statistics*\n\n"
        "*Overview:*\n"
        "• Total Referrals: {total}\n"
        "• Active Referrals: {active}\n"
        "• Total Earnings: {total_earnings}\n"
        "• This Month: {monthly_earnings}\n\n"
        "*Recent Monthly Stats:*\n"
    ).format(
        total=total_referrals,
        active=active_referrals,
        total_earnings=format_currency(wallet.total_referral_earnings, "IRR"),
        monthly_earnings=format_currency(monthly_earnings, "IRR")
    )
    
    for stat in monthly_stats:
        message += _(
            "📅 {month}:\n"
            "• Earnings: {earnings}\n"
            "• Transactions: {count}\n\n"
        ).format(
            month=stat["month"].strftime("%B %Y"),
            earnings=format_currency(stat["earnings"], "IRR"),
            count=stat["count"]
        )
    
    keyboard = [
        [
            InlineKeyboardButton(_("📜 History"), callback_data="ref_history"),
            InlineKeyboardButton(_("🎁 Rewards"), callback_data="ref_rewards")
        ],
        [
            InlineKeyboardButton(_("📢 Share"), callback_data="ref_share"),
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return REFERRAL_MENU

async def ref_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show referral transaction history."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    wallet = user.wallet
    
    # Get paginated referral transactions
    page = context.user_data.get("ref_history_page", 1)
    per_page = 5
    
    transactions = wallet.transactions.filter(
        transaction_type="referral"
    ).order_by("-created_at")
    
    total_pages = (transactions.count() + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    page_transactions = transactions[start:end]
    
    message = _(
        "📜 *Referral History*\n\n"
        "Page {page} of {total_pages}\n\n"
    ).format(page=page, total_pages=total_pages)
    
    for tx in page_transactions:
        message += _(
            "*{date}*\n"
            "Amount: {amount}\n"
            "Description: {desc}\n\n"
        ).format(
            date=tx.created_at.strftime("%Y-%m-%d %H:%M"),
            amount=format_currency(tx.amount, "IRR"),
            desc=tx.description
        )
    
    # Create pagination keyboard
    keyboard = []
    
    if total_pages > 1:
        row = []
        if page > 1:
            row.append(InlineKeyboardButton("◀️", callback_data=f"ref_history_{page-1}"))
        row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            row.append(InlineKeyboardButton("▶️", callback_data=f"ref_history_{page+1}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(_("⬅️ Back"), callback_data="back")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return REFERRAL_MENU

async def ref_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show referral rewards and commission rates."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    
    # Get all active plans with their referral bonuses
    plans = SubscriptionPlan.objects.filter(
        is_active=True
    ).order_by("price")
    
    message = _(
        "🎁 *Referral Rewards*\n\n"
        "Earn commission when your referrals purchase subscriptions!\n\n"
        "*Commission Rates:*\n"
    )
    
    for plan in plans:
        message += _(
            "• {name}: {percent}%\n"
            "  ({amount} per subscription)\n"
        ).format(
            name=plan.name,
            percent=plan.referral_bonus_percent,
            amount=format_currency(
                (plan.price * Decimal(str(plan.referral_bonus_percent))) / Decimal('100'),
                "IRR"
            )
        )
    
    message += _(
        "\n*Your Stats:*\n"
        "• Total Earnings: {earnings}\n"
        "• Total Referrals: {referrals}\n"
        "• Average Commission: {avg_commission}\n"
    ).format(
        earnings=format_currency(user.wallet.total_referral_earnings, "IRR"),
        referrals=user.referrals.count(),
        avg_commission=format_currency(
            user.wallet.total_referral_earnings / max(user.referrals.count(), 1),
            "IRR"
        )
    )
    
    keyboard = [
        [
            InlineKeyboardButton(_("📢 Share"), callback_data="ref_share"),
            InlineKeyboardButton(_("📊 Stats"), callback_data="ref_stats")
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
    
    return REFERRAL_MENU

async def ref_share(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show referral sharing options."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    wallet = user.wallet
    
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start={wallet.referral_code}"
    
    message = _(
        "📢 *Share Your Referral Link*\n\n"
        "*Your Referral Code:*\n"
        "`{code}`\n\n"
        "*Referral Link:*\n"
        "`{link}`\n\n"
        "Share this link with your friends and earn commission when they subscribe!\n\n"
        "*How it works:*\n"
        "1. Share your referral link\n"
        "2. Friends join using your link\n"
        "3. You earn commission on their subscriptions\n"
        "4. Get paid automatically to your wallet"
    ).format(
        code=wallet.referral_code,
        link=referral_link
    )
    
    # Create share message
    share_text = _(
        "🌟 Get Premium VPN Access!\n\n"
        "• Fast & Secure Connections\n"
        "• Multiple Locations\n"
        "• 24/7 Support\n\n"
        "Join using my referral link:\n"
        "{link}"
    ).format(link=referral_link)
    
    keyboard = [
        [
            InlineKeyboardButton(
                _("📱 Share on Telegram"),
                url=f"https://t.me/share/url?url={referral_link}&text={share_text}"
            )
        ],
        [
            InlineKeyboardButton(_("📊 View Stats"), callback_data="ref_stats"),
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return REFERRAL_MENU 