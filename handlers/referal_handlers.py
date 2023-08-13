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

from keyboards.keyboards import ref_kb, start_kb
from lexicon.lexicon import LEXICON_RU
from services.db_func import check_user

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')

router: Router = Router()


@router.callback_query(Text(text='ref'))
async def get_ref(callback: CallbackQuery, state: FSMContext, bot: Bot):
    text = LEXICON_RU['referal_text']
    await callback.message.answer(text, reply_markup=ref_kb)
    await callback.message.delete()


@router.callback_query(Text(text='ref_link'))
async def get_ref(callback: CallbackQuery, state: FSMContext, bot: Bot):
    link = await create_start_link(bot, str(callback.from_user.id), encode=True)
    await callback.message.answer(f'Ваша реферальная ссылка:\n{link}')
    await callback.message.delete()


@router.callback_query(Text(text='ref_balance'))
async def ref_balance(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user = check_user(callback.from_user.id)
    text = (
        f'Количество приглашенных: {user.referral_count}\n'
        f'Купили подписку: {user.referral_buy_count}\n'
        f'Ваш баланс: {user.referral_buy_count * 5} USDT'
    )
    url_button_1 = InlineKeyboardButton(
        text='Вывести средства',
        callback_data=f'cash_out')
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    kb_builder.row(url_button_1)
    keyboard = kb_builder.as_markup()
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(Text(text='cash_out'))
async def ref_balance(callback: CallbackQuery, state: FSMContext, bot: Bot):
    text = LEXICON_RU['cash_out_text']
    await callback.message.answer(text, reply_markup=start_kb)
    await callback.message.delete()