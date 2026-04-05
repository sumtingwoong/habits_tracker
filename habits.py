from storage import load_data, save_data
from datetime import date


def add_habit(name):
    data = load_data()
    data["habits"].append(name)
    save_data(data)
    print(f"Habit {name} added")


def list_habits():
    data = load_data()
    for i in data["habits"]:
        print(f'- {i}')


def mark_habit(name):
    data = load_data()
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
    save_data(data)
    print('Marked')


# def stats():
#     data = load_data()
#
#     result = {}
#     for habit in data["habits"]:
#         result[habit] = 0
#
#     for e in data["entries"]:
#         if e["value"] == 1:
#             result[e["habit"]] += 1
#
#     for h, count in result.items():
#         print(f"{h}: {count} days")

def stats():
    data = load_data()

    habits = sorted({e["habit"] for e in data["entries"]})
    dates = sorted({e["date"] for e in data["entries"]})

    lookup = {(e["date"], e["habit"]): e["value"] for e in data["entries"]}

    table = []

    header = ["date"] + habits
    table.append(header)

    for date in dates:
        row = [date]
        for habit in habits:
            val = lookup.get((date, habit), 0)
            row.append("✔" if val == 1 else "✖")
        table.append(row)

    col_widths = [max(len(str(row[i])) for row in table) for i in range(len(header))]

    def format_row(row):
        return "| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"

    print(format_row(header))
    print("|-" + "-|-".join("-" * w for w in col_widths) + "-|")

    for row in table[1:]:
        print(format_row(row))
