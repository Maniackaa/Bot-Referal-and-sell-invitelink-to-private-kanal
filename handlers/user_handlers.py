import datetime

from aiogram import Router, Bot, F
from aiogram.filters import Command, Text
from aiogram.types import CallbackQuery, Message, ChatInviteLink, \
    InlineKeyboardButton

from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link, decode_payload
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config_data.conf import LOGGING_CONFIG, conf, tz
import logging.config

from keyboards.keyboards import start_kb, custom_kb
from lexicon.lexicon import LEXICON_RU
from services.db_func import create_user, check_user
from services.referal import add_referal_count

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')

router: Router = Router()


@router.message(Command(commands=["start"]))
async def process_start_command(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    referal = message.text[7:]
    new_user = create_user(message.from_user, referal)
    if new_user:
        reference = str(decode_payload(referal))
        if reference and reference != new_user.tg_id:
            add_referal_count(reference)
        await message.answer(LEXICON_RU['start_text'], reply_markup=start_kb)
    else:
        await message.answer(LEXICON_RU['start_text'], reply_markup=start_kb)


@router.callback_query(Text(text='demo'))
async def get_demo_info(callback: CallbackQuery, state: FSMContext, bot: Bot):
    text = LEXICON_RU['demo_text']
    await callback.message.answer(text, reply_markup=custom_kb(1, {'Получить пробный доступ': 'get_demo'}))
    await callback.message.delete()


@router.callback_query(Text(text='get_demo'))
async def get_demo(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user = check_user(callback.from_user.id)
    print(user.member_expire)
    if user.demo_used:
        await callback.message.answer('Вы уже использовали демо-доступ')
    elif user.member_expire:
        await callback.message.answer('У вас уже есть доступ')
    else:
        link: ChatInviteLink = await bot.create_chat_invite_link(
            chat_id=conf.tg_bot.GROUP_ID,
            creates_join_request=False,
            expire_date=(datetime.datetime.now(tz=conf.tg_bot.TIMEZONE) + datetime.timedelta(hours=24)),
            member_limit=1)
        text = LEXICON_RU['get_demo']
        url_button_1 = InlineKeyboardButton(
            text='Перейти в группу',
            url=f'{link.invite_link}')
        kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
        kb_builder.row(url_button_1)
        keyboard = kb_builder.as_markup()
        await callback.message.answer(text, reply_markup=keyboard)
        user.set('member_expire', link.expire_date)
        user.set('demo_used', 1)
        await bot.unban_chat_member(chat_id=conf.tg_bot.GROUP_ID,
                                    user_id=callback.from_user.id,
                                    only_if_banned=True)
    await callback.message.delete()


@router.callback_query(Text(text='check_expire'))
async def check_expire(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user = check_user(callback.from_user.id)
    expire_data: datetime.datetime = user.member_expire
    if expire_data:
        now = datetime.datetime.now(tz=tz).replace(tzinfo=None)
        life_time: datetime.timedelta = expire_data - now
        life_days = life_time.total_seconds() / 60 / 60 // 24
        print('expire_data', expire_data)
        print('life_time', life_time)
        print('now', now)
        if life_days >= 0:
            await callback.message.answer(f'Ваша подписка действительна еще {int(life_days)} дн.\nДо {expire_data}')
        else:
            await callback.message.answer(
                f'Ваша подписка не действительна')
    else:
        await callback.message.answer(
            f'Ваша подписка не действительна')
    await callback.message.delete()

