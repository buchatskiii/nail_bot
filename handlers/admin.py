"""
Обработчики для админ-панели
"""
import datetime
import calendar

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards.inline import (
    get_admin_panel_keyboard,
    get_admin_dates_keyboard,
    get_admin_slots_keyboard,
    get_admin_appointments_keyboard,
    get_main_menu_keyboard,
    get_back_keyboard,
)
from config import ADMIN_ID

router = Router()


# ==================== Фильтр администратора ====================

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id == ADMIN_ID


# ==================== FSM Состояния для админ-панели ====================

class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_for_date_add = State()  # Ожидание ввода даты для добавления рабочего дня
    waiting_for_date_slot_add = State()  # Ожидание ввода даты для добавления слота
    waiting_for_time_slot_add = State()  # Ожидание ввода времени для добавления слота
    waiting_for_date_slot_remove = State()  # Ожидание ввода даты для удаления слота
    waiting_for_time_slot_remove = State()  # Ожидание ввода времени для удаления слота
    waiting_for_date_close = State()  # Ожидание ввода даты для закрытия дня
    waiting_for_date_view = State()  # Ожидание ввода даты для просмотра расписания


# ==================== Команда /admin ====================

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Открывает админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return

    await message.answer(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="HTML"
    )


# ==================== Открытие админ-панели ====================

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    """Открывает админ-панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Добавление рабочего дня ====================

@router.callback_query(F.data == "admin_add_day")
async def admin_add_day_start(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс добавления рабочего дня"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    today = datetime.date.today()
    await callback.message.edit_text(
        "📅 <b>Добавление рабочего дня</b>\n\n"
        "Введите дату в формате <b>ДД.ММ.ГГГГ</b>\n"
        f"Например: {today.strftime('%d.%m.%Y')}\n\n"
        "Или нажмите кнопку ниже, чтобы вернуться:",
        reply_markup=get_back_keyboard("admin_panel"),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_date_add)
    await callback.answer()


@router.message(AdminStates.waiting_for_date_add)
async def admin_add_day_process(message: Message, state: FSMContext):
    """Обрабатывает ввод даты для добавления рабочего дня"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    try:
        # Парсим дату
        date_obj = datetime.datetime.strptime(message.text.strip(), "%d.%m.%Y")
        date_str = date_obj.strftime("%Y-%m-%d")

        # Проверяем, что дата не в прошлом
        if date_obj.date() < datetime.date.today():
            await message.answer(
                "❌ Нельзя добавить рабочий день в прошлом.\n"
                "Введите другую дату:"
            )
            return

        # Добавляем рабочий день
        if db.add_working_day(date_str):
            await message.answer(
                f"✅ <b>Рабочий день добавлен!</b>\n\n"
                f"📅 {date_obj.strftime('%d.%m.%Y')}\n\n"
                "Теперь добавьте временные слоты для этого дня.",
                reply_markup=get_admin_panel_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "❌ Этот день уже добавлен как рабочий.\n"
                "Введите другую дату:"
            )
            return

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Введите дату в формате <b>ДД.ММ.ГГГГ</b>:",
            parse_mode="HTML"
        )
        return

    await state.clear()


# ==================== Добавление временного слота ====================

@router.callback_query(F.data == "admin_add_slot")
async def admin_add_slot_start(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс добавления временного слота"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    await callback.message.edit_text(
        "🕐 <b>Добавление временного слота</b>\n\n"
        "Введите дату в формате <b>ДД.ММ.ГГГГ</b>\n"
        "Например: 25.06.2026",
        reply_markup=get_back_keyboard("admin_panel"),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_date_slot_add)
    await callback.answer()


@router.message(AdminStates.waiting_for_date_slot_add)
async def admin_add_slot_date(message: Message, state: FSMContext):
    """Обрабатывает ввод даты для добавления слота"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    try:
        date_obj = datetime.datetime.strptime(message.text.strip(), "%d.%m.%Y")
        date_str = date_obj.strftime("%Y-%m-%d")

        # Сохраняем дату
        await state.update_data(slot_date=date_str)

        await message.answer(
            f"📅 Дата: <b>{date_obj.strftime('%d.%m.%Y')}</b>\n\n"
            "🕐 Введите время в формате <b>ЧЧ:ММ</b>\n"
            "Например: 10:00\n\n"
            "<i>Можно добавить несколько слотов, вводя время по одному.</i>",
            reply_markup=get_back_keyboard("admin_panel"),
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_for_time_slot_add)

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Введите дату в формате <b>ДД.ММ.ГГГГ</b>:",
            parse_mode="HTML"
        )


@router.message(AdminStates.waiting_for_time_slot_add)
async def admin_add_slot_time(message: Message, state: FSMContext):
    """Обрабатывает ввод времени для добавления слота"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    try:
        time_str = message.text.strip()
        # Проверяем формат времени
        datetime.datetime.strptime(time_str, "%H:%M")

        data = await state.get_data()
        date_str = data["slot_date"]

        if db.add_time_slot(date_str, time_str):
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            await message.answer(
                f"✅ <b>Слот добавлен!</b>\n\n"
                f"📅 {date_obj.strftime('%d.%m.%Y')} в {time_str}\n\n"
                "Введите ещё один слот или нажмите кнопку «Назад»:",
                reply_markup=get_back_keyboard("admin_panel"),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ Слот {time_str} уже существует для этой даты.\n"
                "Введите другое время:"
            )

    except ValueError:
        await message.answer(
            "❌ Неверный формат времени.\n"
            "Введите время в формате <b>ЧЧ:ММ</b>:",
            parse_mode="HTML"
        )


# ==================== Удаление временного слота ====================

@router.callback_query(F.data == "admin_remove_slot")
async def admin_remove_slot_start(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс удаления временного слота"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    await callback.message.edit_text(
        "🗑️ <b>Удаление временного слота</b>\n\n"
        "Введите дату в формате <b>ДД.ММ.ГГГГ</b>\n"
        "Например: 25.06.2026",
        reply_markup=get_back_keyboard("admin_panel"),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_date_slot_remove)
    await callback.answer()


@router.message(AdminStates.waiting_for_date_slot_remove)
async def admin_remove_slot_date(message: Message, state: FSMContext):
    """Обрабатывает ввод даты для удаления слота"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    try:
        date_obj = datetime.datetime.strptime(message.text.strip(), "%d.%m.%Y")
        date_str = date_obj.strftime("%Y-%m-%d")

        # Получаем все слоты для этой даты
        slots = db.get_all_slots(date_str)

        if not slots:
            await message.answer(
                f"❌ На дату {date_obj.strftime('%d.%m.%Y')} нет слотов.\n"
                "Введите другую дату:"
            )
            return

        await message.answer(
            f"📅 <b>Слоты на {date_obj.strftime('%d.%m.%Y')}:</b>\n\n"
            "Выберите слот для удаления:",
            reply_markup=get_admin_slots_keyboard(slots, date_str, "remove_slot"),
            parse_mode="HTML"
        )
        await state.clear()

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Введите дату в формате <b>ДД.ММ.ГГГГ</b>:",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("remove_slot_"))
async def admin_remove_slot_confirm(callback: CallbackQuery):
    """Подтверждает удаление слота"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    # data: remove_slot_YYYY-MM-DD_HH:MM
    data = callback.data.replace("remove_slot_", "")
    parts = data.split("_")
    date_str = parts[0]
    time_str = parts[1]

    if db.remove_time_slot(date_str, time_str):
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        await callback.message.edit_text(
            f"✅ <b>Слот удалён!</b>\n\n"
            f"📅 {date_obj.strftime('%d.%m.%Y')} в {time_str}",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Не удалось удалить слот.", show_alert=True)

    await callback.answer()


# ==================== Закрытие дня ====================

@router.callback_query(F.data == "admin_close_day")
async def admin_close_day_start(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс закрытия дня"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    await callback.message.edit_text(
        "🚫 <b>Закрытие дня для записи</b>\n\n"
        "Введите дату в формате <b>ДД.ММ.ГГГГ</b>\n"
        "Например: 25.06.2026",
        reply_markup=get_back_keyboard("admin_panel"),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_date_close)
    await callback.answer()


@router.message(AdminStates.waiting_for_date_close)
async def admin_close_day_process(message: Message, state: FSMContext):
    """Обрабатывает ввод даты для закрытия дня"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    try:
        date_obj = datetime.datetime.strptime(message.text.strip(), "%d.%m.%Y")
        date_str = date_obj.strftime("%Y-%m-%d")

        if db.close_day(date_str):
            await message.answer(
                f"✅ <b>День закрыт для записи!</b>\n\n"
                f"📅 {date_obj.strftime('%d.%m.%Y')}\n\n"
                "Все слоты этого дня стали недоступными.",
                reply_markup=get_admin_panel_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "❌ Не удалось закрыть день. Возможно, он не добавлен как рабочий.\n"
                "Введите другую дату:"
            )
            return

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Введите дату в формате <b>ДД.ММ.ГГГГ</b>:",
            parse_mode="HTML"
        )
        return

    await state.clear()


# ==================== Просмотр расписания ====================

@router.callback_query(F.data == "admin_view_schedule")
async def admin_view_schedule_start(callback: CallbackQuery, state: FSMContext):
    """Начинает просмотр расписания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    await callback.message.edit_text(
        "📋 <b>Просмотр расписания</b>\n\n"
        "Введите дату в формате <b>ДД.ММ.ГГГГ</b>\n"
        "Например: 25.06.2026\n\n"
        "Или нажмите «Назад» для возврата:",
        reply_markup=get_back_keyboard("admin_panel"),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_date_view)
    await callback.answer()


@router.message(AdminStates.waiting_for_date_view)
async def admin_view_schedule_process(message: Message, state: FSMContext):
    """Показывает расписание на выбранную дату"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещён.")
        return

    try:
        date_obj = datetime.datetime.strptime(message.text.strip(), "%d.%m.%Y")
        date_str = date_obj.strftime("%Y-%m-%d")

        # Получаем все слоты
        slots = db.get_all_slots(date_str)
        # Получаем записи на эту дату
        appointments = db.get_all_appointments(date_str)

        text = f"📋 <b>Расписание на {date_obj.strftime('%d.%m.%Y')}</b>\n\n"

        if not slots:
            text += "❌ На этот день нет слотов."
        else:
            text += "<b>Слоты:</b>\n"
            for slot in slots:
                status = "✅ Свободен" if slot["is_available"] else "❌ Занят"
                text += f"  {slot['time']} — {status}\n"

        if appointments:
            text += f"\n<b>Записи клиентов:</b>\n"
            for app in appointments:
                text += f"  🕐 {app['time']} — {app['name']} ({app['phone']})\n"
        else:
            text += "\n<i>Нет записей на этот день.</i>"

        await message.answer(
            text,
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="HTML"
        )

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Введите дату в формате <b>ДД.ММ.ГГГГ</b>:",
            parse_mode="HTML"
        )
        return

    await state.clear()


# ==================== Отмена записи клиента (админ) ====================

@router.callback_query(F.data == "admin_cancel_appointment")
async def admin_cancel_appointment_list(callback: CallbackQuery):
    """Показывает список записей для отмены админом"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    appointments = db.get_upcoming_appointments()

    if not appointments:
        await callback.message.edit_text(
            "📋 <b>Нет активных записей.</b>",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "❌ <b>Выберите запись для отмены:</b>",
        reply_markup=get_admin_appointments_keyboard(appointments),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cancel_app_"))
async def admin_cancel_appointment_confirm(callback: CallbackQuery, bot: Bot):
    """Подтверждает отмену записи админом"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    appointment_id = int(callback.data.replace("admin_cancel_app_", ""))

    # Получаем информацию о записи до отмены
    appointment = db.get_appointment_by_id(appointment_id)
    if not appointment:
        await callback.answer("❌ Запись не найдена.", show_alert=True)
        return

    # Отменяем запись
    if db.cancel_appointment(appointment_id):
        # Удаляем задачу напоминания
        from utils.reminder import remove_reminder_job
        remove_reminder_job(appointment_id)

        date_obj = datetime.datetime.strptime(appointment["date"], "%Y-%m-%d")
        date_formatted = date_obj.strftime("%d.%m.%Y")

        await callback.message.edit_text(
            "✅ <b>Запись отменена администратором!</b>\n\n"
            f"👤 Клиент: <b>{appointment['name']}</b>\n"
            f"📞 Телефон: <b>{appointment['phone']}</b>\n"
            f"📅 Дата: <b>{date_formatted}</b>\n"
            f"🕐 Время: <b>{appointment['time']}</b>\n\n"
            "Слот снова доступен для записи.",
            reply_markup=get_admin_panel_keyboard(),
            parse_mode="HTML"
        )

        # Уведомляем клиента об отмене
        try:
            user_text = (
                "❌ <b>Ваша запись была отменена администратором.</b>\n\n"
                f"📅 Дата: <b>{date_formatted}</b>\n"
                f"🕐 Время: <b>{appointment['time']}</b>\n\n"
                "Вы можете записаться заново в главном меню."
            )
            await bot.send_message(
                appointment["user_id"],
                user_text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка уведомления клиента об отмене: {e}")
    else:
        await callback.answer("❌ Не удалось отменить запись.", show_alert=True)

    await callback.answer()
