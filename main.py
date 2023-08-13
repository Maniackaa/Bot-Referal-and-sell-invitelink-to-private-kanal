import asyncio
import datetime

from aiogram import Bot, Dispatcher

from config_data.conf import LOGGING_CONFIG, conf, tz
from handlers import user_handlers, pay_handlers, referal_handlers

import logging.config

from keyboards.keyboards import start_kb
from lexicon.lexicon import LEXICON_RU
from services.db_func import find_expired
from services.redis_func import get_used_nums, del_used_nums

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')


async def redis_cleaner(life=24):
    """Очищает давно используемые числа, страше life часов"""
    while True:
        logger.info(f'Очистка старых чисел с редис')
        all_nums = get_used_nums()
        logger.info(f'Использованные числа:\n{all_nums}')
        now = datetime.datetime.now(tz=tz)
        life_delta = datetime.timedelta(hours=life)
        for num, addet_time in all_nums.items():
            if now > addet_time + life_delta:
                print('Пора удалять')
                del_used_nums(0)
            else:
                print('осталось жить', addet_time + life_delta - now)
        await asyncio.sleep(10 * 60)


async def checker(bot):
    """Находит список у кого просрочен доступ и банит их"""
    while True:
        to_ban = find_expired()
        logger.debug(f'Список просроченных: {to_ban}')
        if to_ban:
            for user in to_ban:
                try:
                    user.set('member_expire', None)
                    text_after_expire = LEXICON_RU['text_after_expire']
                    await bot.ban_chat_member(chat_id=conf.tg_bot.GROUP_ID,
                                              user_id=user.tg_id)
                    await bot.send_message(chat_id=user.tg_id,
                                           text=text_after_expire,
                                           reply_markup=start_kb)
                    logger.debug(f'Пользователь {user.tg_id} удален')
                except Exception as err:
                    logger.error(f'Ошибка {err}')
        await asyncio.sleep(1 * 60)


async def main():
    logger.info('Starting bot Etagi')
    bot: Bot = Bot(token=conf.tg_bot.token, parse_mode='HTML')

    dp: Dispatcher = Dispatcher()
    dp.include_router(user_handlers.router)
    dp.include_router(pay_handlers.router)
    dp.include_router(referal_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)

    asyncio.create_task(checker(bot))
    asyncio.create_task(redis_cleaner())

    try:
        admins = conf.tg_bot.admin_ids
        if admins:
            await bot.send_message(
                conf.tg_bot.admin_ids[0], f'Бот запущен.')
    except:
        err_log.critical(f'Не могу отравить сообщение {conf.tg_bot.admin_ids[0]}')

    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped!')