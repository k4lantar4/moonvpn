from aiogram.fsm.state import State, StatesGroup

class ReceiptAdminStates(StatesGroup):
    """States for admin handling receipts"""
    AWAITING_MESSAGE_TO_USER = State()
    AWAITING_NOTE = State() 