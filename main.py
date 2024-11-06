import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramForbiddenError

import asyncio

API_TOKEN = 'YOUR_API_TOKEN_HERE'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

user_order = {}
user_order_confirmed = {}
user_order_number = {}
order_picked_up = {}

order_counter = 1

main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Переглянути меню", callback_data="menu")],
    [InlineKeyboardButton(text="Де ми знаходимося", callback_data="location")],
    [InlineKeyboardButton(text="Графік роботи", callback_data="hours")],
])

menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Еспресо - 45 грн", callback_data="order_espresso")],
    [InlineKeyboardButton(text="Капучіно - 55 грн", callback_data="order_cappuccino")],
    [InlineKeyboardButton(text="Лате - 60 грн", callback_data="order_latte")],
    [InlineKeyboardButton(text="Чай - 30 грн", callback_data="order_tea")],
    [InlineKeyboardButton(text="Амерекано - 40 грн", callback_data="order_americano")],
    [InlineKeyboardButton(text="Гарячий шоколад - 70 грн", callback_data="order_hotchocolate")],
    [InlineKeyboardButton(text="Шоколадний торт - 55 грн", callback_data="order_chocolatecake")],
    [InlineKeyboardButton(text="Еклер - 35 грн", callback_data="order_eclair")],
    [InlineKeyboardButton(text="Пончик - 40 грн", callback_data="order_donut")],
    [InlineKeyboardButton(text="Круасан - 35 грн", callback_data="order_croissant")],
    [InlineKeyboardButton(text="Чизкейк - 55 грн", callback_data="order_cheesecake")],
    [InlineKeyboardButton(text="Переглянути замовлення", callback_data="view_order")],
])


@router.message(Command("start"))
async def send_welcome(message: Message):
    try:
        await message.answer("Вітаємо в нашій кав'ярні! Оберіть дію:", reply_markup=main_keyboard)
    except TelegramForbiddenError:
        logging.warning(f"Бот був заблокований користувачем {message.from_user.id}")


@router.callback_query(lambda c: c.data == "menu")
async def show_menu(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Ось наше меню:", reply_markup=menu_keyboard)


@router.callback_query(lambda c: c.data == "location")
async def show_location(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Наша адреса: вул. Кавова, 12, Київ")


@router.callback_query(lambda c: c.data == "hours")
async def show_hours(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Графік роботи: Пн-Пт 8:00 - 22:00, Сб-Нд 9:00 - 23:00")


@router.callback_query(lambda c: c.data and c.data.startswith("order_"))
async def add_to_order(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_order_confirmed.get(user_id):
        await callback_query.answer("Ваше замовлення вже оформлено. Заберіть його перед тим, як додавати нові товари.")
        return

    item = callback_query.data.split("_")[1]
    item_name, item_price = {
        "espresso": ("Еспресо", 45),
        "cappuccino": ("Капучіно", 55),
        "latte": ("Лате", 60),
        "tea": ("Чай", 30),
        "americano": ("Амерекано", 40),
        "hotchocolate": ("Гарячий шоколад", 70),
        "chocolatecake": ("Шоколадний торт", 55),
        "eclair": ("Еклер", 35),
        "donut": ("Пончик", 40),
        "croissant": ("Круасан", 35),
        "cheesecake": ("Чизкейк", 55),
    }.get(item, ("Невідомий товар", 0))

    if user_id not in user_order:
        user_order[user_id] = []
    user_order[user_id].append((item_name, item_price))

    await callback_query.answer(f"{item_name} додано до вашого замовлення!")


@router.callback_query(lambda c: c.data == "view_order")
async def view_order(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    order_items = user_order.get(user_id, [])

    if not order_items:
        await callback_query.answer("Ваше замовлення порожнє.")
        return

    order_text = "Ваше поточне замовлення:\n" + "\n".join([f"{name} - {price} грн" for name, price in order_items])
    total_price = sum(price for _, price in order_items)
    order_text += f"\nЗагальна сума: {total_price} грн"

    order_management_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оформити замовлення", callback_data="checkout")],
        [InlineKeyboardButton(text="Скасувати замовлення", callback_data="clear_order")]
    ])

    await callback_query.message.answer(order_text, reply_markup=order_management_keyboard)


@router.callback_query(lambda c: c.data == "clear_order")
async def clear_order(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    # Очищаємо дані замовлення для користувача
    user_order.pop(user_id, None)
    user_order_confirmed.pop(user_id, None)
    user_order_number.pop(user_id, None)

    await callback_query.message.answer("Ваше замовлення скасовано. Ви можете створити нове замовлення.", reply_markup=menu_keyboard)


@router.callback_query(lambda c: c.data == "checkout")
async def checkout_order(callback_query: types.CallbackQuery):
    global order_counter
    user_id = callback_query.from_user.id
    order_items = user_order.get(user_id, [])

    if not order_items:
        await callback_query.answer("Ваше замовлення порожнє.")
        return

    order_number = order_counter
    user_order_number[user_id] = order_number
    order_counter += 1

    user_order_confirmed[user_id] = True

    payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатити онлайн", callback_data="pay_online")],
        [InlineKeyboardButton(text="Оплата при отриманні", callback_data="pay_on_pickup")]
    ])

    await callback_query.message.answer(
        f"Ваше замовлення №{order_number} оформлено!\nОберіть спосіб оплати:",
        reply_markup=payment_keyboard
    )


@router.callback_query(lambda c: c.data == "pay_online")
async def pay_online(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    order_number = user_order_number[user_id]

    await callback_query.message.answer(
        f"Для оплати онлайн використовуйте номер карти: 1234 5678 9012 3456.\n"
        f"Покажіть квитанцію та номер замовлення #{order_number} на касі для отримання замовлення."
    )

    await send_pickup_info(callback_query)

@router.callback_query(lambda c: c.data == "pay_on_pickup")
async def pay_on_pickup(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    order_number = user_order_number[user_id]

    await callback_query.message.answer(
        f"Для оплати при отриманні назвіть номер замовлення #{order_number} на касі та оплатіть будь-яким зручним способом."
    )

    await send_pickup_info(callback_query)

async def send_pickup_info(callback_query: types.CallbackQuery):
    # Змінено текст кнопки на "Підтвердити замовлення"
    pickup_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Підтвердити замовлення", callback_data="confirm_order")]
    ])
    pickup_info = (
        "Забрати замовлення можна за адресою: вул. Кавова, 12, Київ.\n"
        "Графік роботи: Пн-Пт 8:00 - 22:00, Сб-Нд 9:00 - 23:00.\n\n"
        "Якщо ви сплатили онлайн, покажіть квитанцію та номер замовлення на касі.\n"
        "При оплаті на місці назвіть номер замовлення та оплатіть будь-яким зручним способом."
    )
    await callback_query.message.answer(pickup_info, reply_markup=pickup_keyboard)

# Змінили callback data на "confirm_order" для обробки підтвердження замовлення
@router.callback_query(lambda c: c.data == "confirm_order")
async def confirm_order(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    order_picked_up[user_id] = True

    new_order_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Створити нове замовлення", callback_data="new_order")]
    ])
    await callback_query.message.answer("Ваше замовлення підтверджено! Дякуємо за замовлення.", reply_markup=new_order_keyboard)

@router.callback_query(lambda c: c.data == "new_order")
async def start_new_order(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_order[user_id] = []
    user_order_confirmed[user_id] = False

    await callback_query.message.answer("Ви можете розпочати нове замовлення:", reply_markup=menu_keyboard)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
