#!/usr/bin/env python3
"""
Модуль клавиатур для Crypto Helper Bot
Содержит функции для создания inline клавиатур
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .currency_pairs import get_all_currency_pairs


class KeyboardBuilder:
    """Класс для создания клавиатур бота"""
    
    @staticmethod
    def create_currency_pairs_keyboard() -> InlineKeyboardMarkup:
        """
        Создание упрощенной клавиатуры выбора валютных пар
        
        Returns:
            InlineKeyboardMarkup: Клавиатура с валютными парами
        """
        currency_pairs = get_all_currency_pairs()
        keyboard = []
        
        # Создаем кнопки для валютных пар по 2 в ряд
        pair_items = list(currency_pairs.items())
        for i in range(0, len(pair_items), 2):
            row = []
            for j in range(2):
                if i + j < len(pair_items):
                    callback, pair_info = pair_items[i + j]
                    button_text = f"{pair_info['emoji']} {pair_info['name']}"
                    row.append(InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"pair_{callback}"
                    ))
            keyboard.append(row)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def create_amount_input_keyboard() -> InlineKeyboardMarkup:
        """
        Создание простой клавиатуры для ввода суммы
        
        Returns:
            InlineKeyboardMarkup: Клавиатура управления
        """
        keyboard = [
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_amount"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def create_margin_input_keyboard() -> InlineKeyboardMarkup:
        """
        Создание простой клавиатуры для ввода наценки
        
        Returns:
            InlineKeyboardMarkup: Клавиатура управления
        """
        keyboard = [
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_margin"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def create_result_keyboard() -> InlineKeyboardMarkup:
        """
        Создание клавиатуры для результата расчета
        
        Returns:
            InlineKeyboardMarkup: Клавиатура с действиями
        """
        keyboard = [
            [
                InlineKeyboardButton(text="🔄 Пересчитать", callback_data="recalculate_margin"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_currency_pairs_keyboard() -> InlineKeyboardMarkup:
    """
    Функция-обертка для создания клавиатуры валютных пар
    (для обратной совместимости)
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с валютными парами
    """
    return KeyboardBuilder.create_currency_pairs_keyboard()


def create_amount_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Функция-обертка для создания клавиатуры ввода суммы
    (для обратной совместимости)
    
    Returns:
        InlineKeyboardMarkup: Клавиатура управления
    """
    return KeyboardBuilder.create_amount_input_keyboard()


def create_margin_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Функция-обертка для создания клавиатуры ввода наценки
    (для обратной совместимости)
    
    Returns:
        InlineKeyboardMarkup: Клавиатура управления
    """
    return KeyboardBuilder.create_margin_input_keyboard()


def create_result_keyboard() -> InlineKeyboardMarkup:
    """
    Функция-обертка для создания клавиатуры результата
    (для обратной совместимости)
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с действиями
    """
    return KeyboardBuilder.create_result_keyboard()