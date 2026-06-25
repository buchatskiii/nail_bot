"""
Простой HTTP-сервер для раздачи .ics файлов.
Нужен для того, чтобы на iOS можно было открыть .ics файл
по ссылке и добавить событие в календарь одним нажатием.

При запуске бота этот сервер стартует на отдельном порту (8080)
и раздаёт .ics файлы из папки ics/ с правильным Content-Type.
"""
import os
import logging
from aiohttp import web

logger = logging.getLogger(__name__)

# Папка для хранения .ics файлов
ICS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ics")


def ensure_ics_dir():
    """Создаёт папку для .ics файлов, если её нет"""
    os.makedirs(ICS_DIR, exist_ok=True)


def get_ics_url(filename: str, server_host: str = "139.100.234.22", server_port: int = 8080) -> str:
    """
    Возвращает полную ссылку на .ics файл.

    Args:
        filename: Имя файла (например, appointment_123.ics)
        server_host: IP или домен сервера
        server_port: Порт HTTP-сервера

    Returns:
        str: Полная ссылка на файл
    """
    return f"http://{server_host}:{server_port}/ics/{filename}"


def save_ics_file(filename: str, content: str) -> str:
    """
    Сохраняет .ics файл на диск.

    Args:
        filename: Имя файла
        content: Содержимое .ics файла

    Returns:
        str: Полный путь к сохранённому файлу
    """
    ensure_ics_dir()
    filepath = os.path.join(ICS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Сохранён .ics файл: {filepath}")
    return filepath


def delete_ics_file(filename: str):
    """Удаляет .ics файл с диска"""
    filepath = os.path.join(ICS_DIR, filename)
    if os.path.exists(filepath):
        os.unlink(filepath)
        logger.info(f"Удалён .ics файл: {filepath}")


async def handle_ics_request(request: web.Request) -> web.Response:
    """
    Обрабатывает запрос на получение .ics файла.
    Отдаёт файл с правильным Content-Type для iOS.
    """
    filename = request.match_info.get("filename", "")
    filepath = os.path.join(ICS_DIR, filename)

    if not os.path.exists(filepath):
        return web.Response(text="Файл не найден", status=404)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return web.Response(
        text=content,
        content_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Access-Control-Allow-Origin": "*",
        }
    )


async def start_ics_server(host: str = "0.0.0.0", port: int = 8080):
    """
    Запускает HTTP-сервер для раздачи .ics файлов.

    Args:
        host: Хост для прослушивания (0.0.0.0 - все интерфейсы)
        port: Порт для прослушивания
    """
    ensure_ics_dir()

    app = web.Application()
    app.router.add_get("/ics/{filename}", handle_ics_request)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)

    await site.start()
    logger.info(f"ICS сервер запущен на http://{host}:{port}")
