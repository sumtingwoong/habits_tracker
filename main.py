from habits import add_habit, list_habits, mark_habit, stats

while True:
    cmd = input("\nEnter command: ")

    if cmd == "add":
        name = input("Enter name of habits: ")
        if name == '-1':
            continue
        add_habit(name)

    elif cmd == "list":
        list_habits()
    elif cmd == "mark":
        name = input("Habit: ")
        if name == '-1':
            continue
        mark_habit(name)
    elif cmd == "stats":
        stats()
    elif cmd == "exit":
        break
    else:
        print("Unknown command")
