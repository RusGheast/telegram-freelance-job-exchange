from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from database import SessionLocal
from models import Order, User, WithdrawalRequest
from states import AdminOrderPost
from config import config
from keyboards import withdrawal_approve_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()

@router.message(F.from_user.id == config.ADMIN_ID, F.text == "/new_order")
async def new_order_start(msg: Message, state: FSMContext):
    await msg.answer("Введите заголовок заказа:")
    await state.set_state(AdminOrderPost.waiting_for_title)

@router.message(AdminOrderPost.waiting_for_title)
async def new_order_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await msg.answer("Введите описание заказа:")
    await state.set_state(AdminOrderPost.waiting_for_description)

@router.message(AdminOrderPost.waiting_for_description)
async def new_order_description(msg: Message, state: FSMContext):
    data = await state.get_data()
    async with SessionLocal() as session:
        session.add(Order(title=data["title"], description=msg.text))
        await session.commit()
    await msg.answer("Заказ опубликован!")
    await state.clear()

@router.message(F.from_user.id == config.ADMIN_ID, F.text.startswith("/confirm_"))
async def confirm_order(msg: Message):
    try:
        parts = msg.text.split("_")
        order_id = int(parts[1])
        amount = int(parts[2]) if len(parts) > 2 else 10
    except:
        await msg.answer("Неверный формат команды. Используйте: /confirm_<id>_<сумма>")
        return

    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if not order or not order.taken_by or order.completed:
            await msg.answer("Невозможно подтвердить заказ.")
            return

        user = await session.get(User, order.taken_by)
        user.balance += amount
        user.completed_orders += 1
        order.completed = True
        await session.commit()
        await msg.answer(f"Заказ подтверждён. Начислено {amount} монет.")
        await msg.bot.send_message(user.tg_id, f"✅ Ваш заказ подтверждён! Начислено {amount} монет.")

@router.message(F.from_user.id == config.ADMIN_ID, F.text == "/withdrawals")
async def list_withdrawals(msg: Message):
    async with SessionLocal() as session:
        requests = (await session.scalars(select(WithdrawalRequest).where(WithdrawalRequest.processed == False))).all()
        if not requests:
            await msg.answer("Нет необработанных заявок на вывод.")
        else:
            for req in requests:
                user = await session.get(User, req.user_id)
                text = f"Заявка #{req.id} от @{user.username}\nСумма: {req.amount} монет"
                await msg.answer(text, reply_markup=withdrawal_approve_kb(req.id))

@router.callback_query(F.data.startswith("approve_withdraw_"))
async def approve_withdrawal(callback: CallbackQuery):
    request_id = int(callback.data.split("_")[-1])
    async with SessionLocal() as session:
        request = await session.get(WithdrawalRequest, request_id)
        if not request or request.processed:
            await callback.answer("Заявка уже обработана или не найдена.", show_alert=True)
            return

        request.processed = True
        await session.commit()

        user = await session.get(User, request.user_id)
        await callback.message.edit_text(f"✅ Вывод подтверждён: @{user.username}, {request.amount} монет")
        await callback.bot.send_message(user.tg_id, f"✅ Администратор подтвердил ваш вывод: {request.amount} монет")

@router.message(F.from_user.id == config.ADMIN_ID, F.text.startswith("/delete_order_"))
async def delete_order_request(msg: Message):
    parts = msg.text.split("_")
    if len(parts) < 3:
        await msg.answer("❌ Неверный формат команды. Используйте /delete_order_<id>")
        return

    order_id_str = parts[-1]
    if not order_id_str.isdigit():
        await msg.answer("❌ ID заказа должен быть числом.")
        return

    order_id = int(order_id_str)

    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if not order:
            await msg.answer("❌ Заказ с таким ID не найден.")
            return
        if order.taken:
            await msg.answer("❌ Нельзя удалить заказ, который уже взят исполнителем.")
            return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить удаление", callback_data=f"confirm_delete_{order_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")]
        ])
    await msg.answer(f"Вы уверены, что хотите удалить заказ ID {order_id}?", reply_markup=kb)

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: types.CallbackQuery):
    await callback.message.edit_text("Удаление заказа отменено.")
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(callback: types.CallbackQuery):
    try:
        order_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Ошибка в данных.", show_alert=True)
        return

    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        if not order:
            await callback.message.edit_text("❌ Заказ уже удалён или не найден.")
            await callback.answer()
            return
        if order.taken:
            await callback.message.edit_text("❌ Нельзя удалить заказ, который уже взят исполнителем.")
            await callback.answer()
            return
        await session.delete(order)
        await session.commit()

    await callback.message.edit_text(f"✅ Заказ ID {order_id} успешно удалён.")
    await callback.answer("Заказ удалён.")