"""
Модуль для проверки подписки пользователя на Telegram-канал
"""
from aiogram import Bot

from config import CHANNEL_ID


async def check_subscription(user_id: int, bot: Bot) -> bool:
    """
    Проверяет, подписан ли пользователь на канал.

    Args:
        user_id: ID пользователя Telegram
        bot: Экземпляр бота для выполнения запросов

    Returns:
        True, если пользователь подписан, иначе False
    """
    # Если CHANNEL_ID не указан, пропускаем проверку
    if CHANNEL_ID == 0:
        return True

    try:
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
