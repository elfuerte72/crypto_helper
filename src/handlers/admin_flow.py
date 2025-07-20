#!/usr/bin/env python3
"""
Admin Flow для Crypto Helper Bot (Новая логика)
Основной флоу для команды /admin_bot с пошаговым выбором валют
ТОЛЬКО РЕАЛЬНЫЕ API - БЕЗ ЗАГЛУШЕК!
"""

import asyncio
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
from .formatters import (
    MessageFormatter, 
    SafeMessageEditor, 
    LoadingMessageFormatter
)
from .validators import ExchangeValidator, ValidationResult

# Импорт API сервисов - ТОЛЬКО РЕАЛЬНЫЕ API
try:
    from ..services.api_service import api_service
    from ..services.fiat_rates_service import fiat_rates_service
    from ..services.models import RapiraAPIError, APILayerError
    from ..utils.logger import get_bot_logger
    from ..config import config
except ImportError:
    # Для прямого запуска файлов
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from services.api_service import api_service
    from services.fiat_rates_service import fiat_rates_service
    from services.models import RapiraAPIError, APILayerError
    from utils.logger import get_bot_logger
    from config import config

# Initialize components
logger = get_bot_logger()
admin_flow_router = Router()


# === АСИНХРОННАЯ ОБРАБОТКА API ЗАПРОСОВ (TASK-CRYPTO-002) ===

async def get_exchange_rate_with_loading(
    message: Message,
    source_currency: Currency,
    target_currency: Currency
) -> Optional[Decimal]:
    """
    Получить курс обмена с показом промежуточных сообщений загрузки
    Решает проблему callback timeout показом прогресса
    
    Args:
        message: Сообщение для обновления
        source_currency: Исходная валюта
        target_currency: Целевая валюта
        
    Returns:
        Optional[Decimal]: Курс обмена или None при ошибке
    """
    # Определяем источник API
    api_name = "Rapira API" if source_currency == Currency.USDT or target_currency == Currency.USDT else "APILayer"
    
    # Показываем сообщение загрузки
    loading_text = LoadingMessageFormatter.format_api_loading_message(api_name)
    edit_success = await SafeMessageEditor.safe_edit_message(
        message, loading_text, parse_mode='HTML'
    )
    
    if not edit_success:
        logger.warning("Не удалось обновить сообщение загрузки")
    
    # Выполняем API запрос с меньшим таймаутом
    try:
        # Используем сокращенный таймаут для callback обработки
        base_rate = await asyncio.wait_for(
            ExchangeCalculator.get_base_rate_for_pair(source_currency, target_currency),
            timeout=config.CALLBACK_API_TIMEOUT
        )
        logger.info(f"✅ Получен базовый курс: {base_rate}")
        return base_rate
        
    except asyncio.TimeoutError:
        logger.error(f"❌ API timeout ({config.CALLBACK_API_TIMEOUT}s) для пары {source_currency.value}/{target_currency.value}")
        
        # Показываем ошибку таймаута
        timeout_text = (
            f"⚠️ <b>Ошибка таймаута</b>\n\n"
            f"❌ Сервер {api_name} не отвечает ({config.CALLBACK_API_TIMEOUT}с)\n\n"
            f"🔄 Попробуйте еще раз через несколько секунд"
        )
        await SafeMessageEditor.safe_edit_message(
            message, timeout_text, parse_mode='HTML'
        )
        return None
        
    except (RapiraAPIError, APILayerError) as e:
        logger.error(f"❌ Ошибка API: {e}")
        
        # Показываем ошибку API
        api_error_text = (
            f"❌ <b>Ошибка API</b>\n\n"
            f"⚠️ {str(e)}\n\n"
            f"🔄 Попробуйте еще раз через несколько секунд"
        )
        await SafeMessageEditor.safe_edit_message(
            message, api_error_text, parse_mode='HTML'
        )
        return None
        
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        
        # Показываем общую ошибку
        error_text = (
            "❌ <b>Внутренняя ошибка</b>\n\n"
            "⚠️ Произошла неожиданная ошибка\n\n"
            "🔄 Попробуйте еще раз"
        )
        await SafeMessageEditor.safe_edit_message(
            message, error_text, parse_mode='HTML'
        )
        return None


async def safe_callback_answer_and_edit(
    callback_query: CallbackQuery,
    new_text: str,
    reply_markup=None,
    answer_text: str = "",
    show_alert: bool = False
) -> bool:
    """
    Безопасно ответить на callback и отредактировать сообщение
    Комбинирует ответ на callback и редактирование сообщения
    
    Args:
        callback_query: Callback query
        new_text: Новый текст сообщения
        reply_markup: Новая клавиатура
        answer_text: Текст ответа callback
        show_alert: Показать алерт
        
    Returns:
        bool: True если все операции успешны
    """
    # Отвечаем на callback параллельно
    answer_task = asyncio.create_task(
        SafeMessageEditor.safe_answer_callback(
            callback_query, answer_text, show_alert
        )
    )
    
    # Редактируем сообщение
    edit_success = await SafeMessageEditor.safe_edit_message(
        callback_query.message, new_text, reply_markup, parse_mode='HTML'
    )
    
    # Ожидаем завершение ответа callback
    answer_success = await answer_task
    
    if not answer_success:
        logger.warning("Не удалось ответить на callback query")
    
    if not edit_success:
        logger.warning("Не удалось отредактировать сообщение")
    
    return edit_success and answer_success


class ExchangeCalculator:
    """Калькулятор для расчета курсов и сумм обмена - ТОЛЬКО РЕАЛЬНЫЕ API"""
    
    @staticmethod
    async def get_usdt_rub_rate() -> Decimal:
        """Получить курс USDT/RUB от Rapira API"""
        try:
            logger.info("Получение курса USDT/RUB от Rapira API")
            rate = await api_service.get_exchange_rate('USDT/RUB')
            
            if rate and rate.rate > 0:
                result = Decimal(str(rate.rate))
                logger.info(f"✅ Получен курс USDT/RUB: {result} (источник: {rate.source})")
                return result
            else:
                logger.error("Rapira API вернул невалидный курс USDT/RUB")
                raise RapiraAPIError("Невалидный курс USDT/RUB")
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения курса USDT/RUB: {e}")
            raise RapiraAPIError(f"Не удалось получить курс USDT/RUB: {str(e)}")
    
    @staticmethod
    async def get_usd_rub_rate() -> Decimal:
        """Получить курс USD/RUB от APILayer"""
        try:
            logger.info("Получение курса USD/RUB от APILayer")
            rate = await fiat_rates_service.get_fiat_exchange_rate('USD/RUB')
            
            if rate and rate.rate > 0:
                result = Decimal(str(rate.rate))
                logger.info(f"✅ Получен курс USD/RUB: {result} (источник: {rate.source})")
                return result
            else:
                logger.error("APILayer вернул невалидный курс USD/RUB")
                raise APILayerError("Невалидный курс USD/RUB")
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения курса USD/RUB: {e}")
            raise APILayerError(f"Не удалось получить курс USD/RUB: {str(e)}")
    
    @staticmethod
    async def get_eur_rub_rate() -> Decimal:
        """Получить курс EUR/RUB от APILayer"""
        try:
            logger.info("Получение курса EUR/RUB от APILayer")
            rate = await fiat_rates_service.get_fiat_exchange_rate('EUR/RUB')
            
            if rate and rate.rate > 0:
                result = Decimal(str(rate.rate))
                logger.info(f"✅ Получен курс EUR/RUB: {result} (источник: {rate.source})")
                return result
            else:
                logger.error("APILayer вернул невалидный курс EUR/RUB")
                raise APILayerError("Невалидный курс EUR/RUB")
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения курса EUR/RUB: {e}")
            raise APILayerError(f"Не удалось получить курс EUR/RUB: {str(e)}")
    
    @staticmethod
    async def get_thb_rub_rate() -> Decimal:
        """Получить курс THB/RUB от APILayer"""
        try:
            logger.info("Получение курса THB/RUB от APILayer")
            rate = await fiat_rates_service.get_fiat_exchange_rate('THB/RUB')
            
            if rate and rate.rate > 0:
                result = Decimal(str(rate.rate))
                logger.info(f"✅ Получен курс THB/RUB: {result} (источник: {rate.source})")
                return result
            else:
                logger.error("APILayer вернул невалидный курс THB/RUB")
                raise APILayerError("Невалидный курс THB/RUB")
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения курса THB/RUB: {e}")
            raise APILayerError(f"Не удалось получить курс THB/RUB: {str(e)}")
    
    @staticmethod
    async def get_aed_rub_rate() -> Decimal:
        """Получить курс AED/RUB от APILayer"""
        try:
            logger.info("Получение курса AED/RUB от APILayer")
            rate = await fiat_rates_service.get_fiat_exchange_rate('AED/RUB')
            
            if rate and rate.rate > 0:
                result = Decimal(str(rate.rate))
                logger.info(f"✅ Получен курс AED/RUB: {result} (источник: {rate.source})")
                return result
            else:
                logger.error("APILayer вернул невалидный курс AED/RUB")
                raise APILayerError("Невалидный курс AED/RUB")
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения курса AED/RUB: {e}")
            raise APILayerError(f"Не удалось получить курс AED/RUB: {str(e)}")
    
    @staticmethod
    async def get_zar_rub_rate() -> Decimal:
        """Получить курс ZAR/RUB от APILayer"""
        try:
            logger.info("Получение курса ZAR/RUB от APILayer")
            rate = await fiat_rates_service.get_fiat_exchange_rate('ZAR/RUB')
            
            if rate and rate.rate > 0:
                result = Decimal(str(rate.rate))
                logger.info(f"✅ Получен курс ZAR/RUB: {result} (источник: {rate.source})")
                return result
            else:
                logger.error("APILayer вернул невалидный курс ZAR/RUB")
                raise APILayerError("Невалидный курс ZAR/RUB")
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения курса ZAR/RUB: {e}")
            raise APILayerError(f"Не удалось получить курс ZAR/RUB: {str(e)}")
    
    @staticmethod
    async def get_idr_rub_rate() -> Decimal:
        """Получить курс IDR/RUB от APILayer"""
        try:
            logger.info("Получение курса IDR/RUB от APILayer")
            rate = await fiat_rates_service.get_fiat_exchange_rate('IDR/RUB')
            
            if rate and rate.rate > 0:
                result = Decimal(str(rate.rate))
                logger.info(f"✅ Получен курс IDR/RUB: {result} (источник: {rate.source})")
                return result
            else:
                logger.error("APILayer вернул невалидный курс IDR/RUB")
                raise APILayerError("Невалидный курс IDR/RUB")
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения курса IDR/RUB: {e}")
            raise APILayerError(f"Не удалось получить курс IDR/RUB: {str(e)}")
    
    @staticmethod
    async def get_usdt_to_fiat_rate(target_currency: Currency) -> Decimal:
        """
        Получить курс USDT к фиатной валюте через кросс-конвертацию
        Логика: USDT/RUB ÷ TARGET/RUB = USDT/TARGET (обратный курс)
        Пример: USDT/USD = USDT/RUB ÷ USD/RUB = 100 ÷ 100 = 1.0
        """
        logger.info(f"Получение курса USDT/{target_currency.value} через кросс-конвертацию")
        
        try:
            # Получаем USDT/RUB
            usdt_rub_rate = await ExchangeCalculator.get_usdt_rub_rate()
            
            # Получаем TARGET/RUB
            if target_currency == Currency.USD:
                target_rub_rate = await ExchangeCalculator.get_usd_rub_rate()
            elif target_currency == Currency.EUR:
                target_rub_rate = await ExchangeCalculator.get_eur_rub_rate()
            elif target_currency == Currency.THB:
                target_rub_rate = await ExchangeCalculator.get_thb_rub_rate()
            elif target_currency == Currency.AED:
                target_rub_rate = await ExchangeCalculator.get_aed_rub_rate()
            elif target_currency == Currency.ZAR:
                target_rub_rate = await ExchangeCalculator.get_zar_rub_rate()
            elif target_currency == Currency.IDR:
                target_rub_rate = await ExchangeCalculator.get_idr_rub_rate()
            else:
                raise ValueError(f"Неподдерживаемая валюта для кросс-конвертации: {target_currency.value}")
            
            # Рассчитываем кросс-курс: USDT/TARGET = USDT/RUB ÷ TARGET/RUB
            cross_rate = usdt_rub_rate / target_rub_rate
            
            logger.info(
                f"✅ Кросс-курс USDT/{target_currency.value}: "
                f"USDT/RUB ({usdt_rub_rate}) ÷ {target_currency.value}/RUB ({target_rub_rate}) = {cross_rate}"
            )
            
            return cross_rate.quantize(Decimal('0.000001'))  # Округляем до 6 знаков
            
        except Exception as e:
            logger.error(f"❌ Ошибка кросс-конвертации USDT/{target_currency.value}: {e}")
            raise
    
    @staticmethod
    async def get_base_rate_for_pair(source_currency: Currency, target_currency: Currency) -> Decimal:
        """
        Получить базовый курс для валютной пары - СТРОГО С API
        
        Логика:
        - RUB → USDT: получаем USDT/RUB от Rapira API (для обратного расчета)
        - RUB → USD: получаем USD/RUB от APILayer
        - RUB → EUR: получаем EUR/RUB от APILayer  
        - USDT → RUB: получаем USDT/RUB от Rapira API
        """
        logger.info(f"Получение базового курса для пары {source_currency.value} → {target_currency.value}")
        
        try:
            if source_currency == Currency.RUB and target_currency == Currency.USDT:
                # RUB → USDT: получаем USDT/RUB для обратного расчета
                return await ExchangeCalculator.get_usdt_rub_rate()
                
            elif source_currency == Currency.RUB and target_currency == Currency.USD:
                # RUB → USD: получаем USD/RUB
                return await ExchangeCalculator.get_usd_rub_rate()
                
            elif source_currency == Currency.RUB and target_currency == Currency.EUR:
                # RUB → EUR: получаем EUR/RUB
                return await ExchangeCalculator.get_eur_rub_rate()
                
            elif source_currency == Currency.RUB and target_currency == Currency.THB:
                # RUB → THB: получаем THB/RUB
                return await ExchangeCalculator.get_thb_rub_rate()
                
            elif source_currency == Currency.RUB and target_currency == Currency.AED:
                # RUB → AED: получаем AED/RUB
                return await ExchangeCalculator.get_aed_rub_rate()
                
            elif source_currency == Currency.RUB and target_currency == Currency.ZAR:
                # RUB → ZAR: получаем ZAR/RUB
                return await ExchangeCalculator.get_zar_rub_rate()
                
            elif source_currency == Currency.RUB and target_currency == Currency.IDR:
                # RUB → IDR: получаем IDR/RUB
                return await ExchangeCalculator.get_idr_rub_rate()
                
            elif source_currency == Currency.USDT and target_currency == Currency.RUB:
                # USDT → RUB: получаем USDT/RUB
                return await ExchangeCalculator.get_usdt_rub_rate()
                
            elif source_currency == Currency.USDT and target_currency in [Currency.USD, Currency.EUR, Currency.THB, Currency.AED, Currency.ZAR, Currency.IDR]:
                # USDT → фиатная валюта: получаем кросс-курс
                return await ExchangeCalculator.get_usdt_to_fiat_rate(target_currency)
                
            else:
                raise ValueError(f"Неподдерживаемая валютная пара: {source_currency.value} → {target_currency.value}")
                
        except (RapiraAPIError, APILayerError) as e:
            logger.error(f"❌ API ошибка для пары {source_currency.value}/{target_currency.value}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка для пары {source_currency.value}/{target_currency.value}: {e}")
            raise
    
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
        
        logger.info(f"Расчет итогового курса: {source.value}→{target.value}, базовый={base_rate}, наценка={margin_percent}%")
        
        if source == Currency.RUB:
            # Клиент отдает рубли - увеличиваем курс (меньше получит криптовалюты/фиата)
            final_rate = base_rate * (Decimal('1') + margin_factor)
            logger.info(f"RUB→{target.value}: {base_rate} × (1 + {margin_percent}/100) = {final_rate}")
        elif source == Currency.USDT:
            # Клиент отдает USDT - уменьшаем курс (меньше получит целевой валюты)
            final_rate = base_rate * (Decimal('1') - margin_factor)
            logger.info(f"USDT→{target.value}: {base_rate} × (1 - {margin_percent}/100) = {final_rate}")
        else:
            # На будущее - другие исходные валюты
            final_rate = base_rate * (Decimal('1') - margin_factor)
            logger.info(f"{source.value}→{target.value}: {base_rate} × (1 - {margin_percent}/100) = {final_rate}")
        
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
        logger.info(f"Расчет результата: {amount} {source.value} → {target.value}, курс={final_rate}")
        
        if source == Currency.RUB:
            # Делим сумму рублей на курс
            result = amount / final_rate
            logger.info(f"RUB→{target.value}: {amount} / {final_rate} = {result}")
        elif source == Currency.USDT:
            # Умножаем сумму USDT на курс
            result = amount * final_rate
            logger.info(f"USDT→{target.value}: {amount} × {final_rate} = {result}")
        else:
            # На будущее - другие исходные валюты
            result = amount * final_rate
            logger.info(f"{source.value}→{target.value}: {amount} × {final_rate} = {result}")
        
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
    """Обработка выбора исходной валюты - ОБНОВЛЕНО ДЛЯ TASK-CRYPTO-002"""
    user_id = callback_query.from_user.id
    
    # Валидируем callback данные
    validation = ExchangeValidator.validate_callback_data(callback_query.data, 'source_')
    if not validation.is_valid:
        await SafeMessageEditor.safe_answer_callback(
            callback_query, "❌ Ошибка выбора валюты", show_alert=True
        )
        return
    
    try:
        source_currency = Currency(validation.value)
    except ValueError:
        await SafeMessageEditor.safe_answer_callback(
            callback_query, "❌ Неизвестная валюта", show_alert=True
        )
        return
    
    logger.info(f"Выбрана исходная валюта: user_id={user_id}, source={source_currency.value}")
    
    # Сохраняем в состоянии
    await state.update_data(source_currency=source_currency.value)
    
    # Переходим к выбору целевой валюты
    await state.set_state(ExchangeFlow.WAITING_FOR_TARGET_CURRENCY)
    
    # Формируем сообщение и клавиатуру
    message_text = MessageFormatter.format_source_selected_message(source_currency)
    keyboard = create_target_currency_keyboard(source_currency)
    
    # Используем безопасное редактирование с ответом на callback
    await safe_callback_answer_and_edit(
        callback_query,
        message_text,
        keyboard,
        answer_text="✅ Исходная валюта выбрана"
    )


# === ОБРАБОТЧИКИ ВЫБОРА ЦЕЛЕВОЙ ВАЛЮТЫ ===

@admin_flow_router.callback_query(
    ExchangeFlow.WAITING_FOR_TARGET_CURRENCY,
    F.data.startswith('target_')
)
async def handle_target_currency_selection(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора целевой валюты - ОБНОВЛЕНО ДЛЯ TASK-CRYPTO-002"""
    user_id = callback_query.from_user.id
    
    # Мгновенно отвечаем на callback для избежания timeout
    await SafeMessageEditor.safe_answer_callback(
        callback_query, "⏳ Проверка валютной пары..."
    )
    
    # Валидируем callback данные
    validation = ExchangeValidator.validate_callback_data(callback_query.data, 'target_')
    if not validation.is_valid:
        error_text = "❌ <b>Ошибка выбора валюты</b>\n\nПопробуйте еще раз."
        await SafeMessageEditor.safe_edit_message(
            callback_query.message, error_text, parse_mode='HTML'
        )
        return
    
    try:
        target_currency = Currency(validation.value)
    except ValueError:
        error_text = "❌ <b>Неизвестная валюта</b>\n\nПопробуйте еще раз."
        await SafeMessageEditor.safe_edit_message(
            callback_query.message, error_text, parse_mode='HTML'
        )
        return
    
    # Получаем исходную валюту из состояния
    data = await state.get_data()
    source_currency = Currency(data['source_currency'])
    
    # Валидируем валютную пару
    pair_validation = ExchangeValidator.validate_currency_pair(source_currency, target_currency)
    if not pair_validation.is_valid:
        error_text = f"❌ <b>Недопустимая пара</b>\n\n{pair_validation.error}"
        await SafeMessageEditor.safe_edit_message(
            callback_query.message, error_text, parse_mode='HTML'
        )
        return
    
    logger.info(f"Выбрана валютная пара: user_id={user_id}, {source_currency.value}→{target_currency.value}")
    
    # Получаем базовый курс с показом прогресса
    base_rate = await get_exchange_rate_with_loading(
        callback_query.message, source_currency, target_currency
    )
    
    if base_rate is None:
        # Ошибка уже отображена в get_exchange_rate_with_loading
        return
    
    logger.info(f"✅ Получен базовый курс: {base_rate}")
    
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
    
    # Безопасно редактируем сообщение
    await SafeMessageEditor.safe_edit_message(
        callback_query.message,
        message_text,
        keyboard,
        parse_mode='HTML'
    )


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
    """Возврат к выбору исходной валюты - ОБНОВЛЕНО ДЛЯ TASK-CRYPTO-002"""
    await state.set_state(ExchangeFlow.WAITING_FOR_SOURCE_CURRENCY)
    
    welcome_text = MessageFormatter.format_welcome_message()
    keyboard = create_source_currency_keyboard()
    
    await safe_callback_answer_and_edit(
        callback_query,
        welcome_text, 
        keyboard,
        answer_text="⬅️ Возврат к выбору валюты"
    )


@admin_flow_router.callback_query(F.data == 'back_to_target')
async def handle_back_to_target(callback_query: CallbackQuery, state: FSMContext):
    """Возврат к выбору целевой валюты - ОБНОВЛЕНО ДЛЯ TASK-CRYPTO-002"""
    data = await state.get_data()
    source_currency = Currency(data['source_currency'])
    
    await state.set_state(ExchangeFlow.WAITING_FOR_TARGET_CURRENCY)
    
    message_text = MessageFormatter.format_source_selected_message(source_currency)
    keyboard = create_target_currency_keyboard(source_currency)
    
    await safe_callback_answer_and_edit(
        callback_query,
        message_text, 
        keyboard,
        answer_text="⬅️ Возврат к выбору целевой валюты"
    )


@admin_flow_router.callback_query(F.data == 'back_to_margin')
async def handle_back_to_margin(callback_query: CallbackQuery, state: FSMContext):
    """Возврат к вводу наценки - ОБНОВЛЕНО ДЛЯ TASK-CRYPTO-002"""
    data = await state.get_data()
    source_currency = Currency(data['source_currency'])
    target_currency = Currency(data['target_currency'])
    base_rate = Decimal(data['base_rate'])
    
    await state.set_state(ExchangeFlow.WAITING_FOR_MARGIN)
    
    message_text = MessageFormatter.format_target_selected_message(
        source_currency, target_currency, base_rate
    )
    keyboard = create_margin_input_keyboard()
    
    await safe_callback_answer_and_edit(
        callback_query,
        message_text, 
        keyboard,
        answer_text="⬅️ Возврат к вводу наценки"
    )


@admin_flow_router.callback_query(F.data == 'new_exchange')
async def handle_new_exchange(callback_query: CallbackQuery, state: FSMContext):
    """Начать новую сделку - ОБНОВЛЕНО ДЛЯ TASK-CRYPTO-002"""
    await state.clear()
    await state.set_state(ExchangeFlow.WAITING_FOR_SOURCE_CURRENCY)
    
    welcome_text = MessageFormatter.format_welcome_message()
    keyboard = create_source_currency_keyboard()
    
    await safe_callback_answer_and_edit(
        callback_query,
        welcome_text, 
        keyboard,
        answer_text="🔄 Начинаем новую сделку"
    )


@admin_flow_router.callback_query(F.data == 'main_menu')
async def handle_main_menu(callback_query: CallbackQuery, state: FSMContext):
    """Возврат в главное меню - ОБНОВЛЕНО ДЛЯ TASK-CRYPTO-002"""
    await state.clear()
    
    menu_text = (
        "📋 <b>Главное меню</b>\n\n"
        "Используйте команду /admin_bot для расчета курса обмена"
    )
    
    await safe_callback_answer_and_edit(
        callback_query,
        menu_text,
        reply_markup=None,
        answer_text="📋 Переход в главное меню"
    )


@admin_flow_router.callback_query(F.data == 'cancel_exchange')
async def handle_cancel_exchange(callback_query: CallbackQuery, state: FSMContext):
    """Отмена операции обмена - ОБНОВЛЕНО ДЛЯ TASK-CRYPTO-002"""
    await state.clear()
    
    cancel_text = MessageFormatter.format_cancel_message("Обмен валют")
    
    await safe_callback_answer_and_edit(
        callback_query,
        cancel_text,
        reply_markup=None,
        answer_text="❌ Операция отменена"
    )


# === ОБРАБОТЧИКИ ОШИБОК ===

@admin_flow_router.callback_query()
async def handle_unknown_callback(callback_query: CallbackQuery):
    """Обработка неизвестных callback'ов - ОБНОВЛЕНО ДЛЯ TASK-CRYPTO-002"""
    logger.warning(f"Неизвестный callback: {callback_query.data}")
    await SafeMessageEditor.safe_answer_callback(
        callback_query, "❌ Неизвестная команда", show_alert=True
    )


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