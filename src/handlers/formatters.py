#!/usr/bin/env python3
"""
Formatters для Crypto Helper Bot (Новая логика)
Форматирование сообщений для пошагового флоу обмена валют
"""

from decimal import Decimal
from .fsm_states import Currency


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
        rate_text = MessageFormatter._format_unified_rate(base_rate)
        
        return (
            f"✅ Направление: <b>{pair_text}</b>\n"
            f"📊 Текущий курс: {rate_text}\n\n"
            f"💰 Введите наценку в процентах (от 0.1% до 10%)\n"
            f"Или выберите готовое значение:"
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
        base_rate_text = MessageFormatter._format_unified_rate(base_rate)
        final_rate_text = MessageFormatter._format_unified_rate(final_rate)
        
        return (
            f"✅ Направление: <b>{pair_text}</b>\n"
            f"📊 Базовый курс: {base_rate_text}\n"
            f"💰 Наценка: <b>{margin_percent}%</b>\n"
            f"🎯 Итоговый курс: <b>{final_rate_text}</b>\n\n"
            f"💵 Введите сумму в {source.value}:\n"
            f"Или выберите готовое значение:"
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
        rate_text = MessageFormatter._format_unified_rate(final_rate)
        
        # Форматируем суммы
        amount_text = f"{amount:,.0f}".replace(",", " ")
        result_text = f"{result:,.2f}".replace(",", " ")
        
        return (
            f"✅ <b>Сделка рассчитана</b>\n\n"
            f"🔄 <b>{pair_text}</b>\n"
            f"• Сумма: <b>{amount_text} {source.value}</b>\n"
            f"• Курс (с наценкой {margin_percent}%): {rate_text}\n"
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
            "Введите число от 0.1 до 10 (например: 2.5)\n"
            "Или выберите готовое значение:"
        )
    
    @staticmethod
    def format_amount_validation_error() -> str:
        """Форматировать ошибку валидации суммы"""
        return (
            "❌ <b>Неверная сумма</b>\n\n"
            "Введите положительное число (например: 1000)\n"
            "Или выберите готовое значение:"
        )
    
    @staticmethod
    def _get_pair_text(source: Currency, target: Currency) -> str:
        """Получить текстовое представление валютной пары"""
        return f"{source.value} → {target.value}"
    
    @staticmethod
    def _format_unified_rate(rate: Decimal) -> str:
        """Форматировать курс в унифицированном виде"""
        formatted_rate = f"{rate:.2f}".replace(".", ",")
        return f"<b>1 USDT = {formatted_rate} RUB</b>"


# Для обратной совместимости (временно)
def format_welcome_message() -> str:
    """DEPRECATED: Используйте MessageFormatter.format_welcome_message()"""
    return MessageFormatter.format_welcome_message()


def format_cancel_message(operation: str = "Операция") -> str:
    """DEPRECATED: Используйте MessageFormatter.format_cancel_message()"""
    return MessageFormatter.format_cancel_message(operation) 