import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, GLPI_URL, APP_TOKEN, ADMIN_IDS
from glpi import init_session, create_ticket, get_my_tickets
from states import NewTicket
import db

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def start(message: Message):
    token = db.get_user_token(message.from_user.id)
    if not token:
        await message.answer(
            "Привет 👋\nПришли свой API токен из GLPI\n\n"
            "После этого будут доступны команды:\n"
            "/new — новая заявка\n"
            "/my — мои заявки\n"
            "/logout — выход"
        )
    else:
        await message.answer(
            "Ты уже авторизован ✅\n\n"
            "/new — новая заявка\n"
            "/my — мои заявки\n"
            "/logout — выход"
        )


@dp.message(Command("logout"))
async def logout(message: Message, state: FSMContext):
    db.set_user_token(message.from_user.id, None)
    await state.clear()
    await message.answer("🚪 Ты вышел из аккаунта GLPI")


@dp.message(Command("new"))
async def new_ticket(message: Message, state: FSMContext):
    token = db.get_user_token(message.from_user.id)
    if not token:
        await message.answer("❗ Сначала авторизуйся через /start")
        return

    await state.set_state(NewTicket.title)
    await message.answer("📝 Введи тему заявки")


@dp.message(NewTicket.title)
async def ticket_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(NewTicket.description)
    await message.answer("✏️ Опиши проблему")


@dp.message(NewTicket.description)
async def ticket_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    user_token = db.get_user_token(message.from_user.id)

    session_token = init_session(GLPI_URL, APP_TOKEN, user_token)
    if not session_token:
        await message.answer("❌ Ошибка авторизации в GLPI")
        await state.clear()
        return

    ticket_id = create_ticket(
        GLPI_URL,
        APP_TOKEN,
        session_token,
        data["title"],
        message.text
    )

    await state.clear()

    if not ticket_id:
        await message.answer("❌ Не удалось создать заявку")
        return

    ticket_url = f"{GLPI_URL}/front/ticket.form.php?id={ticket_id}"

    # ✅ Исправленные кнопки
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Открыть в GLPI", url=ticket_url)]
        ]
    )

    await message.answer(f"✅ Заявка создана!\nНомер: {ticket_id}", reply_markup=keyboard)

    # уведомление админам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🆕 Новая заявка\n№{ticket_id}\nОт: {message.from_user.full_name}\nТема: {data['title']}",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"⚠️ Не удалось уведомить администратора {admin_id}: {e}")


@dp.message(Command("my"))
async def my_tickets(message: Message):
    user_token = db.get_user_token(message.from_user.id)
    if not user_token:
        await message.answer("❗ Сначала авторизуйся через /start")
        return

    session_token = init_session(GLPI_URL, APP_TOKEN, user_token)
    if not session_token:
        await message.answer("❌ Ошибка авторизации")
        return

    tickets = get_my_tickets(GLPI_URL, APP_TOKEN, session_token)
    if not tickets:
        await message.answer("📭 У тебя пока нет заявок")
        return

    text = "📋 *Мои заявки:*\n\n"
    for t in tickets:
        text += f"№{t['id']} — {t['name']}\n"

    await message.answer(text, parse_mode="Markdown")


@dp.message(F.text)
async def get_token(message: Message):
    token = message.text.strip()
    if not init_session(GLPI_URL, APP_TOKEN, token):
        await message.answer("❌ Неверный токен или нет прав")
        return

    db.set_user_token(message.from_user.id, token)
    await message.answer(
        "✅ Токен принят!\n\n"
        "/new — новая заявка\n"
        "/my — мои заявки\n"
        "/logout — выход"
    )


async def main():
    print("🚀 Бот запущен и готов к работе")
    try:
        await dp.start_polling(bot)
    finally:
        print("🛑 Бот завершил работу")


if __name__ == "__main__":
    asyncio.run(main())
