import asyncio
import datetime

from aiogram import Bot, Dispatcher

from config_data.conf import LOGGING_CONFIG, conf, tz
from handlers import user_handlers, pay_handlers, referal_handlers

import logging.config

from keyboards.keyboards import start_kb
from lexicon.lexicon import LEXICON_RU
from services.db_func import find_expired, get_channel_from_id, \
    delete_subscribe_and_ban
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
                del_used_nums(num)
            else:
                logger.debug(f'{num} осталось жить {addet_time + life_delta - now}')
        await asyncio.sleep(10 * 60)


async def checker(bot):
    """Находит список у кого просрочен доступ и банит их"""
    while True:
        expires = find_expired()
        if expires:
            for expire in expires:
                try:
                    await delete_subscribe_and_ban(expire, bot)
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