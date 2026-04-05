class Habit:
    def __init__(self, name):
        self.name = name


class Entry:
    def __init__(self, habit_name, date, value):
        self.habit_name = habit_name
        self.date = date
        self.value = value