from dataclasses import dataclass

import pytz
from environs import Env
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default_formatter': {
            'format': "%(asctime)s - [%(levelname)8s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
        },
    },

    'handlers': {
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'default_formatter',
        },
        'rotating_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{BASE_DIR / "logs" / "bot"}.log',
            'backupCount': 2,
            'maxBytes': 10 * 1024 * 1024,
            'mode': 'a',
            'encoding': 'UTF-8',
            'formatter': 'default_formatter',
        },
        'errors_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'{BASE_DIR / "logs" / "errors_bot"}.log',
            'backupCount': 2,
            'maxBytes': 10 * 1024 * 1024,
            'mode': 'a',
            'encoding': 'UTF-8',
            'formatter': 'default_formatter',
        },
    },
    'loggers': {
        'bot_logger': {
            'handlers': ['stream_handler', 'rotating_file_handler'],
            'level': 'DEBUG',
            'propagate': True
        },
        'errors_logger': {
            'handlers': ['stream_handler', 'errors_file_handler'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}


# @dataclass
# class DatabaseConfig:
#     database: str  # Название базы данных
#     db_host: str  # URL-адрес базы данных
#     db_port: str  # URL-адрес базы данных
#     db_user: str  # Username пользователя базы данных
#     db_password: str  # Пароль к базе данных


@dataclass
class PostgresConfig:
    database: str  # Название базы данных
    db_host: str  # URL-адрес базы данных
    db_port: str  # URL-адрес базы данных
    db_user: str  # Username пользователя базы данных
    db_password: str  # Пароль к базе данных


@dataclass
class RedisConfig:
    redis_db_num: str  # Название базы данных
    redis_host: str  # URL-адрес базы данных
    REDIS_PORT: str  # URL-адрес базы данных
    REDIS_PASSWORD: str


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту
    admin_ids: list[str]  # Список id администраторов бота
    base_dir = BASE_DIR
    TIMEZONE: pytz.timezone
    GROUP_TYPE: str
    GROUP_ID: str


@dataclass
class Logic:
    pass


@dataclass
class Config:
    tg_bot: TgBot
    db: PostgresConfig
    logic: Logic
    redis_db: RedisConfig


def load_config(path: str | None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(tg_bot=TgBot(token=env('BOT_TOKEN'),
                               admin_ids=list(map(str, env.list('ADMIN_IDS'))),
                               TIMEZONE=pytz.timezone(env('TIMEZONE')),
                               GROUP_TYPE=env('GROUP_TYPE'),
                               GROUP_ID=env('GROUP_ID'),
                               ),
                  redis_db=RedisConfig(
                      redis_db_num=env('redis_db_num'),
                      redis_host=env('redis_host'),
                      REDIS_PORT=env('REDIS_PORT'),
                      REDIS_PASSWORD=env('REDIS_PASSWORD'),
                      ),
                  db=PostgresConfig(
                      database=env('POSTGRES_DB'),
                      db_host=env('DB_HOST'),
                      db_port=env('DB_PORT'),
                      db_user=env('POSTGRES_USER'),
                      db_password=env('POSTGRES_PASSWORD'),
                      ),
                  logic=Logic(),
                  )


conf = load_config('.env')
conf.db.db_url = f"postgresql+psycopg2://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}"
tz = conf.tg_bot.TIMEZONE

# print('BOT_TOKEN:', config.tg_bot.token)
# print('ADMIN_IDS:', config.tg_bot.admin_ids)
# print()
# print('DATABASE:', config.db.database)
# print('DB_HOST:', config.db.db_host)
# print('DB_port:', config.db.db_port)
# print('DB_USER:', config.db.db_user)
# print('DB_PASSWORD:', config.db.db_password)
# print(config.tg_bot.admin_ids)
print(conf.db.db_url)