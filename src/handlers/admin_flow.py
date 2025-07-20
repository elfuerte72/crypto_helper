#!/usr/bin/env python3
"""
Admin Flow для Crypto Helper Bot (Новая логика)
Основной флоу для команды /admin_bot с пошаговым выбором валют
"""

from decimal import Decimal
from typing import Dict, Any, Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# Импорты модулей новой логики
from .fsm_states import ExchangeFlow, Currency, get_available_targets, is_valid_pair
from .keyboards import (
    create_source_currency_keyboard,
    create_target_currency_keyboard,
    create_margin_input_keyboard,
    create_amount_input_keyboard,
    create_result_keyboard
)
from .formatters import MessageFormatter
from .validators import ExchangeValidator, ValidationResult

# Импорт API сервисов
try:
    from ..services.api_service import APIService, APIError
    from ..services.fiat_rates_service import FiatRatesService
except ImportError:
    # Заглушки для сервисов, если они недоступны
    class APIService:
        @staticmethod
        async def get_usdt_rub_rate() -> Decimal:
            return Decimal('80.00')  # Заглушка
    
    class FiatRatesService:
        @staticmethod
        async def get_usd_usdt_rate() -> Decimal:
            return Decimal('0.998')  # Заглушка
        
        @staticmethod
        async def get_eur_usdt_rate() -> Decimal:
            return Decimal('0.920')  # Заглушка
    
    class APIError(Exception):
        pass

try:
    from ..utils.logger import get_bot_logger
except ImportError:
    import logging
    def get_bot_logger():
        return logging.getLogger(__name__)

# Initialize components
logger = get_bot_logger()
admin_flow_router = Router()


class ExchangeCalculator:
    """Калькулятор для расчета курсов и сумм обмена"""
    
    @staticmethod
    async def get_base_rate() -> Decimal:
        """Получить базовый курс USDT/RUB"""
        try:
            api_service = APIService()
            rate = await api_service.get_usdt_rub_rate()
            logger.info(f"Получен базовый курс USDT/RUB: {rate}")
            return rate
        except APIError as e:
            logger.error(f"Ошибка получения курса от API: {e}")
            # Fallback курс
            return Decimal('80.00')
    
    @staticmethod
    async def get_cross_rate(target_currency: Currency) -> Decimal:
        """Получить кросс-курс для других валют через USDT"""
        if target_currency == Currency.USD:
            try:
                fiat_service = FiatRatesService()
                usd_usdt_rate = await fiat_service.get_usd_usdt_rate()
                usdt_rub_rate = await ExchangeCalculator.get_base_rate()
                # 1 USD = X RUB через USDT
                cross_rate = usdt_rub_rate / usd_usdt_rate
                logger.info(f"Кросс-курс USD/RUB: {cross_rate}")
                return cross_rate
            except Exception as e:
                logger.error(f"Ошибка расчета кросс-курса USD: {e}")
                return Decimal('82.00')  # Fallback
        
        elif target_currency == Currency.EUR:
            try:
                fiat_service = FiatRatesService()
                eur_usdt_rate = await fiat_service.get_eur_usdt_rate()
                usdt_rub_rate = await ExchangeCalculator.get_base_rate()
                # 1 EUR = X RUB через USDT
                cross_rate = usdt_rub_rate / eur_usdt_rate
                logger.info(f"Кросс-курс EUR/RUB: {cross_rate}")
                return cross_rate
            except Exception as e:
                logger.error(f"Ошибка расчета кросс-курса EUR: {e}")
                return Decimal('87.00')  # Fallback
        
        else:
            # Для USDT возвращаем базовый курс
            return await ExchangeCalculator.get_base_rate()
    
    @staticmethod
    def calculate_final_rate(
        source: Currency,
        target: Currency,
        base_rate: Decimal,
        margin_percent: Decimal
    ) -> Decimal:
        """
        Рассчитать итоговый курс с учетом наценки
        
        Логика наценки:
        - RUB → USDT/USD/EUR: итоговый_курс = базовый × (1 + наценка/100)
        - USDT → RUB: итоговый_курс = базовый × (1 - наценка/100)
        """
        margin_factor = margin_percent / Decimal('100')
        
        if source == Currency.RUB:
            # Клиент отдает рубли - увеличиваем курс (меньше получит криптовалюты)
            final_rate = base_rate * (Decimal('1') + margin_factor)
        else:
            # Клиент отдает криптовалюту - уменьшаем курс (меньше получит рублей)
            final_rate = base_rate * (Decimal('1') - margin_factor)
        
        return final_rate.quantize(Decimal('0.01'))
    
    @staticmethod
    def calculate_result(
        source: Currency,
        target: Currency,
        amount: Decimal,
        final_rate: Decimal
    ) -> Decimal:
        """
        Рассчитать результат обмена
        
        Логика:
        - RUB → USDT/USD/EUR: результат = сумма_RUB / итоговый_курс
        - USDT → RUB: результат = сумма_USDT × итоговый_курс
        """
        if source == Currency.RUB:
            # Делим сумму рублей на курс
            result = amount / final_rate
        else:
            # Умножаем сумму криптовалюты на курс
            result = amount * final_rate
        
        return result.quantize(Decimal('0.01'))


# === ОБРАБОТЧИКИ КОМАНД ===

@admin_flow_router.message(Command('admin_bot'))
async def start_exchange_flow(message: Message, state: FSMContext):
    """Запуск нового флоу обмена валют"""
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    
    logger.info(f"Запуск нового флоу обмена: user_id={user_id}, username=@{username}")
    
    # Очищаем предыдущее состояние
    await state.clear()
    
    # Устанавливаем начальное состояние
    await state.set_state(ExchangeFlow.WAITING_FOR_SOURCE_CURRENCY)
    
    # Отправляем приветственное сообщение
    welcome_text = MessageFormatter.format_welcome_message()
    keyboard = create_source_currency_keyboard()
    
    await message.reply(
        welcome_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    logger.info(f"Приветственное сообщение отправлено пользователю {user_id}")


# === ОБРАБОТЧИКИ ВЫБОРА ИСХОДНОЙ ВАЛЮТЫ ===

@admin_flow_router.callback_query(
    ExchangeFlow.WAITING_FOR_SOURCE_CURRENCY,
    F.data.startswith('source_')
)
async def handle_source_currency_selection(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора исходной валюты"""
    user_id = callback_query.from_user.id
    
    # Валидируем callback данные
    validation = ExchangeValidator.validate_callback_data(callback_query.data, 'source_')
    if not validation.is_valid:
        await callback_query.answer("❌ Ошибка выбора валюты", show_alert=True)
        return
    
    try:
        source_currency = Currency(validation.value)
    except ValueError:
        await callback_query.answer("❌ Неизвестная валюта", show_alert=True)
        return
    
    logger.info(f"Выбрана исходная валюта: user_id={user_id}, source={source_currency.value}")
    
    # Сохраняем в состоянии
    await state.update_data(source_currency=source_currency.value)
    
    # Переходим к выбору целевой валюты
    await state.set_state(ExchangeFlow.WAITING_FOR_TARGET_CURRENCY)
    
    # Формируем сообщение и клавиатуру
    message_text = MessageFormatter.format_source_selected_message(source_currency)
    keyboard = create_target_currency_keyboard(source_currency)
    
    await callback_query.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    await callback_query.answer()


# === ОБРАБОТЧИКИ ВЫБОРА ЦЕЛЕВОЙ ВАЛЮТЫ ===

@admin_flow_router.callback_query(
    ExchangeFlow.WAITING_FOR_TARGET_CURRENCY,
    F.data.startswith('target_')
)
async def handle_target_currency_selection(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора целевой валюты"""
    user_id = callback_query.from_user.id
    
    # Валидируем callback данные
    validation = ExchangeValidator.validate_callback_data(callback_query.data, 'target_')
    if not validation.is_valid:
        await callback_query.answer("❌ Ошибка выбора валюты", show_alert=True)
        return
    
    try:
        target_currency = Currency(validation.value)
    except ValueError:
        await callback_query.answer("❌ Неизвестная валюта", show_alert=True)
        return
    
    # Получаем исходную валюту из состояния
    data = await state.get_data()
    source_currency = Currency(data['source_currency'])
    
    # Валидируем валютную пару
    pair_validation = ExchangeValidator.validate_currency_pair(source_currency, target_currency)
    if not pair_validation.is_valid:
        await callback_query.answer(f"❌ {pair_validation.error}", show_alert=True)
        return
    
    logger.info(f"Выбрана валютная пара: user_id={user_id}, {source_currency.value}→{target_currency.value}")
    
    # Получаем базовый курс
    if target_currency == Currency.RUB:
        base_rate = await ExchangeCalculator.get_base_rate()
    else:
        base_rate = await ExchangeCalculator.get_cross_rate(target_currency)
    
    # Сохраняем в состоянии
    await state.update_data(
        target_currency=target_currency.value,
        base_rate=str(base_rate)
    )
    
    # Переходим к вводу наценки
    await state.set_state(ExchangeFlow.WAITING_FOR_MARGIN)
    
    # Формируем сообщение и клавиатуру
    message_text = MessageFormatter.format_target_selected_message(
        source_currency, target_currency, base_rate
    )
    keyboard = create_margin_input_keyboard()
    
    await callback_query.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    await callback_query.answer()


# === ОБРАБОТЧИКИ ВВОДА НАЦЕНКИ ===

@admin_flow_router.callback_query(
    ExchangeFlow.WAITING_FOR_MARGIN,
    F.data.startswith('margin_')
)
async def handle_margin_callback(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора наценки через кнопки"""
    validation = ExchangeValidator.validate_callback_data(callback_query.data, 'margin_')
    if not validation.is_valid:
        await callback_query.answer("❌ Ошибка выбора наценки", show_alert=True)
        return
    
    await process_margin_input(callback_query, state, validation.value, is_callback=True)


@admin_flow_router.message(ExchangeFlow.WAITING_FOR_MARGIN, F.text)
async def handle_margin_text_input(message: Message, state: FSMContext):
    """Обработка ввода наценки текстом"""
    await process_margin_input(message, state, message.text, is_callback=False)


async def process_margin_input(
    update, state: FSMContext, margin_text: str, is_callback: bool
):
    """Общая обработка ввода наценки"""
    user_id = update.from_user.id
    
    # Валидируем наценку
    validation = ExchangeValidator.validate_margin_input(margin_text)
    if not validation.is_valid:
        error_text = MessageFormatter.format_margin_validation_error()
        keyboard = create_margin_input_keyboard()
        
        if is_callback:
            await update.message.edit_text(error_text, reply_markup=keyboard, parse_mode='HTML')
            await update.answer(f"❌ {validation.error}", show_alert=True)
        else:
            await update.reply(error_text, reply_markup=keyboard, parse_mode='HTML')
        return
    
    margin_percent = validation.value
    logger.info(f"Принята наценка: user_id={user_id}, margin={margin_percent}%")
    
    # Получаем данные из состояния
    data = await state.get_data()
    source_currency = Currency(data['source_currency'])
    target_currency = Currency(data['target_currency'])
    base_rate = Decimal(data['base_rate'])
    
    # Рассчитываем итоговый курс
    final_rate = ExchangeCalculator.calculate_final_rate(
        source_currency, target_currency, base_rate, margin_percent
    )
    
    # Сохраняем в состоянии
    await state.update_data(
        margin_percent=str(margin_percent),
        final_rate=str(final_rate)
    )
    
    # Переходим к вводу суммы
    await state.set_state(ExchangeFlow.WAITING_FOR_AMOUNT)
    
    # Формируем сообщение и клавиатуру
    message_text = MessageFormatter.format_margin_selected_message(
        source_currency, target_currency, base_rate, margin_percent, final_rate
    )
    keyboard = create_amount_input_keyboard()
    
    if is_callback:
        await update.message.edit_text(
            message_text, reply_markup=keyboard, parse_mode='HTML'
        )
        await update.answer()
    else:
        await update.reply(
            message_text, reply_markup=keyboard, parse_mode='HTML'
        )


# === ОБРАБОТЧИКИ ВВОДА СУММЫ ===

@admin_flow_router.callback_query(
    ExchangeFlow.WAITING_FOR_AMOUNT,
    F.data.startswith('amount_')
)
async def handle_amount_callback(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора суммы через кнопки"""
    validation = ExchangeValidator.validate_callback_data(callback_query.data, 'amount_')
    if not validation.is_valid:
        await callback_query.answer("❌ Ошибка выбора суммы", show_alert=True)
        return
    
    await process_amount_input(callback_query, state, validation.value, is_callback=True)


@admin_flow_router.message(ExchangeFlow.WAITING_FOR_AMOUNT, F.text)
async def handle_amount_text_input(message: Message, state: FSMContext):
    """Обработка ввода суммы текстом"""
    await process_amount_input(message, state, message.text, is_callback=False)


async def process_amount_input(
    update, state: FSMContext, amount_text: str, is_callback: bool
):
    """Общая обработка ввода суммы"""
    user_id = update.from_user.id
    
    # Получаем данные из состояния
    data = await state.get_data()
    source_currency = Currency(data['source_currency'])
    
    # Валидируем сумму
    validation = ExchangeValidator.validate_amount_input(amount_text, source_currency)
    if not validation.is_valid:
        error_text = MessageFormatter.format_amount_validation_error()
        keyboard = create_amount_input_keyboard()
        
        if is_callback:
            await update.message.edit_text(error_text, reply_markup=keyboard, parse_mode='HTML')
            await update.answer(f"❌ {validation.error}", show_alert=True)
        else:
            await update.reply(error_text, reply_markup=keyboard, parse_mode='HTML')
        return
    
    amount = validation.value
    logger.info(f"Принята сумма: user_id={user_id}, amount={amount} {source_currency.value}")
    
    # Получаем остальные данные
    target_currency = Currency(data['target_currency'])
    margin_percent = Decimal(data['margin_percent'])
    final_rate = Decimal(data['final_rate'])
    
    # Рассчитываем результат
    result = ExchangeCalculator.calculate_result(
        source_currency, target_currency, amount, final_rate
    )
    
    # Сохраняем в состоянии
    await state.update_data(
        amount=str(amount),
        result=str(result)
    )
    
    # Переходим к показу результата
    await state.set_state(ExchangeFlow.SHOWING_RESULT)
    
    # Формируем финальное сообщение
    message_text = MessageFormatter.format_final_result(
        source_currency, target_currency, amount, margin_percent, final_rate, result
    )
    keyboard = create_result_keyboard()
    
    if is_callback:
        await update.message.edit_text(
            message_text, reply_markup=keyboard, parse_mode='HTML'
        )
        await update.answer()
    else:
        await update.reply(
            message_text, reply_markup=keyboard, parse_mode='HTML'
        )
    
    logger.info(
        f"Сделка завершена: user_id={user_id}, "
        f"{source_currency.value}→{target_currency.value}, "
        f"amount={amount}, result={result}"
    )


# === ОБРАБОТЧИКИ НАВИГАЦИИ ===

@admin_flow_router.callback_query(F.data == 'back_to_source')
async def handle_back_to_source(callback_query: CallbackQuery, state: FSMContext):
    """Возврат к выбору исходной валюты"""
    await state.set_state(ExchangeFlow.WAITING_FOR_SOURCE_CURRENCY)
    
    welcome_text = MessageFormatter.format_welcome_message()
    keyboard = create_source_currency_keyboard()
    
    await callback_query.message.edit_text(
        welcome_text, reply_markup=keyboard, parse_mode='HTML'
    )
    await callback_query.answer()


@admin_flow_router.callback_query(F.data == 'back_to_target')
async def handle_back_to_target(callback_query: CallbackQuery, state: FSMContext):
    """Возврат к выбору целевой валюты"""
    data = await state.get_data()
    source_currency = Currency(data['source_currency'])
    
    await state.set_state(ExchangeFlow.WAITING_FOR_TARGET_CURRENCY)
    
    message_text = MessageFormatter.format_source_selected_message(source_currency)
    keyboard = create_target_currency_keyboard(source_currency)
    
    await callback_query.message.edit_text(
        message_text, reply_markup=keyboard, parse_mode='HTML'
    )
    await callback_query.answer()


@admin_flow_router.callback_query(F.data == 'back_to_margin')
async def handle_back_to_margin(callback_query: CallbackQuery, state: FSMContext):
    """Возврат к вводу наценки"""
    data = await state.get_data()
    source_currency = Currency(data['source_currency'])
    target_currency = Currency(data['target_currency'])
    base_rate = Decimal(data['base_rate'])
    
    await state.set_state(ExchangeFlow.WAITING_FOR_MARGIN)
    
    message_text = MessageFormatter.format_target_selected_message(
        source_currency, target_currency, base_rate
    )
    keyboard = create_margin_input_keyboard()
    
    await callback_query.message.edit_text(
        message_text, reply_markup=keyboard, parse_mode='HTML'
    )
    await callback_query.answer()


@admin_flow_router.callback_query(F.data == 'new_exchange')
async def handle_new_exchange(callback_query: CallbackQuery, state: FSMContext):
    """Начать новую сделку"""
    await state.clear()
    await state.set_state(ExchangeFlow.WAITING_FOR_SOURCE_CURRENCY)
    
    welcome_text = MessageFormatter.format_welcome_message()
    keyboard = create_source_currency_keyboard()
    
    await callback_query.message.edit_text(
        welcome_text, reply_markup=keyboard, parse_mode='HTML'
    )
    await callback_query.answer("🔄 Начинаем новую сделку")


@admin_flow_router.callback_query(F.data == 'main_menu')
async def handle_main_menu(callback_query: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    menu_text = (
        "📋 <b>Главное меню</b>\n\n"
        "Используйте команду /admin_bot для расчета курса обмена"
    )
    
    await callback_query.message.edit_text(menu_text, parse_mode='HTML')
    await callback_query.answer()


@admin_flow_router.callback_query(F.data == 'cancel_exchange')
async def handle_cancel_exchange(callback_query: CallbackQuery, state: FSMContext):
    """Отмена операции обмена"""
    await state.clear()
    
    cancel_text = MessageFormatter.format_cancel_message("Обмен валют")
    
    await callback_query.message.edit_text(cancel_text, parse_mode='HTML')
    await callback_query.answer("❌ Операция отменена")


# === ОБРАБОТЧИКИ ОШИБОК ===

@admin_flow_router.callback_query()
async def handle_unknown_callback(callback_query: CallbackQuery):
    """Обработка неизвестных callback'ов"""
    logger.warning(f"Неизвестный callback: {callback_query.data}")
    await callback_query.answer("❌ Неизвестная команда", show_alert=True)


@admin_flow_router.message()
async def handle_unknown_message(message: Message, state: FSMContext):
    """Обработка неожиданных сообщений"""
    current_state = await state.get_state()
    
    if current_state:
        error_text = (
            "❌ <b>Неожиданное сообщение</b>\n\n"
            "Используйте кнопки для навигации или введите корректное значение."
        )
    else:
        error_text = (
            "❌ <b>Неизвестная команда</b>\n\n"
            "Используйте /admin_bot для начала расчета курса."
        )
    
    await message.reply(error_text, parse_mode='HTML')