# https://developers.tron.network/docs/get-trc20-transaction-history
import datetime
import requests
import logging.config

from config_data.conf import conf
from config_data.conf import LOGGING_CONFIG


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')


def get_wallet_transactions(period=24) -> list | None:
    """Достает историю транзакций за период в часах"""
    try:
        logger.debug(f'Читаем транзакции за {period} часа')
        params = {
            'limit': '20',
        }
        response = requests.get(
            'https://api.trongrid.io/v1/accounts/TBx5CybQrY197WPEiFVoMqz4ENfHCs7tGL/transactions/trc20',
            params=params)
        result = response.json()
        history = result['data']
        result_history = []
        result_values = []
        for row in history:
            date_time = row['block_timestamp']
            operation_time = datetime.datetime.fromtimestamp(date_time / 1000, tz=conf.tg_bot.TIMEZONE)
            delta = datetime.datetime.now(tz=conf.tg_bot.TIMEZONE) - operation_time
            delta_hour = delta.total_seconds() / 60 / 60
            value = row['value']
            to = row['to']
            if to == 'TBx5CybQrY197WPEiFVoMqz4ENfHCs7tGL' and delta_hour < period:
                # print(value, delta_hour, operation_time)
                result_history.append(
                    {'operation_time': operation_time,
                     'value': round(int(value) / 1000000, 2)}
                )
                result_values.append(round(int(value) / 1000000, 2))
        logger.debug(f'Найденые транзакции: {result_values}')
        return result_values
    except Exception as err:
        logger.debug(f'Ошибка при распознавании истории кошелька', exc_info=True)

x = get_wallet_transactions()
# print(x)