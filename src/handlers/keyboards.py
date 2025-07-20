#!/usr/bin/env python3
"""
Keyboards для Crypto Helper Bot (Новая логика)
Клавиатуры для пошагового флоу обмена валют
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .fsm_states import Currency, SUPPORTED_SOURCES, get_available_targets


def create_source_currency_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру для выбора исходной валюты"""
    builder = InlineKeyboardBuilder()
    
    for currency in SUPPORTED_SOURCES:
        text = ("🟢 RUB (Рубли)" if currency == Currency.RUB 
                else "🔶 USDT (Tether)")
        builder.button(
            text=text,
            callback_data=f"source_{currency.value}"
        )
    
    builder.button(
        text="❌ Отмена",
        callback_data="cancel_exchange"
    )
    
    # Размещаем кнопки в столбец
    builder.adjust(1)
    return builder.as_markup()


def create_target_currency_keyboard(
    source_currency: Currency
) -> InlineKeyboardMarkup:
    """Создать клавиатуру для выбора целевой валюты"""
    builder = InlineKeyboardBuilder()
    
    available_targets = get_available_targets(source_currency)
    
    for currency in available_targets:
        if currency == Currency.RUB:
            text = "🟢 RUB (Рубли)"
        elif currency == Currency.USDT:
            text = "🔶 USDT (Tether)"
        elif currency == Currency.USD:
            text = "💵 USD (Доллары)"
        elif currency == Currency.EUR:
            text = "💶 EUR (Евро)"
        else:
            text = currency.value
            
        builder.button(
            text=text,
            callback_data=f"target_{currency.value}"
        )
    
    builder.button(
        text="⬅️ Назад",
        callback_data="back_to_source"
    )
    builder.button(
        text="❌ Отмена",
        callback_data="cancel_exchange"
    )
    
    # Размещаем целевые валюты в столбец, управляющие кнопки в ряд
    builder.adjust(1, 2)
    return builder.as_markup()


def create_margin_input_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру для ввода наценки с предустановленными значениями"""
    builder = InlineKeyboardBuilder()
    
    # Быстрые кнопки с популярными значениями наценки
    preset_margins = ["0.5", "1.0", "1.5", "2.0", "2.5", "3.0"]
    
    for margin in preset_margins:
        builder.button(
            text=f"{margin}%",
            callback_data=f"margin_{margin}"
        )
    
    builder.button(
        text="⬅️ Назад",
        callback_data="back_to_target"
    )
    builder.button(
        text="❌ Отмена",
        callback_data="cancel_exchange"
    )
    
    # Размещаем по 3 кнопки наценки в ряд
    builder.adjust(3, 3, 2)
    return builder.as_markup()


def create_amount_input_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру для ввода суммы с предустановленными значениями"""
    builder = InlineKeyboardBuilder()
    
    # Быстрые кнопки с популярными суммами
    preset_amounts = ["1000", "5000", "10000", "50000", "100000", "500000"]
    
    for amount in preset_amounts:
        # Форматируем сумму для отображения
        formatted_amount = f"{int(amount):,}".replace(",", " ")
        builder.button(
            text=formatted_amount,
            callback_data=f"amount_{amount}"
        )
    
    builder.button(
        text="⬅️ Назад",
        callback_data="back_to_margin"
    )
    builder.button(
        text="❌ Отмена",
        callback_data="cancel_exchange"
    )
    
    # Размещаем по 3 кнопки сумм в ряд
    builder.adjust(3, 3, 2)
    return builder.as_markup()


def create_result_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру для результата расчета"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="🔄 Новая сделка",
        callback_data="new_exchange"
    )
    builder.button(
        text="📋 Главное меню",
        callback_data="main_menu"
    )
    
    builder.adjust(2)
    return builder.as_markup()


# Для обратной совместимости (временно)
def create_currency_pairs_keyboard() -> InlineKeyboardMarkup:
    """DEPRECATED: Используйте create_source_currency_keyboard()"""
    return create_source_currency_keyboard()


def create_amount_selection_keyboard() -> InlineKeyboardMarkup:
    """DEPRECATED: Используйте create_amount_input_keyboard()"""
    return create_amount_input_keyboard()


def create_margin_selection_keyboard() -> InlineKeyboardMarkup:
    """DEPRECATED: Используйте create_margin_input_keyboard()"""
    return create_margin_input_keyboard()


class KeyboardBuilder:
    """DEPRECATED: Используйте функции создания клавиатур напрямую"""
    
    @staticmethod
    def source_currency():
        return create_source_currency_keyboard()
    
    @staticmethod
    def target_currency(source: Currency):
        return create_target_currency_keyboard(source) 