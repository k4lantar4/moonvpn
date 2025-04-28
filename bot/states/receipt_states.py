from aiogram.fsm.state import State, StatesGroup

class ReceiptAdminStates(StatesGroup):
    """States for admin handling receipts"""
    AWAITING_MESSAGE_TO_USER = State()
    AWAITING_NOTE = State()
    AWAITING_REJECTION_REASON = State()

class DepositStates(StatesGroup):
    """States for user deposit flow"""
    AWAITING_AMOUNT = State()
    AWAITING_CARD_SELECTION = State()
    AWAITING_RECEIPT = State()
    AWAITING_DEPOSIT_CONFIRMATION = State() 