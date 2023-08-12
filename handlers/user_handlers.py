import datetime

from aiogram import Dispatcher, types, Router, Bot, F
from aiogram.filters import Command, CommandStart, Text, StateFilter, \
    BaseFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, URLInputFile, ChatInviteLink

from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link, decode_payload

from config_data.config import LOGGING_CONFIG, config
import logging.config

from keyboards.keyboards import start_kb
from services.db_func import create_user, check_user
from services.referal import add_referal_count

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('bot_logger')
err_log = logging.getLogger('errors_logger')

router: Router = Router()


class FSMCheckUser(StatesGroup):
    send_phone = State()


@router.message(Command(commands=["start"]))
async def process_start_command(message: Message, state: FSMContext):
    await state.clear()
    referal = message.text[7:]
    new_user = create_user(message.from_user, referal)
    if new_user:
        reference = decode_payload(referal)
        if reference:
            add_referal_count(reference)
        await message.answer('Добро пожаловать!', reply_markup=start_kb)
    else:
        user = check_user(message.from_user.id)
        await message.answer('Добро пожаловать!', reply_markup=start_kb)
        await message.answer(f'Ваш реферальный счетчик: {user.referral_count}')


@router.callback_query(Text(text='ref'))
async def get_ref(callback: CallbackQuery, state: FSMContext, bot: Bot):
    link = await create_start_link(bot, str(callback.from_user.id), encode=True)
    await callback.message.answer(f'Ваша реферальная ссылка:\n{link}')
    await callback.message.delete()


@router.callback_query(Text(text='demo'))
async def get_ref(callback: CallbackQuery, state: FSMContext, bot: Bot):
    link: ChatInviteLink = await bot.create_chat_invite_link(
        chat_id=config.tg_bot.GROUP_ID,
        creates_join_request=False,
        expire_date=datetime.datetime.now() + datetime.timedelta(minutes=3),
        member_limit=1)
    await callback.message.answer(f'Ваша ссылка (до {link.expire_date}):\n{link.invite_link}')
    await callback.message.delete()
    user = check_user(callback.from_user.id)
    user.set('member_expire', link.expire_date)
    await bot.unban_chat_member(chat_id=config.tg_bot.GROUP_ID,
                                user_id=callback.from_user.id,
                                only_if_banned=True)


@router.message(Command(commands=["ban"]))
async def process_start_command(message: Message, state: FSMContext, bot: Bot):
    await bot.ban_chat_member(chat_id=config.tg_bot.GROUP_ID, user_id=6247356284)


@router.message(Command(commands=["unban"]))
async def process_start_command(message: Message, state: FSMContext, bot: Bot):
    await bot.unban_chat_member(chat_id=config.tg_bot.GROUP_ID, user_id=6247356284)


