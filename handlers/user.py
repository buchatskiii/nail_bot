"""
Обработчики для пользовательских команд и callback-запросов
"""
import datetime
import calendar

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards.inline import (
    get_main_menu_keyboard,
    get_calendar_keyboard,
    get_time_slots_keyboard,
    get_confirmation_keyboard,
    get_subscription_check_keyboard,
    get_my_appointments_keyboard,
    get_portfolio_keyboard,
    get_back_keyboard,
)
from config import ADMIN_ID, SCHEDULE_CHANNEL_ID, CHANNEL_ID, BOT_TOKEN
from utils.subscription import check_subscription

router = Router()


# ==================== Обработчик "пустых" кнопок ====================

@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Игнорирует нажатия на неактивные кнопки (заголовки, пустые дни)"""
    await callback.answer()


# ==================== Диагностическая команда ====================

@router.message(Command("chatid"))
async def cmd_chatid(message: Message, bot: Bot):
    """Показывает ID текущего чата (для диагностики)"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Если команда вызвана в канале (forward)
    if message.forward_from_chat:
        chat_id = message.forward_from_chat.id

    await message.answer(
        f"🆔 <b>Информация:</b>\n\n"
        f"Ваш ID: <code>{user_id}</code>\n"
        f"ID чата: <code>{chat_id}</code>\n\n"
        f"<i>Если это ID канала — используйте его с префиксом -100</i>",
        parse_mode="HTML"
    )


# ==================== FSM Состояния ====================

class BookingStates(StatesGroup):
    """Состояния для процесса бронирования"""
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_confirmation = State()


# ==================== Команда /start ====================

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    is_admin = user.id == ADMIN_ID

    welcome_text = (
        f"👋 <b>Добро пожаловать, {user.first_name}!</b>\n\n"
        "Я — бот для записи к мастеру маникюра. 💅\n\n"
        "С моей помощью вы можете:\n"
        "📅 Записаться на удобное время\n"
        "📋 Посмотреть свои записи\n"
        "💰 Узнать цены на услуги\n"
        "📷 Посмотреть портфолио\n\n"
        "Выберите действие в меню ниже:"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(is_admin=is_admin),
        parse_mode="HTML"
    )


# ==================== Главное меню ====================

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    user = callback.from_user
    is_admin = user.id == ADMIN_ID

    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Прайсы ====================

@router.callback_query(F.data == "prices")
async def show_prices(callback: CallbackQuery):
    """Показывает прайс-лист"""
    prices_text = (
        "💰 <b>Прайс-лист на услуги</b>\n\n"
        "💅 <b>Маникюр:</b>\n"
        "• Френч — <b>1000₽</b>\n"
        "• Квадрат — <b>500₽</b>\n\n"
        "📌 Точную стоимость уточняйте у мастера"
    )

    await callback.message.edit_text(
        prices_text,
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Портфолио ====================

@router.callback_query(F.data == "portfolio")
async def show_portfolio(callback: CallbackQuery):
    """Показывает портфолио"""
    portfolio_text = (
        "📷 <b>Портфолио мастера</b>\n\n"
        "Нажмите на кнопку ниже, чтобы посмотреть "
        "работы в Pinterest:"
    )

    await callback.message.edit_text(
        portfolio_text,
        reply_markup=get_portfolio_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Проверка подписки ====================

@router.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Проверяет подписку пользователя на канал"""
    user_id = callback.from_user.id

    if await check_subscription(user_id, bot):
        await callback.message.edit_text(
            "✅ <b>Подписка подтверждена!</b>\n\n"
            "Теперь вы можете записаться на услугу.",
            reply_markup=get_main_menu_keyboard(is_admin=(user_id == ADMIN_ID)),
            parse_mode="HTML"
        )
        # Сохраняем флаг, что подписка проверена
        await state.update_data(subscription_checked=True)
    else:
        await callback.answer(
            "❌ Вы ещё не подписались на канал. Пожалуйста, подпишитесь и нажмите «Проверить подписку».",
            show_alert=True
        )
    await callback.answer()


# ==================== Бронирование: выбор даты ====================

@router.callback_query(F.data == "book_appointment")
async def book_appointment(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Начинает процесс бронирования"""
    user_id = callback.from_user.id

    # Проверяем подписку на канал
    if CHANNEL_ID != 0:
        try:
            is_subscribed = await check_subscription(user_id, bot)
        except Exception:
            is_subscribed = False

        if not is_subscribed:
            await callback.message.edit_text(
                "📢 <b>Для записи необходимо подписаться на канал</b>\n\n"
                "Пожалуйста, подпишитесь на наш канал и нажмите «Проверить подписку»:",
                reply_markup=get_subscription_check_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer()
            return

    # Проверяем, нет ли уже активной записи
    if db.has_user_appointment(user_id):
        await callback.message.edit_text(
            "⚠️ <b>У вас уже есть активная запись!</b>\n\n"
            "Вы можете записаться только на один слот. "
            "Пожалуйста, отмените текущую запись в разделе «Мои записи».",
            reply_markup=get_main_menu_keyboard(is_admin=(user_id == ADMIN_ID)),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Показываем календарь
    today = datetime.date.today()
    year = today.year
    month = today.month

    # Получаем рабочие дни на месяц
    end_of_month = datetime.date(year, month, calendar.monthrange(year, month)[1])
    start_date = today.isoformat()
    end_date = end_of_month.isoformat()
    working_days = db.get_working_days(start_date, end_date)

    await callback.message.edit_text(
        "📅 <b>Выберите дату для записи:</b>\n\n"
        "✅ — рабочие дни\n"
        "❌ — прошедшие дни\n"
        "Цифры без отметок — нерабочие дни",
        reply_markup=get_calendar_keyboard(year, month, working_days),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Навигация по календарю ====================

@router.callback_query(F.data.startswith("cal_"))
async def calendar_navigation(callback: CallbackQuery):
    """Навигация по месяцам в календаре"""
    data = callback.data.split("_")

    if data[1] == "today":
        today = datetime.date.today()
        year = today.year
        month = today.month
    else:
        year = int(data[1])
        month = int(data[2])

    # Получаем рабочие дни на месяц
    end_of_month = datetime.date(year, month, calendar.monthrange(year, month)[1])
    start_date = datetime.date.today().isoformat()
    end_date = end_of_month.isoformat()
    working_days = db.get_working_days(start_date, end_date)

    await callback.message.edit_text(
        "📅 <b>Выберите дату для записи:</b>\n\n"
        "✅ — рабочие дни\n"
        "❌ — прошедшие дни\n"
        "Цифры без отметок — нерабочие дни",
        reply_markup=get_calendar_keyboard(year, month, working_days),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Возврат к календарю ====================

@router.callback_query(F.data == "back_to_calendar")
async def back_to_calendar(callback: CallbackQuery, state: FSMContext):
    """Возврат к календарю"""
    await state.clear()
    today = datetime.date.today()
    year = today.year
    month = today.month

    end_of_month = datetime.date(year, month, calendar.monthrange(year, month)[1])
    start_date = today.isoformat()
    end_date = end_of_month.isoformat()
    working_days = db.get_working_days(start_date, end_date)

    await callback.message.edit_text(
        "📅 <b>Выберите дату для записи:</b>\n\n"
        "✅ — рабочие дни\n"
        "❌ — прошедшие дни\n"
        "Цифры без отметок — нерабочие дни",
        reply_markup=get_calendar_keyboard(year, month, working_days),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Выбор даты ====================

@router.callback_query(F.data.startswith("date_"))
async def select_date(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор даты"""
    date = callback.data.replace("date_", "")

    # Проверяем, не закрыт ли день
    if db.is_day_closed(date):
        await callback.answer("❌ Этот день закрыт для записи.", show_alert=True)
        return

    # Получаем доступные слоты
    available_slots = db.get_available_slots(date)

    if not available_slots:
        await callback.answer(
            "❌ На эту дату нет доступных слотов.",
            show_alert=True
        )
        return

    # Сохраняем выбранную дату
    await state.update_data(selected_date=date)

    await callback.message.edit_text(
        f"📅 <b>Выберите время:</b>",
        reply_markup=get_time_slots_keyboard(available_slots, date),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Выбор времени ====================

@router.callback_query(F.data.startswith("slot_"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор времени"""
    data = callback.data.replace("slot_", "")
    # data имеет формат: YYYY-MM-DD_HH:MM
    parts = data.split("_")
    date = parts[0]
    time = parts[1]

    # Проверяем, доступен ли ещё слот
    if not db.is_slot_available(date, time):
        await callback.answer(
            "❌ Этот слот уже занят. Пожалуйста, выберите другое время.",
            show_alert=True
        )
        # Обновляем список слотов
        available_slots = db.get_available_slots(date)
        if available_slots:
            await callback.message.edit_text(
                "📅 <b>Выберите время:</b>",
                reply_markup=get_time_slots_keyboard(available_slots, date),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ На эту дату больше нет доступных слотов.",
                reply_markup=get_back_keyboard("back_to_calendar"),
                parse_mode="HTML"
            )
        return

    # Сохраняем выбранное время
    await state.update_data(selected_date=date, selected_time=time)

    # Форматируем дату для отображения
    date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
    date_formatted = date_obj.strftime("%d.%m.%Y")

    await callback.message.edit_text(
        f"📅 <b>Вы выбрали:</b>\n"
        f"Дата: <b>{date_formatted}</b>\n"
        f"Время: <b>{time}</b>\n\n"
        "✏️ <b>Введите ваше имя:</b>",
        reply_markup=get_back_keyboard("back_to_calendar"),
        parse_mode="HTML"
    )

    # Переходим в состояние ожидания имени
    await state.set_state(BookingStates.waiting_for_name)
    await callback.answer()


# ==================== Ввод имени ====================

@router.message(BookingStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обрабатывает ввод имени"""
    name = message.text.strip()

    if len(name) < 2 or len(name) > 50:
        await message.answer(
            "❌ Пожалуйста, введите корректное имя (от 2 до 50 символов):"
        )
        return

    await state.update_data(client_name=name)

    await message.answer(
        "📞 <b>Введите ваш номер телефона:</b>\n\n"
        "Например: +7 (999) 123-45-67",
        reply_markup=get_back_keyboard("back_to_calendar"),
        parse_mode="HTML"
    )

    await state.set_state(BookingStates.waiting_for_phone)


# ==================== Ввод телефона ====================

@router.message(BookingStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обрабатывает ввод номера телефона"""
    phone = message.text.strip()

    # Простая проверка номера телефона
    # Убираем все нецифровые символы для проверки
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) < 10 or len(digits) > 15:
        await message.answer(
            "❌ Пожалуйста, введите корректный номер телефона "
            "(например: +7 (999) 123-45-67):"
        )
        return

    await state.update_data(client_phone=phone)

    # Получаем все данные для подтверждения
    data = await state.get_data()
    date = data.get("selected_date")
    time = data.get("selected_time")
    name = data.get("client_name")

    if not all([date, time, name]):
        await message.answer(
            "❌ <b>Сессия истекла.</b>\n\n"
            "Пожалуйста, начните запись заново.",
            reply_markup=get_main_menu_keyboard(is_admin=(message.from_user.id == ADMIN_ID)),
            parse_mode="HTML"
        )
        await state.clear()
        return

    # Форматируем дату
    date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
    date_formatted = date_obj.strftime("%d.%m.%Y")

    await message.answer(
        f"📋 <b>Подтверждение записи:</b>\n\n"
        f"👤 Имя: <b>{name}</b>\n"
        f"📞 Телефон: <b>{phone}</b>\n"
        f"📅 Дата: <b>{date_formatted}</b>\n"
        f"🕐 Время: <b>{time}</b>\n\n"
        "Всё верно?",
        reply_markup=get_confirmation_keyboard(date, time),
        parse_mode="HTML"
    )

    await state.set_state(BookingStates.waiting_for_confirmation)


# ==================== Подтверждение записи ====================

@router.callback_query(F.data.startswith("confirm_"), BookingStates.waiting_for_confirmation)
async def confirm_booking(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Подтверждает запись"""
    data = await state.get_data()
    date = data["selected_date"]
    time = data["selected_time"]
    name = data["client_name"]
    phone = data["client_phone"]
    user_id = callback.from_user.id
    username = callback.from_user.username or ""

    # Проверяем, доступен ли ещё слот
    if not db.is_slot_available(date, time):
        await callback.message.edit_text(
            "❌ <b>К сожалению, этот слот уже занят.</b>\n\n"
            "Пожалуйста, выберите другое время.",
            reply_markup=get_main_menu_keyboard(is_admin=(user_id == ADMIN_ID)),
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return

    # Проверяем, нет ли уже записи у пользователя
    if db.has_user_appointment(user_id):
        await callback.message.edit_text(
            "⚠️ <b>У вас уже есть активная запись!</b>\n\n"
            "Вы можете записаться только на один слот.",
            reply_markup=get_main_menu_keyboard(is_admin=(user_id == ADMIN_ID)),
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return

    # Бронируем слот
    if not db.book_slot(date, time):
        await callback.message.edit_text(
            "❌ <b>Произошла ошибка при бронировании.</b>\n\n"
            "Пожалуйста, попробуйте ещё раз.",
            reply_markup=get_main_menu_keyboard(is_admin=(user_id == ADMIN_ID)),
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return

    # Создаём запись в БД
    if not db.create_appointment(user_id, username, name, phone, date, time):
        # Если не удалось создать запись, освобождаем слот
        db.release_slot(date, time)
        await callback.message.edit_text(
            "❌ <b>Произошла ошибка при сохранении записи.</b>\n\n"
            "Пожалуйста, попробуйте ещё раз.",
            reply_markup=get_main_menu_keyboard(is_admin=(user_id == ADMIN_ID)),
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return

    # Форматируем дату
    date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
    date_formatted = date_obj.strftime("%d.%m.%Y")

    # Отправляем подтверждение пользователю
    await callback.message.edit_text(
        "✅ <b>Запись успешно создана!</b>\n\n"
        f"👤 Имя: <b>{name}</b>\n"
        f"📞 Телефон: <b>{phone}</b>\n"
        f"📅 Дата: <b>{date_formatted}</b>\n"
        f"🕐 Время: <b>{time}</b>\n\n"
        "Ждём вас! 💅",
        reply_markup=get_main_menu_keyboard(is_admin=(user_id == ADMIN_ID)),
        parse_mode="HTML"
    )

    # Отправляем уведомление администратору
    if ADMIN_ID:
        admin_text = (
            "📌 <b>Новая запись!</b>\n\n"
            f"👤 Имя: <b>{name}</b>\n"
            f"📞 Телефон: <b>{phone}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📅 Дата: <b>{date_formatted}</b>\n"
            f"🕐 Время: <b>{time}</b>\n"
        )
        try:
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки уведомления админу: {e}")

    # Отправляем сообщение в канал с расписанием
    if SCHEDULE_CHANNEL_ID:
        channel_text = (
            "📅 <b>Новая запись в расписании</b>\n\n"
            f"👤 Клиент: <b>{name}</b>\n"
            f"📞 Телефон: <code>{phone}</code>\n"
            f"📅 Дата: <b>{date_formatted}</b>\n"
            f"🕐 Время: <b>{time}</b>\n"
        )
        try:
            await bot.send_message(SCHEDULE_CHANNEL_ID, channel_text, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки в канал расписания: {e}")

    # Планируем напоминание, если до записи больше 24 часов
    from utils.reminder import schedule_reminder
    await schedule_reminder(bot, user_id, date, time, name)

    await state.clear()
    await callback.answer()


# ==================== Отмена бронирования ====================

@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    """Отменяет процесс бронирования"""
    await state.clear()
    user = callback.from_user
    is_admin = user.id == ADMIN_ID

    await callback.message.edit_text(
        "❌ <b>Бронирование отменено.</b>\n\n"
        "Вы можете записаться в любое удобное время.",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Мои записи ====================

@router.callback_query(F.data == "my_appointments")
async def my_appointments(callback: CallbackQuery):
    """Показывает записи пользователя"""
    user_id = callback.from_user.id
    appointments = db.get_user_appointments(user_id)

    if not appointments:
        await callback.message.edit_text(
            "📋 <b>У вас нет активных записей.</b>\n\n"
            "Вы можете записаться, нажав «Записаться» в главном меню.",
            reply_markup=get_main_menu_keyboard(is_admin=(user_id == ADMIN_ID)),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Формируем текст со списком записей
    text = "📋 <b>Ваши записи:</b>\n\n"
    for app in appointments:
        date_obj = datetime.datetime.strptime(app["date"], "%Y-%m-%d")
        date_formatted = date_obj.strftime("%d.%m.%Y")
        text += f"📅 {date_formatted} в {app['time']}\n"

    text += "\n<i>Нажмите на запись, чтобы отменить её:</i>"

    await callback.message.edit_text(
        text,
        reply_markup=get_my_appointments_keyboard(appointments),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== Отмена записи пользователем ====================

@router.callback_query(F.data.startswith("cancel_user_"))
async def cancel_user_appointment(callback: CallbackQuery, bot: Bot):
    """Отменяет запись пользователя"""
    appointment_id = int(callback.data.replace("cancel_user_", ""))
    user_id = callback.from_user.id

    # Получаем информацию о записи до отмены
    appointment = db.get_appointment_by_id(appointment_id)
    if not appointment:
        await callback.answer("❌ Запись не найдена.", show_alert=True)
        return

    # Проверяем, что запись принадлежит этому пользователю
    if appointment["user_id"] != user_id:
        await callback.answer("❌ Это не ваша запись.", show_alert=True)
        return

    # Отменяем запись
    if db.cancel_appointment(appointment_id):
        # Удаляем задачу напоминания
        from utils.reminder import remove_reminder_job
        remove_reminder_job(appointment_id)

        date_obj = datetime.datetime.strptime(appointment["date"], "%Y-%m-%d")
        date_formatted = date_obj.strftime("%d.%m.%Y")

        await callback.message.edit_text(
            "✅ <b>Запись успешно отменена!</b>\n\n"
            f"📅 {date_formatted} в {appointment['time']}\n\n"
            "Слот снова доступен для записи.",
            reply_markup=get_main_menu_keyboard(is_admin=(user_id == ADMIN_ID)),
            parse_mode="HTML"
        )

        # Уведомляем администратора
        if ADMIN_ID:
            admin_text = (
                "❌ <b>Запись отменена пользователем</b>\n\n"
                f"👤 Имя: <b>{appointment['name']}</b>\n"
                f"📞 Телефон: <b>{appointment['phone']}</b>\n"
                f"📅 Дата: <b>{date_formatted}</b>\n"
                f"🕐 Время: <b>{appointment['time']}</b>\n"
            )
            try:
                await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
            except Exception as e:
                print(f"Ошибка отправки уведомления админу: {e}")
    else:
        await callback.answer("❌ Не удалось отменить запись.", show_alert=True)

    await callback.answer()
