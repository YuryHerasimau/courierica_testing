import os
import logging
from logging.handlers import RotatingFileHandler
from functions import get_current_path


def create_logs() -> str:
    """
    Создает директорию для логов и возвращает путь к файлу логов.

    :return: Путь к файлу логов.
    """
    file_name = "logs.log"
    log_dir = get_current_path("logs")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    return os.path.join(log_dir, file_name)


def get_logger(name: str) -> logging.Logger:
    """
    Создает и настраивает логгер.

    :param name: Имя логгера (обычно __name__).
    :return: Настроенный логгер.
    """
    log_file = create_logs()
    max_bytes = 1 * 1024 * 1024  # 1 Mb
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(levelname)s | %(asctime)s | %(message)s | file: %(name)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = RotatingFileHandler(
        filename=log_file,
        encoding="utf-8",
        maxBytes=max_bytes,
        backupCount=10,  # total is 10 Mb
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
