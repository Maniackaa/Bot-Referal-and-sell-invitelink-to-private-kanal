from config_data.config import LOGGING_CONFIG
from database.db import Session, User

import logging.config

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')


def add_referal_count(reference):
    """Добавялем реферальный переход"""
    with Session() as session:
        user: User = session.query(User).filter(
            User.tg_id == str(reference)).first()
        logger.debug(f'Результат: {user}')
        user.referral_count += 1
        session.commit()
        logger.debug(f'Счетчик перехода {reference} увеличен до {user.referral_count}')
        return True
