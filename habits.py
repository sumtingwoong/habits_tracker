from __future__ import annotations

from collections import defaultdict
from datetime import datetime, date as date_type
from typing import Dict, List, Tuple

from storage import load_data, save_data


# ---------------------------------------------------------------------------
# Existing CLI functions (kept for compatibility)
# ---------------------------------------------------------------------------

def add_habit(name: str) -> None:
    data = load_data()
    data["habits"].append(name)
    save_data(data)
    print(f"Habit {name} added")


def list_habits() -> None:
    data = load_data()
    for i in data["habits"]:
        print(f"- {i}")


def mark_habit(name: str) -> None:
    data = load_data()
    if name not in data["habits"]:
        print("Habit not found")
        return

    value = int(input("1 (yes) / 0 (no): "))

    entry = {
        "habit": name,
        "date": str(date_type.today()),
        "value": value,
    }

    data["entries"].append(entry)
    save_data(data)
    print("Marked")


def stats() -> None:
    """Old table output for CLI (unchanged)."""
    data = load_data()

    habits = sorted({e["habit"] for e in data["entries"]})
    dates = sorted({e["date"] for e in data["entries"]})

    lookup = {(e["date"], e["habit"]): e["value"] for e in data["entries"]}

    table = []

    header = ["date"] + habits
    table.append(header)

    for d in dates:
        row = [d]
        for habit in habits:
            val = lookup.get((d, habit), 0)
            row.append("✔" if val == 1 else "✖")
        table.append(row)

    col_widths = [max(len(str(row[i])) for row in table) for i in range(len(header))]

    def format_row(row):
        return "| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"

    print(format_row(header))
    print("|-" + "-|-".join("-" * w for w in col_widths) + "-|")

    for row in table[1:]:
        print(format_row(row))


# ---------------------------------------------------------------------------
# Bot-friendly stats (day + month)
# ---------------------------------------------------------------------------

def _parse_yyyy_mm_dd(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def _fmt_dd_mm_yyyy(s: str) -> str:
    try:
        return _parse_yyyy_mm_dd(s).strftime("%d-%m-%Y")
    except Exception:
        return s


def _fmt_month_ru(dt: datetime) -> str:
    months = [
        "январь", "февраль", "март", "апрель", "май", "июнь",
        "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
    ]
    return f"{months[dt.month - 1]} {dt.year}"


def get_stats_day_text(day: str, habits: List[str], lookup: Dict[Tuple[str, str], int]) -> str:
    lines = [f"📅 {_fmt_dd_mm_yyyy(day)}"]
    for h in habits:
        val = lookup.get((day, h), 0)
        emoji = "✅" if val == 1 else "❌"
        lines.append(f"{emoji} {h}")
    return "\n".join(lines)


def get_day_stats(user_id: int, day_index: int = 0) -> Tuple[str, int]:
    """
    Returns (text_for_one_day, total_days).
    day_index=0 => newest day.
    """
    data = load_data(user_id)
    entries = data.get("entries", [])
    if not entries:
        return "📊 Нет данных для статистики.", 0

    all_days = sorted({e["date"] for e in entries}, reverse=True)
    total_days = len(all_days)

    if day_index < 0:
        day_index = 0
    if day_index >= total_days:
        day_index = total_days - 1

    day = all_days[day_index]

    habits = sorted({e["habit"] for e in entries})
    lookup = {(e["date"], e["habit"]): e["value"] for e in entries}

    return get_stats_day_text(day, habits, lookup), total_days


def get_month_stats(user_id: int, month_index: int = 0) -> Tuple[str, int]:
    """
    Returns (text_for_one_month, total_months).
    month_index=0 => newest month by entries.
    Output: aggregated counts per habit: ✅ done / total-days-with-any-entry-in-month
    """
    data = load_data(user_id)
    entries = data.get("entries", [])
    if not entries:
        return "📅 Статистика за месяц недоступна (нет данных).", 0

    # Determine months available (YYYY-MM) sorted newest first
    months = sorted({e["date"][:7] for e in entries}, reverse=True)
    total_months = len(months)

    if month_index < 0:
        month_index = 0
    if month_index >= total_months:
        month_index = total_months - 1

    ym = months[month_index]

    # All days within that month that have any entry
    days_in_month = sorted({e["date"] for e in entries if e["date"].startswith(ym)})
    total_days = len(days_in_month)

    habits = sorted({e["habit"] for e in entries})
    lookup = {(e["date"], e["habit"]): e["value"] for e in entries}

    # Count done per habit across days (value==1)
    done_counts = {h: 0 for h in habits}
    for d in days_in_month:
        for h in habits:
            if lookup.get((d, h), 0) == 1:
                done_counts[h] += 1

    # Month title
    try:
        dt_month = datetime.strptime(ym + "-01", "%Y-%m-%d")
        month_title = _fmt_month_ru(dt_month)
    except Exception:
        month_title = ym

    lines = [f"🗓 Месяц: {month_title}", f"Дней с отметками: {total_days}"]
    lines.append("")
    for h in habits:
        done = done_counts[h]
        # Visual quick signal: if done == total_days then ✅ else ❌
        status = "✅" if total_days > 0 and done == total_days else "❌"
        lines.append(f"{status} {h}: {done}/{total_days}")

    return "\n".join(lines), total_months