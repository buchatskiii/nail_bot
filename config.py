"""
Конфигурационный файл бота
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")

# ID администратора (владельца бота)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ID канала для расписания (куда отправляются уведомления о записях)
SCHEDULE_CHANNEL_ID = int(os.getenv("SCHEDULE_CHANNEL_ID", "0"))

# ID канала для проверки подписки
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))  # ID канала для проверки подписки
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/your_channel")  # Ссылка на канал

# Настройки расписания
DAYS_AHEAD = 30  # На сколько дней вперёд формировать расписание
WORK_START_HOUR = 9  # Начало рабочего дня (час)
WORK_END_HOUR = 18  # Конец рабочего дня (час)
SLOT_DURATION = 60  # Длительность одного слота в минутах

# Путь к базе данных
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "nail_bot.db")
