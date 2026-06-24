"""
Модуль для проверки подписки пользователя на Telegram-канал
"""
from aiogram import Bot
from aiogram.types import ChatMember

from config import CHANNEL_ID, BOT_TOKEN

# Создаём экземпляр бота для проверки подписки
_bot = None


async def get_bot() -> Bot:
    """Возвращает экземпляр бота"""
    global _bot
    if _bot is None:
        _bot = Bot(token=BOT_TOKEN)
    return _bot


async def check_subscription(user_id: int) -> bool:
    """
    Проверяет, подписан ли пользователь на канал.

    Args:
        user_id: ID пользователя Telegram

    Returns:
        True, если пользователь подписан, иначе False
    """
    # Если CHANNEL_ID не указан, пропускаем проверку
    if CHANNEL_ID == 0:
        return True

    try:
        bot = await get_bot()
        chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)

        # Проверяем статус участника
        # "member", "administrator" или "creator" считаются подпиской
        if chat_member.status in ("member", "administrator", "creator"):
            return True

        return False
    except Exception as e:
        # Если произошла ошибка (например, бот не в канале),
        # пропускаем проверку
        print(f"Ошибка проверки подписки: {e}")
        return False
