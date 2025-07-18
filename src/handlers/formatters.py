#!/usr/bin/env python3
"""
Модуль форматирования сообщений для Crypto Helper Bot
Содержит функции для форматирования результатов и шаблоны сообщений
"""

from decimal import Decimal
from typing import Dict, Any
from .calculation_logic import CalculationResult, MarginCalculator


class MessageFormatter:
    """Класс для форматирования сообщений бота"""
    
    @staticmethod
    def format_calculation_result(result: CalculationResult) -> str:
        """
        Форматирование результата расчета для отображения
        
        Args:
            result: Результат расчета
            
        Returns:
            str: Отформатированный результат
        """
        # Определяем валюты
        base_currency = result.pair_info['base']
        quote_currency = result.pair_info['quote']
        
        # Форматируем значения
        base_rate_display = MessageFormatter._format_rate_display(
            result.pair_info, float(result.base_rate)
        )
        final_rate_display = MessageFormatter._format_rate_display(
            result.pair_info, float(result.final_rate)
        )
        amount_display = MarginCalculator.format_amount_display(result.amount, base_currency)
        
        # Форматируем суммы
        amount_base_str = MarginCalculator.format_currency_value(result.amount_base_rate, quote_currency)
        amount_final_str = MarginCalculator.format_currency_value(result.amount_final_rate, quote_currency)
        amount_diff_str = MarginCalculator.format_currency_value(abs(result.amount_difference), quote_currency)
        
        # Определяем знаки изменения
        change_sign = "+" if result.rate_change >= 0 else "-"
        amount_change_sign = "+" if result.amount_difference >= 0 else "-"
        change_emoji = "📈" if result.rate_change >= 0 else "📉"
        
        # Определяем цвет для наценки
        margin_emoji = "📈" if result.margin >= 0 else "📉"
        margin_sign = "+" if result.margin >= 0 else ""
        
        # Временная метка
        timestamp = result.exchange_rate_data.get('timestamp', '')[:19].replace('T', ' ')
        
        message = (
            f"✅ <b>Расчет курса завершен</b>\n\n"
            f"{result.pair_info['emoji']} <b>{result.pair_info['name']}</b>\n"
            f"📝 <i>{result.pair_info['description']}</i>\n\n"
            
            f"💰 <b>Сумма расчета:</b> <code>{amount_display}</code> {base_currency}\n"
            f"💹 <b>Базовый курс:</b> {base_rate_display}\n"
            f"{margin_emoji} <b>Наценка:</b> <code>{margin_sign}{result.margin}%</code>\n"
            f"💎 <b>Итоговый курс:</b> {final_rate_display}\n\n"
            
            f"📊 <b>Расчет сумм:</b>\n"
            f"• По базовому курсу: <code>{amount_base_str}</code> {quote_currency}\n"
            f"• По итоговому курсу: <code>{amount_final_str}</code> {quote_currency}\n"
            f"{change_emoji} • Разница: <code>{amount_change_sign}{amount_diff_str}</code> {quote_currency}\n\n"
            
            f"🔢 <b>Детали расчета:</b>\n"
            f"• Базовый курс: {base_rate_display}\n"
            f"• Наценка: {margin_sign}{result.margin}% (множитель: {1 + result.margin/100:.6f})\n"
            f"• Итоговый курс: {final_rate_display}\n"
            f"• Расчет: {amount_display} × итоговый курс = {amount_final_str}\n\n"
            
            f"🕐 <b>Время получения курса:</b> {timestamp}\n"
            f"📡 <b>Источник:</b> {result.exchange_rate_data.get('source', 'N/A')}"
        )
        
        return message
    
    @staticmethod
    def format_amount_request(pair_info: Dict[str, Any]) -> str:
        """
        Форматирование запроса суммы для расчета
        
        Args:
            pair_info: Информация о валютной паре
            
        Returns:
            str: Отформатированное сообщение
        """
        return (
            f"💱 <b>Расчет курса с наценкой</b>\n\n"
            f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n"
            f"📝 <i>{pair_info['description']}</i>\n\n"
            f"💰 <b>Введите сумму в {pair_info['base']}:</b>\n\n"
            f"Пример: 1000 или 500.50"
        )
    
    @staticmethod
    def format_margin_request(
        pair_info: Dict[str, Any], 
        amount: Decimal, 
        exchange_rate_data: Dict[str, Any]
    ) -> str:
        """
        Форматирование запроса наценки
        
        Args:
            pair_info: Информация о валютной паре
            amount: Сумма для расчета
            exchange_rate_data: Данные о курсе
            
        Returns:
            str: Отформатированное сообщение
        """
        amount_display = MarginCalculator.format_amount_display(
            amount, pair_info['base']
        )
        rate = float(exchange_rate_data['rate'])
        
        # Форматируем курс в удобном виде
        rate_display = MessageFormatter._format_rate_display(
            pair_info, rate
        )
        
        return (
            f"💱 <b>Расчет курса с наценкой</b>\n\n"
            f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n"
            f"📝 <i>{pair_info['description']}</i>\n\n"
            f"💰 <b>Сумма:</b> <code>{amount_display}</code> "
            f"{pair_info['base']}\n"
            f"💹 <b>Текущий курс:</b> {rate_display}\n\n"
            f"📈 <b>Введите наценку в %:</b>\n\n"
            f"Пример: 5 или -1.2"
        )
    
    @staticmethod
    def format_error_message(error_type: str, error_details: str = "") -> str:
        """
        Форматирование сообщения об ошибке
        
        Args:
            error_type: Тип ошибки
            error_details: Детали ошибки
            
        Returns:
            str: Отформатированное сообщение об ошибке
        """
        error_messages = {
            'api_error': (
                f"❌ <b>Ошибка получения курса</b>\n\n"
                f"Не удалось получить текущий курс валютной пары:\n"
                f"<code>{error_details}</code>\n\n"
                f"🔄 Попробуйте позже или обратитесь к администратору.\n\n"
                f"🏠 Используйте /admin_bot для возврата к главному меню."
            ),
            'validation_amount': (
                f"❌ <b>Ошибка ввода суммы</b>\n\n"
                f"{error_details}\n\n"
                f"Пример: 1000 или 500.50"
            ),
            'validation_margin': (
                f"❌ <b>Ошибка ввода наценки</b>\n\n"
                f"{error_details}\n\n"
                f"Пример: 5 или -1.2"
            ),
            'generic': (
                f"❌ <b>Произошла ошибка</b>\n\n"
                f"{error_details or 'Не удалось выполнить операцию.'}\n"
                f"Попробуйте позже.\n\n"
                f"🏠 Используйте /admin_bot для возврата к главному меню."
            ),
            'invalid_content': (
                f"❌ <b>Некорректный ввод</b>\n\n"
                f"Пожалуйста, введите {error_details} в виде числа."
            )
        }
        
        return error_messages.get(error_type, error_messages['generic'])
    
    @staticmethod
    def format_welcome_message() -> str:
        """
        Форматирование приветственного сообщения
        
        Returns:
            str: Отформатированное приветственное сообщение
        """
        return (
            "🔧 <b>Панель управления</b>\n\n"
            "Добро пожаловать в Crypto Helper Bot!\n\n"
            "📊 <b>Выберите валютную пару:</b>\n\n"
            "• Выберите пару из списка\n"
            "• Укажите наценку\n"
            "• Укажите сумму\n"
            "• Получите результат\n\n"
            "💡 <i>Курсы обновляются в реальном времени</i>"
        )
    
    @staticmethod
    def format_cancel_message(operation: str) -> str:
        """
        Форматирование сообщения об отмене операции
        
        Args:
            operation: Название операции
            
        Returns:
            str: Отформатированное сообщение
        """
        return (
            f"❌ <b>{operation} отменена</b>\n\n"
            f"Операция была отменена пользователем.\n\n"
            f"🏠 Используйте /admin_bot для возврата к главному меню."
        )
    
    @staticmethod
    def format_margin_request_simple(
        pair_info: Dict[str, Any], 
        exchange_rate_data: Dict[str, Any]
    ) -> str:
        """
        Упрощенное форматирование запроса наценки
        
        Args:
            pair_info: Информация о валютной паре
            exchange_rate_data: Данные о курсе
            
        Returns:
            str: Отформатированное сообщение
        """
        rate = float(exchange_rate_data['rate'])
        
        # Форматируем курс в удобном виде
        rate_display = MessageFormatter._format_rate_display(
            pair_info, rate
        )
        
        return (
            f"💱 <b>Расчет курса с наценкой</b>\n\n"
            f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n"
            f"💹 <b>Текущий курс:</b> {rate_display}\n\n"
            f"📈 <b>Введите наценку в %:</b>\n\n"
            f"Пример: 5 или -1.2"
        )
    
    @staticmethod
    def format_rate_comparison(
        pair_info: Dict[str, Any], 
        exchange_rate_data: Dict[str, Any],
        margin: Decimal,
        final_rate: Decimal
    ) -> str:
        """
        Форматирование сравнения курсов
        
        Args:
            pair_info: Информация о валютной паре
            exchange_rate_data: Данные о курсе
            margin: Наценка в процентах
            final_rate: Итоговый курс
            
        Returns:
            str: Отформатированное сообщение
        """
        base_rate = float(exchange_rate_data['rate'])
        
        # Форматируем курсы в удобном виде
        base_rate_display = MessageFormatter._format_rate_display(
            pair_info, base_rate
        )
        final_rate_display = MessageFormatter._format_rate_display(
            pair_info, float(final_rate)
        )
        
        # Определяем знаки и эмодзи
        margin_sign = "+" if margin >= 0 else ""
        margin_emoji = "📈" if margin >= 0 else "📉"
        
        return (
            f"💱 <b>Сравнение курсов</b>\n\n"
            f"{pair_info['emoji']} <b>{pair_info['name']}</b>\n\n"
            f"💹 <b>Курс по бирже:</b> {base_rate_display}\n"
            f"{margin_emoji} <b>Наценка:</b> <code>{margin_sign}{margin}%</code>\n"
            f"💰 <b>Курс с наценкой:</b> {final_rate_display}\n\n"
            f"💰 <b>Введите сумму для расчета:</b>\n\n"
            f"Пример: 1000 или 500.50"
        )
    
    @staticmethod
    def format_calculation_result_simple(result: CalculationResult) -> str:
        """
        Упрощенное форматирование результата расчета
        
        Args:
            result: Результат расчета
            
        Returns:
            str: Отформатированный результат
        """
        # Определяем валюты
        base_currency = result.pair_info['base']
        quote_currency = result.pair_info['quote']
        
        # Форматируем значения
        base_rate_display = MessageFormatter._format_rate_display(
            result.pair_info, float(result.base_rate)
        )
        final_rate_display = MessageFormatter._format_rate_display(
            result.pair_info, float(result.final_rate)
        )
        amount_display = MarginCalculator.format_amount_display(result.amount, base_currency)
        amount_final_str = MarginCalculator.format_currency_value(result.amount_final_rate, quote_currency)
        
        # Определяем знаки и эмодзи
        margin_sign = "+" if result.margin >= 0 else ""
        margin_emoji = "📈" if result.margin >= 0 else "📉"
        
        return (
            f"✅ <b>Расчет завершен</b>\n\n"
            f"{result.pair_info['emoji']} <b>{result.pair_info['name']}</b>\n\n"
            f"💰 <b>Сумма:</b> <code>{amount_display}</code> {base_currency}\n"
            f"💹 <b>Курс по бирже:</b> {base_rate_display}\n"
            f"{margin_emoji} <b>Наценка:</b> <code>{margin_sign}{result.margin}%</code>\n"
            f"💰 <b>Курс с наценкой:</b> {final_rate_display}\n\n"
            f"💵 <b>Итого к получению:</b> <code>{amount_final_str}</code> {quote_currency}"
        )
    
    @staticmethod
    def _format_rate_display(
        pair_info: Dict[str, Any], 
        rate: float
    ) -> str:
        """
        Форматирование курса в удобном для чтения виде
        
        Args:
            pair_info: Информация о валютной паре
            rate: Курс для форматирования
            
        Returns:
            str: Отформатированный курс
        """
        base_currency = pair_info['base']
        quote_currency = pair_info['quote']
        
        # Для пар с рублем показываем в удобном формате
        if base_currency == 'RUB' and quote_currency in ['USDT', 'BTC', 'ETH', 'TON']:
            # RUB/USDT -> показываем как "1 USDT = X RUB"
            if rate > 0:
                inverted_rate = 1.0 / rate
                formatted_rate = MarginCalculator.format_currency_value(
                    Decimal(str(inverted_rate)), base_currency
                )
                return f"<code>1 {quote_currency} = {formatted_rate} {base_currency}</code>"
        
        elif quote_currency == 'RUB' and base_currency in ['USDT', 'BTC', 'ETH', 'TON']:
            # BTC/RUB -> показываем как "1 BTC = X RUB"
            formatted_rate = MarginCalculator.format_currency_value(
                Decimal(str(rate)), quote_currency
            )
            return f"<code>1 {base_currency} = {formatted_rate} {quote_currency}</code>"
        
        # Для остальных пар - стандартный формат
        formatted_rate = MarginCalculator.format_currency_value(
            Decimal(str(rate)), quote_currency
        )
        return f"<code>{formatted_rate}</code> {quote_currency}"