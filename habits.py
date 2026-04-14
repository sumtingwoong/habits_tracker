from storage import load_data, save_data
from datetime import date


def add_habit(user_id: int, name: str):
    data = load_data(user_id)
    data["habits"].append(name)
    save_data(user_id, data)
    print(f"Habit {name} added")


def delete_habit(user_id: int, name: str):
    data = load_data(user_id)
    if name in data["habits"]:
        data["habits"].remove(name)
        save_data(user_id, data)
        print(f"Habit {name} deleted")


def list_habits(user_id: int):
    data = load_data(user_id)
    for i in data["habits"]:
        print(f'- {i}')


def mark_habit(user_id: int, name: str):
    data = load_data(user_id)
    if name not in data["habits"]:
        print('Habit not found')
        return

    value = int(input("1 (yes) / 0 (no): "))

    entry = {
        "habit": name,
        "date": str(date.today()),
        "value": value
    }

    data["entries"].append(entry)
    save_data(user_id, data)
    print('Marked')


def format_date(date_str: str):
    """Convert YYYY-MM-DD to DD-MM-YYYY"""
    try:
        year, month, day = date_str.split('-')
        return f"{day}-{month}-{year}"
    except:
        return date_str


def get_stats_page(user_id: int, page: int = 0, items_per_page: int = 30) -> tuple[str, bool]:
    """
    Returns stats for a specific page and whether more pages exist.
    page: 0 for newest, 1 for next 30 days older, etc.
    """
    data = load_data(user_id)

    if not data["entries"]:
        return "📊 Нет данных для статистики.", False

    habits = sorted({e["habit"] for e in data["entries"]})
    dates = sorted({e["date"] for e in data["entries"]}, reverse=True)  # Newest first

    # Calculate pagination
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    has_more = len(dates) > end_idx

    paginated_dates = dates[start_idx:end_idx]

    lookup = {(e["date"], e["habit"]): e["value"] for e in data["entries"]}

    # Build compact output
    output = []
    for d in paginated_dates:
        formatted_date = format_date(d)
        output.append(f"\n📅 {formatted_date}")

        for habit in habits:
            val = lookup.get((d, habit), 0)
            emoji = "✅" if val == 1 else "❌"
            # Escape special characters for markdown
            habit_escaped = habit.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")
            output.append(f"  • {habit_escaped} {emoji}")

    result = "".join(output)
    return result, has_more


def stats(user_id: int):
    """CLI version - shows first page"""
    output, _ = get_stats_page(user_id, page=0)
    print(output)