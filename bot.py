"""
Главный файл бота для записи к мастеру маникюра
Запуск и настройка бота
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from config import BOT_TOKEN
from handlers.user import router as user_router
from handlers.admin import router as admin_router
from utils.reminder import start_scheduler, restore_reminders

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    """Устанавливает команды бота в меню Telegram"""
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("Команды бота установлены")


async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")

    # Проверяем наличие токена
    if not BOT_TOKEN or BOT_TOKEN == "ВАШ_ТОКЕН_БОТА":
        logger.error(
            "Токен бота не указан! "
            "Создайте файл .env и укажите BOT_TOKEN"
        )
        return

    # Создаём экземпляры бота и диспетчера
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем роутеры
    dp.include_router(user_router)
    dp.include_router(admin_router)

    # Устанавливаем команды бота (чтобы /start всегда была в меню)
    await set_bot_commands(bot)

    # Запускаем планировщик напоминаний
    start_scheduler()

    # Восстанавливаем задачи напоминаний из БД
    await restore_reminders(bot)

    # Пропускаем накопившиеся обновления и запускаем бота
    logger.info("Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
