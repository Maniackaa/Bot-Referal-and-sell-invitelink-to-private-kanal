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
from services.db_func import create_user, check_user, get_channels, \
    get_user_subscribe_text, update_subscribe
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
    if user.demo_used:
        await callback.message.answer('Вы уже использовали демо-доступ')
    else:
        user.set('demo_used', 1)
        channels = get_channels()
        for channel in channels:
            link: ChatInviteLink = await bot.create_chat_invite_link(
                chat_id=channel.channel_id,
                creates_join_request=False,
                expire_date=(datetime.datetime.now(tz=conf.tg_bot.TIMEZONE) + datetime.timedelta(hours=24)),
                member_limit=1)
            text = LEXICON_RU['get_demo'].format(channel.title)
            url_button_1 = InlineKeyboardButton(
                text=f'Перейти на {channel.title}',
                url=f'{link.invite_link}')
            kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
            kb_builder.row(url_button_1)
            keyboard = kb_builder.as_markup()
            await callback.message.answer(text, reply_markup=keyboard)
            await bot.unban_chat_member(chat_id=conf.tg_bot.GROUP_ID,
                                        user_id=callback.from_user.id,
                                        only_if_banned=True)
            # user.set('demo_expire', link.expire_date)
            update_subscribe(user, channel.id, 1)


    await callback.message.delete()


@router.callback_query(Text(text='check_expire'))
async def check_expire(callback: CallbackQuery, state: FSMContext, bot: Bot):
    subscribes_text = get_user_subscribe_text(callback.from_user.id)
    await callback.message.answer(subscribes_text)



@router.callback_query(Text(text='support'))
async def support(callback: CallbackQuery, state: FSMContext, bot: Bot):
    text = LEXICON_RU['support_text']
    await callback.message.answer(text, reply_markup=start_kb)
    await callback.message.delete()
