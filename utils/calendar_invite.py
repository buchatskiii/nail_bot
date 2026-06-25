"""
Модуль для создания .ics файлов (календарных событий)
"""
import datetime
from typing import Optional

# Московское время (UTC+3)
TIMEZONE_ID = "Europe/Moscow"
TIMEZONE_OFFSET = "+03:00"


def _format_dt(dt: datetime.datetime) -> str:
    """Форматирует дату в iCalendar формат с часовым поясом"""
    return dt.strftime(f"%Y%m%dT%H%M%S")


def create_ics_content(
    summary: str,
    description: str,
    location: str,
    start_datetime: datetime.datetime,
    duration_hours: int = 2,
    uid: Optional[str] = None,
) -> str:
    """
    Создаёт содержимое .ics файла для добавления события в календарь.
    Использует московское время (UTC+3) для корректной работы на iOS/Android.

    Args:
        summary: Название события
        description: Описание события
        location: Место проведения
        start_datetime: Дата и время начала (локальное, Europe/Moscow)
        duration_hours: Длительность в часах
        uid: Уникальный ID события (если не указан, генерируется)

    Returns:
        str: Содержимое .ics файла
    """
    if uid is None:
        uid = f"nail-bot-{start_datetime.strftime('%Y%m%d%H%M%S')}-{abs(hash(start_datetime.isoformat()))}"

    end_datetime = start_datetime + datetime.timedelta(hours=duration_hours)
    dt_stamp = datetime.datetime.now()

    dt_start = _format_dt(start_datetime)
    dt_end = _format_dt(end_datetime)
    dt_stamp_str = _format_dt(dt_stamp)

    # Экранируем спецсимволы для DESCRIPTION
    description_escaped = description.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Nail Bot//RU\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "X-WR-CALNAME:Запись к мастеру\r\n"
        "X-WR-TIMEZONE:Europe/Moscow\r\n"
        "BEGIN:VTIMEZONE\r\n"
        f"TZID:{TIMEZONE_ID}\r\n"
        "X-LIC-LOCATION:Europe/Moscow\r\n"
        "BEGIN:STANDARD\r\n"
        "TZOFFSETFROM:+0300\r\n"
        "TZOFFSETTO:+0300\r\n"
        "TZNAME:MSK\r\n"
        "DTSTART:19700101T000000\r\n"
        "END:STANDARD\r\n"
        "END:VTIMEZONE\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{dt_stamp_str}\r\n"
        f"DTSTART;TZID={TIMEZONE_ID}:{dt_start}\r\n"
        f"DTEND;TZID={TIMEZONE_ID}:{dt_end}\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DESCRIPTION:{description_escaped}\r\n"
        f"LOCATION:{location}\r\n"
        "STATUS:CONFIRMED\r\n"
        "SEQUENCE:0\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-PT1H\r\n"
        "ACTION:DISPLAY\r\n"
        f"DESCRIPTION:Напоминание: {summary}\r\n"
        "END:VALARM\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

    return ics_content
