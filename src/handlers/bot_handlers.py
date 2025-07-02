#!/usr/bin/env python3
"""
Модуль основных обработчиков для Crypto Helper Bot
Содержит FSM обработчики и логику взаимодействия с пользователем
"""

from decimal import Decimal
from typing import Dict, Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# Локальные импорты
from .fsm_states import MarginCalculationForm, MarginCalculationError
from .currency_pairs import get_currency_pair_info
from .validation import InputValidator, ValidationError
from .calculation_logic import calculate_margin_rate, CalculationResult
from .formatters import MessageFormatter
from .keyboards import (
    KeyboardBuilder, 
    create_currency_pairs_keyboard,
    create_amount_selection_keyboard,
    create_margin_selection_keyboard,
    create_result_keyboard
)

try:
    from ..utils.logger import get_bot_logger
    from ..services.api_service import api_service, RapiraAPIError
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.logger import get_bot_logger
    from services.api_service import api_service, RapiraAPIError

# Initialize logger
logger = get_bot_logger()

# Create router for margin calculation handlers
margin_router = Router()


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
        
        # Создаем клавиатуру и сообщение
        keyboard = create_amount_selection_keyboard()
        message_text = MessageFormatter.format_amount_request(pair_info)
        
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
        error_message = MessageFormatter.format_error_message('generic')
        
        await callback_query.message.edit_text(
            error_message,
            parse_mode='HTML'
        )
        
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)
        await state.clear()
        
        logger.error(f"Неожиданная ошибка при начале расчета: {e}")


@margin_router.message(MarginCalculationForm.waiting_for_amount, F.text)
async def handle_amount_text_input(message: Message, state: FSMContext):
    """
    Обработчик текстового ввода суммы
    """
    try:
        # Валидируем введенную сумму
        amount = InputValidator.validate_amount(message.text)
        
        # Обрабатываем сумму
        await process_amount_input(message, amount, state)
        
    except ValidationError as e:
        error_message = MessageFormatter.format_error_message('validation_amount', str(e))
        await message.reply(error_message, parse_mode='HTML')
    except Exception as e:
        error_message = MessageFormatter.format_error_message('generic', 
            "Не удалось обработать введенную сумму. Попробуйте еще раз.")
        await message.reply(error_message, parse_mode='HTML')
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
        
        # Переходим в состояние ожидания наценки
        await state.set_state(MarginCalculationForm.waiting_for_margin)
        
        # Создаем клавиатуру и сообщение
        keyboard = create_margin_selection_keyboard()
        message_text = MessageFormatter.format_margin_request(
            pair_info, amount, exchange_rate.to_dict()
        )
        
        if from_callback:
            await message.edit_text(message_text, parse_mode='HTML', reply_markup=keyboard)
        else:
            await message.answer(message_text, parse_mode='HTML', reply_markup=keyboard)
        
        logger.info(
            f"Переход к выбору наценки: "
            f"user_id={message.from_user.id}, "
            f"pair={pair_info['name']}, "
            f"amount={amount} {pair_info['base']}, "
            f"rate={exchange_rate.rate}"
        )
        
    except RapiraAPIError as e:
        error_message = MessageFormatter.format_error_message('api_error', str(e))
        
        if from_callback:
            await message.edit_text(error_message, parse_mode='HTML')
        else:
            await message.answer(error_message, parse_mode='HTML')
        
        await state.clear()
        logger.error(f"Ошибка получения курса: {e}")
    
    except Exception as e:
        error_message = MessageFormatter.format_error_message('generic', 
            "Не удалось обработать сумму. Попробуйте начать заново.")
        
        if from_callback:
            await message.edit_text(error_message, parse_mode='HTML')
        else:
            await message.answer(error_message, parse_mode='HTML')
        
        await state.clear()
        logger.error(f"Ошибка при обработке суммы: {e}")


@margin_router.message(MarginCalculationForm.waiting_for_margin, F.text)
async def handle_margin_text_input(message: Message, state: FSMContext):
    """
    Обработчик текстового ввода процентной наценки
    """
    try:
        # Валидируем введенную наценку
        margin = InputValidator.validate_margin(message.text)
        
        # Обрабатываем наценку
        await process_margin_input(message, margin, state)
        
    except ValidationError as e:
        error_message = MessageFormatter.format_error_message('validation_margin', str(e))
        await message.reply(error_message, parse_mode='HTML')
    except Exception as e:
        error_message = MessageFormatter.format_error_message('generic',
            "Не удалось обработать введенную наценку. Попробуйте еще раз.")
        await message.reply(error_message, parse_mode='HTML')
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
        exchange_rate_data = data.get('exchange_rate')
        calculation_amount = data.get('calculation_amount')
        
        if not all([pair_info, exchange_rate_data, calculation_amount]):
            raise MarginCalculationError("Данные расчета потеряны, начните заново")
        
        # Рассчитываем результат
        result = calculate_margin_rate(
            pair_info=pair_info,
            amount=Decimal(str(calculation_amount)),
            margin=margin,
            exchange_rate_data=exchange_rate_data
        )
        
        # Сохраняем результаты расчета
        await state.update_data(
            margin_percent=float(margin),
            final_rate=float(result.final_rate),
            rate_change=float(result.rate_change),
            calculation_result=result.to_dict()
        )
        
        # Переходим в состояние показа результата
        await state.set_state(MarginCalculationForm.showing_result)
        
        # Форматируем и отправляем результат
        result_message = MessageFormatter.format_calculation_result(result)
        result_keyboard = create_result_keyboard()
        
        if from_callback:
            await message.edit_text(result_message, parse_mode='HTML', reply_markup=result_keyboard)
        else:
            await message.answer(result_message, parse_mode='HTML', reply_markup=result_keyboard)
        
        logger.info(
            f"Расчет наценки завершен: "
            f"user_id={message.from_user.id}, "
            f"pair={pair_info['name']}, "
            f"margin={margin}%, "
            f"final_rate={result.final_rate}"
        )
        
    except Exception as e:
        error_message = MessageFormatter.format_error_message('generic',
            "Не удалось рассчитать курс с наценкой. Попробуйте начать заново.")
        
        if from_callback:
            await message.edit_text(error_message, parse_mode='HTML')
        else:
            await message.answer(error_message, parse_mode='HTML')
        
        await state.clear()
        logger.error(f"Ошибка при обработке наценки: {e}")


# Callback обработчики
@margin_router.callback_query(lambda c: c.data == 'cancel_amount')
async def handle_cancel_amount(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик отмены выбора суммы"""
    await state.clear()
    
    cancel_message = MessageFormatter.format_cancel_message("Расчет")
    await callback_query.message.edit_text(cancel_message, parse_mode='HTML')
    await callback_query.answer("Операция отменена")
    logger.info(f"Пользователь {callback_query.from_user.id} отменил выбор суммы")


@margin_router.callback_query(lambda c: c.data == 'cancel_margin')
async def handle_cancel_margin(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик отмены расчета наценки"""
    await state.clear()
    
    cancel_message = MessageFormatter.format_cancel_message("Расчет наценки")
    await callback_query.message.edit_text(cancel_message, parse_mode='HTML')
    await callback_query.answer("Операция отменена")
    logger.info(f"Пользователь {callback_query.from_user.id} отменил расчет наценки")


@margin_router.callback_query(lambda c: c.data == 'back_to_main')
async def handle_back_to_main(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик возврата к главному меню"""
    await state.clear()
    
    keyboard = create_currency_pairs_keyboard()
    welcome_message = MessageFormatter.format_welcome_message()
    
    await callback_query.message.edit_text(
        welcome_message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    await callback_query.answer("Возврат к главному меню")


@margin_router.callback_query(lambda c: c.data == 'recalculate_margin', MarginCalculationForm.showing_result)
async def handle_recalculate_margin(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик пересчета с новой наценкой"""
    # Возвращаемся к состоянию ввода наценки
    await state.set_state(MarginCalculationForm.waiting_for_margin)
    
    # Получаем сохраненные данные
    data = await state.get_data()
    pair_info = data.get('pair_info')
    calculation_amount = data.get('calculation_amount')
    exchange_rate_data = data.get('exchange_rate')
    
    # Создаем клавиатуру и сообщение
    keyboard = create_margin_selection_keyboard()
    message_text = MessageFormatter.format_margin_request(
        pair_info, Decimal(str(calculation_amount)), exchange_rate_data
    )
    
    await callback_query.message.edit_text(
        message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    await callback_query.answer("Введите новую наценку")


# Обработчики для неожиданных сообщений в состояниях FSM
@margin_router.message(MarginCalculationForm.waiting_for_amount, ~F.text)
async def handle_unexpected_content_waiting_amount(message: Message, state: FSMContext):
    """Обработчик неожиданного контента в состоянии ожидания суммы"""
    error_message = MessageFormatter.format_error_message('invalid_content', 'сумму для расчета')
    await message.reply(error_message, parse_mode='HTML')


@margin_router.message(MarginCalculationForm.waiting_for_margin, ~F.text)
async def handle_unexpected_content_waiting_margin(message: Message, state: FSMContext):
    """Обработчик неожиданного контента в состоянии ожидания наценки"""
    error_message = MessageFormatter.format_error_message('invalid_content', 'процентную наценку')
    await message.reply(error_message, parse_mode='HTML')


@margin_router.message(MarginCalculationForm.showing_result)
async def handle_unexpected_message_showing_result(message: Message, state: FSMContext):
    """Обработчик неожиданных сообщений в состоянии показа результата"""
    await message.reply(
        "💡 <b>Результат уже рассчитан</b>\n\n"
        "Используйте кнопки выше для:\n"
        "• Пересчета с новой наценкой\n"
        "• Возврата к главному меню",
        parse_mode='HTML'
    )