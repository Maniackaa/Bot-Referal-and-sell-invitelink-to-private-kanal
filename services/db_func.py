import asyncio
import datetime
import logging
from typing import Optional

from config_data.conf import LOGGING_CONFIG, conf
import logging.config

from database.db import User, Session
from services.redis_func import get_used_nums

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')


def check_user(tg_id: int | str) -> User:
    """Возвращает найденного пользователя по tg_id"""
    # logger.debug(f'Ищем юзера {tg_id}')
    with Session() as session:
        user: User = session.query(User).filter(User.tg_id == str(tg_id)).first()
        # logger.debug(f'Результат: {user}')
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
    """Находит юзеров, подписка которых кончилась и не пустая"""
    with Session() as session:
        admins = conf.tg_bot.admin_ids
        now = datetime.datetime.now(tz=conf.tg_bot.TIMEZONE)
        users = session.query(User).filter(User.member_expire < now).filter(
            User.tg_id.notin_(admins)).all()
        logger.debug(f'Просроченные юзеры: {users}')
        return users


def get_new_delta(tg_id: int):
    """Выбирает неиспользованную дельту и присваивает юзеру"""
    with Session() as session:
        try:
            user: User = session.query(User).filter(User.tg_id == str(tg_id)).first()
            # Если дельта есть и не просрочилась, выдаем ее
            now = datetime.datetime.now(tz=conf.tg_bot.TIMEZONE).replace(tzinfo=None)
            if user.delta_end and now < user.delta_end:
                return user.delta_num
            # Присваиваем и возвращаем новую дельту
            user_with_delta = session.query(User).filter(
                User.delta_num.is_not(None)).all()
            used_num = [x.delta_num for x in user_with_delta]
            logger.debug(f'Использованные числа: {used_num}')
            redis_used_nums = get_used_nums().keys()
            for i in range(1, 1000):
                if i not in used_num and i not in redis_used_nums:
                    logger.debug(f'Новое число: {i}')
                    user.delta_num = i
                    user.delta_end = datetime.datetime.now(tz=conf.tg_bot.TIMEZONE) + datetime.timedelta(hours=24)
                    session.commit()
                    return i
        except Exception as err:
            logger.error(f'Ошибка чтения used_delta')
            raise err


if __name__ == '__main__':
    pass

