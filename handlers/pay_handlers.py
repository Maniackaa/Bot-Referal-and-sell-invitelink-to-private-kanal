import datetime

from aiogram import Router, Bot, F
from aiogram.filters import Command, Text
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, ChatInviteLink

from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link, decode_payload

from config_data.conf import LOGGING_CONFIG, conf
import logging.config

from keyboards.keyboards import pay_kb1, pay_kb2, start_kb
from lexicon.lexicon import LEXICON_RU, TARIFFS
from services.db_func import get_new_delta, check_user
from services.redis_func import add_num_to_used_nums
from services.referal import update_referral_buy
from services.wallet import get_wallet_transactions

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')

router: Router = Router()


class FSMPay(StatesGroup):
    pay = State()


@router.callback_query(Text(text='pay'))
async def pay(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.delete()
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


@router.callback_query(Text(text='cancel'))
async def pay(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(LEXICON_RU['start_text'],
                                  reply_markup=start_kb)


@router.callback_query(Text(text='check_pay'))
async def pay(callback: CallbackQuery, state: FSMContext, bot: Bot):
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
        # Определяем срок ссылки
        if user.member_expire:
            new_expire = user.member_expire + datetime.timedelta(days=days[tarif - 1])
        else:
            new_expire = datetime.datetime.now(tz=conf.tg_bot.TIMEZONE) + datetime.timedelta(days=days[tarif - 1])
        user.set('member_expire', new_expire)
        await bot.unban_chat_member(chat_id=conf.tg_bot.GROUP_ID,
                                    user_id=callback.from_user.id,
                                    only_if_banned=True)
        link: ChatInviteLink = await bot.create_chat_invite_link(
            chat_id=conf.tg_bot.GROUP_ID,
            creates_join_request=False,
            expire_date=new_expire,
            member_limit=1)
        await callback.message.answer(f'Ваша ссылка (до {link.expire_date.astimezone(tz=conf.tg_bot.TIMEZONE)}):\n{link.invite_link}')
        # Обрабатываем реферральную систему
        if user.referral:
            logger.debug(f'Есть реферал: {user.referral}')
            update_referral_buy(user)

    else:
        await callback.message.answer('Транзакция не найдена')
        data = await state.get_data()
        text = data.get('text')
        await callback.message.answer(text, parse_mode='HTML',
                                      reply_markup=pay_kb2)
        await callback.message.delete()



