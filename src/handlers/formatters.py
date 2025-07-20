#!/usr/bin/env python3
"""
Formatters для Crypto Helper Bot (Новая логика)
Форматирование сообщений для пошагового флоу обмена валют
+ Утилиты для безопасного редактирования сообщений (TASK-CRYPTO-002)
"""

import asyncio
import hashlib
from decimal import Decimal
from typing import Optional, Union
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from .fsm_states import Currency

try:
    from ..config import config
    from ..utils.logger import get_bot_logger
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config
    from utils.logger import get_bot_logger

logger = get_bot_logger()


class MessageFormatter:
    """Класс для форматирования сообщений бота"""
    
    @staticmethod
    def format_welcome_message() -> str:
        """Форматировать приветственное сообщение /admin_bot"""
        return (
            "🔄 <b>Калькулятор обмена валют</b>\n\n"
            "Выберите валюту, которую <b>отдает клиент</b>:"
        )
    
    @staticmethod
    def format_source_selected_message(currency: Currency) -> str:
        """Форматировать сообщение после выбора исходной валюты"""
        currency_names = {
            Currency.RUB: "рубли",
            Currency.USDT: "USDT"
        }
        
        currency_name = currency_names.get(currency, currency.value)
        
        return (
            f"✅ Клиент отдает: <b>{currency_name}</b>\n\n"
            f"Теперь выберите валюту, которую клиент <b>получает</b>:"
        )
    
    @staticmethod
    def format_target_selected_message(
        source: Currency, 
        target: Currency,
        base_rate: Decimal
    ) -> str:
        """Форматировать сообщение после выбора целевой валюты"""
        pair_text = MessageFormatter._get_pair_text(source, target)
        rate_text = MessageFormatter._format_rate_for_pair(source, target, base_rate)
        
        return (
            f"✅ Направление: <b>{pair_text}</b>\n"
            f"📊 Текущий курс: {rate_text}\n\n"
            f"💰 Введите наценку в процентах ( 1% или 6.8%):"
        )
    
    @staticmethod
    def format_margin_selected_message(
        source: Currency,
        target: Currency, 
        base_rate: Decimal,
        margin_percent: Decimal,
        final_rate: Decimal
    ) -> str:
        """Форматировать сообщение после выбора наценки"""
        pair_text = MessageFormatter._get_pair_text(source, target)
        base_rate_text = MessageFormatter._format_rate_for_pair(source, target, base_rate)
        final_rate_text = MessageFormatter._format_rate_for_pair(source, target, final_rate)
        
        return (
            f"✅ Направление: <b>{pair_text}</b>\n"
            f"📊 Базовый курс: {base_rate_text}\n"
            f"💰 Наценка: <b>{margin_percent}%</b>\n"
            f"🎯 Итоговый курс: <b>{final_rate_text}</b>\n\n"
            f"💵 Введите сумму в {source.value}:"
        )
    
    @staticmethod
    def format_final_result(
        source: Currency,
        target: Currency,
        amount: Decimal,
        margin_percent: Decimal,
        final_rate: Decimal,
        result: Decimal
    ) -> str:
        """Форматировать финальный результат сделки"""
        pair_text = MessageFormatter._get_pair_text(source, target)
        rate_text = MessageFormatter._format_rate_for_pair(source, target, final_rate)
        
        # Форматируем суммы
        amount_text = f"{amount:,.0f}".replace(",", " ")
        result_text = f"{result:,.2f}".replace(",", " ")
        
        return (
            f"✅ <b>Сделка рассчитана</b>\n\n"
            f"🔄 <b>{pair_text}</b>\n"
            f"• Сумма: <b>{amount_text} {source.value}</b>\n"
            f"• Итоговый курс: {rate_text}\n"
            f"• Итого: <b>{result_text} {target.value}</b>\n\n"
            f"Выберите дальнейшее действие:"
        )
    
    @staticmethod
    def format_cancel_message(operation: str = "Операция") -> str:
        """Форматировать сообщение отмены"""
        return f"❌ <b>{operation} отменена</b>\n\nВведите /admin_bot для начала."
    
    @staticmethod
    def format_error_message(error: str) -> str:
        """Форматировать сообщение об ошибке"""
        return f"❌ <b>Ошибка:</b> {error}\n\nПопробуйте еще раз."
    
    @staticmethod
    def format_margin_validation_error() -> str:
        """Форматировать ошибку валидации наценки"""
        return (
            "❌ <b>Неверная наценка</b>\n\n"
            "Введите число от 0.1 до 10 (например: 2.5):"
        )
    
    @staticmethod
    def format_amount_validation_error() -> str:
        """Форматировать ошибку валидации суммы"""
        return (
            "❌ <b>Неверная сумма</b>\n\n"
            "Введите положительное число (например: 1000):"
        )
    
    @staticmethod
    def _get_pair_text(source: Currency, target: Currency) -> str:
        """Получить текстовое представление валютной пары"""
        return f"{source.value} → {target.value}"
    
    @staticmethod
    def _format_rate_for_pair(source: Currency, target: Currency, rate: Decimal) -> str:
        """Форматировать курс с учетом валютной пары"""
        formatted_rate = f"{rate:.2f}".replace(".", ",")
        
        # Для RUB → любая валюта: показываем сколько рублей за 1 единицу целевой валюты
        if source == Currency.RUB:
            return f"<b>1 {target.value} = {formatted_rate} RUB</b>"
        # Для USDT → RUB: показываем сколько рублей за 1 USDT  
        elif source == Currency.USDT and target == Currency.RUB:
            return f"<b>1 USDT = {formatted_rate} RUB</b>"
        # Для USDT → другие валюты: показываем сколько целевой валюты за 1 USDT
        elif source == Currency.USDT:
            return f"<b>1 USDT = {formatted_rate} {target.value}</b>"
        # Остальные случаи (на будущее)
        else:
            return f"<b>1 {source.value} = {formatted_rate} {target.value}</b>"
    
    @staticmethod
    def _format_unified_rate(rate: Decimal) -> str:
        """Форматировать курс в унифицированном виде (DEPRECATED)"""
        formatted_rate = f"{rate:.2f}".replace(".", ",")
        return f"<b>1 USDT = {formatted_rate} RUB</b>"


class SafeMessageEditor:
    """
    Утилита для безопасного редактирования сообщений Telegram
    Исправляет ошибки "message is not modified" и callback timeout
    """
    
    @staticmethod
    def _get_message_hash(text: str, markup_data: str = "") -> str:
        """Получить хэш содержимого сообщения для проверки изменений"""
        content = f"{text}|{markup_data}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    @staticmethod
    async def safe_edit_message(
        message: Message,
        new_text: str,
        reply_markup=None,
        parse_mode: str = 'HTML',
        max_attempts: int = None
    ) -> bool:
        """
        Безопасно редактировать сообщение с проверкой изменений
        
        Args:
            message: Сообщение для редактирования
            new_text: Новый текст
            reply_markup: Новая клавиатура
            parse_mode: Режим парсинга
            max_attempts: Максимум попыток
            
        Returns:
            bool: True если успешно отредактировано
        """
        max_attempts = max_attempts or config.MAX_MESSAGE_EDIT_ATTEMPTS
        
        # Проверяем, изменился ли контент
        current_text = message.text or message.caption or ""
        markup_data = str(reply_markup) if reply_markup else ""
        
        current_hash = SafeMessageEditor._get_message_hash(current_text, str(message.reply_markup))
        new_hash = SafeMessageEditor._get_message_hash(new_text, markup_data)
        
        if current_hash == new_hash:
            logger.debug("Message content unchanged, skipping edit")
            return True
        
        # Пытаемся отредактировать с повторными попытками
        for attempt in range(max_attempts):
            try:
                await message.edit_text(
                    text=new_text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                logger.debug(f"Message edited successfully on attempt {attempt + 1}")
                return True
                
            except TelegramBadRequest as e:
                error_msg = str(e).lower()
                
                if "message is not modified" in error_msg:
                    logger.debug("Message is not modified (content identical)")
                    return True
                    
                elif "message to edit not found" in error_msg:
                    logger.warning("Message to edit not found")
                    return False
                    
                elif "bad request" in error_msg and attempt < max_attempts - 1:
                    logger.warning(f"Bad request on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(0.5)
                    continue
                    
                else:
                    logger.error(f"TelegramBadRequest: {e}")
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error editing message: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(0.5)
                    continue
                return False
        
        logger.error(f"Failed to edit message after {max_attempts} attempts")
        return False
    
    @staticmethod
    async def safe_answer_callback(
        callback_query: CallbackQuery,
        text: str = "",
        show_alert: bool = False,
        timeout: float = None
    ) -> bool:
        """
        Безопасно ответить на callback query с таймаутом
        
        Args:
            callback_query: Callback query
            text: Текст ответа
            show_alert: Показать алерт
            timeout: Таймаут в секундах
            
        Returns:
            bool: True если успешно отвечено
        """
        timeout = timeout or config.CALLBACK_ANSWER_TIMEOUT
        
        try:
            await asyncio.wait_for(
                callback_query.answer(text=text, show_alert=show_alert),
                timeout=timeout
            )
            logger.debug("Callback query answered successfully")
            return True
            
        except asyncio.TimeoutError:
            logger.warning(f"Callback answer timeout after {timeout}s")
            return False
            
        except TelegramBadRequest as e:
            error_msg = str(e).lower()
            if "query is too old" in error_msg:
                logger.warning("Callback query is too old")
            else:
                logger.error(f"TelegramBadRequest answering callback: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error answering callback: {e}")
            return False


class LoadingMessageFormatter:
    """
    Форматирование промежуточных сообщений загрузки
    Решает проблему callback timeout показом прогресса
    """
    
    @staticmethod
    def format_loading_message(operation: str = "Загрузка", step: int = 1, total: int = 3) -> str:
        """
        Форматировать сообщение загрузки с прогрессом
        
        Args:
            operation: Описание операции
            step: Текущий шаг
            total: Общее количество шагов
            
        Returns:
            str: Форматированное сообщение
        """
        progress_bar = LoadingMessageFormatter._create_progress_bar(step, total)
        
        return (
            f"⏳ <b>{operation}...</b>\n\n"
            f"Прогресс: {progress_bar} {step}/{total}\n\n"
            f"<i>Пожалуйста, подождите...</i>"
        )
    
    @staticmethod
    def format_api_loading_message(api_name: str = "API") -> str:
        """
        Форматировать сообщение загрузки API запроса
        
        Args:
            api_name: Название API
            
        Returns:
            str: Форматированное сообщение
        """
        return (
            f"🔄 <b>Получение курса от {api_name}</b>\n\n"
            f"⏳ Выполняется запрос к серверу...\n\n"
            f"<i>Это может занять несколько секунд</i>"
        )
    
    @staticmethod
    def format_calculation_loading_message() -> str:
        """
        Форматировать сообщение расчета курса
        
        Returns:
            str: Форматированное сообщение
        """
        return (
            "🧮 <b>Расчет курса</b>\n\n"
            "⏳ Применение наценки и расчет результата...\n\n"
            "<i>Секундочку...</i>"
        )
    
    @staticmethod
    def _create_progress_bar(current: int, total: int, length: int = 10) -> str:
        """
        Создать текстовый прогресс-бар
        
        Args:
            current: Текущее значение
            total: Максимальное значение
            length: Длина прогресс-бара
            
        Returns:
            str: Прогресс-бар
        """
        filled = int((current / total) * length)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}]"
    
    @staticmethod
    def format_error_with_retry(error_msg: str, attempt: int, max_attempts: int) -> str:
        """
        Форматировать сообщение ошибки с информацией о повторных попытках
        
        Args:
            error_msg: Сообщение об ошибке
            attempt: Номер попытки
            max_attempts: Максимум попыток
            
        Returns:
            str: Форматированное сообщение
        """
        return (
            f"⚠️ <b>Ошибка (попытка {attempt}/{max_attempts})</b>\n\n"
            f"❌ {error_msg}\n\n"
            f"🔄 Повторная попытка через несколько секунд..."
        )


# Для обратной совместимости (временно)
def format_welcome_message() -> str:
    """DEPRECATED: Используйте MessageFormatter.format_welcome_message()"""
    return MessageFormatter.format_welcome_message()


def format_cancel_message(operation: str = "Операция") -> str:
    """DEPRECATED: Используйте MessageFormatter.format_cancel_message()"""
    return MessageFormatter.format_cancel_message(operation) 