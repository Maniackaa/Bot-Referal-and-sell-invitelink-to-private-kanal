import asyncio
import datetime
import logging
from typing import Optional

from config_data.config import LOGGING_CONFIG, config
import logging.config

from database.db import User, Session

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')


def check_user(tg_id: int | str) -> User:
    """Возвращает найденного пользователя по tg_id"""
    logger.debug(f'Ищем юзера {tg_id}')
    with Session() as session:
        user: User = session.query(User).filter(User.tg_id == str(tg_id)).first()
        logger.debug(f'Результат: {user}')
        return user


def create_user(user, refferal=None) -> Optional[User]:
    """Из юзера ТГ создает User"""
    try:
        old_user = check_user(user.id)
        if old_user:
            logger.debug('Пользователь есть в базе')
            return None
        # Создание нового пользователя
        logger.debug('Добавляем пользователя')
        with Session() as session:
            new_user = User(tg_id=user.id,
                            username=user.username,
                            register_date=datetime.datetime.now(),
                            referral=refferal
                            )
            session.add(new_user)
            session.commit()
            logger.debug(f'Пользователь создан: {new_user}')
        return new_user
    except Exception as err:
        err_log.error('Пользователь не создан', exc_info=True)


def find_expired():
    with Session() as session:
        admins = config.tg_bot.admin_ids
        print(admins)
        now = datetime.datetime.utcnow()
        users = session.query(User).filter(User.member_expire < now).filter(
            User.tg_id.notin_(config.tg_bot.admin_ids)).all()
        print(users)
        logger.debug(f'Просроченные юзеры: {users}')
        return users


if __name__ == '__main__':
    pass

