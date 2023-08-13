from aiogram.utils.deep_linking import decode_payload

from config_data.conf import LOGGING_CONFIG
from database.db import Session, User

import logging.config

from services.db_func import check_user

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


def update_referral_buy(user: User):
    """Обработка рефера при покупке"""
    referral_id = decode_payload(user.referral)
    # Добавим рефералу счетчик покупки
    ref_user: User = check_user(referral_id)
    ref_user.set('referral_buy_count', ref_user.referral_buy_count + 1)
    logger.debug(f'{user} сделал покупку. Его реферал - {referral_id}: {ref_user}. Счетчик: {ref_user.referral_buy_count + 1}')