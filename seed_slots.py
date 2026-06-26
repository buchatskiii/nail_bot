"""
Скрипт для массового добавления рабочих дней и слотов на 2 недели вперёд.
Слоты: с 9:00 до 18:00 каждые 2 часа (9, 11, 13, 15, 17)
"""
import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "nail_bot.db")



def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=14)

    times = ["09:00", "11:00", "13:00", "15:00", "17:00"]
    added_days = 0
    added_slots = 0

    current = today
    while current <= end_date:
        # Пропускаем воскресенье (6) и субботу (5) — выходные
        # Если нужны все дни недели, раскомментируй строку ниже
        # if current.weekday() >= 5:  # 5=суббота, 6=воскресенье
        #     current += datetime.timedelta(days=1)
        #     continue

        date_str = current.isoformat()

        # Добавляем рабочий день
        cursor.execute(
            "INSERT OR IGNORE INTO working_days (date) VALUES (?)",
            (date_str,)
        )
        if cursor.rowcount > 0:
            added_days += 1

        # Добавляем слоты
        for time_str in times:
            cursor.execute(
                "INSERT OR IGNORE INTO time_slots (date, time) VALUES (?, ?)",
                (date_str, time_str)
            )
            if cursor.rowcount > 0:
                added_slots += 1
            else:
                # Если слот уже есть, делаем его доступным
                cursor.execute(
                    "UPDATE time_slots SET is_available = 1 WHERE date = ? AND time = ?",
                    (date_str, time_str)
                )

        current += datetime.timedelta(days=1)

    conn.commit()
    conn.close()

    print(f"✅ Добавлено рабочих дней: {added_days}")
    print(f"✅ Добавлено/обновлено слотов: {added_slots}")
    print(f"📅 Период: {today} — {end_date}")
    print(f"🕐 Слоты: {', '.join(times)}")


if __name__ == "__main__":
    seed()
