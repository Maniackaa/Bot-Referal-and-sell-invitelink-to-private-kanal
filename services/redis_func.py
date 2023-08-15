import datetime

from config_data.conf import tz
from database.redis_db import r

import logging.config
from config_data.conf import LOGGING_CONFIG, conf
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')

# r.flushall()
key_prefix = 'used_num_'


def add_num_to_used_nums(num: int):
    """Добавляет в базу число с датой добавления"""
    try:
        logger.debug(f'Добавяем {num} в базу редис')
        key = f'{key_prefix}{num}'
        value = datetime.datetime.now().timestamp()
        r.set(key, value)
        logger.debug(f'Добавлено {key} {value}')
    except Exception as err:
        err_log.error(f'Ошибка добавления в редис', exc_info=True)


def get_used_nums() -> dict:
    """Возвращает использованные числа
    {1: datetime.datetime(2023, 8, 13, 8, 58, 42, 24578, tzinfo=<DstTzInfo 'Europe/Moscow' MSK+3:00:00 STD>),}
    """
    logger.debug('Достаём числа с базы')
    pattern = f'{key_prefix}*'
    used_nums = {}
    for key in r.scan_iter(pattern):
        # print(key)
        num = int(key.decode().split(key_prefix)[1])
        value = float(r.get(key).decode())
        value_time = datetime.datetime.fromtimestamp(value).astimezone(tz=tz)
        used_nums[num] = value_time
    return used_nums


def del_used_nums(num):
    key = f'{key_prefix}{num}'
    r.delete(key)


if __name__ == '__main__':
    res = get_used_nums()
    print(res)

