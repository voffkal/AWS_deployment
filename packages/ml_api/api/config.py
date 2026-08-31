import logging
from logging.handlers import TimedRotatingFileHandler
import pathlib
import os
import sys

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent

FORMATTER = logging.Formatter(
    "%(asctime)s — %(name)s — %(levelname)s —"
    "%(funcName)s:%(lineno)d — %(message)s")

LOG_DIR = PACKAGE_ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'ml_api.log'
UPLOAD_FOLDER = PACKAGE_ROOT / 'uploads'

UPLOAD_FOLDER.mkdir(exist_ok=True)


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler():
    file_handler = TimedRotatingFileHandler(
        LOG_FILE,
        when='midnight'
    )

    file_handler.setFormatter(FORMATTER)
    file_handler.setLevel(logging.WARNING)

    return file_handler


def get_logger(*, logger_name):
    """Get logger with prepared handlers."""

    logger = logging.getLogger(logger_name)

    logger.setLevel(logging.INFO)

    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler())
    logger.propagate = False

    return logger


class Config:
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')
    SERVER_PORT = 5000
    UPLOAD_FOLDER = UPLOAD_FOLDER


class ProductionConfig(Config):
    DEBUG = False
    # NOTE: these are assignments, not annotations. Using ``:`` here would
    # only record a type hint and silently ignore the environment.
    SERVER_ADDRESS = os.environ.get('SERVER_ADDRESS', '0.0.0.0')
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True