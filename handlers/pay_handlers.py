import datetime

from aiogram import Router, Bot, F
from aiogram.filters import Command, Text
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, ChatInviteLink

from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link, decode_payload

from config_data.conf import LOGGING_CONFIG, conf
import logging.config

from keyboards.keyboards import pay_kb1, pay_kb2, start_kb, custom_kb
from lexicon.lexicon import LEXICON_RU, TARIFFS
from services.db_func import get_new_delta, check_user, get_channels, \
    update_subscribe
from services.redis_func import add_num_to_used_nums
from services.referal import update_referral_buy
from services.wallet import get_wallet_transactions

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')

router: Router = Router()


class FSMPay(StatesGroup):
    pay = State()
    select_channel = State()


@router.callback_query(Text(text='pay'))
async def pay(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.delete()
    # Выбор подписки для продления:
    text = 'Выберите канал для продления подписки:\n'
    channels = get_channels()
    text_channels = [
        f'<b>{ch.title}</b>\n{ch.description}\n\n'
        for ch in channels]
    text += ''.join(text_channels)
    channels = get_channels()
    channel_kb_btn = {}
    for channel in channels:
        channel_kb_btn[channel.title] = f'channel:{channel.id}'
    channel_kb = custom_kb(1, channel_kb_btn)
    await callback.message.answer('Выберите канал',
                                  reply_markup=channel_kb)


@router.callback_query(Text(startswith='channel:'))
async def pay(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(FSMPay.select_channel)
    channel_pk = int(callback.data.split('channel:')[1])
    await state.update_data(channel_pk=channel_pk)
    await callback.message.answer('На какой срок хотите купить подписку?', reply_markup=pay_kb1)


def get_pay_text(callback):
    delta = get_new_delta(callback.from_user.id)
    pay_days = int(callback.data.split('pay_')[1])
    price = TARIFFS[pay_days]
    value = price + delta / 100
    text = f'<b>Оплата на {pay_days} дней.</b>\n'
    text += LEXICON_RU[callback.data].format(value)
    return text


@router.callback_query(Text(startswith='pay_'))
async def pay(callback: CallbackQuery, state: FSMContext, bot: Bot):
    text = get_pay_text(callback)
    await state.set_state(FSMPay.pay)
    await state.update_data(text=text)
    await callback.message.answer(text, parse_mode='HTML', reply_markup=pay_kb2)
    await callback.message.delete()


@router.callback_query(Text(text='check_pay'))
async def pay(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    prices = list(TARIFFS.values())
    print(prices)
    days = list(TARIFFS.keys())
    print(days)
    tarif = 0
    user = check_user(callback.from_user.id)
    transactions = get_wallet_transactions()
    for tarif_num, price in enumerate(prices, 1):
        if price + user.delta_num / 100 in transactions:
            print(tarif_num, 'Транзакция найдена')
            tarif = tarif_num
        else:
            print(tarif_num, 'Транзакция НЕ найдена')
    if tarif:
        await callback.message.answer('Ваша оплата прошла успешно')
        await callback.message.delete()
        await state.clear()
        # Добавляем использованный номер в базу использованных
        add_num_to_used_nums(user.delta_num)
        # Очищаем занятое число в базе
        user.set('delta_num', None)
        user.set('delta_end', None)
        # Обрабатываем реферральную систему
        if user.referral:
            logger.debug(f'Есть реферал: {user.referral}')
            update_referral_buy(user)
        await state.set_state(FSMPay.select_channel)
        await state.update_data(tarif=tarif)
        # Отправялем ссылку

        channel_pk = data['channel_pk']
        print(channel_pk)
        days = list(TARIFFS.keys())[tarif - 1]
        subscribe, channel = update_subscribe(check_user(callback.from_user.id), channel_pk, days)
        await state.clear()
        user = check_user(callback.from_user.id)
        await bot.unban_chat_member(chat_id=channel.channel_id,
                                    user_id=user.tg_id,
                                    only_if_banned=True)
        link: ChatInviteLink = await bot.create_chat_invite_link(
            chat_id=channel.channel_id,
            creates_join_request=False,
            expire_date=subscribe.expire,
            member_limit=1)
        text = f'Вы обновили подписку на канал {channel.title} до {subscribe.expire}\n' \
               f'Ваша ссылка: {link.invite_link}'
        await callback.message.delete()
        await callback.message.answer(text)

    else:
        await callback.message.answer('Транзакция не найдена')
        data = await state.get_data()
        text = data.get('text')
        await callback.message.answer(text, parse_mode='HTML',
                                      reply_markup=pay_kb2)
        await callback.message.delete()


@router.callback_query(Text(text='cancel'))
async def pay(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(LEXICON_RU['start_text'],
                                  reply_markup=start_kb)
