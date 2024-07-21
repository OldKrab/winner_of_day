import logging
from logging.handlers import BufferingHandler, RotatingFileHandler
import sys


class TelegramAdminHandler(logging.Handler):
    def __init__(self):
        self.bot = None
        self.admin = None
    def emit(self, record):
        msg = self.format(record)
        record.__dict__["bot"]
        

def get_logger(logger_name: str, log_file: str = "log.log") -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "> %(asctime)s [%(levelname)s, %(name)s]: %(message)s", datefmt="%H:%M:%S %m-%d"
    )
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=0
    )  # Set max file size to 10 MB
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
