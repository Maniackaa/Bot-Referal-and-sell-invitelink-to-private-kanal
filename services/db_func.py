import asyncio
import datetime
import logging
from typing import Optional

from config_data.conf import LOGGING_CONFIG, conf, tz
import logging.config

from database.db import User, Session, Channel, Subscribe
from keyboards.keyboards import start_kb
from lexicon.lexicon import TARIFFS, LEXICON_RU
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


def find_expired() -> list[Subscribe]:
    """Находит просроченные подписки"""
    with Session() as session:
        admins = conf.tg_bot.admin_ids
        now = datetime.datetime.now(tz=conf.tg_bot.TIMEZONE)
        expires = session.query(Subscribe).filter(Subscribe.expire < now).filter(
            User.tg_id.notin_(admins)).all()
        logger.debug(f'Просроченные подписки: {expires}')
        return expires


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
            err_log.error(f'Ошибка чтения used_delta')
            raise err


def get_channels():
    """Список активных каналов"""
    with Session() as session:
        channels = session.query(Channel).filter(Channel.is_active == 1).all()
        return channels


def get_channel_from_id(pk) -> Channel:
    with Session() as session:
        channel = session.query(Channel).filter(Channel.id == pk).one_or_none()
        return channel


def update_subscribe(user: User, channel_pk: int, days: int) -> tuple[Subscribe, Channel]:
    """"Обновляет в базе подписку"""
    logger.debug(f'update_subscribe {user} Канал: {channel_pk} Дней: {days}')
    with Session() as session:
        try:
            subscribe: Subscribe = session.query(Subscribe).filter(
                Subscribe.user_id == user.id, Subscribe.channel_id == channel_pk).one_or_none()
            now = datetime.datetime.now(tz=tz).replace(tzinfo=None)
            if subscribe:
                logger.debug('Подписка есть')
                if subscribe.expire:
                    new_expire = subscribe.expire + datetime.timedelta(days)
                else:
                    new_expire = now + datetime.timedelta(days)
                subscribe.expire = new_expire
            else:
                logger.debug('Подписки нет')
                subscribe = Subscribe(
                    channel_id=channel_pk,
                    user_id=user.id,
                    expire=now + datetime.timedelta(days)
                )
                session.add(subscribe)
            session.commit()
            return subscribe, subscribe.channel
        except Exception as err:
            err_log.error('Ошибка при подписке')


def get_user_subscribe_text(tg_id) -> str:
    with Session() as session:
        try:
            user: User = session.query(User).filter(User.tg_id == str(tg_id)).first()
            subscribes: list[Subscribe] = user.subscribes
            if subscribes:
                text = 'Ваши акnивные подписки:\n'
                for subscribe in subscribes:
                    expire: datetime.datetime = subscribe.expire
                    expired = expire.strftime("%d.%m.%Y")
                    print(subscribe.expire, type(subscribe.expire))
                    sub_text = f'{subscribe.channel.title}: до {expired}\n\n'
                    text += sub_text
            else:
                text = 'У вас нет активных подписок'
            logger.debug(f'Подписки: {text}]')
            return text
        except Exception as err:
            err_log.error('Ошибка чтения полписок')


async def delete_subscribe_and_ban(expire: Subscribe, bot):
    """Удаляет подписку, банинт пользователя и отправляет сообщение"""
    with Session() as session:
        try:
            expire = session.query(Subscribe).filter(
                Subscribe.id == expire.id).one_or_none()
            channel = expire.channel
            text_after_expire = LEXICON_RU['text_after_expire'].format(channel.title)
            user = expire.user
            print(user)
            session.delete(expire)
            session.commit()
            await bot.ban_chat_member(chat_id=channel.channel_id,
                                      user_id=user.tg_id)
            await bot.send_message(chat_id=channel.channel_id,
                                   text=text_after_expire,
                                   reply_markup=start_kb)
            logger.debug(f'Пользователь {user.tg_id} удален')
        except Exception as err:
            err_log.error('Ошибка при отписке', exc_info=True)


if __name__ == '__main__':
    pass

