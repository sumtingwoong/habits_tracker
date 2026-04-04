# 📊 Habit Tracker

A simple and extensible habit tracker written in Python.
It starts as a CLI application and will evolve into a Telegram bot.

Простой и расширяемый трекер привычек на Python.  
Начинается как CLI-приложение и будет развиваться в Telegram-бота.

---

## 🚀 Features (CLI version) | Возможности (CLI версия)

- ➕ Add habits | Добавление привычек  
- 📋 View habits list | Просмотр списка привычек  
- ✅ Mark as completed (1 / 0) | Отметка выполнения (1 / 0)  
- 📈  Basic statistics |Базовая статистика  
- 💾 Save data as JSON | Сохранение данных в JSON  

---

## 🧱 Architecture | Архитектура
habit_tracker/
│
├── main.py # CLI interface | CLI интерфейс
├── habits.py # program logic | логика
├── storage.py # JSON
├── models.py # data structures | структуры данных
└── data.json # data base | база данных

### Principles | Принципы:
- Separation of logic and interface | Разделение логики и интерфейса  
- Reusable business logic | Переиспользуемая бизнес-логика  
- A simple interface replacement | Простая замена интерфейса (CLI → Telegram)  

---

##  Available commands | Доступные команды:

- add     # add habit | добавить привычку
- list    # list of habbits | список привычек
- mark    # mark as done | отметить выполнение
- stats   # statistic | статистика
- exit    # exit | выход

## Tools | Технологии:
- Python 3
- JSON (as data base | в качестве хранилища)