import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
from config import TELEGRAM_BOT_TOKEN
from database import init_db, add_event, get_user_events, delete_event, get_event
from calendar_export import generate_ics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


class EventState(StatesGroup):
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_description = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для планирования событий.\n\n"
        "📅 Доступные команды:\n"
        "/plan - создать новое событие\n"
        "/my_events - просмотреть мои события\n"
        "/delete - удалить событие\n"
        "/help - справка"
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 **Справка**\n\n"
        "Я помогу вам запланировать событие и отправить файл для импорта в календарь.\n\n"
        "**Как создать событие:**\n"
        "1. Отправьте команду /plan\n"
        "2. Введите название события\n"
        "3. Введите дату (ГГГГ-ММ-ДД)\n"
        "4. Введите время (ЧЧ:ММ)\n"
        "5. Введите описание (или нажмите 'Пропустить')\n\n"
        "После создания вы получите .ics файл для импорта в Google Calendar или Apple Calendar."
    )


@dp.message(Command("plan"))
async def cmd_plan(message: types.Message, state: FSMContext):
    await message.answer("📝 Введите **название события**:")
    await state.set_state(EventState.waiting_for_title)


@dp.message(EventState.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "📅 Введите **дату события** в формате ГГГГ-ММ-ДД (например, 2026-05-15):"
    )
    await state.set_state(EventState.waiting_for_date)


@dp.message(EventState.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%Y-%m-%d")
        await state.update_data(date=message.text)
        await message.answer(
            "🕐 Введите **время события** в формате ЧЧ:ММ (например, 14:30):"
        )
        await state.set_state(EventState.waiting_for_time)
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Пожалуйста, используйте формат ГГГГ-ММ-ДД:"
        )


@dp.message(EventState.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%H:%M")
        await state.update_data(time=message.text)
        await message.answer(
            "📝 Введите **описание события** (или отправьте 'Пропустить', чтобы оставить пустым):"
        )
        await state.set_state(EventState.waiting_for_description)
    except ValueError:
        await message.answer(
            "❌ Неверный формат времени. Пожалуйста, используйте формат ЧЧ:ММ:"
        )


@dp.message(EventState.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    description = None
    if message.text.lower() != "пропустить":
        description = message.text

    user_data = await state.get_data()
    user_id = message.from_user.id

    event_id = await add_event(
        user_id=user_id,
        title=user_data["title"],
        description=description,
        event_date=user_data["date"],
        event_time=user_data["time"]
    )

    # Генерируем .ics файл
    ics_content = generate_ics(
        title=user_data["title"],
        event_date=user_data["date"],
        event_time=user_data["time"],
        description=description
    )

    # Сохраняем файл временно
    filename = f"event_{event_id}.ics"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(ics_content)

    # Отправляем файл
    input_file = FSInputFile(filename)
    await message.answer_document(
        document=input_file,
        caption=(
            f"✅ Событие создано!\n\n"
            f"📌 **{user_data['title']}**\n"
            f"📅 {user_data['date']} в {user_data['time']}\n\n"
            "📎 Скачайте файл выше и откройте его для добавления в календарь."
        )
    )

    await state.clear()


@dp.message(Command("my_events"))
async def cmd_my_events(message: types.Message):
    user_id = message.from_user.id
    events = await get_user_events(user_id)

    if not events:
        await message.answer("📭 У вас пока нет запланированных событий.")
        return

    text = "📅 **Ваши события:**\n\n"
    for event in events:
        text += (
            f"**#{event['id']} {event['title']}**\n"
            f"📅 {event['event_date']} в {event['event_time']}\n"
        )
        if event['description']:
            text += f"📝 {event['description']}\n"
        text += "\n"

    await message.answer(text)


@dp.message(Command("delete"))
async def cmd_delete(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Укажите ID события для удаления.\n"
            "Пример: `/delete 5`\n\n"
            "Узнать ID можно через команду /my_events"
        )
        return

    try:
        event_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return

    user_id = message.from_user.id
    deleted = await delete_event(user_id, event_id)

    if deleted:
        await message.answer(f"✅ Событие #{event_id} удалено.")
    else:
        await message.answer(
            "❌ Событие не найдено или принадлежит другому пользователю."
        )


async def main():
    await init_db()
    logger.info("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
