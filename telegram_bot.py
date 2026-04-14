import asyncio
import os
import sys
from datetime import date
from io import StringIO

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

from habits import add_habit, delete_habit, stats
from storage import load_data, save_data

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_IDS_STR = os.getenv("USER_IDS")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")
if not USER_IDS_STR:
    raise RuntimeError("USER_IDS is not set. Copy .env.example to .env and fill it in.")

# Парсим список ID
ALLOWED_USER_IDS = [int(uid.strip()) for uid in USER_IDS_STR.split(",")]

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_user(user_id: int) -> bool:
    """Return True only for authorised users."""
    return user_id in ALLOWED_USER_IDS


def _escape_md(text: str) -> str:
    """Escape Markdown v1 special characters in text."""
    for char in ("_", "*", "`", "["):
        text = text.replace(char, f"\\{char}")
    return text


def _build_list_keyboard(habits: list[str]) -> InlineKeyboardMarkup:
    """Inline keyboard where each button deletes a habit on click."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🗑 {h}", callback_data=f"del_{h}")]
            for h in habits
        ]
    )


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

@dp.message(Command("start"))
async def start_handler(message: types.Message) -> None:
    if not _is_user(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/list"), KeyboardButton(text="/mark")],
            [KeyboardButton(text="/stats"), KeyboardButton(text="/add")],
        ],
        resize_keyboard=True,
    )
    await message.answer(
        "👋 Привет! Я трекер привычек.\n\n"
        "Доступные команды:\n"
        "➕ /add <название> — добавить привычку\n"
        "📋 /list — список привычек (с удалением)\n"
        "✅ /mark — отметить выполнение\n"
        "🗑 /delete <название> — удалить привычку\n"
        "📊 /stats — статистика",
        reply_markup=keyboard,
    )


# ---------------------------------------------------------------------------
# /add
# ---------------------------------------------------------------------------

@dp.message(Command("add"))
async def add_handler(message: types.Message) -> None:
    if not _is_user(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    user_id = message.from_user.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("❌ Использование: /add <название привычки>")
        return

    habit_name = parts[1].strip()
    data = load_data(user_id)

    if habit_name in data["habits"]:
        await message.answer(f"⚠️ Привычка «{habit_name}» уже существует!")
        return

    add_habit(user_id, habit_name)
    await message.answer(f"✅ Привычка «{habit_name}» добавлена!")


# ---------------------------------------------------------------------------
# /delete
# ---------------------------------------------------------------------------

@dp.message(Command("delete"))
async def delete_handler(message: types.Message) -> None:
    if not _is_user(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    user_id = message.from_user.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("❌ Использование: /delete <название привычки>")
        return

    habit_name = parts[1].strip()
    data = load_data(user_id)

    if habit_name not in data["habits"]:
        await message.answer(f"❌ Привычка «{habit_name}» не найдена!")
        return

    delete_habit(user_id, habit_name)
    await message.answer(f"🗑 Привычка «{habit_name}» удалена!")


# ---------------------------------------------------------------------------
# /list  +  inline delete callback
# ---------------------------------------------------------------------------

@dp.message(Command("list"))
async def list_handler(message: types.Message) -> None:
    if not _is_user(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    user_id = message.from_user.id
    data = load_data(user_id)
    habits = data["habits"]

    if not habits:
        await message.answer("📋 Список привычек пуст.")
        return

    text = "📋 *Список привычек* (нажми кнопку для удаления):\n" + "\n".join(
        f"• {_escape_md(h)}" for h in habits
    )
    await message.answer(text, reply_markup=_build_list_keyboard(habits), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("del_"))
async def delete_callback(callback: types.CallbackQuery) -> None:
    if not _is_user(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    user_id = callback.from_user.id
    habit_name = callback.data[4:]
    data = load_data(user_id)

    if habit_name not in data["habits"]:
        await callback.answer("❌ Привычка не найдена!")
        return

    delete_habit(user_id, habit_name)
    await callback.answer(f"🗑 «{habit_name}» удалена!")

    data = load_data(user_id)
    habits = data["habits"]
    if not habits:
        await callback.message.edit_text("📋 Список привычек пуст.")
    else:
        text = "📋 *Список привычек* (нажми кнопку для удаления):\n" + "\n".join(
            f"• {_escape_md(h)}" for h in habits
        )
        await callback.message.edit_text(
            text, reply_markup=_build_list_keyboard(habits), parse_mode="Markdown"
        )


# ---------------------------------------------------------------------------
# /mark  +  inline habit-select and yes/no callbacks
# ---------------------------------------------------------------------------

@dp.message(Command("mark"))
async def mark_handler(message: types.Message) -> None:
    if not _is_user(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    user_id = message.from_user.id
    data = load_data(user_id)
    habits = data["habits"]

    if not habits:
        await message.answer("❌ Нет привычек для отметки!")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=h, callback_data=f"mark_{h}")]
            for h in habits
        ]
    )
    await message.answer("✏️ Выбери привычку для отметки:", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("mark_"))
async def mark_select_callback(callback: types.CallbackQuery) -> None:
    if not _is_user(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    habit_name = callback.data[5:]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"yes_{habit_name}"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"no_{habit_name}"),
            ]
        ]
    )
    await callback.message.edit_text(
        f"Выполнил сегодня привычку *{_escape_md(habit_name)}*?",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@dp.callback_query(F.data.startswith("yes_") | F.data.startswith("no_"))
async def mark_confirm_callback(callback: types.CallbackQuery) -> None:
    if not _is_user(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    user_id = callback.from_user.id

    if callback.data.startswith("yes_"):
        habit_name = callback.data[4:]
        value = 1
    else:
        habit_name = callback.data[3:]
        value = 0

    data = load_data(user_id)
    today = str(date.today())
    # Update existing entry for today if present, otherwise append
    for entry in data["entries"]:
        if entry["habit"] == habit_name and entry["date"] == today:
            entry["value"] = value
            break
    else:
        data["entries"].append({"habit": habit_name, "date": today, "value": value})
    save_data(user_id, data)

    status = "выполнена ✅" if value == 1 else "не выполнена ❌"
    await callback.message.edit_text(
        f"Привычка *{_escape_md(habit_name)}* отмечена как {status}!", parse_mode="Markdown"
    )


# ---------------------------------------------------------------------------
# /stats
# ---------------------------------------------------------------------------

@dp.message(Command("stats"))
async def stats_handler(message: types.Message) -> None:
    if not _is_user(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    user_id = message.from_user.id
    data = load_data(user_id)
    if not data["entries"]:
        await message.answer("📊 Нет данных для статистики.")
        return

    # Capture the text table printed by stats()
    old_stdout = sys.stdout
    sys.stdout = buf = StringIO()
    try:
        stats(user_id)
    finally:
        sys.stdout = old_stdout

    output = buf.getvalue()
    await message.answer(f"📊 *Статистика:*\n```\n{output}```", parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())