from aiogram.fsm.state import StatesGroup, State

class OrderTaking(StatesGroup):
    waiting_for_order_id = State()

class Withdrawal(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment_details = State()

class AdminOrderPost(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()