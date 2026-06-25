"""
Модуль для создания .ics файлов (календарных событий)
"""
import datetime
from typing import Optional


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
    
    Args:
        summary: Название события
        description: Описание события
        location: Место проведения
        start_datetime: Дата и время начала
        duration_hours: Длительность в часах
        uid: Уникальный ID события (если не указан, генерируется)
    
    Returns:
        str: Содержимое .ics файла
    """
    if uid is None:
        uid = f"nail-bot-{start_datetime.strftime('%Y%m%d%H%M%S')}-{hash(start_datetime.isoformat())}"
    
    end_datetime = start_datetime + datetime.timedelta(hours=duration_hours)
    
    # Форматируем даты в формат iCalendar (UTC)
    dt_start = start_datetime.strftime("%Y%m%dT%H%M%S")
    dt_end = end_datetime.strftime("%Y%m%dT%H%M%S")
    dt_stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    
    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Nail Bot//RU\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{dt_stamp}\r\n"
        f"DTSTART:{dt_start}\r\n"
        f"DTEND:{dt_end}\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DESCRIPTION:{description}\r\n"
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
