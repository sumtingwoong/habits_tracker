import asyncio
import os
from datetime import date

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

from habits import add_habit, get_day_stats, get_month_stats
from storage import load_data, save_data

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_IDS_STR = os.getenv("USER_IDS")  # comma-separated list

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")
if not USER_IDS_STR:
    raise RuntimeError("USER_IDS is not set. Copy .env.example to .env and fill it in.")

ALLOWED_USER_IDS = {int(x.strip()) for x in USER_IDS_STR.split(",") if x.strip()}

bot = Bot(token=TOKEN)
dp = Dispatcher()

# per-user navigation state
user_day_index: dict[int, int] = {}
user_month_index: dict[int, int] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_user(user_id: int) -> bool:
    return user_id in ALLOWED_USER_IDS


def _escape_md(text: str) -> str:
    for char in ("_", "*", "`", "["):
        text = text.replace(char, f"\\{char}")
    return text


def _build_list_keyboard(habits: list[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🗑 {h}", callback_data=f"del_{h}")]
            for h in habits
        ]
    )


def _stats_keyboard(day_index: int, total_days: int, month_index: int, total_months: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    nav_row: list[InlineKeyboardButton] = []
    if total_days > 0 and day_index < total_days - 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Предыдущий день", callback_data="stats:day:older"))
    if total_days > 0 and day_index > 0:
        nav_row.append(InlineKeyboardButton(text="➡️ Следующий день", callback_data="stats:day:newer"))
    if nav_row:
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(text=f"День {day_index + 1}/{max(total_days, 1)}", callback_data="stats:noop")])

    month_nav_row: list[InlineKeyboardButton] = []
    if total_months > 0 and month_index < total_months - 1:
        month_nav_row.append(InlineKeyboardButton(text="⬅️ Предыдущий месяц", callback_data="stats:month:older"))
    if total_months > 0 and month_index > 0:
        month_nav_row.append(InlineKeyboardButton(text="➡️ Следующий месяц", callback_data="stats:month:newer"))
    if month_nav_row:
        rows.append(month_nav_row)

    rows.append([InlineKeyboardButton(text=f"Месяц {month_index + 1}/{max(total_months, 1)}", callback_data="stats:noop")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _render_stats(message: types.Message, user_id: int, edit: bool) -> None:
    d_idx = user_day_index.get(user_id, 0)
    m_idx = user_month_index.get(user_id, 0)

    day_text, total_days = get_day_stats(user_id, d_idx)
    month_text, total_months = get_month_stats(user_id, m_idx)

    kb = _stats_keyboard(d_idx, total_days, m_idx, total_months)

    text = (
        "📊 Статистика\n\n"
        f"{day_text}\n\n"
        f"{month_text}"
    )

    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


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
        "📊 /stats — статистика (день + месяц)",
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

    # Persist
    data["habits"].append(habit_name)
    save_data(user_id, data)
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

    data["habits"].remove(habit_name)
    save_data(user_id, data)
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

    data["habits"].remove(habit_name)
    save_data(user_id, data)
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
# /stats (day + month)
# ---------------------------------------------------------------------------

@dp.message(Command("stats"))
async def stats_handler(message: types.Message) -> None:
    if not _is_user(message.from_user.id):
        await message.answer("❌ Доступ запрещён")
        return

    user_id = message.from_user.id
    user_day_index[user_id] = 0
    user_month_index[user_id] = 0
    await _render_stats(message, user_id, edit=False)


@dp.callback_query(F.data.startswith("stats:"))
async def stats_callback(callback: types.CallbackQuery) -> None:
    if not _is_user(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    user_id = callback.from_user.id
    _, _, scope, direction = callback.data.split(":", 3)

    if scope == "day":
        if direction == "older":
            user_day_index[user_id] = user_day_index.get(user_id, 0) + 1
        elif direction == "newer":
            user_day_index[user_id] = max(user_day_index.get(user_id, 0) - 1, 0)
    elif scope == "month":
        if direction == "older":
            user_month_index[user_id] = user_month_index.get(user_id, 0) + 1
        elif direction == "newer":
            user_month_index[user_id] = max(user_month_index.get(user_id, 0) - 1, 0)

    # clamp to existing ranges by re-fetching totals
    # day
    _, total_days = get_day_stats(user_id, user_day_index.get(user_id, 0))
    if total_days > 0:
        user_day_index[user_id] = min(max(user_day_index.get(user_id, 0), 0), total_days - 1)
    else:
        user_day_index[user_id] = 0

    # month
    _, total_months = get_month_stats(user_id, user_month_index.get(user_id, 0))
    if total_months > 0:
        user_month_index[user_id] = min(max(user_month_index.get(user_id, 0), 0), total_months - 1)
    else:
        user_month_index[user_id] = 0

    await _render_stats(callback.message, user_id, edit=True)
    await callback.answer()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())