"""
Скрипт для добавления тестовых данных в базу данных
"""
import sqlite3
import datetime
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DB_PATH

# Сначала инициализируем БД через модуль database
from database import db

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

today = datetime.date.today()

# Добавляем рабочие дни на ближайшие 7 дней
count_days = 0
count_slots = 0

for i in range(1, 8):
    date = today + datetime.timedelta(days=i)
    date_str = date.strftime('%Y-%m-%d')
    try:
        cursor.execute('INSERT INTO working_days (date) VALUES (?)', (date_str,))
        if cursor.rowcount > 0:
            count_days += 1
    except sqlite3.IntegrityError:
        pass
    
    # Добавляем слоты для каждого рабочего дня (с 10:00 до 18:00, каждый час)
    for hour in range(10, 19):
        time_str = f'{hour:02d}:00'
        try:
            cursor.execute('INSERT INTO time_slots (date, time) VALUES (?, ?)', (date_str, time_str))
            if cursor.rowcount > 0:
                count_slots += 1
        except sqlite3.IntegrityError:
            pass

conn.commit()
conn.close()
print(f'✅ Тестовые данные добавлены!')
print(f'📅 Добавлено {count_days} рабочих дней')
print(f'🕐 Добавлено {count_slots} слотов')
