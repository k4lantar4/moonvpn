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

# Initialize router
receipt_router = Router(name="receipt_router")
logger = logging.getLogger(__name__)

# The function get_receipt_admin_keyboard used to be here, it has been moved to bot/keyboards/receipt_keyboards.py

@receipt_router.message(F.photo | F.text)
async def process_user_receipt(message: Message, state: FSMContext, session: AsyncSession):
    """Handles user submission of a receipt (photo or text)."""
    user_id = message.from_user.id
    text_reference = message.caption or message.text
    photo_file_id = message.photo[-1].file_id if message.photo else None
    submitted_at = message.date

    # --- TODO: Determine card_id --- 
    # How is the target bank card selected or known?
    # Example: Maybe from FSM state?
    state_data = await state.get_data()
    card_id = state_data.get("selected_card_id") 
    if not card_id:
        await message.reply("❌ لطفاً ابتدا کارت بانکی مورد نظر را انتخاب کنید.") # Please select the bank card first.
        return
    # --- End TODO ---

    # --- TODO: Determine amount --- 
    # Amount is required by model but might not be in message.
    # Placeholder - needs logic for extraction or user input.
    amount = state_data.get("payment_amount", 0.0) # Example: Get from state
    if amount <= 0:
         await message.reply("❌ مبلغ مشخص نشده یا نامعتبر است.") # Amount not specified or invalid.
         return
    # --- End TODO ---

    # --- TODO: Determine Order/Transaction context --- 
    order_id = state_data.get("order_id")
    transaction_id = state_data.get("transaction_id")
    # --- End TODO ---

    # Create receipt log entry (initial)
    # This assumes a PaymentService exists and handles the logic
    # payment_service = PaymentService(session)
    # Alternatively, use repositories directly if service layer is thin
    receipt_repo = ReceiptLogRepository(session)
    payment_service = PaymentService(session) # Instantiate or get service
    try:
        new_receipt = await receipt_repo.create_receipt_log(
            user_id=user_id,
            card_id=card_id,
            amount=amount, # Use determined amount
            status=ReceiptStatus.PENDING,
            text_reference=text_reference,
            photo_file_id=photo_file_id,
            order_id=order_id,
            transaction_id=transaction_id,
            submitted_at=submitted_at,
            # tracking_code needs generation/extraction logic
            tracking_code=f"TEMP-{user_id}-{int(submitted_at.timestamp())}" # Placeholder tracking code
        )
        await session.flush() # Ensure ID is available

        # --- Call Service to Format, Send to Channel & Update Log --- 
        send_success = await payment_service.send_receipt_to_admin_channel(new_receipt.id)
        
        if send_success:
            await message.reply("✅ رسید شما دریافت شد و برای بررسی به کانال مدیریت ارسال گردید.") # Your receipt was received and sent to the admin channel for review.
        else:
            # Inform user, but log the issue internally for admin follow-up
            await message.reply("✅ رسید شما دریافت شد، اما مشکلی در ارسال به کانال مدیریت رخ داد. لطفاً منتظر بمانید.") # Your receipt was received, but there was an issue sending it to the admin channel. Please wait.

    except Exception as e:
        # Log error
        print(f"Error processing receipt: {e}")
        await message.reply("⚠️ خطایی در پردازش رسید رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.") # An error occurred while processing the receipt.


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
    client_service: ClientService,
    receipt_repo: ReceiptLogRepository,
    order_repo: OrderRepository,
    plan_repo: PlanRepository,
    server_repo: ServerRepository,
    bot: Bot
):
    """Handles the 'Confirm Receipt' button press by admin."""
    receipt_id = int(call.data.split(":")[1])
    admin_user_id = call.from_user.id
    logger.info(f"Admin {admin_user_id} trying to confirm receipt {receipt_id}")

    receipt = await receipt_repo.get_by_id(receipt_id)

    if not receipt:
        await call.answer("❌ رسید پیدا نشد.", show_alert=True)
        logger.warning(f"Receipt {receipt_id} not found for confirmation attempt by admin {admin_user_id}.")
        return

    if receipt.status != ReceiptStatus.PENDING:
        await call.answer(f"⚠️ وضعیت رسید قبلاً به {receipt.status.value} تغییر کرده است.", show_alert=True)
        logger.info(f"Receipt {receipt_id} already has status {receipt.status.value}. Confirmation aborted by admin {admin_user_id}.")
        return

    # --- START: Added logic as per request ---

    # 1. Fetch related order
    if not receipt.order_id:
        logger.error(f"Receipt {receipt_id} confirmed by {admin_user_id} has no associated order_id.")
        await call.answer("❌ این رسید به هیچ سفارشی مرتبط نیست.", show_alert=True)
        # Optionally, update receipt status to an error state
        await receipt_repo.update_status(receipt_id, ReceiptStatus.ERROR, admin_user_id, note="Missing order_id")
        return

    order = await order_repo.get_by_id(receipt.order_id)
    if not order:
        logger.error(f"Order {receipt.order_id} associated with receipt {receipt_id} not found.")
        await call.answer(f"❌ سفارش مرتبط با این رسید (ID: {receipt.order_id}) پیدا نشد.", show_alert=True)
        await receipt_repo.update_status(receipt_id, ReceiptStatus.ERROR, admin_user_id, note=f"Associated Order {receipt.order_id} not found")
        return

    # Check if order is already fulfilled or failed
    if order.status in [OrderStatus.CREATED, OrderStatus.FAILED]:
         logger.warning(f"Order {order.id} associated with receipt {receipt_id} has status {order.status}. Confirmation skipped.")
         await call.answer(f"⚠️ سفارش مرتبط (ID: {order.id}) قبلاً پردازش شده یا ناموفق بوده ({order.status}).", show_alert=True)
         # Update receipt to Approved but skip account creation if order is already processed
         await receipt_repo.update_status(receipt_id, ReceiptStatus.APPROVED, admin_user_id)
         # Edit the admin message to reflect this outcome
         await call.message.edit_text(f"{call.message.text}\n\n✅ رسید تایید شد (سفارش {order.id} قبلاً پردازش شده بود).")
         return

    # Approve the receipt first
    logger.info(f"Approving receipt {receipt_id} by admin {admin_user_id}.")
    updated_receipt = await receipt_repo.update_status(receipt_id, ReceiptStatus.APPROVED, admin_user_id)
    if not updated_receipt:
        logger.error(f"Failed to update receipt {receipt_id} status to APPROVED for admin {admin_user_id}.")
        await call.answer("❌ خطایی در بروزرسانی وضعیت رسید رخ داد.", show_alert=True)
        return

    try:
        # 2. Create account
        logger.info(f"Creating client account for order {order.id} (triggered by receipt {receipt_id} confirmation).")
        client_account = await client_service.create_client_account_for_order(order.id)

        if not client_account:
            logger.error(f"Client account creation failed for order {order.id}. Rolling back receipt status.")
            await call.answer("❌ ساخت اکانت برای این سفارش ناموفق بود.", show_alert=True)
            # Revert receipt status? Or set order to FAILED?
            await receipt_repo.update_status(receipt_id, ReceiptStatus.ERROR, admin_user_id, note="Account creation failed")
            await order_repo.update_status(order.id, OrderStatus.FAILED)
            await call.message.edit_text(f"{call.message.text}\n\n🚫 خطا در ساخت اکانت. وضعیت رسید به ERROR و سفارش به FAILED تغییر کرد.")
            return

        logger.info(f"Client account {client_account.id} created successfully for order {order.id}.")

        # Fetch Plan and Panel/Server for message formatting
        plan = await plan_repo.get_by_id(order.plan_id)
        panel = await server_repo.get_panel_by_server_id(client_account.server_id) # Assumes relation or method exists

        if not plan:
             logger.warning(f"Plan {order.plan_id} not found for order {order.id}. Cannot format full message.")
             # Proceed with generic message or handle error?
             plan_traffic_gb = "N/A"
             plan_name = "N/A" # Or some default
        else:
             plan_traffic_gb = plan.traffic_gb
             plan_name = plan.name

        location_emoji = "🇩🇪" # Default or fetch dynamically based on panel/server info if available
        protocol = "VLESS" # Default or fetch dynamically if needed
        location_name = "آلمان" # Default or fetch dynamically
        if panel:
             # Example: Dynamically set based on panel data if available
             location_emoji = panel.location_emoji or location_emoji
             location_name = panel.location_name or location_name
             # protocol might also come from panel or client_account details

        # 3. Format message for user
        expiry_date_shamsi = format_shamsi_date(client_account.expiry_date) if client_account.expiry_date else "نامشخص"

        formatted_message = f"""
✅ سرویس شما با موفقیت فعال شد!

📡 لوکیشن: {location_emoji} {location_name}
🔒 پروتکل: {protocol}
📅 انقضا: {expiry_date_shamsi}
📶 حجم کل: {plan_traffic_gb} گیگ

🔗 لینک اتصال:
`{client_account.config_url}`

🌐 اشتراک عمومی:
`{client_account.subscription_url}`

📱 برای مشاهده سرویس‌های فعال: /myaccounts
"""
        # 4. Send final message to user
        logger.info(f"Notifying user {order.user_id} about successful account creation for order {order.id}.")
        await notification_service.notify_user(user_id=order.user_id, message=formatted_message)

        # 5. Update Order status to CREATED and set fulfilled_at
        logger.info(f"Updating order {order.id} status to CREATED and setting fulfilled_at.")
        await order_repo.update_status(order.id, OrderStatus.CREATED)
        await order_repo.set_fulfilled_at(order.id, datetime.now())

        # --- END: Added logic ---

        # Edit the admin message to confirm success
        await call.message.edit_text(f"{call.message.text}\n\n✅ رسید تایید شد، اکانت ساخته شد و پیام برای کاربر ارسال گردید.")
        await call.answer("✅ عملیات با موفقیت انجام شد.", show_alert=True)
        logger.info(f"Receipt {receipt_id} confirmed, account created for order {order.id}, user notified.")

    except Exception as e:
        logger.exception(f"Error during post-receipt confirmation processing for receipt {receipt_id}, order {order.id}: {e}")
        await call.answer("❌ خطای داخلی در پردازش پس از تایید رسید.", show_alert=True)
        # Attempt to notify admin/user about the error
        admin_error_msg = f"Error processing receipt {receipt_id} / order {order.id} after confirmation: {e}"
        user_error_msg = "⚠️ خطایی در فرآیند فعال‌سازی سرویس شما پس از تایید پرداخت رخ داد. لطفاً با پشتیبانی تماس بگیرید."
        # await notification_service.notify_admin(admin_error_msg) # If exists
        if order and order.user_id:
             await notification_service.notify_user(user_id=order.user_id, message=user_error_msg)
        # Consider setting order/receipt to an error state
        await receipt_repo.update_status(receipt_id, ReceiptStatus.ERROR, admin_user_id, note=f"Error after approval: {e}")
        if order:
            await order_repo.update_status(order.id, OrderStatus.FAILED)
        await call.message.edit_text(f"{call.message.text}\n\n🚫 خطای داخلی پس از تایید رسید رخ داد. وضعیت رسید به ERROR و سفارش به FAILED تغییر کرد.")


@receipt_router.callback_query(F.data.startswith("reject_receipt:"))
async def handle_reject_receipt(
    call: CallbackQuery,
    session: AsyncSession,
    notification_service: NotificationService,
    receipt_repo: ReceiptLogRepository,
    bot: Bot
):
    """Handles the 'Reject Receipt' button press by admin."""
    receipt_id = int(call.data.split(":")[1])
    admin_user_id = call.from_user.id
    logger.info(f"Admin {admin_user_id} trying to reject receipt {receipt_id}")

    receipt = await receipt_repo.get_by_id(receipt_id)

    if not receipt:
        await call.answer("❌ رسید پیدا نشد.", show_alert=True)
        logger.warning(f"Receipt {receipt_id} not found for rejection attempt by admin {admin_user_id}.")
        return

    if receipt.status != ReceiptStatus.PENDING:
        await call.answer(f"⚠️ وضعیت رسید قبلاً به {receipt.status.value} تغییر کرده است.", show_alert=True)
        logger.info(f"Receipt {receipt_id} already has status {receipt.status.value}. Rejection aborted by admin {admin_user_id}.")
        return

    # Update receipt status to REJECTED
    logger.info(f"Rejecting receipt {receipt_id} by admin {admin_user_id}.")
    updated_receipt = await receipt_repo.update_status(receipt_id, ReceiptStatus.REJECTED, admin_user_id)

    if not updated_receipt:
        logger.error(f"Failed to update receipt {receipt_id} status to REJECTED for admin {admin_user_id}.")
        await call.answer("❌ خطایی در بروزرسانی وضعیت رسید رخ داد.", show_alert=True)
        return

    # Notify the user about rejection
    user_message = f"❌ رسید شما (ID: {receipt_id}) متاسفانه توسط مدیریت رد شد. لطفاً برای اطلاعات بیشتر یا ارسال مجدد با پشتیبانی تماس بگیرید."
    if receipt.user_id: # Use receipt.user_id directly if available
        try:
             logger.info(f"Notifying user {receipt.user_id} about rejection of receipt {receipt_id}.")
             await notification_service.notify_user(user_id=receipt.user_id, message=user_message)
        except Exception as e:
             logger.error(f"Failed to notify user {receipt.user_id} about rejection of receipt {receipt_id}: {e}")
             # Log error, maybe notify admin?
    else:
         logger.warning(f"Cannot notify user about rejection of receipt {receipt_id}: user_id not found on receipt.")


    # Update the admin message
    await call.message.edit_text(f"{call.message.text}\n\n❌ رسید رد شد و به کاربر اطلاع داده شد.")
    await call.answer("✅ رسید با موفقیت رد شد.", show_alert=True)
    logger.info(f"Receipt {receipt_id} rejected successfully by admin {admin_user_id}.")


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