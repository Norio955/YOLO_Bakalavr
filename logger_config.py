import sys
import os
from loguru import logger
from dotenv import load_dotenv

# Завантажуємо налаштування з файлу .env
load_dotenv()

# Словник локалізованих помилок для користувача (100% вимога)
ERROR_REGISTRY = {
    "ERR-CAM-001": "Не вдалося підключитися до камери. Перевірте кабель або дозволи.",
    "ERR-MDL-201": "Файл нейромережі YOLOv11 не знайдено. Перевірте шлях до файлу weights.",
    "ERR-IMG-301": "Неможливо прочитати зображення. Можливо, файл пошкоджений.",
    "ERR-SYS-500": "Невідома системна помилка. Перезапустіть додаток.",
}


def get_user_error_message(error_code):
    return ERROR_REGISTRY.get(error_code, ERROR_REGISTRY["ERR-SYS-500"])


def setup_logger():
    # Читаємо рівень логування
    log_level = os.getenv("APP_LOG_LEVEL", "INFO")

    # Видаляємо стандартний вивід
    logger.remove()

    # Додаємо вивід у консоль для розробника з кольорами
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan> - <level>{message}</level>",
    )

    # Додаємо запис у файл із ротацією
    # Файл обрізається при досягненні 5 МБ, старі зберігаються 7 днів у ZIP
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/road_signs_{time:YYYY-MM-DD}.log",
        rotation="5 MB",
        retention="7 days",
        compression="zip",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )

    logger.info(f"Система логування запущена. Рівень: {log_level}")
    return logger


# Ініціалізуємо логер при імпорті
app_logger = setup_logger()
