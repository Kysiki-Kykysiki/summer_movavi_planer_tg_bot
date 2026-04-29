import uuid
from datetime import datetime, timedelta
from typing import Optional


def generate_ics(
    title: str,
    event_date: str,
    event_time: str,
    description: Optional[str] = None,
    duration_hours: int = 1
) -> str:
    """
    Генерирует .ics файл для импорта в Google Calendar или Apple Calendar.

    Args:
        title: Название события
        event_date: Дата в формате YYYY-MM-DD
        event_time: Время в формате HH:MM
        description: Описание события (опционально)
        duration_hours: Длительность в часах

    Returns:
        Строка с содержимым .ics файла
    """
    # Парсим дату и время
    start_dt = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")

    # Вычисляем время окончания
    end_dt = start_dt + timedelta(hours=duration_hours)

    # Форматируем в формат iCalendar с указанием часового пояса
    # Формат: YYYYMMDDTHHMMSS (локальное время)
    dt_start = start_dt.strftime("%Y%m%dT%H%M%S")
    dt_end = end_dt.strftime("%Y%m%dT%H%M%S")

    # Форматируем DTSTAMP в UTC формате
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    # Генерируем уникальный идентификатор
    uid = str(uuid.uuid4())

    # Формируем описание
    desc_text = description if description else ""

    # Экранируем специальные символы для iCalendar
    def escape_ics(text: str) -> str:
        text = text.replace("\\", "\\\\")
        text = text.replace(";", "\\;")
        text = text.replace(",", "\\,")
        text = text.replace("\n", "\\n")
        return text

    title_escaped = escape_ics(title)
    desc_escaped = escape_ics(desc_text)

    # Для Apple Calendar важно указать X-WR-CALNAME и использовать правильный формат
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Planner Bot//RU
X-WR-CALNAME:{title_escaped}
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{uid}@plannerbot
DTSTAMP:{dtstamp}
DTSTART;TZID=Europe/Moscow:{dt_start}
DTEND;TZID=Europe/Moscow:{dt_end}
SUMMARY:{title_escaped}
DESCRIPTION:{desc_escaped}
TRANSP:OPAQUE
SEQUENCE:0
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

    return ics_content
