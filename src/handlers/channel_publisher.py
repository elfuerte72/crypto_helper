#!/usr/bin/env python3
"""
Модуль для публикации результатов расчета курса в канал
Crypto Helper Bot - Channel Publisher
"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

try:
    from ..config import config
    from ..utils.logger import get_bot_logger
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config
    from utils.logger import get_bot_logger

# Initialize logger
logger = get_bot_logger()


class ChannelPublisherError(Exception):
    """Исключение для ошибок публикации в канал"""
    pass


class ChannelPublisher:
    """Класс для публикации результатов расчета курса в канал"""
    
    @staticmethod
    def format_channel_message(
        pair_info: Dict[str, Any],
        base_rate: Decimal,
        margin: Decimal,
        final_rate: Decimal,
        rate_change: Decimal,
        exchange_rate_data: Dict[str, Any],
        manager_name: str = "Менеджер"
    ) -> str:
        """
        Форматирование сообщения для публикации в канал
        
        Args:
            pair_info: Информация о валютной паре
            base_rate: Базовый курс
            margin: Процентная наценка
            final_rate: Итоговый курс
            rate_change: Изменение курса
            exchange_rate_data: Данные о курсе
            manager_name: Имя менеджера
            
        Returns:
            str: Отформатированное сообщение для канала
        """
        # Определяем валюты
        base_currency = pair_info['base']
        quote_currency = pair_info['quote']
        
        # Форматируем значения для отображения
        base_rate_str = ChannelPublisher._format_currency_value(base_rate, quote_currency)
        final_rate_str = ChannelPublisher._format_currency_value(final_rate, quote_currency)
        
        # Определяем знак изменения и эмодзи
        change_sign = "+" if rate_change >= 0 else "-"
        change_emoji = "📈" if rate_change >= 0 else "📉"
        margin_emoji = "📈" if margin >= 0 else "📉"
        margin_sign = "+" if margin >= 0 else ""
        
        # Временная метка
        now = datetime.now()
        timestamp = now.strftime("%d.%m.%Y %H:%M")
        
        # Создаем сообщение для канала
        channel_message = (
            f"💱 <b>{pair_info['name']}</b>\n\n"
            f"{change_emoji} <b>Актуальный курс:</b> <code>{final_rate_str}</code> {quote_currency}\n"
            f"{margin_emoji} <b>Наценка:</b> <code>{margin_sign}{margin}%</code>\n\n"
            f"📊 <b>Детали:</b>\n"
            f"• Базовый курс: {base_rate_str} {quote_currency}\n"
            f"• Итоговый курс: {final_rate_str} {quote_currency}\n\n"
            f"🕐 <b>Обновлено:</b> {timestamp}\n"
            f"👤 <b>Менеджер:</b> {manager_name}\n\n"
            f"📡 <i>Данные получены через Rapira API</i>\n"
            f"🤖 <i>Crypto Helper Bot</i>"
        )
        
        return channel_message
    
    @staticmethod
    def format_private_message(
        pair_info: Dict[str, Any],
        base_rate: Decimal,
        margin: Decimal,
        final_rate: Decimal,
        rate_change: Decimal,
        exchange_rate_data: Dict[str, Any],
        manager_name: str = "Менеджер"
    ) -> str:
        """
        Форматирование сообщения для отправки в ЛС (режим разработки)
        
        Args:
            pair_info: Информация о валютной паре
            base_rate: Базовый курс
            margin: Процентная наценка
            final_rate: Итоговый курс
            rate_change: Изменение курса
            exchange_rate_data: Данные о курсе
            manager_name: Имя менеджера
            
        Returns:
            str: Отформатированное сообщение для ЛС
        """
        # Определяем валюты
        base_currency = pair_info['base']
        quote_currency = pair_info['quote']
        
        # Форматируем значения
        base_rate_str = ChannelPublisher._format_currency_value(base_rate, quote_currency)
        final_rate_str = ChannelPublisher._format_currency_value(final_rate, quote_currency)
        rate_change_str = ChannelPublisher._format_currency_value(abs(rate_change), quote_currency)
        
        # Определяем знак изменения и эмодзи
        change_sign = "+" if rate_change >= 0 else "-"
        change_emoji = "📈" if rate_change >= 0 else "📉"
        margin_emoji = "📈" if margin >= 0 else "📉"
        margin_sign = "+" if margin >= 0 else ""
        
        # Временная метка
        now = datetime.now()
        timestamp = now.strftime("%d.%m.%Y %H:%M:%S")
        source_timestamp = exchange_rate_data.get('timestamp', '')[:19].replace('T', ' ')
        
        # Создаем расширенное сообщение для ЛС
        private_message = (
            f"🧪 <b>РЕЖИМ РАЗРАБОТКИ - Результат публикации</b>\n\n"
            f"💱 <b>{pair_info['name']}</b>\n"
            f"📝 <i>{pair_info['description']}</i>\n\n"
            f"📊 <b>Результат расчета:</b>\n"
            f"• Базовый курс: <code>{base_rate_str}</code> {quote_currency}\n"
            f"{margin_emoji} Наценка: <code>{margin_sign}{margin}%</code>\n"
            f"• Итоговый курс: <code>{final_rate_str}</code> {quote_currency}\n"
            f"{change_emoji} Изменение: <code>{change_sign}{rate_change_str}</code> {quote_currency}\n\n"
            f"👤 <b>Менеджер:</b> {manager_name}\n"
            f"🕐 <b>Время расчета:</b> {timestamp}\n"
            f"📡 <b>Время получения курса:</b> {source_timestamp}\n"
            f"🔗 <b>Источник:</b> {exchange_rate_data.get('source', 'N/A')}\n\n"
            f"📋 <b>Сообщение для канала:</b>\n"
            f"<code>{ChannelPublisher.format_channel_message(pair_info, base_rate, margin, final_rate, rate_change, exchange_rate_data, manager_name)}</code>\n\n"
            f"💡 <i>В продакшене это сообщение будет отправлено в канал</i>"
        )
        
        return private_message
    
    @staticmethod
    def _format_currency_value(value: Decimal, currency: str) -> str:
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
        elif currency in ['RUB', 'USD', 'EUR', 'ZAR', 'THB', 'AED', 'IDR']:
            # Для фиатных валют - 2 знака
            return f"{value:.2f}"
        else:
            # Для остальных - автоматическое определение
            if value >= 1:
                return f"{value:.4f}"
            else:
                return f"{value:.8f}"
    
    @staticmethod
    async def publish_to_channel(
        bot: Bot,
        channel_id: str,
        message_text: str
    ) -> Optional[Message]:
        """
        Публикация сообщения в канал
        
        Args:
            bot: Экземпляр бота
            channel_id: ID канала
            message_text: Текст сообщения
            
        Returns:
            Message: Отправленное сообщение или None при ошибке
            
        Raises:
            ChannelPublisherError: При ошибке публикации
        """
        try:
            # Отправляем сообщение в канал
            sent_message = await bot.send_message(
                chat_id=channel_id,
                text=message_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            logger.info(f"Сообщение успешно опубликовано в канал {channel_id}")
            return sent_message
            
        except TelegramForbiddenError as e:
            error_msg = f"Нет прав для публикации в канал {channel_id}: {e}"
            logger.error(error_msg)
            raise ChannelPublisherError(error_msg)
            
        except TelegramBadRequest as e:
            error_msg = f"Некорректный запрос при публикации в канал {channel_id}: {e}"
            logger.error(error_msg)
            raise ChannelPublisherError(error_msg)
            
        except Exception as e:
            error_msg = f"Неожиданная ошибка при публикации в канал {channel_id}: {e}"
            logger.error(error_msg)
            raise ChannelPublisherError(error_msg)
    
    @staticmethod
    async def send_to_private_chat(
        bot: Bot,
        user_id: int,
        message_text: str
    ) -> Optional[Message]:
        """
        Отправка сообщения в ЛС пользователя (режим разработки)
        
        Args:
            bot: Экземпляр бота
            user_id: ID пользователя
            message_text: Текст сообщения
            
        Returns:
            Message: Отправленное сообщение или None при ошибке
            
        Raises:
            ChannelPublisherError: При ошибке отправки
        """
        try:
            # Отправляем сообщение в ЛС
            sent_message = await bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
            logger.info(f"Сообщение успешно отправлено в ЛС пользователя {user_id}")
            return sent_message
            
        except TelegramForbiddenError as e:
            error_msg = f"Пользователь {user_id} заблокировал бота: {e}"
            logger.error(error_msg)
            raise ChannelPublisherError(error_msg)
            
        except TelegramBadRequest as e:
            error_msg = f"Некорректный запрос при отправке в ЛС {user_id}: {e}"
            logger.error(error_msg)
            raise ChannelPublisherError(error_msg)
            
        except Exception as e:
            error_msg = f"Неожиданная ошибка при отправке в ЛС {user_id}: {e}"
            logger.error(error_msg)
            raise ChannelPublisherError(error_msg)
    
    @staticmethod
    async def publish_result(
        bot: Bot,
        pair_info: Dict[str, Any],
        base_rate: Decimal,
        margin: Decimal,
        final_rate: Decimal,
        rate_change: Decimal,
        exchange_rate_data: Dict[str, Any],
        manager_name: str,
        user_id: int,
        channel_id: Optional[str] = None,
        development_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Основная функция публикации результата
        
        Args:
            bot: Экземпляр бота
            pair_info: Информация о валютной паре
            base_rate: Базовый курс
            margin: Процентная наценка
            final_rate: Итоговый курс
            rate_change: Изменение курса
            exchange_rate_data: Данные о курсе
            manager_name: Имя менеджера
            user_id: ID пользователя
            channel_id: ID канала (опционально)
            development_mode: Режим разработки
            
        Returns:
            Dict[str, Any]: Результат публикации
        """
        result = {
            'success': False,
            'message': '',
            'sent_message': None,
            'target': 'unknown'
        }
        
        try:
            if development_mode or not channel_id:
                # Режим разработки - отправляем в ЛС разработчику
                message_text = ChannelPublisher.format_private_message(
                    pair_info=pair_info,
                    base_rate=base_rate,
                    margin=margin,
                    final_rate=final_rate,
                    rate_change=rate_change,
                    exchange_rate_data=exchange_rate_data,
                    manager_name=manager_name
                )
                
                sent_message = await ChannelPublisher.send_to_private_chat(
                    bot=bot,
                    user_id=user_id,
                    message_text=message_text
                )
                
                result.update({
                    'success': True,
                    'message': 'Результат отправлен в ЛС (режим разработки)',
                    'sent_message': sent_message,
                    'target': 'private_chat'
                })
                
            else:
                # Продакшен режим - публикуем в канал
                message_text = ChannelPublisher.format_channel_message(
                    pair_info=pair_info,
                    base_rate=base_rate,
                    margin=margin,
                    final_rate=final_rate,
                    rate_change=rate_change,
                    exchange_rate_data=exchange_rate_data,
                    manager_name=manager_name
                )
                
                sent_message = await ChannelPublisher.publish_to_channel(
                    bot=bot,
                    channel_id=channel_id,
                    message_text=message_text
                )
                
                result.update({
                    'success': True,
                    'message': 'Результат опубликован в канал',
                    'sent_message': sent_message,
                    'target': 'channel'
                })
            
            logger.info(
                f"Публикация завершена успешно: "
                f"user_id={user_id}, pair={pair_info['name']}, "
                f"target={result['target']}, margin={margin}%"
            )
            
        except ChannelPublisherError as e:
            result.update({
                'success': False,
                'message': str(e),
                'target': 'error'
            })
            logger.error(f"Ошибка публикации: {e}")
            
        except Exception as e:
            result.update({
                'success': False,
                'message': f"Неожиданная ошибка: {str(e)}",
                'target': 'error'
            })
            logger.error(f"Неожиданная ошибка при публикации: {e}")
        
        return result