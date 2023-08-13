from aiogram.types import KeyboardButton, ReplyKeyboardMarkup,\
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


kb1 = {
    'Оплатить': 'pay',
    'Проверить подписку': 'check_expire',
    'Демо доступ': 'demo',
    'Реферальная программа': 'ref',
}


def custom_kb(width: int, buttons_dict: dict) -> InlineKeyboardMarkup:
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons = []
    for key, val in buttons_dict.items():
        callback_button = InlineKeyboardButton(
            text=key,
            callback_data=val)
        buttons.append(callback_button)
    kb_builder.row(*buttons, width=width)
    return kb_builder.as_markup()


start_kb = custom_kb(1, kb1)

pay_kb1_btn = {
    '30 дней': 'pay_30',
    '90 дней': 'pay_90',
    '180 дней': 'pay_180',
    'Отменить': 'cancel'
}

pay_kb1 = custom_kb(1, pay_kb1_btn)

pay_kb2_btn = {
    'Я оплатил, проверить': 'check_pay',
    'Отменить': 'cancel'
}
pay_kb2 = custom_kb(1, pay_kb2_btn)

ref_kb_btn = {
    'Пригласить реферала': 'ref_link',
    'Баланс': 'ref_balance',
    # 'Список рефералов': 'ref_list',
}
ref_kb = custom_kb(1, ref_kb_btn)