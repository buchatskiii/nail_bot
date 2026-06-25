"""
Модуль с inline-клавиатурами для бота
"""
import calendar
import datetime
from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CHANNEL_LINK


def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню бота"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 Записаться", callback_data="book_appointment")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Мои записи", callback_data="my_appointments")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Прайсы", callback_data="prices")
    )
    builder.row(
        InlineKeyboardButton(text="📷 Портфолио", callback_data="portfolio")
    )

    if is_admin:
        builder.row(
            InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel")
        )

    return builder.as_markup()


def get_calendar_keyboard(year: int, month: int, working_days: List[str]) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру-календарь на указанный месяц.
    working_days — список дат (YYYY-MM-DD), которые являются рабочими.
    """
    builder = InlineKeyboardBuilder()

    # Заголовок с месяцем и годом
    month_name = calendar.month_name[month]
    builder.row(
        InlineKeyboardButton(
            text=f"{month_name} {year}",
            callback_data="ignore"
        )
    )

    # Дни недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    builder.row(*[InlineKeyboardButton(text=d, callback_data="ignore") for d in week_days])

    # Календарная сетка
    cal = calendar.monthcalendar(year, month)
    today = datetime.date.today()

    for week in cal:
        row_buttons = []
        for day in week:
            if day == 0:
                row_buttons.append(
                    InlineKeyboardButton(text=" ", callback_data="ignore")
                )
            else:
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                is_working = date_str in working_days
                is_past = datetime.date(year, month, day) < today

                if is_working and not is_past:
                    row_buttons.append(
                        InlineKeyboardButton(
                            text=f"✅ {day}",
                            callback_data=f"date_{date_str}"
                        )
                    )
                elif is_past:
                    row_buttons.append(
                        InlineKeyboardButton(
                            text=f"❌ {day}",
                            callback_data="ignore"
                        )
                    )
                else:
                    row_buttons.append(
                        InlineKeyboardButton(
                            text=f"{day}",
                            callback_data="ignore"
                        )
                    )
        builder.row(*row_buttons)

    # Навигация по месяцам
    nav_buttons = []
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1

    nav_buttons.append(
        InlineKeyboardButton(text="◀️", callback_data=f"cal_{prev_year}_{prev_month}")
    )
    nav_buttons.append(
        InlineKeyboardButton(text="Сегодня", callback_data="cal_today")
    )
    nav_buttons.append(
        InlineKeyboardButton(text="▶️", callback_data=f"cal_{next_year}_{next_month}")
    )
    builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_time_slots_keyboard(slots: List[str], date: str) -> InlineKeyboardMarkup:
    """Клавиатура с доступными временными слотами"""
    builder = InlineKeyboardBuilder()

    # Форматируем дату для отображения
    date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
    date_formatted = date_obj.strftime("%d.%m.%Y")
    day_name = get_weekday_name(date_obj.weekday())

    builder.row(
        InlineKeyboardButton(
            text=f"📅 {day_name}, {date_formatted}",
            callback_data="ignore"
        )
    )

    # Слоты по 2 в ряд
    for i in range(0, len(slots), 2):
        row = []
        row.append(
            InlineKeyboardButton(
                text=f"🕐 {slots[i]}",
                callback_data=f"slot_{date}_{slots[i]}"
            )
        )
        if i + 1 < len(slots):
            row.append(
                InlineKeyboardButton(
                    text=f"🕐 {slots[i + 1]}",
                    callback_data=f"slot_{date}_{slots[i + 1]}"
                )
            )
        builder.row(*row)

    builder.row(
        InlineKeyboardButton(text="🔙 Назад к календарю", callback_data="back_to_calendar")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_confirmation_keyboard(date: str, time: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения записи"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{date}_{time}"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_booking")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_subscription_check_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для проверки подписки на канал"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)
    )
    builder.row(
        InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_my_appointments_keyboard(appointments: List[dict]) -> InlineKeyboardMarkup:
    """Клавиатура со списком записей пользователя для отмены"""
    builder = InlineKeyboardBuilder()

    for app in appointments:
        date_obj = datetime.datetime.strptime(app["date"], "%Y-%m-%d")
        date_formatted = date_obj.strftime("%d.%m.%Y")
        builder.row(
            InlineKeyboardButton(
                text=f"❌ {date_formatted} в {app['time']}",
                callback_data=f"cancel_user_{app['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 Добавить рабочий день", callback_data="admin_add_day")
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить рабочий день", callback_data="admin_remove_day")
    )
    builder.row(
        InlineKeyboardButton(text="🕐 Добавить слот", callback_data="admin_add_slot")
    )
    builder.row(
        InlineKeyboardButton(text="🗑️ Удалить слот", callback_data="admin_remove_slot")
    )
    builder.row(
        InlineKeyboardButton(text="🚫 Закрыть день", callback_data="admin_close_day")
    )
    builder.row(
        InlineKeyboardButton(text="✅ Открыть день", callback_data="admin_open_day")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Просмотр расписания", callback_data="admin_view_schedule")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отменить запись клиента", callback_data="admin_cancel_appointment")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Все записи", callback_data="admin_all_appointments")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )

    return builder.as_markup()


def get_admin_dates_keyboard(dates: List[str], action: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора даты в админ-панели"""
    builder = InlineKeyboardBuilder()

    for date_str in dates:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        date_formatted = date_obj.strftime("%d.%m.%Y")
        day_name = get_weekday_name(date_obj.weekday())
        builder.row(
            InlineKeyboardButton(
                text=f"{day_name}, {date_formatted}",
                callback_data=f"{action}_{date_str}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    )

    return builder.as_markup()


def get_admin_slots_keyboard(slots: List[dict], date: str, action: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора слота в админ-панели"""
    builder = InlineKeyboardBuilder()

    for slot in slots:
        status = "✅" if slot["is_available"] else "❌"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {slot['time']}",
                callback_data=f"{action}_{date}_{slot['time']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    )

    return builder.as_markup()


def get_admin_appointments_keyboard(appointments: List[dict]) -> InlineKeyboardMarkup:
    """Клавиатура для отмены записи клиента админом"""
    builder = InlineKeyboardBuilder()

    for app in appointments:
        date_obj = datetime.datetime.strptime(app["date"], "%Y-%m-%d")
        date_formatted = date_obj.strftime("%d.%m.%Y")
        text = f"❌ {app['name']} - {date_formatted} {app['time']}"
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"admin_cancel_app_{app['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")
    )

    return builder.as_markup()


def get_back_keyboard(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    """Простая клавиатура с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)
    )
    return builder.as_markup()


def get_back_with_home_keyboard(back_callback: str = "back_to_menu") -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад и кнопкой главного меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_portfolio_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для портфолио"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📷 Смотреть портфолио", url="https://ru.pinterest.com/crystalwithluv/_created/")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_weekday_name(weekday: int) -> str:
    """Возвращает название дня недели на русском"""
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    return days[weekday]
