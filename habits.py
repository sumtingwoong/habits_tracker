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


def stats(user_id: int):
    data = load_data(user_id)

    if not data["entries"]:
        print("No data yet")
        return

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
