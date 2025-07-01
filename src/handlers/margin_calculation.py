#!/usr/bin/env python3
"""
Обработчики расчета курса с наценкой для Crypto Helper Bot
Включает FSM для управления диалогом с пользователем
"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

try:
    from ..config import config
    from ..utils.logger import get_bot_logger
    from ..services.api_service import api_service, ExchangeRate, RapiraAPIError
    from .admin_handlers import CURRENCY_PAIRS, get_currency_pair_info
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config
    from utils.logger import get_bot_logger
    from services.api_service import api_service, ExchangeRate, RapiraAPIError
    from handlers.admin_handlers import CURRENCY_PAIRS, get_currency_pair_info

# Initialize logger
logger = get_bot_logger()

# Create router for margin calculation handlers
margin_router = Router()


class MarginCalculationForm(StatesGroup):
    """FSM состояния для расчета курса с наценкой"""
    waiting_for_amount = State()
    waiting_for_margin = State()
    showing_result = State()


class MarginCalculationError(Exception):
    """Исключение для ошибок расчета наценки"""
    pass


class AmountValidator:
    """Класс для валидации суммы расчета"""
    
    @staticmethod
    def validate_amount(amount_text: str) -> Decimal:
        """
        Строгая валидация и преобразование суммы для расчета
        Принимает только числовые значения (int или float)
        
        Args:
            amount_text: Текст с суммой
            
        Returns:
            Decimal: Валидная сумма
            
        Raises:
            MarginCalculationError: При некорректной сумме
        """
        try:
            # Удаляем только пробелы и заменяем запятую на точку
            clean_text = amount_text.strip().replace(',', '.')
            
            # Проверяем, что строка содержит только цифры, точку и знак минуса
            if not clean_text.replace('.', '').replace('-', '').isdigit():
                # Проверяем наличие недопустимых символов
                invalid_chars = []
                for char in clean_text:
                    if not (char.isdigit() or char in ['.', '-']):
                        invalid_chars.append(char)
                
                if invalid_chars:
                    raise MarginCalculationError(
                        f"Недопустимые символы: {', '.join(set(invalid_chars))}. "
                        f"Используйте только числа, например: 1000, 500.50, 1250"
                    )
            
            # Проверяем, что есть хотя бы одна цифра
            if not any(char.isdigit() for char in clean_text):
                raise MarginCalculationError(
                    "Введите числовое значение, например: 1000, 500.50, 1250"
                )
            
            # Проверяем количество точек (не больше одной)
            if clean_text.count('.') > 1:
                raise MarginCalculationError(
                    "Неверный формат числа. Используйте только одну точку для десятичной дроби"
                )
            
            # Преобразуем в Decimal для точных вычислений
            amount = Decimal(clean_text)
            
            # Проверяем диапазон (от 0.01 до 1,000,000,000)
            if amount <= 0:
                raise MarginCalculationError(
                    "Сумма должна быть больше нуля"
                )
            
            if amount > Decimal('1000000000'):
                raise MarginCalculationError(
                    "Сумма слишком большая (максимум: 1,000,000,000)"
                )
            
            if amount < Decimal('0.01'):
                raise MarginCalculationError(
                    "Минимальная сумма: 0.01"
                )
            
            return amount
            
        except (InvalidOperation, ValueError) as e:
            raise MarginCalculationError(
                "Некорректный формат суммы. Используйте только числовые значения, например: 1000, 500.50, 1250"
            )
    
    @staticmethod
    def validate_margin(margin_text: str) -> Decimal:
        """
        Строгая валидация и преобразование процентной наценки
        Принимает только числовые значения (int или float)
        
        Args:
            margin_text: Текст с процентной наценкой
            
        Returns:
            Decimal: Валидная процентная наценка
            
        Raises:
            MarginCalculationError: При некорректной наценке
        """
        try:
            # Удаляем пробелы и знак процента, заменяем запятую на точку
            clean_text = margin_text.strip().replace('%', '').replace(',', '.')
            
            # Проверяем, что строка содержит только цифры, точку и знак минуса
            if not clean_text.replace('.', '').replace('-', '').replace('+', '').isdigit():
                # Проверяем наличие недопустимых символов
                invalid_chars = []
                for char in clean_text:
                    if not (char.isdigit() or char in ['.', '-', '+']):
                        invalid_chars.append(char)
                
                if invalid_chars:
                    raise MarginCalculationError(
                        f"Недопустимые символы: {', '.join(set(invalid_chars))}. "
                        f"Используйте только числа, например: 5, 2.5, -1.2"
                    )
            
            # Проверяем, что есть хотя бы одна цифра
            if not any(char.isdigit() for char in clean_text):
                raise MarginCalculationError(
                    "Введите числовое значение, например: 5, 2.5, -1.2"
                )
            
            # Проверяем количество точек (не больше одной)
            if clean_text.count('.') > 1:
                raise MarginCalculationError(
                    "Неверный формат числа. Используйте только одну точку для десятичной дроби"
                )
            
            # Проверяем знаки + и - (только в начале)
            if '+' in clean_text[1:] or '-' in clean_text[1:]:
                raise MarginCalculationError(
                    "Знак '+' или '-' может быть только в начале числа"
                )
            
            # Преобразуем в Decimal для точных вычислений
            margin = Decimal(clean_text)
            
            # Проверяем диапазон (от -100% до +1000%)
            if margin < -100:
                raise MarginCalculationError(
                    "Наценка не может быть меньше -100% (это означало бы отрицательную цену)"
                )
            
            if margin > 1000:
                raise MarginCalculationError(
                    "Наценка не может быть больше 1000% (слишком высокая наценка)"
                )
            
            return margin
            
        except (InvalidOperation, ValueError) as e:
            raise MarginCalculationError(
                "Некорректный формат наценки. Используйте только числовые значения, например: 5, 2.5, -1.2"
            )
    
    @staticmethod
    def calculate_final_rate(base_rate: Decimal, margin_percent: Decimal) -> Decimal:
        """
        Расчет итогового курса с наценкой
        
        Args:
            base_rate: Базовый курс
            margin_percent: Процентная наценка
            
        Returns:
            Decimal: Итоговый курс с наценкой
        """
        # Формула: итоговый_курс = базовый_курс * (1 + наценка/100)
        margin_multiplier = Decimal('1') + (margin_percent / Decimal('100'))
        final_rate = base_rate * margin_multiplier
        
        # Округляем до 8 знаков после запятой (стандарт для криптовалют)
        return final_rate.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def format_currency_value(value: Decimal, currency: str) -> str:
        """
        Форматирование значения валюты для отображения
        
        Args:
            value: Значение для форматирования
            currency: Код валюты
            
        Returns:
            str: Отформатированное значение
        """
        # Определяем количество знаков после запятой в зависимости от валюты
        if currency in ['BTC', 'ETH']:
            # Для основных криптовалют - больше знаков
            return f"{value:.8f}"
        elif currency in ['USDT', 'USDC', 'DAI']:
            # Для стейблкоинов - меньше знаков
            return f"{value:.4f}"
        elif currency in ['RUB', 'USD', 'EUR']:
            # Для фиатных валют - 2 знака
            return f"{value:.2f}"
        else:
            # Для остальных - автоматическое определение
            if value >= 1:
                return f"{value:.4f}"
            else:
                return f"{value:.8f}"
    
    @staticmethod
    def format_amount_display(amount: Decimal, currency: str) -> str:
        """
        Форматирование суммы для отображения
        
        Args:
            amount: Сумма для форматирования
            currency: Код валюты
            
        Returns:
            str: Отформатированная сумма
        """
        # Определяем количество знаков после запятой в зависимости от валюты
        if currency in ['BTC', 'ETH']:
            # Для основных криптовалют - больше знаков
            return f"{amount:.8f}"
        elif currency in ['USDT', 'USDC', 'DAI']:
            # Для стейблкоинов - меньше знаков
            return f"{amount:.4f}"
        elif currency in ['RUB', 'USD', 'EUR']:
            # Для фиатных валют - 2 знака
            return f"{amount:.2f}"
        else:
            # Для остальных - автоматическое определение
            if amount >= 1:
                return f"{amount:.4f}"
            else:
                return f"{amount:.8f}"


async def start_margin_calculation(
    callback_query: CallbackQuery,
    pair_callback: str,
    state: FSMContext
) -> None:
    """
    Начало процесса расчета курса с наценкой
    Теперь сначала спрашиваем сумму для расчета
    
    Args:
        callback_query: Callback query от пользователя
        pair_callback: Callback данные валютной пары
        state: FSM контекст
    """
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "N/A"
    
    logger.info(
        f"Начало расчета с наценкой: "
        f"user_id={user_id}, username=@{username}, pair={pair_callback}"
    )
    
    # Получаем информацию о валютной паре
    pair_info = get_currency_pair_info(pair_callback)
    if not pair_info:
        await callback_query.answer(
            "❌ Ошибка: информация о валютной паре не найдена",
            show_alert=True
        )
        return
    
    try:
        # Сохраняем данные в FSM (пока без курса)
        await state.update_data(
            pair_callback=pair_callback,
            pair_info=pair_info
        )
        
        # Переходим в состояние ожидания суммы
        await state.set_state(MarginCalculationForm.waiting_for_amount)
        
        # Создаем клавиатуру с предустановленными суммами
        keyboard = create_amount_selection_keyboard()
        
        # Формируем сообщение с запросом суммы
        message_text = (
            f"💱 <b>Расчет курса с наценкой</b>\n\n"
            f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n"
            f"📝 <i>{pair_info['description']}</i>\n\n"
            f"💰 <b>Укажите сумму для расчета:</b>\n\n"
            f"• Выберите из предложенных вариантов ниже\n"
            f"• Или введите свое значение (например: 1000, 5000, 250.50)\n"
            f"• Можно указывать сумму в {pair_info['base']}\n\n"
            f"💡 <i>Диапазон: от 0.01 до 1,000,000,000</i>"
        )
        
        await callback_query.message.edit_text(
            message_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        await callback_query.answer("Укажите сумму для расчета")
        
        logger.info(
            f"Запрос суммы отправлен: "
            f"user_id={user_id}, pair={pair_info['name']}"
        )
        
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ <b>Произошла ошибка</b>\n\n"
            f"Не удалось начать расчет.\n"
            f"Попробуйте позже.\n\n"
            f"🏠 Используйте /admin_bot для возврата к главному меню.",
            parse_mode='HTML'
        )
        
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)
        await state.clear()
        
        logger.error(f"Неожиданная ошибка при начале расчета: {e}")


def create_amount_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Создание простой клавиатуры для ввода суммы (без готовых кнопок)
    
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


def create_margin_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Создание простой клавиатуры для ввода наценки (без готовых кнопок)
    
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





@margin_router.callback_query(lambda c: c.data == 'cancel_amount')
async def handle_cancel_amount(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик отмены выбора суммы
    """
    await state.clear()
    
    await callback_query.message.edit_text(
        "❌ <b>Расчет отменен</b>\n\n"
        "Операция была отменена пользователем.\n\n"
        "🏠 Используйте /admin_bot для возврата к главному меню.",
        parse_mode='HTML'
    )
    
    await callback_query.answer("Операция отменена")
    logger.info(f"Пользователь {callback_query.from_user.id} отменил выбор суммы")





@margin_router.message(MarginCalculationForm.waiting_for_amount, F.text)
async def handle_amount_text_input(message: Message, state: FSMContext):
    """
    Обработчик текстового ввода суммы
    """
    try:
        # Валидируем введенную сумму
        amount = AmountValidator.validate_amount(message.text)
        
        # Обрабатываем сумму
        await process_amount_input(message, amount, state)
        
    except MarginCalculationError as e:
        await message.reply(
            f"❌ <b>Ошибка ввода суммы</b>\n\n"
            f"{str(e)}\n\n"
            f"💡 <b>Примеры корректного ввода:</b>\n"
            f"• <code>1000</code> (1000 единиц)\n"
            f"• <code>500.50</code> (500.50 единиц)\n"
            f"• <code>25000</code> (25000 единиц)\n"
            f"• <code>100</code> (100 единиц)\n\n"
            f"🔢 <b>Диапазон:</b> от 0.01 до 1,000,000,000",
            parse_mode='HTML'
        )
    except Exception as e:
        await message.reply(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось обработать введенную сумму.\n"
            "Попробуйте еще раз.",
            parse_mode='HTML'
        )
        logger.error(f"Ошибка при обработке текстового ввода суммы: {e}")


async def process_amount_input(
    message: Message,
    amount: Decimal,
    state: FSMContext,
    from_callback: bool = False
) -> None:
    """
    Обработка введенной суммы и переход к вводу наценки
    
    Args:
        message: Сообщение пользователя
        amount: Валидированная сумма
        state: FSM контекст
        from_callback: Флаг, что вызов из callback
    """
    try:
        # Получаем сохраненные данные
        data = await state.get_data()
        pair_info = data.get('pair_info')
        
        if not pair_info:
            raise MarginCalculationError("Данные о валютной паре потеряны, начните заново")
        
        # Получаем текущий курс для валютной пары
        async with api_service:
            exchange_rate = await api_service.get_exchange_rate(pair_info['name'])
            
        if not exchange_rate:
            raise RapiraAPIError("Не удалось получить курс валютной пары")
        
        # Сохраняем данные в FSM
        await state.update_data(
            calculation_amount=float(amount),
            exchange_rate=exchange_rate.to_dict(),
            base_rate=float(exchange_rate.rate)
        )
        
        # Переходим в состояние ожидания наценки (ИСПРАВЛЕНО)
        await state.set_state(MarginCalculationForm.waiting_for_margin)
        
        # Создаем клавиатуру для выбора наценки
        keyboard = create_margin_selection_keyboard()
        
        # Отображаем сумму в зависимости от валюты
        amount_display = AmountValidator.format_amount_display(amount, pair_info['base'])
        
        # Формируем сообщение с запросом наценки
        message_text = (
            f"💱 <b>Расчет курса с наценкой</b>\n\n"
            f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n"
            f"📝 <i>{pair_info['description']}</i>\n\n"
            f"💰 <b>Сумма расчета:</b> <code>{amount_display}</code> {pair_info['base']}\n"
            f"💹 <b>Текущий курс:</b> <code>{exchange_rate.rate:.8f}</code> {pair_info['quote']}\n"
            f"🕐 <b>Время получения:</b> {exchange_rate.timestamp[:19].replace('T', ' ')}\n"
            f"📊 <b>Источник:</b> {exchange_rate.source}\n\n"
            f"📈 <b>Укажите процентную наценку:</b>\n\n"
            f"• Введите числовое значение (например: 5, 2.5, -1.2)\n"
            f"• Положительные значения увеличивают курс\n"
            f"• Отрицательные значения уменьшают курс\n\n"
            f"💡 <i>Диапазон: от -100% до +1000%</i>"
        )
        
        if from_callback:
            # Если вызов из callback, редактируем сообщение
            await message.edit_text(
                message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            # Если вызов из текстового сообщения, отправляем новое
            await message.answer(
                message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        
        logger.info(
            f"Переход к выбору наценки: "
            f"user_id={message.from_user.id}, "
            f"pair={pair_info['name']}, "
            f"amount={amount_display} {pair_info['base']}, "
            f"rate={exchange_rate.rate}"
        )
        
    except RapiraAPIError as e:
        error_message = (
            f"❌ <b>Ошибка получения курса</b>\n\n"
            f"Не удалось получить текущий курс валютной пары:\n"
            f"<code>{str(e)}</code>\n\n"
            f"🔄 Попробуйте позже или обратитесь к администратору.\n\n"
            f"🏠 Используйте /admin_bot для возврата к главному меню."
        )
        
        if from_callback:
            await message.edit_text(error_message, parse_mode='HTML')
        else:
            await message.answer(error_message, parse_mode='HTML')
        
        await state.clear()
        logger.error(f"Ошибка получения курса: {e}")
    
    except Exception as e:
        error_message = (
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось обработать сумму.\n"
            "Попробуйте начать заново.\n\n"
            "🏠 Используйте /admin_bot для возврата к главному меню."
        )
        
        if from_callback:
            await message.edit_text(error_message, parse_mode='HTML')
        else:
            await message.answer(error_message, parse_mode='HTML')
        
        await state.clear()
        logger.error(f"Ошибка при обработке суммы: {e}")





@margin_router.callback_query(lambda c: c.data == 'cancel_margin')
async def handle_cancel_margin(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик отмены расчета наценки
    """
    await state.clear()
    
    await callback_query.message.edit_text(
        "❌ <b>Расчет наценки отменен</b>\n\n"
        "Операция была отменена пользователем.\n\n"
        "🏠 Используйте /admin_bot для возврата к главному меню.",
        parse_mode='HTML'
    )
    
    await callback_query.answer("Операция отменена")
    logger.info(f"Пользователь {callback_query.from_user.id} отменил расчет наценки")


@margin_router.callback_query(lambda c: c.data == 'back_to_main')
async def handle_back_to_main(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик возврата к главному меню
    """
    await state.clear()
    
    # Импортируем функцию создания клавиатуры из admin_handlers
    from .admin_handlers import create_currency_pairs_keyboard
    
    keyboard = create_currency_pairs_keyboard()
    
    admin_message = (
        "🔧 <b>Административная панель</b>\n\n"
        "Добро пожаловать в панель управления Crypto Helper Bot!\n\n"
        "📊 <b>Выберите валютную пару для получения курса:</b>\n\n"
        "• Выберите нужную валютную пару из списка ниже\n"
        "• Укажите процентную наценку\n"
        "• Получите актуальный курс с наценкой\n\n"
        "💡 <i>Курсы обновляются в реальном времени через Rapira API</i>"
    )
    
    await callback_query.message.edit_text(
        admin_message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    await callback_query.answer("Возврат к главному меню")





@margin_router.message(MarginCalculationForm.waiting_for_margin, F.text)
async def handle_margin_text_input(message: Message, state: FSMContext):
    """
    Обработчик текстового ввода процентной наценки
    """
    try:
        # Валидируем введенную наценку
        margin = AmountValidator.validate_margin(message.text)
        
        # Обрабатываем наценку
        await process_margin_input(message, margin, state)
        
    except MarginCalculationError as e:
        await message.reply(
            f"❌ <b>Ошибка ввода наценки</b>\n\n"
            f"{str(e)}\n\n"
            f"💡 <b>Примеры корректного ввода:</b>\n"
            f"• <code>5</code> (5% наценка)\n"
            f"• <code>2.5</code> (2.5% наценка)\n"
            f"• <code>-1.2</code> (-1.2% скидка)\n"
            f"• <code>0</code> (без наценки)\n\n"
            f"🔢 <b>Диапазон:</b> от -100% до +1000%",
            parse_mode='HTML'
        )
    except Exception as e:
        await message.reply(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось обработать введенную наценку.\n"
            "Попробуйте еще раз.",
            parse_mode='HTML'
        )
        logger.error(f"Ошибка при обработке текстового ввода наценки: {e}")


async def process_margin_input(
    message: Message,
    margin: Decimal,
    state: FSMContext,
    from_callback: bool = False
) -> None:
    """
    Обработка введенной наценки и расчет итогового курса
    
    Args:
        message: Сообщение пользователя
        margin: Валидированная наценка
        state: FSM контекст
        from_callback: Флаг, что вызов из callback
    """
    try:
        # Получаем сохраненные данные
        data = await state.get_data()
        pair_info = data.get('pair_info')
        base_rate = Decimal(str(data.get('base_rate')))
        exchange_rate_data = data.get('exchange_rate')
        calculation_amount = data.get('calculation_amount')
        
        if not all([pair_info, base_rate, exchange_rate_data, calculation_amount]):
            raise MarginCalculationError("Данные расчета потеряны, начните заново")
        
        # Рассчитываем итоговый курс
        final_rate = AmountValidator.calculate_final_rate(base_rate, margin)
        
        # Рассчитываем абсолютное изменение
        rate_change = final_rate - base_rate
        
        # Сохраняем результаты расчета
        await state.update_data(
            margin_percent=float(margin),
            final_rate=float(final_rate),
            rate_change=float(rate_change)
        )
        
        # Переходим в состояние показа результата
        await state.set_state(MarginCalculationForm.showing_result)
        
        # Форматируем результат
        result_message = format_calculation_result(
            pair_info=pair_info,
            base_rate=base_rate,
            margin=margin,
            final_rate=final_rate,
            rate_change=rate_change,
            exchange_rate_data=exchange_rate_data,
            calculation_amount=Decimal(str(calculation_amount))
        )
        
        # Создаем клавиатуру для результата
        result_keyboard = create_result_keyboard()
        
        if from_callback:
            # Если вызов из callback, редактируем сообщение
            await message.edit_text(
                result_message,
                parse_mode='HTML',
                reply_markup=result_keyboard
            )
        else:
            # Если вызов из текстового сообщения, отправляем новое
            await message.answer(
                result_message,
                parse_mode='HTML',
                reply_markup=result_keyboard
            )
        
        logger.info(
            f"Расчет наценки завершен: "
            f"user_id={message.from_user.id}, "
            f"pair={pair_info['name']}, "
            f"margin={margin}%, "
            f"base_rate={base_rate}, "
            f"final_rate={final_rate}"
        )
        
    except Exception as e:
        error_message = (
            "❌ <b>Ошибка расчета</b>\n\n"
            "Не удалось рассчитать курс с наценкой.\n"
            "Попробуйте начать заново.\n\n"
            "🏠 Используйте /admin_bot для возврата к главному меню."
        )
        
        if from_callback:
            await message.edit_text(error_message, parse_mode='HTML')
        else:
            await message.answer(error_message, parse_mode='HTML')
        
        await state.clear()
        logger.error(f"Ошибка при обработке наценки: {e}")


def format_calculation_result(
    pair_info: Dict[str, Any],
    base_rate: Decimal,
    margin: Decimal,
    final_rate: Decimal,
    rate_change: Decimal,
    exchange_rate_data: Dict[str, Any],
    calculation_amount: Decimal
) -> str:
    """
    Форматирование результата расчета для отображения
    
    Args:
        pair_info: Информация о валютной паре
        base_rate: Базовый курс
        margin: Процентная наценка
        final_rate: Итоговый курс
        rate_change: Изменение курса
        exchange_rate_data: Данные о курсе
        calculation_amount: Сумма для расчета
        
    Returns:
        str: Отформатированный результат
    """
    # Определяем валюты
    base_currency = pair_info['base']
    quote_currency = pair_info['quote']
    
    # Форматируем значения
    base_rate_str = AmountValidator.format_currency_value(base_rate, quote_currency)
    final_rate_str = AmountValidator.format_currency_value(final_rate, quote_currency)
    rate_change_str = AmountValidator.format_currency_value(abs(rate_change), quote_currency)
    amount_display = AmountValidator.format_amount_display(calculation_amount, base_currency)
    
    # Рассчитываем суммы в целевой валюте
    amount_base_rate = calculation_amount * base_rate
    amount_final_rate = calculation_amount * final_rate
    amount_difference = amount_final_rate - amount_base_rate
    
    # Форматируем суммы
    amount_base_str = AmountValidator.format_currency_value(amount_base_rate, quote_currency)
    amount_final_str = AmountValidator.format_currency_value(amount_final_rate, quote_currency)
    amount_diff_str = AmountValidator.format_currency_value(abs(amount_difference), quote_currency)
    
    # Определяем знак изменения
    change_sign = "+" if rate_change >= 0 else "-"
    amount_change_sign = "+" if amount_difference >= 0 else "-"
    change_emoji = "📈" if rate_change >= 0 else "📉"
    
    # Определяем цвет для наценки
    margin_emoji = "📈" if margin >= 0 else "📉"
    margin_sign = "+" if margin >= 0 else ""
    
    # Временная метка
    timestamp = exchange_rate_data.get('timestamp', '')[:19].replace('T', ' ')
    
    result_message = (
        f"✅ <b>Расчет курса завершен</b>\n\n"
        f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n"
        f"📝 <i>{pair_info['description']}</i>\n\n"
        
        f"💰 <b>Сумма расчета:</b> <code>{amount_display}</code> {base_currency}\n"
        f"💹 <b>Базовый курс:</b> <code>{base_rate_str}</code> {quote_currency}\n"
        f"{margin_emoji} <b>Наценка:</b> <code>{margin_sign}{margin}%</code>\n"
        f"💎 <b>Итоговый курс:</b> <code>{final_rate_str}</code> {quote_currency}\n\n"
        
        f"📊 <b>Расчет сумм:</b>\n"
        f"• По базовому курсу: <code>{amount_base_str}</code> {quote_currency}\n"
        f"• По итоговому курсу: <code>{amount_final_str}</code> {quote_currency}\n"
        f"{change_emoji} • Разница: <code>{amount_change_sign}{amount_diff_str}</code> {quote_currency}\n\n"
        
        f"🔢 <b>Детали расчета:</b>\n"
        f"• Курс: {base_rate_str} {quote_currency} пер 1 {base_currency}\n"
        f"• Наценка: {margin_sign}{margin}% (множитель: {1 + margin/100:.6f})\n"
        f"• Итоговый курс: {base_rate_str} × {1 + margin/100:.6f} = {final_rate_str}\n"
        f"• Расчет: {amount_display} × {final_rate_str} = {amount_final_str}\n\n"
        
        f"🕐 <b>Время получения курса:</b> {timestamp}\n"
        f"📡 <b>Источник:</b> {exchange_rate_data.get('source', 'N/A')}\n\n"
        f"💡 <i>Используйте кнопки ниже для публикации или копирования</i>"
    )
    
    return result_message


def create_result_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для результата расчета
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с действиями
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📤 Опубликовать в канал", callback_data="publish_result"),
            InlineKeyboardButton(text="🔄 Пересчитать", callback_data="recalculate_margin")
        ],
        [
            InlineKeyboardButton(text="📋 Копировать результат", callback_data="copy_result"),
            InlineKeyboardButton(text="📊 Новая пара", callback_data="back_to_main")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@margin_router.callback_query(lambda c: c.data == 'publish_result', MarginCalculationForm.showing_result)
async def handle_publish_result(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик публикации результата в канал
    """
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "N/A"
    full_name = callback_query.from_user.full_name or "Менеджер"
    
    logger.info(f"Запрос публикации от пользователя {user_id} (@{username})")
    
    try:
        # Получаем данные расчета
        data = await state.get_data()
        pair_info = data.get('pair_info')
        base_rate = Decimal(str(data.get('base_rate')))
        margin = Decimal(str(data.get('margin_percent')))
        final_rate = Decimal(str(data.get('final_rate')))
        rate_change = Decimal(str(data.get('rate_change')))
        exchange_rate_data = data.get('exchange_rate')
        
        if not all([pair_info, base_rate, margin, final_rate, exchange_rate_data]):
            raise MarginCalculationError("Данные расчета потеряны")
        
        # Импортируем модуль публикации
        from .channel_publisher import ChannelPublisher
        
        # Определяем режим работы и ID канала
        development_mode = config.DEBUG_MODE or not config.ADMIN_CHANNEL_ID
        channel_id = config.ADMIN_CHANNEL_ID if not development_mode else None
        
        # Получаем бота из callback_query
        bot = callback_query.bot
        
        # Публикуем результат
        publish_result = await ChannelPublisher.publish_result(
            bot=bot,
            pair_info=pair_info,
            base_rate=base_rate,
            margin=margin,
            final_rate=final_rate,
            rate_change=rate_change,
            exchange_rate_data=exchange_rate_data,
            manager_name=full_name,
            user_id=user_id,
            channel_id=channel_id,
            development_mode=development_mode,
            calculation_amount=Decimal(str(data.get('calculation_amount')))
        )
        
        if publish_result['success']:
            # Успешная публикация
            success_message = (
                f"✅ <b>Публикация завершена</b>\n\n"
                f"{publish_result['message']}\n\n"
                f"📊 <b>Опубликованные данные:</b>\n"
                f"• Валютная пара: {pair_info['name']}\n"
                f"• Итоговый курс: {final_rate:.8f} {pair_info['quote']}\n"
                f"• Наценка: {margin:+.2f}%\n"
                f"• Менеджер: {full_name}\n\n"
                f"🎯 <b>Цель:</b> {publish_result['target']}\n\n"
                f"💡 <i>Для новой публикации используйте /admin_bot</i>"
            )
            
            await callback_query.message.edit_text(
                success_message,
                parse_mode='HTML'
            )
            
            await callback_query.answer("✅ Результат опубликован")
            
        else:
            # Ошибка публикации
            error_message = (
                f"❌ <b>Ошибка публикации</b>\n\n"
                f"{publish_result['message']}\n\n"
                f"🔧 <b>Возможные решения:</b>\n"
                f"• Проверьте права бота в канале\n"
                f"• Убедитесь, что бот добавлен в канал\n"
                f"• Проверьте корректность ID канала\n\n"
                f"🏠 Используйте /admin_bot для возврата к главному меню"
            )
            
            await callback_query.message.edit_text(
                error_message,
                parse_mode='HTML'
            )
            
            await callback_query.answer("❌ Ошибка публикации", show_alert=True)
        
        logger.info(
            f"Публикация завершена: user_id={user_id}, "
            f"success={publish_result['success']}, target={publish_result['target']}"
        )
        
    except MarginCalculationError as e:
        await callback_query.message.edit_text(
            f"❌ <b>Ошибка данных</b>\n\n"
            f"{str(e)}\n\n"
            f"Начните расчет заново с команды /admin_bot",
            parse_mode='HTML'
        )
        
        await callback_query.answer("❌ Ошибка данных", show_alert=True)
        await state.clear()
        
        logger.error(f"Ошибка данных при публикации: {e}")
    
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ <b>Произошла ошибка</b>\n\n"
            f"Не удалось опубликовать результат.\n"
            f"Попробуйте позже.\n\n"
            f"🏠 Используйте /admin_bot для возврата к главному меню.",
            parse_mode='HTML'
        )
        
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)
        
        logger.error(f"Неожиданная ошибка при публикации: {e}")


@margin_router.callback_query(lambda c: c.data == 'recalculate_margin', MarginCalculationForm.showing_result)
async def handle_recalculate_margin(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик пересчета с новой наценкой
    """
    # Возвращаемся к состоянию ввода наценки
    await state.set_state(MarginCalculationForm.waiting_for_margin)
    
    # Получаем сохраненные данные
    data = await state.get_data()
    pair_info = data.get('pair_info')
    base_rate = data.get('base_rate')
    exchange_rate_data = data.get('exchange_rate')
    
    # Создаем клавиатуру для выбора наценки
    keyboard = create_margin_selection_keyboard()
    
    # Формируем сообщение
    message_text = (
        f"🔄 <b>Пересчет курса с наценкой</b>\n\n"
        f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n"
        f"📝 <i>{pair_info['description']}</i>\n\n"
        f"💰 <b>Текущий курс:</b> <code>{base_rate:.8f}</code>\n"
        f"🕐 <b>Время получения:</b> {exchange_rate_data.get('timestamp', '')[:19].replace('T', ' ')}\n\n"
        f"📈 <b>Укажите новую процентную наценку:</b>\n\n"
        f"• Выберите из предложенных вариантов ниже\n"
        f"• Или введите свое значение (например: 5, 2.5, -1.2)\n\n"
        f"💡 <i>Диапазон: от -100% до +1000%</i>"
    )
    
    await callback_query.message.edit_text(
        message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    await callback_query.answer("Введите новую наценку")


@margin_router.callback_query(lambda c: c.data == 'copy_result', MarginCalculationForm.showing_result)
async def handle_copy_result(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик копирования результата в текстовом формате
    """
    try:
        # Получаем данные расчета
        data = await state.get_data()
        pair_info = data.get('pair_info')
        base_rate = Decimal(str(data.get('base_rate')))
        margin = Decimal(str(data.get('margin_percent')))
        final_rate = Decimal(str(data.get('final_rate')))
        exchange_rate_data = data.get('exchange_rate')
        
        # Форматируем для копирования (простой текст)
        base_currency = pair_info['base']
        quote_currency = pair_info['quote']
        
        copy_text = (
            f"💱 {pair_info['name']}\n"
            f"📊 Базовый курс: {base_rate:.8f} {quote_currency}\n"
            f"📈 Наценка: {margin:+.2f}%\n"
            f"💎 Итоговый курс: {final_rate:.8f} {quote_currency}\n"
            f"🕐 {exchange_rate_data.get('timestamp', '')[:19].replace('T', ' ')}\n"
            f"📡 Источник: {exchange_rate_data.get('source', 'N/A')}"
        )
        
        # Отправляем текст для копирования
        await callback_query.message.reply(
            f"📋 <b>Результат для копирования:</b>\n\n"
            f"<code>{copy_text}</code>\n\n"
            f"💡 <i>Нажмите на текст выше для копирования</i>",
            parse_mode='HTML'
        )
        
        await callback_query.answer("Результат подготовлен для копирования")
        
    except Exception as e:
        await callback_query.answer("❌ Ошибка при подготовке результата", show_alert=True)
        logger.error(f"Ошибка при копировании результата: {e}")


# Обработчики для неожиданных сообщений в состояниях FSM
@margin_router.message(MarginCalculationForm.waiting_for_amount, ~F.text)
async def handle_unexpected_content_waiting_amount(message: Message, state: FSMContext):
    """
    Обработчик неожиданного контента в состоянии ожидания суммы
    """
    await message.reply(
        "❌ <b>Некорректный ввод</b>\n\n"
        "Пожалуйста, введите сумму для расчета в виде числа.\n\n"
        "💡 <b>Примеры:</b>\n"
        "• <code>1000</code> (1000 единиц)\n"
        "• <code>500.50</code> (500.50 единиц)\n"
        "• <code>25000</code> (25000 единиц)\n\n"
        "Или используйте кнопки выше для быстрого выбора.",
        parse_mode='HTML'
    )


@margin_router.message(MarginCalculationForm.waiting_for_margin, ~F.text)
async def handle_unexpected_content_waiting_margin(message: Message, state: FSMContext):
    """
    Обработчик неожиданного контента в состоянии ожидания наценки
    """
    await message.reply(
        "❌ <b>Некорректный ввод</b>\n\n"
        "Пожалуйста, введите процентную наценку в виде числа.\n\n"
        "💡 <b>Примеры:</b>\n"
        "• <code>5</code> (5% наценка)\n"
        "• <code>-2.5</code> (2.5% скидка)\n"
        "• <code>0</code> (без наценки)\n\n"
        "Или используйте кнопки выше для быстрого выбора.",
        parse_mode='HTML'
    )


@margin_router.message(MarginCalculationForm.showing_result)
async def handle_unexpected_message_showing_result(message: Message, state: FSMContext):
    """
    Обработчик неожиданных сообщений в состоянии показа результата
    """
    await message.reply(
        "💡 <b>Результат уже рассчитан</b>\n\n"
        "Используйте кнопки выше для:\n"
        "• Публикации результата в канал\n"
        "• Пересчета с новой наценкой\n"
        "• Копирования результата\n"
        "• Возврата к главному меню",
        parse_mode='HTML'
    )
    
    @staticmethod
    def format_amount_display(amount: Decimal, currency: str) -> str:
        """
        Форматирование суммы для отображения
        
        Args:
            amount: Сумма для форматирования
            currency: Код валюты
            
        Returns:
            str: Отформатированная сумма
        """
        # Определяем количество знаков после запятой в зависимости от валюты
        if currency in ['BTC', 'ETH']:
            # Для основных криптовалют - больше знаков
            return f"{amount:.8f}"
        elif currency in ['USDT', 'USDC', 'DAI']:
            # Для стейблкоинов - меньше знаков
            return f"{amount:.4f}"
        elif currency in ['RUB', 'USD', 'EUR']:
            # Для фиатных валют - 2 знака
            return f"{amount:.2f}"
        else:
            # Для остальных - автоматическое определение
            if amount >= 1:
                return f"{amount:.4f}"
            else:
                return f"{amount:.8f}"


class AmountValidator:
    """Класс для расчета курса с наценкой - правильное название"""
    
    @staticmethod
    def validate_margin(margin_text: str) -> Decimal:
        """
        Валидация и преобразование процентной наценки
        
        Args:
            margin_text: Текст с процентной наценкой
            
        Returns:
            Decimal: Валидная процентная наценка
            
        Raises:
            MarginCalculationError: При некорректной наценке
        """
        try:
            # Удаляем лишние символы и пробелы
            clean_text = margin_text.strip().replace('%', '').replace(',', '.')
            
            # Преобразуем в Decimal для точных вычислений
            margin = Decimal(clean_text)
            
            # Проверяем диапазон (от -100% до +1000%)
            if margin < -100:
                raise MarginCalculationError(
                    "Наценка не может быть меньше -100% (это означало бы отрицательную цену)"
                )
            
            if margin > 1000:
                raise MarginCalculationError(
                    "Наценка не может быть больше 1000% (слишком высокая наценка)"
                )
            
            return margin
            
        except (InvalidOperation, ValueError) as e:
            raise MarginCalculationError(
                f"Некорректный формат наценки. Используйте числовое значение, например: 5, 2.5, -1.2"
            )
    
    @staticmethod
    def calculate_final_rate(base_rate: Decimal, margin_percent: Decimal) -> Decimal:
        """
        Расчет итогового курса с наценкой
        
        Args:
            base_rate: Базовый курс
            margin_percent: Процентная наценка
            
        Returns:
            Decimal: Итоговый курс с наценкой
        """
        # Формула: итоговый_курс = базовый_курс * (1 + наценка/100)
        margin_multiplier = Decimal('1') + (margin_percent / Decimal('100'))
        final_rate = base_rate * margin_multiplier
        
        # Округляем до 8 знаков после запятой (стандарт для криптовалют)
        return final_rate.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def format_currency_value(value: Decimal, currency: str) -> str:
        """
        Форматирование значения валюты для отображения
        
        Args:
            value: Значение для форматирования
            currency: Код валюты
            
        Returns:
            str: Отформатированное значение
        """
        # Определяем количество знаков после запятой в зависимости от валюты
        if currency in ['BTC', 'ETH']:
            # Для основных криптовалют - больше знаков
            return f"{value:.8f}"
        elif currency in ['USDT', 'USDC', 'DAI']:
            # Для стейблкоинов - меньше знаков
            return f"{value:.4f}"
        elif currency in ['RUB', 'USD', 'EUR']:
            # Для фиатных валют - 2 знака
            return f"{value:.2f}"
        else:
            # Для остальных - автоматическое определение
            if value >= 1:
                return f"{value:.4f}"
            else:
                return f"{value:.8f}"


async def start_margin_calculation(
    callback_query: CallbackQuery,
    pair_callback: str,
    state: FSMContext
) -> None:
    """
    Начало процесса расчета курса с наценкой
    
    Args:
        callback_query: Callback query от пользователя
        pair_callback: Callback данные валютной пары
        state: FSM контекст
    """
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "N/A"
    
    logger.info(
        f"Начало расчета наценки: "
        f"user_id={user_id}, username=@{username}, pair={pair_callback}"
    )
    
    # Получаем информацию о валютной паре
    pair_info = get_currency_pair_info(pair_callback)
    if not pair_info:
        await callback_query.answer(
            "❌ Ошибка: информация о валютной паре не найдена",
            show_alert=True
        )
        return
    
    try:
        # Получаем текущий курс для валютной пары
        async with api_service:
            exchange_rate = await api_service.get_exchange_rate(pair_info['name'])
            
        if not exchange_rate:
            raise RapiraAPIError("Не удалось получить курс валютной пары")
        
        # Сохраняем данные в FSM
        await state.update_data(
            pair_callback=pair_callback,
            pair_info=pair_info,
            exchange_rate=exchange_rate.to_dict(),
            base_rate=float(exchange_rate.rate)
        )
        
        # Переходим в состояние ожидания наценки
        await state.set_state(MarginCalculationForm.waiting_for_margin)
        
        # Создаем клавиатуру для выбора суммы (НОВАЯ ЛОГИКА)
        keyboard = create_amount_selection_keyboard()
        
        # Формируем сообщение с запросом суммы (ИЗМЕНЕНО)
        message_text = (
            f"💱 <b>Расчет курса с наценкой</b>\n\n"
            f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n"
            f"📝 <i>{pair_info['description']}</i>\n\n"
            f"💰 <b>Укажите сумму для расчета:</b>\n\n"
            f"• Введите числовое значение (например: 1000, 500.50, 250)\n"
            f"• Можно указывать сумму в {pair_info['base']}\n\n"
            f"💡 <i>Диапазон: от 0.01 до 1,000,000,000</i>"
        )
        
        await callback_query.message.edit_text(
            message_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        await callback_query.answer("Укажите сумму для расчета")
        
        logger.info(
            f"Запрос суммы отправлен: "
            f"user_id={user_id}, pair={pair_info['name']}"
        )
        
    except RapiraAPIError as e:
        await callback_query.message.edit_text(
            f"❌ <b>Ошибка получения курса</b>\n\n"
            f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n\n"
            f"Не удалось получить текущий курс валютной пары:\n"
            f"<code>{str(e)}</code>\n\n"
            f"🔄 Попробуйте позже или обратитесь к администратору.\n\n"
            f"🏠 Используйте /admin_bot для возврата к главному меню.",
            parse_mode='HTML'
        )
        
        await callback_query.answer("❌ Ошибка получения курса", show_alert=True)
        await state.clear()
        
        logger.error(f"Ошибка получения курса для {pair_info['name']}: {e}")
    
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ <b>Произошла ошибка</b>\n\n"
            f"Не удалось начать расчет наценки.\n"
            f"Попробуйте позже.\n\n"
            f"🏠 Используйте /admin_bot для возврата к главному меню.",
            parse_mode='HTML'
        )
        
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)
        await state.clear()
        
        logger.error(f"Неожиданная ошибка при начале расчета наценки: {e}")


def create_margin_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для выбора процентной наценки
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с вариантами наценки
    """
    # Предустановленные варианты наценки
    margin_options = [
        ('0%', '0'),
        ('1%', '1'),
        ('2%', '2'),
        ('3%', '3'),
        ('5%', '5'),
        ('10%', '10'),
        ('-1%', '-1'),
        ('-2%', '-2'),
        ('-5%', '-5')
    ]
    
    keyboard = []
    
    # Добавляем заголовок
    keyboard.append([
        InlineKeyboardButton(text="📈 Быстрый выбор наценки", callback_data="header_margin")
    ])
    
    # Добавляем кнопки наценки по 3 в ряд
    for i in range(0, len(margin_options), 3):
        row = []
        for j in range(3):
            if i + j < len(margin_options):
                text, value = margin_options[i + j]
                row.append(InlineKeyboardButton(
                    text=text, 
                    callback_data=f"margin_{value}"
                ))
        keyboard.append(row)
    
    # Добавляем кнопки управления
    keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_margin"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@margin_router.callback_query(lambda c: c.data and c.data.startswith('margin_'))
async def handle_margin_selection(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора предустановленной наценки
    """
    # Проверяем, что пользователь в правильном состоянии
    current_state = await state.get_state()
    if current_state != MarginCalculationForm.waiting_for_margin:
        await callback_query.answer("❌ Неожиданное действие", show_alert=True)
        return
    
    # Извлекаем значение наценки
    margin_value = callback_query.data.replace('margin_', '')
    
    try:
        # Валидируем наценку
        margin = MarginCalculator.validate_margin(margin_value)
        
        # Обрабатываем наценку
        await process_margin_input(callback_query.message, margin, state, from_callback=True)
        await callback_query.answer(f"Выбрана наценка: {margin}%")
        
    except MarginCalculationError as e:
        await callback_query.answer(f"❌ {str(e)}", show_alert=True)
    except Exception as e:
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)
        logger.error(f"Ошибка при обработке выбора наценки: {e}")


@margin_router.callback_query(lambda c: c.data == 'cancel_margin')
async def handle_cancel_margin(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик отмены расчета наценки
    """
    await state.clear()
    
    await callback_query.message.edit_text(
        "❌ <b>Расчет наценки отменен</b>\n\n"
        "Операция была отменена пользователем.\n\n"
        "🏠 Используйте /admin_bot для возврата к главному меню.",
        parse_mode='HTML'
    )
    
    await callback_query.answer("Операция отменена")
    logger.info(f"Пользователь {callback_query.from_user.id} отменил расчет наценки")


@margin_router.callback_query(lambda c: c.data == 'back_to_main')
async def handle_back_to_main(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик возврата к главному меню
    """
    await state.clear()
    
    # Импортируем функцию создания клавиатуры из admin_handlers
    from .admin_handlers import create_currency_pairs_keyboard
    
    keyboard = create_currency_pairs_keyboard()
    
    admin_message = (
        "🔧 <b>Административная панель</b>\n\n"
        "Добро пожаловать в панель управления Crypto Helper Bot!\n\n"
        "📊 <b>Выберите валютную пару для получения курса:</b>\n\n"
        "• Выберите нужную валютную пару из списка ниже\n"
        "• Укажите процентную наценку\n"
        "• Получите актуальный курс с наценкой\n\n"
        "💡 <i>Курсы обновляются в реальном времени через Rapira API</i>"
    )
    
    await callback_query.message.edit_text(
        admin_message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    await callback_query.answer("Возврат к главному меню")


@margin_router.callback_query(lambda c: c.data and c.data.startswith('header_'))
async def handle_header_callbacks_margin(callback_query: CallbackQuery):
    """
    Обработчик для кнопок-заголовков (не выполняет действий, только уведомление)
    """
    await callback_query.answer("Это заголовок. Выберите наценку ниже.", show_alert=False)


@margin_router.message(MarginCalculationForm.waiting_for_margin, F.text)
async def handle_margin_text_input(message: Message, state: FSMContext):
    """
    Обработчик текстового ввода процентной наценки
    """
    try:
        # Валидируем введенную наценку
        margin = MarginCalculator.validate_margin(message.text)
        
        # Обрабатываем наценку
        await process_margin_input(message, margin, state)
        
    except MarginCalculationError as e:
        await message.reply(
            f"❌ <b>Ошибка ввода наценки</b>\n\n"
            f"{str(e)}\n\n"
            f"💡 <b>Примеры корректного ввода:</b>\n"
            f"• <code>5</code> (5% наценка)\n"
            f"• <code>2.5</code> (2.5% наценка)\n"
            f"• <code>-1.2</code> (-1.2% скидка)\n"
            f"• <code>0</code> (без наценки)\n\n"
            f"🔢 <b>Диапазон:</b> от -100% до +1000%",
            parse_mode='HTML'
        )
    except Exception as e:
        await message.reply(
            "❌ <b>Произошла ошибка</b>\n\n"
            "Не удалось обработать введенную наценку.\n"
            "Попробуйте еще раз.",
            parse_mode='HTML'
        )
        logger.error(f"Ошибка при обработке текстового ввода наценки: {e}")


async def process_margin_input(
    message: Message,
    margin: Decimal,
    state: FSMContext,
    from_callback: bool = False
) -> None:
    """
    Обработка введенной наценки и расчет итогового курса
    
    Args:
        message: Сообщение пользователя
        margin: Валидированная наценка
        state: FSM контекст
        from_callback: Флаг, что вызов из callback
    """
    try:
        # Получаем сохраненные данные
        data = await state.get_data()
        pair_info = data.get('pair_info')
        base_rate = Decimal(str(data.get('base_rate')))
        exchange_rate_data = data.get('exchange_rate')
        
        if not all([pair_info, base_rate, exchange_rate_data]):
            raise MarginCalculationError("Данные курса потеряны, начните заново")
        
        # Рассчитываем итоговый курс
        final_rate = MarginCalculator.calculate_final_rate(base_rate, margin)
        
        # Рассчитываем абсолютное изменение
        rate_change = final_rate - base_rate
        
        # Сохраняем результаты расчета
        await state.update_data(
            margin_percent=float(margin),
            final_rate=float(final_rate),
            rate_change=float(rate_change)
        )
        
        # Переходим в состояние показа результата
        await state.set_state(MarginCalculationForm.showing_result)
        
        # Форматируем результат
        result_message = format_calculation_result(
            pair_info=pair_info,
            base_rate=base_rate,
            margin=margin,
            final_rate=final_rate,
            rate_change=rate_change,
            exchange_rate_data=exchange_rate_data
        )
        
        # Создаем клавиатуру для результата
        result_keyboard = create_result_keyboard()
        
        if from_callback:
            # Если вызов из callback, редактируем сообщение
            await message.edit_text(
                result_message,
                parse_mode='HTML',
                reply_markup=result_keyboard
            )
        else:
            # Если вызов из текстового сообщения, отправляем новое
            await message.answer(
                result_message,
                parse_mode='HTML',
                reply_markup=result_keyboard
            )
        
        logger.info(
            f"Расчет наценки завершен: "
            f"user_id={message.from_user.id}, "
            f"pair={pair_info['name']}, "
            f"margin={margin}%, "
            f"base_rate={base_rate}, "
            f"final_rate={final_rate}"
        )
        
    except Exception as e:
        error_message = (
            "❌ <b>Ошибка расчета</b>\n\n"
            "Не удалось рассчитать курс с наценкой.\n"
            "Попробуйте начать заново.\n\n"
            "🏠 Используйте /admin_bot для возврата к главному меню."
        )
        
        if from_callback:
            await message.edit_text(error_message, parse_mode='HTML')
        else:
            await message.answer(error_message, parse_mode='HTML')
        
        await state.clear()
        logger.error(f"Ошибка при обработке наценки: {e}")


def format_calculation_result(
    pair_info: Dict[str, Any],
    base_rate: Decimal,
    margin: Decimal,
    final_rate: Decimal,
    rate_change: Decimal,
    exchange_rate_data: Dict[str, Any]
) -> str:
    """
    Форматирование результата расчета для отображения
    
    Args:
        pair_info: Информация о валютной паре
        base_rate: Базовый курс
        margin: Процентная наценка
        final_rate: Итоговый курс
        rate_change: Изменение курса
        exchange_rate_data: Данные о курсе
        
    Returns:
        str: Отформатированный результат
    """
    # Определяем валюты
    base_currency = pair_info['base']
    quote_currency = pair_info['quote']
    
    # Форматируем значения
    base_rate_str = MarginCalculator.format_currency_value(base_rate, quote_currency)
    final_rate_str = MarginCalculator.format_currency_value(final_rate, quote_currency)
    rate_change_str = MarginCalculator.format_currency_value(abs(rate_change), quote_currency)
    
    # Определяем знак изменения
    change_sign = "+" if rate_change >= 0 else "-"
    change_emoji = "📈" if rate_change >= 0 else "📉"
    
    # Определяем цвет для наценки
    margin_emoji = "📈" if margin >= 0 else "📉"
    margin_sign = "+" if margin >= 0 else ""
    
    # Временная метка
    timestamp = exchange_rate_data.get('timestamp', '')[:19].replace('T', ' ')
    
    result_message = (
        f"✅ <b>Расчет курса завершен</b>\n\n"
        f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n"
        f"📝 <i>{pair_info['description']}</i>\n\n"
        f"💰 <b>Исходный курс:</b> <code>{base_rate_str}</code> {quote_currency}\n"
        f"{margin_emoji} <b>Наценка:</b> <code>{margin_sign}{margin}%</code>\n"
        f"💎 <b>Итоговый курс:</b> <code>{final_rate_str}</code> {quote_currency}\n\n"
        f"{change_emoji} <b>Изменение:</b> <code>{change_sign}{rate_change_str}</code> {quote_currency}\n\n"
        f"📊 <b>Детали расчета:</b>\n"
        f"• Базовый курс: {base_rate_str} {quote_currency}\n"
        f"• Наценка: {margin_sign}{margin}%\n"
        f"• Множитель: {1 + margin/100:.6f}\n"
        f"• Результат: {base_rate_str} × {1 + margin/100:.6f} = {final_rate_str}\n\n"
        f"🕐 <b>Время получения курса:</b> {timestamp}\n"
        f"📡 <b>Источник:</b> {exchange_rate_data.get('source', 'N/A')}\n\n"
        f"💡 <i>Для публикации в канал используйте кнопку ниже</i>"
    )
    
    return result_message


def create_result_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для результата расчета
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с действиями
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📤 Опубликовать в канал", callback_data="publish_result"),
            InlineKeyboardButton(text="🔄 Пересчитать", callback_data="recalculate_margin")
        ],
        [
            InlineKeyboardButton(text="📋 Копировать результат", callback_data="copy_result"),
            InlineKeyboardButton(text="📊 Новая пара", callback_data="back_to_main")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@margin_router.callback_query(lambda c: c.data == 'publish_result', MarginCalculationForm.showing_result)
async def handle_publish_result(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик публикации результата в канал
    """
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "N/A"
    full_name = callback_query.from_user.full_name or "Менеджер"
    
    logger.info(f"Запрос публикации от пользователя {user_id} (@{username})")
    
    try:
        # Получаем данные расчета
        data = await state.get_data()
        pair_info = data.get('pair_info')
        base_rate = Decimal(str(data.get('base_rate')))
        margin = Decimal(str(data.get('margin_percent')))
        final_rate = Decimal(str(data.get('final_rate')))
        rate_change = Decimal(str(data.get('rate_change')))
        exchange_rate_data = data.get('exchange_rate')
        
        if not all([pair_info, base_rate, margin, final_rate, exchange_rate_data]):
            raise MarginCalculationError("Данные расчета потеряны")
        
        # Импортируем модуль публикации
        from .channel_publisher import ChannelPublisher
        
        # Определяем режим работы и ID канала
        development_mode = config.DEBUG_MODE or not config.ADMIN_CHANNEL_ID
        channel_id = config.ADMIN_CHANNEL_ID if not development_mode else None
        
        # Получаем бота из callback_query
        bot = callback_query.bot
        
        # Публикуем результат
        publish_result = await ChannelPublisher.publish_result(
            bot=bot,
            pair_info=pair_info,
            base_rate=base_rate,
            margin=margin,
            final_rate=final_rate,
            rate_change=rate_change,
            exchange_rate_data=exchange_rate_data,
            manager_name=full_name,
            user_id=user_id,
            channel_id=channel_id,
            development_mode=development_mode
        )
        
        if publish_result['success']:
            # Успешная публикация
            success_message = (
                f"✅ <b>Публикация завершена</b>\n\n"
                f"{publish_result['message']}\n\n"
                f"📊 <b>Опубликованные данные:</b>\n"
                f"• Валютная пара: {pair_info['name']}\n"
                f"• Итоговый курс: {final_rate:.8f} {pair_info['quote']}\n"
                f"• Наценка: {margin:+.2f}%\n"
                f"• Менеджер: {full_name}\n\n"
                f"🎯 <b>Цель:</b> {publish_result['target']}\n\n"
                f"💡 <i>Для новой публикации используйте /admin_bot</i>"
            )
            
            await callback_query.message.edit_text(
                success_message,
                parse_mode='HTML'
            )
            
            await callback_query.answer("✅ Результат опубликован")
            
        else:
            # Ошибка публикации
            error_message = (
                f"❌ <b>Ошибка публикации</b>\n\n"
                f"{publish_result['message']}\n\n"
                f"🔧 <b>Возможные решения:</b>\n"
                f"• Проверьте права бота в канале\n"
                f"• Убедитесь, что бот добавлен в канал\n"
                f"• Проверьте корректность ID канала\n\n"
                f"🏠 Используйте /admin_bot для возврата к главному меню"
            )
            
            await callback_query.message.edit_text(
                error_message,
                parse_mode='HTML'
            )
            
            await callback_query.answer("❌ Ошибка публикации", show_alert=True)
        
        logger.info(
            f"Публикация завершена: user_id={user_id}, "
            f"success={publish_result['success']}, target={publish_result['target']}"
        )
        
    except MarginCalculationError as e:
        await callback_query.message.edit_text(
            f"❌ <b>Ошибка данных</b>\n\n"
            f"{str(e)}\n\n"
            f"Начните расчет заново с команды /admin_bot",
            parse_mode='HTML'
        )
        
        await callback_query.answer("❌ Ошибка данных", show_alert=True)
        await state.clear()
        
        logger.error(f"Ошибка данных при публикации: {e}")
    
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ <b>Произошла ошибка</b>\n\n"
            f"Не удалось опубликовать результат.\n"
            f"Попробуйте позже.\n\n"
            f"🏠 Используйте /admin_bot для возврата к главному меню.",
            parse_mode='HTML'
        )
        
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)
        
        logger.error(f"Неожиданная ошибка при публикации: {e}")


@margin_router.callback_query(lambda c: c.data == 'recalculate_margin', MarginCalculationForm.showing_result)
async def handle_recalculate_margin(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик пересчета с новой наценкой
    """
    # Возвращаемся к состоянию ввода наценки
    await state.set_state(MarginCalculationForm.waiting_for_margin)
    
    # Получаем сохраненные данные
    data = await state.get_data()
    pair_info = data.get('pair_info')
    base_rate = data.get('base_rate')
    exchange_rate_data = data.get('exchange_rate')
    
    # Создаем клавиатуру для выбора наценки
    keyboard = create_margin_selection_keyboard()
    
    # Формируем сообщение
    message_text = (
        f"🔄 <b>Пересчет курса с наценкой</b>\n\n"
        f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n"
        f"📝 <i>{pair_info['description']}</i>\n\n"
        f"💰 <b>Текущий курс:</b> <code>{base_rate:.8f}</code>\n"
        f"🕐 <b>Время получения:</b> {exchange_rate_data.get('timestamp', '')[:19].replace('T', ' ')}\n\n"
        f"📈 <b>Укажите новую процентную наценку:</b>\n\n"
        f"• Выберите из предложенных вариантов ниже\n"
        f"• Или введите свое значение (например: 5, 2.5, -1.2)\n\n"
        f"💡 <i>Диапазон: от -100% до +1000%</i>"
    )
    
    await callback_query.message.edit_text(
        message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    await callback_query.answer("Введите новую наценку")


@margin_router.callback_query(lambda c: c.data == 'copy_result', MarginCalculationForm.showing_result)
async def handle_copy_result(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик копирования результата в текстовом формате
    """
    try:
        # Получаем данные расчета
        data = await state.get_data()
        pair_info = data.get('pair_info')
        base_rate = Decimal(str(data.get('base_rate')))
        margin = Decimal(str(data.get('margin_percent')))
        final_rate = Decimal(str(data.get('final_rate')))
        exchange_rate_data = data.get('exchange_rate')
        
        # Форматируем для копирования (простой текст)
        base_currency = pair_info['base']
        quote_currency = pair_info['quote']
        
        copy_text = (
            f"💱 {pair_info['name']}\n"
            f"📊 Базовый курс: {base_rate:.8f} {quote_currency}\n"
            f"📈 Наценка: {margin:+.2f}%\n"
            f"💎 Итоговый курс: {final_rate:.8f} {quote_currency}\n"
            f"🕐 {exchange_rate_data.get('timestamp', '')[:19].replace('T', ' ')}\n"
            f"📡 Источник: {exchange_rate_data.get('source', 'N/A')}"
        )
        
        # Отправляем текст для копирования
        await callback_query.message.reply(
            f"📋 <b>Результат для копирования:</b>\n\n"
            f"<code>{copy_text}</code>\n\n"
            f"💡 <i>Нажмите на текст выше для копирования</i>",
            parse_mode='HTML'
        )
        
        await callback_query.answer("Результат подготовлен для копирования")
        
    except Exception as e:
        await callback_query.answer("❌ Ошибка при подготовке результата", show_alert=True)
        logger.error(f"Ошибка при копировании результата: {e}")


# Обработчики для неожиданных сообщений в состояниях FSM
@margin_router.message(MarginCalculationForm.waiting_for_margin, ~F.text)
async def handle_unexpected_content_waiting_margin(message: Message, state: FSMContext):
    """
    Обработчик неожиданного контента в состоянии ожидания наценки
    """
    await message.reply(
        "❌ <b>Некорректный ввод</b>\n\n"
        "Пожалуйста, введите процентную наценку в виде числа.\n\n"
        "💡 <b>Примеры:</b>\n"
        "• <code>5</code> (5% наценка)\n"
        "• <code>-2.5</code> (2.5% скидка)\n"
        "• <code>0</code> (без наценки)\n\n"
        "Или используйте кнопки выше для быстрого выбора.",
        parse_mode='HTML'
    )


@margin_router.message(MarginCalculationForm.showing_result)
async def handle_unexpected_message_showing_result(message: Message, state: FSMContext):
    """
    Обработчик неожиданных сообщений в состоянии показа результата
    """
    await message.reply(
        "💡 <b>Результат уже рассчитан</b>\n\n"
        "Используйте кнопки выше для:\n"
        "• Публикации результата в канал\n"
        "• Пересчета с новой наценкой\n"
        "• Копирования результата\n"
        "• Возврата к главному меню",
        parse_mode='HTML'
    )