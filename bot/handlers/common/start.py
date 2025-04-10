"""Handler for the /start command."""

import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
# from aiogram.fsm.context import FSMContext # Removed FSMContext import
from sqlalchemy.ext.asyncio import AsyncSession

# Import UserService and its dependencies
from bot.services.user_service import UserService
from core.database.repositories.user_repository import UserRepository
from core.database.repositories.role_repository import RoleRepository

# Setup logger for this handler
logger = logging.getLogger(__name__)

router = Router(name="start-command")

# Removed state: FSMContext from the signature
@router.message(CommandStart())
async def handle_start(message: Message, session: AsyncSession):
    """Handles the /start command, registers or greets the user."""
    logger.info("!!!!!! --- Entered handle_start --- !!!!!!")
    user = message.from_user
    if not user:
        logger.warning("Received /start from a user with no user data.")
        return # Cannot process without user info

    user_id = user.id
    full_name = user.full_name
    username = user.username or ""

    logger.info(f"Received /start from user_id={user_id}, username='{username}', full_name='{full_name}'")

    db_user = None # Initialize db_user to None
    is_new = False # Initialize is_new
    # --- User Registration/Greeting Logic ---
    try:
        # Instantiate UserService without arguments
        user_service = UserService()

        # Call service method, passing the session
        logger.debug(f"Calling get_or_create_user for user_id={user_id}")
        db_user, is_new = await user_service.get_or_create_user(
            db_session=session, # Pass session here
            user_id=user_id,
            username=username,
            full_name=full_name
        )
        logger.info(f"User processed: user_id={db_user.id}, is_new={is_new}")
        
        # Commit the session if the operation was successful (user found or created)
        # BaseRepo create() handles its own commit, so maybe commit is not needed here?
        # Let's assume BaseRepo handles commit for create, but maybe not for get.
        # For safety, let's commit here after the operation seems successful.
        await session.commit() 
        logger.debug(f"Session committed after get_or_create_user for user {user_id}")

        # 3. Welcome the user
        if is_new:
            # TODO: Notify admin channel (using NotificationService)
            welcome_text = f"👋 سلام **{full_name}**! به MoonVPN خوش اومدی. 🚀 از الان می‌تونی از امکانات ربات استفاده کنی."
            logger.info(f"New user registered: {user_id}")
        else:
            welcome_text = f"👋 سلام مجدد **{full_name}**! چه خوب که برگشتی. 😊"
            logger.debug(f"Existing user greeted: {user_id}")

    except Exception as e:
        logger.error(f"Error processing /start for user {user_id}: {e}", exc_info=True)
        welcome_text = "⚠️ متاسفانه مشکلی در پردازش درخواست شما پیش آمد. لطفاً لحظاتی دیگر دوباره تلاش کنید."
        # Rollback the session in case of error
        try:
            await session.rollback()
            logger.warning(f"Session rolled back due to error processing /start for user {user_id}.")
        except Exception as rb_err:
            logger.error(f"Failed to rollback session after /start error: {rb_err}")

    # TODO: Add main menu keyboard based on db_user.role
    # from bot.keyboards.reply import get_main_menu_keyboard
    # role_name = db_user.role.name if db_user and db_user.role else 'USER' # Safely access role
    # keyboard = get_main_menu_keyboard(role_name)

    try:
        await message.answer(
            welcome_text,
            # reply_markup=keyboard # Uncomment when keyboard is ready
        )
    except Exception as e:
         logger.error(f"Failed to send welcome message to user {user_id}: {e}", exc_info=True) 