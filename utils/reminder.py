"""
Модуль для управления автонапоминаниями о записи
Использует APScheduler (AsyncIOScheduler) для планирования задач
"""
import datetime
import uuid

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from database import db
from config import BOT_TOKEN

# Создаём планировщик
scheduler = AsyncIOScheduler(
    jobstores={
        "default": MemoryJobStore()
    }
)

# Словарь для хранения соответствия appointment_id -> job_id
# Нужен для удаления задач при отмене записи
_reminder_jobs: dict[int, str] = {}


async def schedule_reminder(bot: Bot, user_id: int, date: str, time: str, name: str):
    """
    Планирует отправку напоминания за 24 часа до записи.

    Args:
        bot: Экземпляр бота
        user_id: ID пользователя
        date: Дата записи (YYYY-MM-DD)
        time: Время записи (HH:MM)
        name: Имя клиента
    """
    try:
        # Парсим дату и время записи
        appointment_dt = datetime.datetime.strptime(
            f"{date} {time}", "%Y-%m-%d %H:%M"
        )
        now = datetime.datetime.now()

        # Вычисляем время отправки напоминания (за 24 часа до записи)
        reminder_time = appointment_dt - datetime.timedelta(hours=24)

        # Если до записи осталось меньше 24 часов, не создаём напоминание
        if reminder_time <= now:
            print(f"Напоминание не создано: до записи {date} {time} менее 24 часов")
            return

        # Получаем ID записи из БД
        appointment = db.get_user_appointment(user_id)
        if not appointment:
            print(f"Не найдена запись для пользователя {user_id}")
            return

        appointment_id = appointment["id"]

        # Создаём уникальный ID задачи
        job_id = f"reminder_{appointment_id}_{uuid.uuid4().hex[:8]}"

        # Планируем задачу
        scheduler.add_job(
            send_reminder,
            trigger="date",
            run_date=reminder_time,
            args=[bot, user_id, date, time, name],
            id=job_id,
            replace_existing=True,
        )

        # Сохраняем соответствие
        _reminder_jobs[appointment_id] = job_id

        print(f"Напоминание запланировано на {reminder_time} для записи {date} {time}")

    except Exception as e:
        print(f"Ошибка при планировании напоминания: {e}")


async def send_reminder(bot: Bot, user_id: int, date: str, time: str, name: str):
    """
    Отправляет напоминание пользователю.

    Args:
        bot: Экземпляр бота
        user_id: ID пользователя
        date: Дата записи
        time: Время записи
        name: Имя клиента
    """
    try:
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        date_formatted = date_obj.strftime("%d.%m.%Y")

        reminder_text = (
            "⏰ <b>Напоминаем о записи!</b>\n\n"
            f"👋 <b>{name}</b>, вы записаны на завтра в <b>{time}</b>.\n\n"
            "Ждём вас! 💅"
        )

        await bot.send_message(
            chat_id=user_id,
            text=reminder_text,
            parse_mode="HTML"
        )

        print(f"Напоминание отправлено пользователю {user_id}")

    except Exception as e:
        print(f"Ошибка при отправке напоминания: {e}")


def remove_reminder_job(appointment_id: int):
    """
    Удаляет задачу напоминания по ID записи.

    Args:
        appointment_id: ID записи в БД
    """
    job_id = _reminder_jobs.pop(appointment_id, None)
    if job_id:
        try:
            scheduler.remove_job(job_id)
            print(f"Задача напоминания {job_id} удалена")
        except Exception as e:
            print(f"Ошибка при удалении задачи напоминания: {e}")


async def restore_reminders(bot: Bot):
    """
    Восстанавливает задачи напоминаний из базы данных при перезапуске бота.
    Должна вызываться при старте бота.
    """
    print("Восстановление задач напоминаний...")
    appointments = db.get_upcoming_appointments()
    now = datetime.datetime.now()

    restored_count = 0
    for appointment in appointments:
        try:
            appointment_dt = datetime.datetime.strptime(
                f"{appointment['date']} {appointment['time']}", "%Y-%m-%d %H:%M"
            )
            reminder_time = appointment_dt - datetime.timedelta(hours=24)

            # Планируем только если время напоминания ещё не прошло
            if reminder_time > now:
                await schedule_reminder(
                    bot,
                    appointment["user_id"],
                    appointment["date"],
                    appointment["time"],
                    appointment["name"]
                )
                restored_count += 1
        except Exception as e:
            print(f"Ошибка восстановления напоминания: {e}")

    print(f"Восстановлено {restored_count} задач напоминаний")


def start_scheduler():
    """Запускает планировщик"""
    scheduler.start()
    print("Планировщик напоминаний запущен")
