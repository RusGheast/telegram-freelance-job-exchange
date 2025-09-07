from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update
from database import SessionLocal
from models import User, WithdrawalRequest, Order
from states import Withdrawal, OrderTaking
from keyboards import main_menu_kb, cancel_order_kb, back
from config import config

router = Router()

@router.message(F.text == "/start")
async def start(msg: Message, state: FSMContext):
    await state.clear()
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.tg_id == msg.from_user.id))
        if not user:
            session.add(User(tg_id=msg.from_user.id, username=msg.from_user.username))
            await session.commit()

    welcome_text = (
        "👋 Добро пожаловать в OrderBot!\n\n"
        "Здесь вы можете:\n"
        "📋 Просматривать доступные заказы\n"
        "📈 Следить за своим профилем и балансом\n"
        "💳 Запрашивать вывод средств за выполненные задания\n\n"
        "Используйте меню ниже, чтобы начать работу!"
    )
    await msg.answer(welcome_text, reply_markup=main_menu_kb())

@router.message(F.text == "📈 Профиль")
async def profile(msg: Message):
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.tg_id == msg.from_user.id))
        await msg.answer(f"👤 @{user.username}\n💰 Баланс: {user.balance}\n📦 Выполнено: {user.completed_orders}")

@router.message(F.text == "📋 Список заказов")
async def list_orders(msg: Message, state: FSMContext):
    async with SessionLocal() as session:
        orders = (await session.scalars(select(Order).where(Order.taken == False))).all()
        if not orders:
            await msg.answer("Нет доступных заказов.")
        else:
            text = "Доступные заказы:\n"
            for order in orders:
                text += f"ID: {order.id}\n📌 {order.title}\n📝 {order.description}\n\n"
            text += "\nВведите ID заказа, который хотите взять."
            await msg.answer(text)
            await state.set_state(OrderTaking.waiting_for_order_id)

@router.message(OrderTaking.waiting_for_order_id)
async def take_order(msg: Message, state: FSMContext):
    if not msg.text or not msg.text.isdigit():
        await msg.answer("❌ Пожалуйста, введите корректный числовой ID заказа.")
        return

    order_id = int(msg.text.strip())
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        user = await session.scalar(select(User).where(User.tg_id == msg.from_user.id))
        if not order or order.taken:
            await msg.answer("❌ Этот заказ недоступен или уже взят.")
        else:
            order.taken = True
            order.taken_by = user.id
            await session.commit()
            await msg.answer(
                "✅ Вы приняли заказ! После выполнения админ подтвердит выполнение.",
                reply_markup=cancel_order_kb(order_id)
            )
            await msg.bot.send_message(
                config.ADMIN_ID,
                f"👷 Заказ принят:\n"
                f"📋 ID заказа: {order.id}\n"
                f"📌 {order.title}\n"
                f"👤 Исполнитель: @{user.username}\n\n"
                f"Для подтверждения выполненного заказа отправьте команду:\n"
                f"/confirm_{order.id}_<сумма>"
                )

    await state.clear()

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        if order and order.taken_by == user.id and not order.completed:
            order.taken = False
            order.taken_by = None
            await session.commit()
            await callback.message.edit_text("Вы отказались от заказа.")
        else:
            await callback.answer("Невозможно отказаться от этого заказа.", show_alert=True)

@router.message(F.text == "💳 Вывод средств")
async def withdraw_request(msg: Message, state: FSMContext):
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.tg_id == msg.from_user.id))
        await msg.answer(f"💰 Ваш текущий баланс: {user.balance} монет")
        if user.balance == 0:
            await msg.answer("⚠️ У вас нулевой баланс, вывод невозможен.")
            return
    await msg.answer("Введите сумму для вывода:\n1 монета = 1 ₽", reply_markup=back)
    await state.set_state(Withdrawal.waiting_for_amount)

@router.message(Withdrawal.waiting_for_amount)
async def process_withdraw_amount(msg: Message, state: FSMContext):
    try:
        amount = int(msg.text)
        if amount <= 0:
            raise ValueError()
    except:
        await msg.answer("Пожалуйста, введите корректное число.")
        return

    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.tg_id == msg.from_user.id))
        if amount > user.balance:
            await msg.answer("Недостаточно средств на балансе.")
            return
        await state.update_data(amount=amount)

        if user.payment_details:
            await msg.answer(
                f"Ваши сохранённые реквизиты для вывода:\n{user.payment_details}\n\n"
                "Если хотите использовать их, отправьте 'Да',\n"
                "или введите новые реквизиты для вывода."
            )
            await state.set_state(Withdrawal.waiting_for_payment_details)
        else:
            await msg.answer("Введите реквизиты для вывода (например, номер карты или номер телефона и банк):")
            await state.set_state(Withdrawal.waiting_for_payment_details)

@router.message(Withdrawal.waiting_for_payment_details)
async def process_withdraw_payment_details(msg: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount")
    payment_input = msg.text.strip()

    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.tg_id == msg.from_user.id))
        if payment_input.lower() == "да" and user.payment_details:
            payment_details = user.payment_details
        else:
            payment_details = payment_input
            user.payment_details = payment_details

        if amount > user.balance:
            await msg.answer("Недостаточно средств на балансе.")
            await state.clear()
            return

        user.balance -= amount
        session.add(WithdrawalRequest(user_id=user.id, amount=amount))
        await session.commit()

        await msg.answer(f"Заявка на вывод {amount} монет создана.\nРеквизиты:\n{payment_details}")
        await msg.bot.send_message(config.ADMIN_ID, f"🔔 Вывод: @{user.username} - {amount} монет\nРеквизиты: {payment_details}")

    await state.clear()

@router.callback_query(F.data == "back")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    welcome_text = (
        "👋 Добро пожаловать в OrderBot!\n\n"
        "Здесь вы можете:\n"
        "📋 Просматривать доступные заказы\n"
        "📈 Следить за своим профилем и балансом\n"
        "💳 Запрашивать вывод средств за выполненные задания\n\n"
        "Используйте меню ниже, чтобы начать работу!"
    )
    await callback.message.edit_text(welcome_text)