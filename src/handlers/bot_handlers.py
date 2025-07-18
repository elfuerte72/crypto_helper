#!/usr/bin/env python3
"""
Модуль основных обработчиков для Crypto Helper Bot
Содержит FSM обработчики и логику взаимодействия с пользователем
"""

import asyncio
from decimal import Decimal

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# Локальные импорты
from .fsm_states import MarginCalculationForm, MarginCalculationError
from .currency_pairs import get_currency_pair_info
from .validation import InputValidator, ValidationError
from .calculation_logic import calculate_margin_rate
from .formatters import MessageFormatter
from .keyboards import (
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


async def start_margin_calculation(callback_query: CallbackQuery, pair_callback: str, state: FSMContext):
    """
    Обработчик начала расчета наценки с улучшенной обработкой таймаутов
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
        try:
            await callback_query.answer(
                "❌ Ошибка: информация о валютной паре не найдена",
                show_alert=True
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке callback answer: {e}")
        return

    # Сначала отвечаем на callback query, чтобы избежать таймаута
    try:
        await callback_query.answer("⏳ Получаем курс валют...")
    except Exception as e:
        logger.warning(f"Не удалось ответить на callback query: {e}")
        # Продолжаем работу даже если callback answer не удался

    try:
        # Получаем текущий курс для валютной пары с таймаутом
        async with asyncio.timeout(25):  # Таймаут 25 секунд
            async with api_service:
                # Формируем правильный формат пары для API
                pair_format = f"{pair_info['base']}/{pair_info['quote']}"
                exchange_rate = await api_service.get_exchange_rate(
                    pair_format
                )
                
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
        
        # Создаем клавиатуру и сообщение
        keyboard = create_margin_selection_keyboard()
        message_text = MessageFormatter.format_margin_request_simple(
            pair_info, exchange_rate.to_dict()
        )
        
        await callback_query.message.edit_text(
            message_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        logger.info(
            f"Запрос наценки отправлен: "
            f"user_id={user_id}, pair={pair_format}, rate={exchange_rate.rate}"
        )
        
    except asyncio.TimeoutError:
        error_message = MessageFormatter.format_error_message(
            'timeout', 
            "Превышено время ожидания ответа от сервера курсов валют"
        )
        
        await callback_query.message.edit_text(
            error_message,
            parse_mode='HTML'
        )
        
        await state.clear()
        logger.error(f"Таймаут при получении курса для пары {pair_callback}")
        
    except RapiraAPIError as e:
        error_message = MessageFormatter.format_error_message(
            'api_error', str(e)
        )
        
        await callback_query.message.edit_text(
            error_message,
            parse_mode='HTML'
        )
        
        await state.clear()
        
        logger.error(f"Ошибка получения курса: {e}")
        
    except Exception as e:
        error_message = MessageFormatter.format_error_message('generic')
        
        await callback_query.message.edit_text(
            error_message,
            parse_mode='HTML'
        )
        
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


@margin_router.message(MarginCalculationForm.showing_rate_comparison, F.text)
async def handle_amount_text_input_from_comparison(message: Message, state: FSMContext):
    """
    Обработчик текстового ввода суммы в состоянии сравнения курсов
    """
    try:
        # Валидируем введенную сумму
        amount = InputValidator.validate_amount(message.text)
        
        # Переходим в состояние ожидания суммы
        await state.set_state(MarginCalculationForm.waiting_for_amount)
        
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
    Обработка введенной суммы и расчет итогового результата
    
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
        exchange_rate_data = data.get('exchange_rate')
        margin_percent = data.get('margin_percent')
        final_rate = data.get('final_rate')
        
        if not all([pair_info, exchange_rate_data, margin_percent is not None, final_rate]):
            raise MarginCalculationError("Данные расчета потеряны, начните заново")
        
        # Рассчитываем результат
        result = calculate_margin_rate(
            pair_info=pair_info,
            amount=amount,
            margin=Decimal(str(margin_percent)),
            exchange_rate_data=exchange_rate_data
        )
        
        # Сохраняем результаты расчета
        await state.update_data(
            calculation_amount=float(amount),
            calculation_result=result.to_dict()
        )
        
        # Переходим в состояние показа результата
        await state.set_state(MarginCalculationForm.showing_result)
        
        # Форматируем и отправляем результат
        result_message = MessageFormatter.format_calculation_result_simple(result)
        result_keyboard = create_result_keyboard()
        
        if from_callback:
            await message.edit_text(result_message, parse_mode='HTML', reply_markup=result_keyboard)
        else:
            await message.answer(result_message, parse_mode='HTML', reply_markup=result_keyboard)
        
        logger.info(
            f"Расчет завершен: "
            f"user_id={message.from_user.id}, "
            f"pair={pair_info['base']}/{pair_info['quote']}, "
            f"amount={amount} {pair_info['base']}, "
            f"margin={margin_percent}%, "
            f"final_rate={final_rate}"
        )
        
    except Exception as e:
        error_message = MessageFormatter.format_error_message('generic',
            "Не удалось рассчитать результат. Попробуйте начать заново.")
        
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
            f"pair={pair_info['base']}/{pair_info['quote']}, "
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
    exchange_rate_data = data.get('exchange_rate')
    
    # Создаем клавиатуру и сообщение
    keyboard = create_margin_selection_keyboard()
    message_text = MessageFormatter.format_margin_request_simple(pair_info, exchange_rate_data)
    
    await callback_query.message.edit_text(
        message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    await callback_query.answer("Введите новую наценку")


@margin_router.callback_query(lambda c: c.data == 'recalculate_amount', MarginCalculationForm.showing_result)
async def handle_recalculate_amount(callback_query: CallbackQuery, state: FSMContext):
    """Обработчик пересчета с новой суммой"""
    # Возвращаемся к состоянию показа сравнения курсов
    await state.set_state(MarginCalculationForm.showing_rate_comparison)
    
    # Получаем сохраненные данные
    data = await state.get_data()
    pair_info = data.get('pair_info')
    exchange_rate_data = data.get('exchange_rate')
    margin_percent = data.get('margin_percent')
    final_rate = data.get('final_rate')
    
    # Создаем клавиатуру и сообщение
    keyboard = create_amount_selection_keyboard()
    message_text = MessageFormatter.format_rate_comparison(
        pair_info, exchange_rate_data, Decimal(str(margin_percent)), Decimal(str(final_rate))
    )
    
    await callback_query.message.edit_text(
        message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    await callback_query.answer("Введите новую сумму")


# Обработчики для неожиданных сообщений в состояниях FSM
@margin_router.message(MarginCalculationForm.waiting_for_margin, ~F.text)
async def handle_unexpected_content_waiting_margin(message: Message, state: FSMContext):
    """Обработчик неожиданного контента в состоянии ожидания наценки"""
    error_message = MessageFormatter.format_error_message('invalid_content', 'процентную наценку')
    await message.reply(error_message, parse_mode='HTML')


@margin_router.message(MarginCalculationForm.showing_rate_comparison, ~F.text)
async def handle_unexpected_content_showing_rate_comparison(message: Message, state: FSMContext):
    """Обработчик неожиданного контента в состоянии показа сравнения курсов"""
    await message.reply(
        "💡 Курсы уже рассчитаны. Введите сумму для расчета или используйте кнопки.",
        parse_mode='HTML'
    )


@margin_router.message(MarginCalculationForm.waiting_for_amount, ~F.text)
async def handle_unexpected_content_waiting_amount(message: Message, state: FSMContext):
    """Обработчик неожиданного контента в состоянии ожидания суммы"""
    error_message = MessageFormatter.format_error_message('invalid_content', 'сумму для расчета')
    await message.reply(error_message, parse_mode='HTML')


@margin_router.message(MarginCalculationForm.showing_result)
async def handle_unexpected_message_showing_result(message: Message, state: FSMContext):
    """Обработчик неожиданных сообщений в состоянии показа результата"""
    await message.reply(
        "💡 Результат уже рассчитан. Используйте кнопки выше.",
        parse_mode='HTML'
    )


# Новые функции для обновленной логики
async def process_margin_input(
    message: Message,
    margin: Decimal,
    state: FSMContext,
    from_callback: bool = False
) -> None:
    """
    Обработка введенной наценки и показ сравнения курсов
    
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
        base_rate = data.get('base_rate')
        
        if not all([pair_info, exchange_rate_data, base_rate]):
            raise MarginCalculationError("Данные расчета потеряны, начните заново")
        
        # Рассчитываем итоговый курс с наценкой
        from .calculation_logic import MarginCalculator
        final_rate = MarginCalculator.calculate_final_rate(Decimal(str(base_rate)), margin)
        
        # Сохраняем данные в FSM
        await state.update_data(
            margin_percent=float(margin),
            final_rate=float(final_rate)
        )
        
        # Переходим в состояние показа сравнения курсов
        await state.set_state(MarginCalculationForm.showing_rate_comparison)
        
        # Создаем клавиатуру и сообщение
        keyboard = create_amount_selection_keyboard()
        message_text = MessageFormatter.format_rate_comparison(
            pair_info, exchange_rate_data, margin, final_rate
        )
        
        if from_callback:
            await message.edit_text(message_text, parse_mode='HTML', reply_markup=keyboard)
        else:
            await message.answer(message_text, parse_mode='HTML', reply_markup=keyboard)
        
        logger.info(
            f"Показ сравнения курсов: "
            f"user_id={message.from_user.id}, "
            f"pair={pair_info['base']}/{pair_info['quote']}, "
            f"margin={margin}%, "
            f"final_rate={final_rate}"
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