"""
Receipt handlers for the MoonVPN bot.

This module implements handlers for processing payment receipts, 
card-to-card transfers, and payment confirmation.
"""
from typing import Optional
from datetime import datetime

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from db.models.receipt_log import ReceiptStatus
from db.repositories.receipt_log_repository import ReceiptLogRepository
from db.repositories.transaction_repo import TransactionRepository
# Assuming PaymentService is available via dependency injection or context
from core.services.payment_service import PaymentService
from core.services.client_service import ClientService
from db.repositories.order_repository import OrderRepository
from db.models.order import OrderStatus
# from core.services.user_service import UserService
from bot.states.receipt_states import DepositStates
from db.models.transaction import TransactionStatus, TransactionType
from core.services.wallet_service import WalletService
from bot.keyboards.receipt_keyboards import create_admin_undo_keyboard

# Initialize router
receipt_router = Router(name="receipt_router")
logger = logging.getLogger(__name__)

# The function get_receipt_admin_keyboard used to be here, it has been moved to bot/keyboards/receipt_keyboards.py

@receipt_router.message(F.photo | F.text, state=DepositStates.AWAITING_RECEIPT)
async def process_user_receipt(message: Message, state: FSMContext, session: AsyncSession):
    """Handles user submission of a receipt (photo or text) when in AWAITING_RECEIPT state."""
    user_id = message.from_user.id
    logger.info(f"Received receipt submission from user {user_id}.")

    # --- Get required info from state --- 
    state_data = await state.get_data()
    card_id = state_data.get("deposit_card_id")
    amount = state_data.get("deposit_amount")
    transaction_id = state_data.get("deposit_transaction_id")

    if not all([card_id, amount, transaction_id]):
        logger.error(f"Missing deposit context in state for user {user_id}. State data: {state_data}")
        await message.reply("❌ خطای داخلی رخ داد. اطلاعات واریز شما یافت نشد. لطفاً دوباره فرآیند واریز را شروع کنید.") # Internal error. Deposit info not found.
        await state.clear() # Clear the state to avoid issues
        return
    
    # Ensure amount is valid
    try:
        amount_decimal = float(amount) # Or Decimal
        if amount_decimal <= 0:
             raise ValueError("Amount must be positive")
    except (ValueError, TypeError):
         logger.error(f"Invalid amount '{amount}' found in state for user {user_id} and transaction {transaction_id}.")
         await message.reply("❌ خطای داخلی: مبلغ ذخیره شده برای واریز نامعتبر است. لطفاً فرآیند را مجدداً آغاز کنید.") # Invalid amount in state
         await state.clear()
         return

    # --- Extract receipt details --- 
    text_reference = message.caption or message.text # Use caption if photo, otherwise text
    photo_file_id = message.photo[-1].file_id if message.photo else None
    submitted_at = message.date
    
    # Generate a more robust tracking code if possible (e.g., based on transaction_id)
    tracking_code = f"RCPT-{transaction_id}" 

    # --- Create Receipt Log --- 
    receipt_repo = ReceiptLogRepository(session)
    payment_service = PaymentService(session) # Instantiate or get service
    try:
        logger.info(f"Creating receipt log for user {user_id}, transaction {transaction_id}, amount {amount_decimal}")
        new_receipt = await receipt_repo.create_receipt_log(
            user_id=user_id,
            card_id=card_id,
            amount=amount_decimal,
            status=ReceiptStatus.PENDING,
            text_reference=text_reference,
            photo_file_id=photo_file_id,
            order_id=None, # Deposits are not directly linked to orders initially
            transaction_id=transaction_id, # Link to the pending transaction
            submitted_at=submitted_at,
            tracking_code=tracking_code
        )
        # await session.flush() # Not needed if create_receipt_log commits or repo handles it
        logger.info(f"Receipt log {new_receipt.id} created for transaction {transaction_id}.")

        # --- Send to Admin Channel --- 
        # The service should fetch channel_id based on card_id
        send_success = await payment_service.send_receipt_to_admin_channel(receipt_id=new_receipt.id)
        
        if send_success:
            await message.reply("✅ رسید شما با موفقیت دریافت و برای بررسی ارسال شد. لطفاً منتظر تایید توسط مدیریت باشید.") # Receipt received and sent for review.
            await state.clear() # Clear state after successful submission
        else:
            # Inform user, but log the issue internally for admin follow-up
            logger.error(f"Failed to send receipt {new_receipt.id} (transaction {transaction_id}) to admin channel.")
            await message.reply("✅ رسید شما دریافت شد، اما مشکلی در ارسال آن برای بررسی رخ داد. لطفاً منتظر بمانید، تیم پشتیبانی پیگیری خواهد کرد.") # Receipt received, but failed to send.
            # Do not clear state here, user might need to retry or support needs info?
            # Or maybe clear state anyway? Let's clear it for now.
            await state.clear()

    except Exception as e:
        logger.error(f"Error processing receipt for user {user_id}, transaction {transaction_id}: {e}", exc_info=True)
        await message.reply("⚠️ خطایی در پردازش رسید شما رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.") # An error occurred while processing the receipt.
        # Maybe clear state here too?
        await state.clear()


async def confirm_payment(
    callback_query: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Confirm a payment after receipt verification.
    
    Args:
        callback_query: The callback query containing payment data
        state: The current FSM state
    """
    # TODO: Implement payment confirmation logic
    pass


async def reject_receipt(
    callback_query: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Reject an invalid receipt.
    
    Args:
        callback_query: The callback query containing receipt data
        state: The current FSM state
    """
    # TODO: Implement receipt rejection logic
    pass


# Register handlers
# Note: The handlers will be registered when this module is imported in bot/main.py 

"""
Callback query handlers for admin managing card-to-card receipts
"""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.receipt_states import ReceiptAdminStates
from core.services.notification_service import NotificationService
from db.models.receipt_log import ReceiptStatus
from db.models.transaction import TransactionStatus

@receipt_router.callback_query(F.data.startswith("confirm_receipt:"))
async def handle_confirm_receipt(
    call: CallbackQuery,
    session: AsyncSession,
    notification_service: NotificationService,
    receipt_repo: ReceiptLogRepository,
    transaction_repo: TransactionRepository,
    wallet_service: WalletService,
    bot: Bot
):
    """Handles the 'Confirm Receipt' button press by admin for deposits."""
    receipt_id = int(call.data.split(":")[1])
    admin_user = call.from_user # Get admin user object for name/mention
    admin_user_id = admin_user.id
    admin_mention = admin_user.mention_html(admin_user.first_name) # Get admin mention

    logger.info(f"Admin {admin_user_id} attempting to confirm receipt {receipt_id}")

    async with session.begin(): # Use a transaction block for atomicity
        receipt = await receipt_repo.get_by_id(receipt_id)

        if not receipt:
            await call.answer("❌ رسید پیدا نشد.", show_alert=True)
            logger.warning(f"Receipt {receipt_id} not found for confirmation attempt by admin {admin_user_id}.")
            return

        if receipt.status != ReceiptStatus.PENDING:
            await call.answer(f"⚠️ وضعیت رسید قبلاً به {receipt.status.value} تغییر کرده است.", show_alert=True)
            logger.info(f"Receipt {receipt_id} already has status {receipt.status.value}. Confirmation aborted by admin {admin_user_id}.")
            return
        
        # --- Find the associated Transaction --- 
        if not receipt.transaction_id:
             logger.error(f"Receipt {receipt_id} confirmed by {admin_user_id} has no associated transaction_id.")
             await call.answer("❌ خطا: این رسید به هیچ تراکنشی مرتبط نیست.", show_alert=True)
             # Update receipt status to ERROR?
             # await receipt_repo.update_status(receipt_id, ReceiptStatus.ERROR, admin_user_id, note="Missing transaction_id") # Requires repo update
             return
             
        transaction = await transaction_repo.get_by_id(receipt.transaction_id)
        if not transaction:
             logger.error(f"Transaction {receipt.transaction_id} associated with receipt {receipt_id} not found.")
             await call.answer(f"❌ خطا: تراکنش مرتبط (ID: {receipt.transaction_id}) پیدا نشد.", show_alert=True)
             # await receipt_repo.update_status(receipt_id, ReceiptStatus.ERROR, admin_user_id, note=f"Associated Transaction {receipt.transaction_id} not found")
             return
             
        # Check transaction status - should be PENDING
        if transaction.status != TransactionStatus.PENDING:
             logger.warning(f"Transaction {transaction.id} for receipt {receipt_id} has status {transaction.status}. Confirmation logic might be duplicated or invalid.")
             await call.answer(f"⚠️ تراکنش مرتبط (ID: {transaction.id}) در وضعیت PENDING نیست ({transaction.status}).", show_alert=True)
             # Update receipt status to approved but don't credit wallet again?
             # await receipt_repo.update_status(receipt_id, ReceiptStatus.APPROVED, admin_user_id)
             # await call.message.edit_text(f"{call.message.text}\n\n✅ رسید تایید شد (تراکنش {transaction.id} قبلاً پردازش شده بود).", reply_markup=None)
             return

        # --- Perform Actions --- 
        try:
            # 1. Update Receipt Status
            logger.info(f"Approving receipt {receipt_id} by admin {admin_user_id}.")
            updated_receipt = await receipt_repo.update_status(receipt_id, ReceiptStatus.APPROVED, admin_user_id)
            if not updated_receipt:
                raise Exception("Failed to update receipt status to APPROVED") # Will trigger rollback

            # 2. Update Transaction Status
            logger.info(f"Updating transaction {transaction.id} status to SUCCESS for receipt {receipt_id}.")
            updated_transaction = await transaction_repo.update_status(transaction.id, TransactionStatus.SUCCESS)
            if not updated_transaction:
                raise Exception(f"Failed to update transaction {transaction.id} status to SUCCESS")

            # 3. Credit User Wallet
            logger.info(f"Crediting wallet for user {receipt.user_id} with amount {receipt.amount} for receipt {receipt.id}.")
            # Ensure amount is Decimal for wallet service if needed
            credit_amount = receipt.amount # Already should be Decimal/float from DB
            success_credit = await wallet_service.credit(receipt.user_id, float(credit_amount), f"Deposit confirmation - Receipt ID: {receipt.id}")
            if not success_credit:
                raise Exception(f"Failed to credit wallet for user {receipt.user_id}, amount {credit_amount}")

            # --- Post-Actions (Notifications, Message Edits) --- 
            # These happen after successful commit (outside the try/except block? No, do before commit)

            # 4. Notify User
            try:
                current_balance = await wallet_service.get_balance(receipt.user_id)
                user_message = (
                    f"✅ واریز شما با موفقیت تایید و به حساب شما اضافه شد.\n\n"
                    f"💰 مبلغ: {format_currency(receipt.amount)}\n"
                    f"💸 موجودی جدید: {format_currency(current_balance)}\n"
                    f"🔖 کد پیگیری رسید: {receipt.tracking_code}"
                )
                await notification_service.notify_user(user_id=receipt.user_id, message=user_message)
                logger.info(f"Successfully notified user {receipt.user_id} about confirmed deposit {receipt.id}.")
            except Exception as notify_err:
                logger.error(f"Failed to notify user {receipt.user_id} about confirmed receipt {receipt.id}: {notify_err}", exc_info=True)
                # Continue processing even if notification fails

            # 5. Edit Admin Message
            try:
                new_keyboard = create_admin_undo_keyboard('confirm', receipt_id)
                # Append confirmation status to the original message text
                original_text = call.message.text or call.message.caption or ""
                # Ensure we don't append confirmation text multiple times
                if "\n\n✅ تایید شد توسط:" not in original_text:
                    new_text = f"{original_text}\n\n✅ تایید شد توسط: {admin_mention}"
                else:
                     new_text = original_text # Avoid appending again
                     
                if call.message.photo:
                     await call.message.edit_caption(caption=new_text, reply_markup=new_keyboard)
                else:
                     await call.message.edit_text(text=new_text, reply_markup=new_keyboard)
                logger.info(f"Edited admin message for confirmed receipt {receipt.id} in channel {receipt.telegram_channel_id}.")
            except Exception as edit_err:
                logger.error(f"Failed to edit admin message for confirmed receipt {receipt.id}: {edit_err}", exc_info=True)
                # Continue processing, but log the failure

            # If all successful, commit the session
            await session.commit()
            await call.answer("✅ رسید با موفقیت تایید شد.", show_alert=False)
            logger.info(f"Successfully confirmed receipt {receipt_id}, credited user {receipt.user_id}.")

        except Exception as e:
            await session.rollback() # Rollback all changes on any error
            logger.exception(f"Error during receipt confirmation process for receipt {receipt_id} by admin {admin_user_id}: {e}")
            await call.answer("❌ خطای داخلی هنگام تایید رسید رخ داد.", show_alert=True)
            # Optionally try to edit the admin message to show an error state?
            # try:
            #     await call.message.edit_reply_markup(reply_markup=None) # Remove keyboard on error
            # except Exception: pass 


@receipt_router.callback_query(F.data.startswith("reject_receipt:"))
async def handle_reject_receipt(
    call: CallbackQuery,
    session: AsyncSession,
    notification_service: NotificationService,
    receipt_repo: ReceiptLogRepository,
    transaction_repo: TransactionRepository,
    bot: Bot
):
    """Handles the 'Reject Receipt' button press by admin for deposits."""
    receipt_id = int(call.data.split(":")[1])
    admin_user = call.from_user
    admin_user_id = admin_user.id
    admin_mention = admin_user.mention_html(admin_user.first_name)

    logger.info(f"Admin {admin_user_id} attempting to reject receipt {receipt_id}")

    async with session.begin(): # Use transaction block
        receipt = await receipt_repo.get_by_id(receipt_id)

        if not receipt:
            await call.answer("❌ رسید پیدا نشد.", show_alert=True)
            logger.warning(f"Receipt {receipt_id} not found for rejection attempt by admin {admin_user_id}.")
            return

        if receipt.status != ReceiptStatus.PENDING:
            await call.answer(f"⚠️ وضعیت رسید قبلاً به {receipt.status.value} تغییر کرده است.", show_alert=True)
            logger.info(f"Receipt {receipt_id} already has status {receipt.status.value}. Rejection aborted by admin {admin_user_id}.")
            return

        # Find the associated Transaction
        if not receipt.transaction_id:
            logger.error(f"Receipt {receipt_id} rejected by {admin_user_id} has no associated transaction_id.")
            await call.answer("❌ خطا: این رسید به هیچ تراکنشی مرتبط نیست.", show_alert=True)
            # Update receipt status to ERROR?
            return

        transaction = await transaction_repo.get_by_id(receipt.transaction_id)
        if not transaction:
            logger.error(f"Transaction {receipt.transaction_id} associated with receipt {receipt_id} not found during rejection.")
            await call.answer(f"❌ خطا: تراکنش مرتبط (ID: {receipt.transaction_id}) پیدا نشد.", show_alert=True)
            return
            
        if transaction.status != TransactionStatus.PENDING:
             logger.warning(f"Transaction {transaction.id} for receipt {receipt_id} has status {transaction.status} during rejection.")
             await call.answer(f"⚠️ تراکنش مرتبط (ID: {transaction.id}) در وضعیت PENDING نیست ({transaction.status}).", show_alert=True)
             # Update receipt status to REJECTED but don't change transaction?
             # await receipt_repo.update_status(receipt_id, ReceiptStatus.REJECTED, admin_user_id)
             # await call.message.edit_text(f"{call.message.text}\n\n❌ رسید رد شد (تراکنش {transaction.id} قبلاً پردازش شده بود).", reply_markup=None)
             return

        # --- Perform Actions --- 
        try:
            # 1. Update Receipt Status
            logger.info(f"Rejecting receipt {receipt_id} by admin {admin_user_id}.")
            # TODO: Maybe ask admin for rejection reason?
            rejection_reason = "Rejected by admin." # Placeholder reason
            updated_receipt = await receipt_repo.update_status_with_reason(
                receipt_id, ReceiptStatus.REJECTED, admin_user_id, rejection_reason
            )
            if not updated_receipt:
                raise Exception("Failed to update receipt status to REJECTED")

            # 2. Update Transaction Status
            logger.info(f"Updating transaction {transaction.id} status to FAILED for rejected receipt {receipt_id}.")
            updated_transaction = await transaction_repo.update_status(transaction.id, TransactionStatus.FAILED)
            if not updated_transaction:
                raise Exception(f"Failed to update transaction {transaction.id} status to FAILED")

            # --- Post-Actions --- 

            # 3. Notify User
            try:
                user_message = (
                    f"❌ متاسفانه واریز شما تایید نشد.\n\n"
                    f"💰 مبلغ: {format_currency(receipt.amount)}\n"
                    f" دلیل رد شدن: {rejection_reason}\n"
                    f"🔖 کد پیگیری رسید: {receipt.tracking_code}\n\n"
                    f"لطفاً در صورت نیاز با پشتیبانی تماس بگیرید."
                )
                await notification_service.notify_user(user_id=receipt.user_id, message=user_message)
                logger.info(f"Successfully notified user {receipt.user_id} about rejected deposit {receipt.id}.")
            except Exception as notify_err:
                logger.error(f"Failed to notify user {receipt.user_id} about rejected receipt {receipt.id}: {notify_err}", exc_info=True)

            # 4. Edit Admin Message
            try:
                new_keyboard = create_admin_undo_keyboard('reject', receipt_id)
                original_text = call.message.text or call.message.caption or ""
                if "\n\n❌ رد شد توسط:" not in original_text:
                     new_text = f"{original_text}\n\n❌ رد شد توسط: {admin_mention}"
                else:
                     new_text = original_text
                     
                if call.message.photo:
                    await call.message.edit_caption(caption=new_text, reply_markup=new_keyboard)
                else:
                    await call.message.edit_text(text=new_text, reply_markup=new_keyboard)
                logger.info(f"Edited admin message for rejected receipt {receipt.id}.")
            except Exception as edit_err:
                logger.error(f"Failed to edit admin message for rejected receipt {receipt.id}: {edit_err}", exc_info=True)

            # Commit changes
            await session.commit()
            await call.answer("✅ رسید با موفقیت رد شد.", show_alert=False)
            logger.info(f"Successfully rejected receipt {receipt_id} by admin {admin_user_id}.")

        except Exception as e:
            await session.rollback()
            logger.exception(f"Error during receipt rejection process for receipt {receipt_id} by admin {admin_user_id}: {e}")
            await call.answer("❌ خطای داخلی هنگام رد رسید رخ داد.", show_alert=True)


@receipt_router.callback_query(F.data.startswith("message_user:"))
async def handle_message_user_request(call: CallbackQuery, state: FSMContext):
    """Initiates the process for an admin to send a message to the user regarding a receipt."""
    receipt_id = int(call.data.split(":")[1])
    admin_user_id = call.from_user.id
    logger.info(f"Admin {admin_user_id} initiated 'message user' for receipt {receipt_id}.")

    # Store receipt_id and potentially user_id in state to use later
    await state.update_data(target_receipt_id=receipt_id)
    await state.set_state(ReceiptAdminStates.AWAITING_MESSAGE_TO_USER)

    await call.message.reply("💬 لطفاً پیامی که می‌خواهید برای کاربر ارسال شود را تایپ کنید:")
    await call.answer()


@receipt_router.message(ReceiptAdminStates.AWAITING_MESSAGE_TO_USER)
async def process_admin_message_for_user(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    notification_service: NotificationService,
    receipt_repo: ReceiptLogRepository,
    bot: Bot
):
    """Sends the admin's message to the user associated with the receipt."""
    state_data = await state.get_data()
    receipt_id = state_data.get("target_receipt_id")
    admin_message = message.text
    admin_user_id = message.from_user.id

    if not receipt_id:
        logger.error(f"Admin {admin_user_id} sent message '{admin_message}' but target_receipt_id not found in state.")
        await message.reply("❌ خطایی رخ داد: اطلاعات رسید در وضعیت ذخیره نشده است.")
        await state.clear()
        return

    receipt = await receipt_repo.get_by_id(receipt_id)
    if not receipt:
        logger.error(f"Admin {admin_user_id} tried to message user for non-existent receipt {receipt_id}.")
        await message.reply(f"❌ رسید با شناسه {receipt_id} پیدا نشد.")
        await state.clear()
        return

    if not receipt.user_id:
        logger.warning(f"Admin {admin_user_id} tried to message user for receipt {receipt_id}, but user_id is missing.")
        await message.reply(f"❌ شناسه کاربر برای رسید {receipt_id} یافت نشد. امکان ارسال پیام نیست.")
        await state.clear()
        return

    # Send the message via NotificationService
    full_message_to_user = f"✉️ پیام از طرف مدیریت در مورد رسید شما (ID: {receipt_id}):\n\n{admin_message}"
    try:
        logger.info(f"Admin {admin_user_id} sending message to user {receipt.user_id} regarding receipt {receipt_id}.")
        await notification_service.notify_user(user_id=receipt.user_id, message=full_message_to_user)
        await message.reply("✅ پیام شما با موفقیت برای کاربر ارسال شد.")
        logger.info(f"Message sent successfully to user {receipt.user_id} by admin {admin_user_id}.")
    except Exception as e:
        logger.error(f"Failed to send message from admin {admin_user_id} to user {receipt.user_id} for receipt {receipt_id}: {e}")
        await message.reply(f"❌ خطایی در ارسال پیام به کاربر رخ داد: {e}")

    # Clear state after sending
    await state.clear()


@receipt_router.callback_query(F.data.startswith("add_note:"))
async def handle_add_note_request(call: CallbackQuery, state: FSMContext):
    """Initiates adding an internal note to a receipt."""
    receipt_id = int(call.data.split(":")[1])
    admin_user_id = call.from_user.id
    logger.info(f"Admin {admin_user_id} initiated 'add note' for receipt {receipt_id}.")

    await state.update_data(target_receipt_id=receipt_id)
    await state.set_state(ReceiptAdminStates.AWAITING_NOTE)

    await call.message.reply("📝 لطفاً یادداشت داخلی که می‌خواهید به این رسید اضافه شود را بنویسید:")
    await call.answer()


@receipt_router.message(ReceiptAdminStates.AWAITING_NOTE)
async def process_admin_note(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    receipt_repo: ReceiptLogRepository
):
    """Adds the admin's note to the specified receipt."""
    state_data = await state.get_data()
    receipt_id = state_data.get("target_receipt_id")
    note_text = message.text
    admin_user_id = message.from_user.id

    if not receipt_id:
        logger.error(f"Admin {admin_user_id} added note '{note_text}' but target_receipt_id not found in state.")
        await message.reply("❌ خطایی رخ داد: اطلاعات رسید در وضعیت ذخیره نشده است.")
        await state.clear()
        return

    try:
        logger.info(f"Admin {admin_user_id} adding note to receipt {receipt_id}.")
        success = await receipt_repo.add_admin_note(receipt_id, admin_user_id, note_text)
        if success:
            await message.reply("✅ یادداشت شما با موفقیت به رسید اضافه شد.")
            logger.info(f"Note added successfully to receipt {receipt_id} by admin {admin_user_id}.")
            # Optionally, update the original admin message to reflect the note was added
        else:
            await message.reply(f"❌ رسید با شناسه {receipt_id} پیدا نشد یا خطایی در افزودن یادداشت رخ داد.")
            logger.warning(f"Failed to add note to receipt {receipt_id} by admin {admin_user_id}.")

    except Exception as e:
        logger.error(f"Error adding note by admin {admin_user_id} to receipt {receipt_id}: {e}")
        await message.reply(f"❌ خطایی در افزودن یادداشت رخ داد: {e}")

    # Clear state
    await state.clear()

@receipt_router.callback_query(F.data.startswith("undo_confirm:"))
async def handle_undo_confirm(
    call: CallbackQuery,
    session: AsyncSession,
    notification_service: NotificationService,
    receipt_repo: ReceiptLogRepository,
    transaction_repo: TransactionRepository,
    wallet_service: WalletService,
    bot: Bot
):
    """Handles the 'Undo Confirmation' button press by admin."""
    receipt_id = int(call.data.split(":")[1])
    admin_user = call.from_user
    admin_user_id = admin_user.id

    logger.info(f"Admin {admin_user_id} attempting to undo confirmation for receipt {receipt_id}")

    async with session.begin():
        receipt = await receipt_repo.get_by_id(receipt_id)
        if not receipt or receipt.status != ReceiptStatus.APPROVED:
            await call.answer("⚠️ این رسید تایید نشده یا وضعیت آن تغییر کرده است.", show_alert=True)
            logger.warning(f"Undo confirm failed for receipt {receipt_id}: Status is {receipt.status if receipt else 'Not Found'}.")
            return
            
        transaction = await transaction_repo.get_by_id(receipt.transaction_id)
        if not transaction or transaction.status != TransactionStatus.SUCCESS:
             await call.answer("⚠️ تراکنش مرتبط موفق نیست یا یافت نشد.", show_alert=True)
             logger.warning(f"Undo confirm failed for receipt {receipt_id}: Transaction {receipt.transaction_id} status is {transaction.status if transaction else 'Not Found'}.")
             return

        try:
            # 1. Revert Transaction Status
            updated_transaction = await transaction_repo.update_status(transaction.id, TransactionStatus.PENDING)
            if not updated_transaction:
                raise Exception(f"Failed to revert transaction {transaction.id} status to PENDING")

            # 2. Revert Receipt Status
            updated_receipt = await receipt_repo.update_status(receipt_id, ReceiptStatus.PENDING, admin_user_id, note="Confirmation undone by admin.") # Needs update_status_with_note?
            if not updated_receipt:
                 # Assuming update_status handles note setting, otherwise need update_status_with_note
                 # Or call add_note separately if needed
                raise Exception("Failed to revert receipt status to PENDING")

            # 3. Debit User Wallet
            debit_amount = receipt.amount
            success_debit = await wallet_service.debit(receipt.user_id, float(debit_amount), f"Undo deposit confirmation - Receipt ID: {receipt.id}")
            if not success_debit:
                 # This is tricky. Transaction/Receipt reverted, but debit failed.
                 # Maybe raise a specific exception? Or log critical error?
                 # For now, raise exception to trigger rollback.
                raise Exception(f"Failed to debit wallet for user {receipt.user_id}, amount {debit_amount} during undo.")

            # --- Post-Actions --- 
            # 4. Edit Admin Message back to original state
            try:
                original_keyboard = get_receipt_admin_keyboard(receipt_id)
                # Remove the "✅ تایید شد توسط..." part from the text/caption
                original_text = call.message.text or call.message.caption or ""
                cleaned_text = original_text.split("\n\n✅ تایید شد توسط:")[0]

                if call.message.photo:
                    await call.message.edit_caption(caption=cleaned_text, reply_markup=original_keyboard)
                else:
                    await call.message.edit_text(text=cleaned_text, reply_markup=original_keyboard)
                logger.info(f"Admin message reverted for receipt {receipt_id} after undo confirm.")
            except Exception as edit_err:
                logger.error(f"Failed to edit admin message during undo confirm for receipt {receipt_id}: {edit_err}", exc_info=True)
                # Continue commit even if edit fails?

            # 5. Notify User? (Optional)
            # Consider notifying the user that the previous confirmation was undone.
            # try:
            #     await notification_service.notify_user(user_id=receipt.user_id, message=f"⚠️ تایید واریز قبلی شما (رسید {receipt.id}) توسط مدیریت لغو شد.")
            # except Exception as notify_err:
            #     logger.error(f"Failed to notify user about undo confirm for receipt {receipt.id}: {notify_err}")
            
            await session.commit()
            await call.answer("✅ عملیات تایید لغو شد.", show_alert=False)
            logger.info(f"Successfully undone confirmation for receipt {receipt_id} by admin {admin_user_id}.")

        except Exception as e:
            await session.rollback()
            logger.exception(f"Error during undo confirmation for receipt {receipt_id} by admin {admin_user_id}: {e}")
            await call.answer("❌ خطای داخلی هنگام لغو تایید رخ داد.", show_alert=True)


@receipt_router.callback_query(F.data.startswith("undo_reject:"))
async def handle_undo_reject(
    call: CallbackQuery,
    session: AsyncSession,
    notification_service: NotificationService,
    receipt_repo: ReceiptLogRepository,
    transaction_repo: TransactionRepository,
    bot: Bot
):
    """Handles the 'Undo Rejection' button press by admin."""
    receipt_id = int(call.data.split(":")[1])
    admin_user = call.from_user
    admin_user_id = admin_user.id

    logger.info(f"Admin {admin_user_id} attempting to undo rejection for receipt {receipt_id}")

    async with session.begin():
        receipt = await receipt_repo.get_by_id(receipt_id)
        if not receipt or receipt.status != ReceiptStatus.REJECTED:
            await call.answer("⚠️ این رسید رد نشده یا وضعیت آن تغییر کرده است.", show_alert=True)
            logger.warning(f"Undo reject failed for receipt {receipt_id}: Status is {receipt.status if receipt else 'Not Found'}.")
            return

        transaction = await transaction_repo.get_by_id(receipt.transaction_id)
        if not transaction or transaction.status != TransactionStatus.FAILED:
            await call.answer("⚠️ تراکنش مرتبط ناموفق نیست یا یافت نشد.", show_alert=True)
            logger.warning(f"Undo reject failed for receipt {receipt_id}: Transaction {receipt.transaction_id} status is {transaction.status if transaction else 'Not Found'}.")
            return

        try:
            # 1. Revert Transaction Status
            updated_transaction = await transaction_repo.update_status(transaction.id, TransactionStatus.PENDING)
            if not updated_transaction:
                raise Exception(f"Failed to revert transaction {transaction.id} status to PENDING")

            # 2. Revert Receipt Status
            updated_receipt = await receipt_repo.update_status(receipt_id, ReceiptStatus.PENDING, admin_user_id, note="Rejection undone by admin.")
            if not updated_receipt:
                raise Exception("Failed to revert receipt status to PENDING")

            # --- Post-Actions --- 
            # 3. Edit Admin Message back to original state
            try:
                original_keyboard = get_receipt_admin_keyboard(receipt_id)
                original_text = call.message.text or call.message.caption or ""
                cleaned_text = original_text.split("\n\n❌ رد شد توسط:")[0]

                if call.message.photo:
                    await call.message.edit_caption(caption=cleaned_text, reply_markup=original_keyboard)
                else:
                    await call.message.edit_text(text=cleaned_text, reply_markup=original_keyboard)
                logger.info(f"Admin message reverted for receipt {receipt_id} after undo reject.")
            except Exception as edit_err:
                logger.error(f"Failed to edit admin message during undo reject for receipt {receipt_id}: {edit_err}", exc_info=True)

            # 4. Notify User? (Optional)
            # Consider notifying the user that the previous rejection was undone.
            
            await session.commit()
            await call.answer("✅ عملیات رد لغو شد.", show_alert=False)
            logger.info(f"Successfully undone rejection for receipt {receipt_id} by admin {admin_user_id}.")

        except Exception as e:
            await session.rollback()
            logger.exception(f"Error during undo rejection for receipt {receipt_id} by admin {admin_user_id}: {e}")
            await call.answer("❌ خطای داخلی هنگام لغو رد رخ داد.", show_alert=True)


@receipt_router.callback_query(F.data.startswith("message_user:"))
async def handle_message_user_request(call: CallbackQuery, state: FSMContext):
    """Initiates the process for an admin to send a message to the user regarding a receipt."""
    receipt_id = int(call.data.split(":")[1])
    admin_user_id = call.from_user.id
    logger.info(f"Admin {admin_user_id} initiated 'message user' for receipt {receipt_id}.")

    # Store receipt_id and potentially user_id in state to use later
    await state.update_data(target_receipt_id=receipt_id)
    await state.set_state(ReceiptAdminStates.AWAITING_MESSAGE_TO_USER)

    await call.message.reply("💬 لطفاً پیامی که می‌خواهید برای کاربر ارسال شود را تایپ کنید:")
    await call.answer()


@receipt_router.message(ReceiptAdminStates.AWAITING_MESSAGE_TO_USER)
async def process_admin_message_for_user(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    notification_service: NotificationService,
    receipt_repo: ReceiptLogRepository,
    bot: Bot
):
    """Sends the admin's message to the user associated with the receipt."""
    state_data = await state.get_data()
    receipt_id = state_data.get("target_receipt_id")
    admin_message = message.text
    admin_user_id = message.from_user.id

    if not receipt_id:
        logger.error(f"Admin {admin_user_id} sent message '{admin_message}' but target_receipt_id not found in state.")
        await message.reply("❌ خطایی رخ داد: اطلاعات رسید در وضعیت ذخیره نشده است.")
        await state.clear()
        return

    receipt = await receipt_repo.get_by_id(receipt_id)
    if not receipt:
        logger.error(f"Admin {admin_user_id} tried to message user for non-existent receipt {receipt_id}.")
        await message.reply(f"❌ رسید با شناسه {receipt_id} پیدا نشد.")
        await state.clear()
        return

    if not receipt.user_id:
        logger.warning(f"Admin {admin_user_id} tried to message user for receipt {receipt_id}, but user_id is missing.")
        await message.reply(f"❌ شناسه کاربر برای رسید {receipt_id} یافت نشد. امکان ارسال پیام نیست.")
        await state.clear()
        return

    # Send the message via NotificationService
    full_message_to_user = f"✉️ پیام از طرف مدیریت در مورد رسید شما (ID: {receipt_id}):\n\n{admin_message}"
    try:
        logger.info(f"Admin {admin_user_id} sending message to user {receipt.user_id} regarding receipt {receipt_id}.")
        await notification_service.notify_user(user_id=receipt.user_id, message=full_message_to_user)
        await message.reply("✅ پیام شما با موفقیت برای کاربر ارسال شد.")
        logger.info(f"Message sent successfully to user {receipt.user_id} by admin {admin_user_id}.")
    except Exception as e:
        logger.error(f"Failed to send message from admin {admin_user_id} to user {receipt.user_id} for receipt {receipt_id}: {e}")
        await message.reply(f"❌ خطایی در ارسال پیام به کاربر رخ داد: {e}")

    # Clear state after sending
    await state.clear()


@receipt_router.callback_query(F.data.startswith("add_note:"))
async def handle_add_note_request(call: CallbackQuery, state: FSMContext):
    """Initiates adding an internal note to a receipt."""
    receipt_id = int(call.data.split(":")[1])
    admin_user_id = call.from_user.id
    logger.info(f"Admin {admin_user_id} initiated 'add note' for receipt {receipt_id}.")

    await state.update_data(target_receipt_id=receipt_id)
    await state.set_state(ReceiptAdminStates.AWAITING_NOTE)

    await call.message.reply("📝 لطفاً یادداشت داخلی که می‌خواهید به این رسید اضافه شود را بنویسید:")
    await call.answer()


@receipt_router.message(ReceiptAdminStates.AWAITING_NOTE)
async def process_admin_note(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    receipt_repo: ReceiptLogRepository
):
    """Adds the admin's note to the specified receipt."""
    state_data = await state.get_data()
    receipt_id = state_data.get("target_receipt_id")
    note_text = message.text
    admin_user_id = message.from_user.id

    if not receipt_id:
        logger.error(f"Admin {admin_user_id} added note '{note_text}' but target_receipt_id not found in state.")
        await message.reply("❌ خطایی رخ داد: اطلاعات رسید در وضعیت ذخیره نشده است.")
        await state.clear()
        return

    try:
        logger.info(f"Admin {admin_user_id} adding note to receipt {receipt_id}.")
        success = await receipt_repo.add_admin_note(receipt_id, admin_user_id, note_text)
        if success:
            await message.reply("✅ یادداشت شما با موفقیت به رسید اضافه شد.")
            logger.info(f"Note added successfully to receipt {receipt_id} by admin {admin_user_id}.")
            # Optionally, update the original admin message to reflect the note was added
        else:
            await message.reply(f"❌ رسید با شناسه {receipt_id} پیدا نشد یا خطایی در افزودن یادداشت رخ داد.")
            logger.warning(f"Failed to add note to receipt {receipt_id} by admin {admin_user_id}.")

    except Exception as e:
        logger.error(f"Error adding note by admin {admin_user_id} to receipt {receipt_id}: {e}")
        await message.reply(f"❌ خطایی در افزودن یادداشت رخ داد: {e}")

    # Clear state
    await state.clear()

# TODO: Remember to register this router in your main bot setup
# e.g., dp.include_router(admin_receipt_handlers.router) 