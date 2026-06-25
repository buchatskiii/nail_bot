"""
Модуль для работы с базой данных SQLite
"""
import sqlite3
import datetime
from typing import List, Optional, Tuple
from config import DB_PATH


class Database:
    """Класс для управления базой данных SQLite"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Создаёт и возвращает соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        """Инициализация таблиц базы данных"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Таблица рабочих дней
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS working_days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                is_closed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица временных слотов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                is_available INTEGER DEFAULT 1,
                UNIQUE(date, time)
            )
        """)

        # Таблица записей клиентов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date)
            )
        """)

        conn.commit()
        conn.close()

    # ==================== Рабочие дни ====================

    def add_working_day(self, date: str) -> bool:
        """
        Добавляет рабочий день.
        Возвращает True, если день успешно добавлен.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO working_days (date) VALUES (?)",
                (date,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def remove_working_day(self, date: str) -> bool:
        """Удаляет рабочий день"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM working_days WHERE date = ?", (date,))
        days_deleted = cursor.rowcount
        cursor.execute("DELETE FROM time_slots WHERE date = ?", (date,))
        conn.commit()
        conn.close()
        return days_deleted > 0

    def close_day(self, date: str) -> list:
        """
        Полностью закрывает день для записи.
        Возвращает список отменённых записей клиентов.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Получаем все записи на этот день до закрытия
            cursor.execute(
                "SELECT id, user_id, name, phone, time FROM appointments WHERE date = ?",
                (date,)
            )
            cancelled_appointments = [dict(row) for row in cursor.fetchall()]
            
            # Закрываем день
            cursor.execute(
                "UPDATE working_days SET is_closed = 1 WHERE date = ?",
                (date,)
            )
            # Делаем все слоты этого дня недоступными
            cursor.execute(
                "UPDATE time_slots SET is_available = 0 WHERE date = ?",
                (date,)
            )
            
            # Удаляем все записи на этот день
            for app in cancelled_appointments:
                cursor.execute("DELETE FROM appointments WHERE id = ?", (app["id"],))
            
            conn.commit()
            return cancelled_appointments
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при закрытии дня {date}: {e}")
            return []
        finally:
            conn.close()

    def open_day(self, date: str) -> bool:
        """Открывает день для записи"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE working_days SET is_closed = 0 WHERE date = ?",
            (date,)
        )
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected

    def is_day_closed(self, date: str) -> bool:
        """Проверяет, закрыт ли день"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT is_closed FROM working_days WHERE date = ?",
            (date,)
        )
        row = cursor.fetchone()
        conn.close()
        return row and row["is_closed"] == 1

    def get_working_days(self, start_date: str, end_date: str) -> List[str]:
        """Возвращает список рабочих дней в диапазоне дат"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT date FROM working_days WHERE date BETWEEN ? AND ? AND is_closed = 0 ORDER BY date",
            (start_date, end_date)
        )
        days = [row["date"] for row in cursor.fetchall()]
        conn.close()
        return days

    # ==================== Временные слоты ====================

    def add_time_slot(self, date: str, time: str) -> bool:
        """Добавляет временной слот для указанной даты"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO time_slots (date, time) VALUES (?, ?)",
                (date, time)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def remove_time_slot(self, date: str, time: str) -> bool:
        """Удаляет временной слот"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM time_slots WHERE date = ? AND time = ?",
            (date, time)
        )
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected

    def get_available_slots(self, date: str) -> List[str]:
        """Возвращает список доступных временных слотов для указанной даты"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT time FROM time_slots WHERE date = ? AND is_available = 1 ORDER BY time",
            (date,)
        )
        slots = [row["time"] for row in cursor.fetchall()]
        conn.close()
        return slots

    def get_all_slots(self, date: str) -> List[dict]:
        """Возвращает все слоты для даты с их статусом"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT time, is_available FROM time_slots WHERE date = ? ORDER BY time",
            (date,)
        )
        slots = [{"time": row["time"], "is_available": row["is_available"]} for row in cursor.fetchall()]
        conn.close()
        return slots

    def is_slot_available(self, date: str, time: str) -> bool:
        """Проверяет, доступен ли слот"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT is_available FROM time_slots WHERE date = ? AND time = ?",
            (date, time)
        )
        row = cursor.fetchone()
        conn.close()
        return row and row["is_available"] == 1

    def book_slot(self, date: str, time: str) -> bool:
        """Бронирует слот (делает недоступным)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE time_slots SET is_available = 0 WHERE date = ? AND time = ? AND is_available = 1",
            (date, time)
        )
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected

    def release_slot(self, date: str, time: str) -> bool:
        """Освобождает слот (делает доступным)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE time_slots SET is_available = 1 WHERE date = ? AND time = ?",
            (date, time)
        )
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected

    # ==================== Записи клиентов ====================

    def create_appointment(self, user_id: int, username: str, name: str,
                           phone: str, date: str, time: str) -> bool:
        """
        Создаёт запись клиента.
        Возвращает True, если запись успешно создана.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO appointments (user_id, username, name, phone, date, time)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, username, name, phone, date, time)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def cancel_appointment(self, appointment_id: int) -> bool:
        """Отменяет запись по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT date, time FROM appointments WHERE id = ?",
            (appointment_id,)
        )
        row = cursor.fetchone()
        if row:
            # Освобождаем слот
            self.release_slot(row["date"], row["time"])
            # Удаляем запись
            cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False

    def cancel_appointment_by_user(self, user_id: int, date: str, time: str) -> bool:
        """Отменяет запись пользователя по дате и времени"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM appointments WHERE user_id = ? AND date = ? AND time = ?",
            (user_id, date, time)
        )
        row = cursor.fetchone()
        if row:
            appointment_id = row["id"]
            conn.close()
            return self.cancel_appointment(appointment_id)
        conn.close()
        return False

    def get_user_appointments(self, user_id: int) -> List[dict]:
        """Возвращает все записи пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, date, time, name, phone, created_at
               FROM appointments WHERE user_id = ? ORDER BY date, time""",
            (user_id,)
        )
        appointments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return appointments

    def get_user_appointment(self, user_id: int) -> Optional[dict]:
        """Возвращает ближайшую запись пользователя (если есть)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        today = datetime.date.today().isoformat()
        cursor.execute(
            """SELECT id, date, time, name, phone, created_at
               FROM appointments
               WHERE user_id = ? AND date >= ?
               ORDER BY date, time LIMIT 1""",
            (user_id, today)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_appointment_by_id(self, appointment_id: int) -> Optional[dict]:
        """Возвращает запись по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, username, name, phone, date, time, created_at FROM appointments WHERE id = ?",
            (appointment_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_appointments(self, date: str = None) -> List[dict]:
        """Возвращает все записи, опционально фильтруя по дате"""
        conn = self._get_connection()
        cursor = conn.cursor()
        if date:
            cursor.execute(
                "SELECT id, user_id, username, name, phone, date, time, created_at FROM appointments WHERE date = ? ORDER BY time",
                (date,)
            )
        else:
            cursor.execute(
                "SELECT id, user_id, username, name, phone, date, time, created_at FROM appointments ORDER BY date, time"
            )
        appointments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return appointments

    def get_upcoming_appointments(self) -> List[dict]:
        """Возвращает все будущие записи"""
        conn = self._get_connection()
        cursor = conn.cursor()
        today = datetime.date.today().isoformat()
        cursor.execute(
            """SELECT id, user_id, username, name, phone, date, time, created_at
               FROM appointments WHERE date >= ? ORDER BY date, time""",
            (today,)
        )
        appointments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return appointments

    def get_all_appointments_with_stats(self) -> dict:
        """
        Возвращает все записи и статистику.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Все записи
        cursor.execute(
            "SELECT id, user_id, username, name, phone, date, time, created_at FROM appointments ORDER BY date DESC, time DESC"
        )
        all_appointments = [dict(row) for row in cursor.fetchall()]
        
        # Статистика
        cursor.execute("SELECT COUNT(*) as cnt FROM appointments")
        total = cursor.fetchone()["cnt"]
        
        today = datetime.date.today().isoformat()
        cursor.execute("SELECT COUNT(*) as cnt FROM appointments WHERE date >= ?", (today,))
        upcoming = cursor.fetchone()["cnt"]
        
        cursor.execute("SELECT COUNT(*) as cnt FROM appointments WHERE date < ?", (today,))
        past = cursor.fetchone()["cnt"]
        
        conn.close()
        
        return {
            "total": total,
            "upcoming": upcoming,
            "past": past,
            "appointments": all_appointments
        }

    def has_user_appointment(self, user_id: int) -> bool:
        """Проверяет, есть ли у пользователя активная запись"""
        conn = self._get_connection()
        cursor = conn.cursor()
        today = datetime.date.today().isoformat()
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM appointments WHERE user_id = ? AND date >= ?",
            (user_id, today)
        )
        row = cursor.fetchone()
        conn.close()
        return row["cnt"] > 0

    def get_appointments_for_reminder(self) -> List[dict]:
        """
        Возвращает записи, для которых нужно отправить напоминание.
        Записи, у которых до даты и времени осталось ровно 24 часа.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.datetime.now()
        target_time = now + datetime.timedelta(hours=24)
        target_date = target_time.strftime("%Y-%m-%d")
        target_hour = target_time.hour
        target_minute = target_time.minute

        # Ищем записи на завтрашнюю дату, где время близко к текущему + 24 часа
        cursor.execute(
            """SELECT id, user_id, username, name, phone, date, time, created_at
               FROM appointments WHERE date = ?""",
            (target_date,)
        )
        appointments = []
        for row in cursor.fetchall():
            app_time = row["time"]
            try:
                app_hour, app_minute = map(int, app_time.split(":"))
                # Проверяем, что время записи в пределах часа от целевого времени
                time_diff = abs((app_hour * 60 + app_minute) - (target_hour * 60 + target_minute))
                if time_diff <= 30:  # В пределах 30 минут
                    appointments.append(dict(row))
            except (ValueError, IndexError):
                continue

        conn.close()
        return appointments
