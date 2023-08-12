import asyncio
import datetime

from aiogram import Bot, Dispatcher

from config_data.config import LOGGING_CONFIG, config
from handlers import user_handlers

import logging.config

from services.db_func import find_expired

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')


async def checker(bot):
    """Находит список у кого просрочен доступ и банит их"""
    while True:
        to_ban = find_expired()
        logger.debug(f'Список просроченных: {to_ban}')
        if to_ban:
            for user in to_ban:
                try:
                    await bot.ban_chat_member(chat_id=config.tg_bot.GROUP_ID,
                                              user_id=user.tg_id)
                    user.set('member_expire', None)
                    logger.debug(f'Пользователь {user.tg_id} удален')
                except Exception as err:
                    logger.error(f'Ошибка {err}')
        await asyncio.sleep(3)


async def main():
    logger.info('Starting bot Etagi')
    bot: Bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp: Dispatcher = Dispatcher()

    # Регистриуем
    asyncio.create_task(checker(bot))
    dp.include_router(user_handlers.router)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await bot.send_message(
            config.tg_bot.admin_ids[0], f'Бот запущен.')
    except:
        err_log.critical(f'Не могу отравить сообщение {config.tg_bot.admin_ids[0]}')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped!')