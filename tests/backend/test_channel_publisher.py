#!/usr/bin/env python3
"""
Unit тесты для модуля публикации в канал
Crypto Helper Bot - Channel Publisher Tests
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from handlers.channel_publisher import ChannelPublisher, ChannelPublisherError


class TestChannelPublisher:
    """Тесты для класса ChannelPublisher"""
    
    @pytest.fixture
    def sample_pair_info(self):
        """Образец информации о валютной паре"""
        return {
            'name': 'RUB/ZAR',
            'base': 'RUB',
            'quote': 'ZAR',
            'emoji': '🇷🇺🇿🇦',
            'description': 'Российский рубль к южноафриканскому рэнду'
        }
    
    @pytest.fixture
    def sample_exchange_rate_data(self):
        """Образец данных о курсе"""
        return {
            'timestamp': '2024-01-15T12:30:45.123456Z',
            'source': 'Rapira API',
            'rate': 0.2134
        }
    
    @pytest.fixture
    def sample_calculation_data(self, sample_pair_info, sample_exchange_rate_data):
        """Образец данных расчета"""
        return {
            'pair_info': sample_pair_info,
            'base_rate': Decimal('0.2134'),
            'margin': Decimal('5.0'),
            'final_rate': Decimal('0.22407'),
            'rate_change': Decimal('0.01067'),
            'exchange_rate_data': sample_exchange_rate_data,
            'manager_name': 'Тест Менеджер',
            'user_id': 123456789
        }
    
    def test_format_currency_value_crypto(self):
        """Тест форматирования криптовалют"""
        # BTC
        value = Decimal('0.00012345')
        result = ChannelPublisher._format_currency_value(value, 'BTC')
        assert result == '0.00012345'
        
        # ETH
        value = Decimal('1.23456789')
        result = ChannelPublisher._format_currency_value(value, 'ETH')
        assert result == '1.23456789'
    
    def test_format_currency_value_stablecoins(self):
        """Тест форматирования стейблкоинов"""
        # USDT
        value = Decimal('1.2345')
        result = ChannelPublisher._format_currency_value(value, 'USDT')
        assert result == '1.2345'
        
        # USDC
        value = Decimal('100.123456')
        result = ChannelPublisher._format_currency_value(value, 'USDC')
        assert result == '100.1235'
    
    def test_format_currency_value_fiat(self):
        """Тест форматирования фиатных валют"""
        # RUB
        value = Decimal('123.456789')
        result = ChannelPublisher._format_currency_value(value, 'RUB')
        assert result == '123.46'
        
        # ZAR
        value = Decimal('0.2134567')
        result = ChannelPublisher._format_currency_value(value, 'ZAR')
        assert result == '0.21'
        
        # USD
        value = Decimal('1.999')
        result = ChannelPublisher._format_currency_value(value, 'USD')
        assert result == '2.00'
    
    def test_format_currency_value_other(self):
        """Тест форматирования других валют"""
        # Большое значение
        value = Decimal('1000.123456')
        result = ChannelPublisher._format_currency_value(value, 'UNKNOWN')
        assert result == '1000.1235'
        
        # Малое значение
        value = Decimal('0.00012345')
        result = ChannelPublisher._format_currency_value(value, 'UNKNOWN')
        assert result == '0.00012345'
    
    def test_format_channel_message(self, sample_calculation_data):
        """Тест форматирования сообщения для канала"""
        message = ChannelPublisher.format_channel_message(
            pair_info=sample_calculation_data['pair_info'],
            base_rate=sample_calculation_data['base_rate'],
            margin=sample_calculation_data['margin'],
            final_rate=sample_calculation_data['final_rate'],
            rate_change=sample_calculation_data['rate_change'],
            exchange_rate_data=sample_calculation_data['exchange_rate_data'],
            manager_name=sample_calculation_data['manager_name']
        )
        
        # Проверяем наличие ключевых элементов
        assert 'RUB/ZAR' in message
        assert '0.22' in message  # Итоговый курс
        assert '+5.0%' in message  # Наценка
        assert 'Тест Менеджер' in message
        assert 'Rapira API' in message
        assert 'Crypto Helper Bot' in message
        
        # Проверяем, что сообщение не пустое
        assert len(message) > 100
    
    def test_format_channel_message_negative_margin(self, sample_calculation_data):
        """Тест форматирования сообщения с отрицательной наценкой"""
        # Изменяем данные для отрицательной наценки
        sample_calculation_data['margin'] = Decimal('-2.5')
        sample_calculation_data['final_rate'] = Decimal('0.20797')
        sample_calculation_data['rate_change'] = Decimal('-0.00543')
        
        message = ChannelPublisher.format_channel_message(
            pair_info=sample_calculation_data['pair_info'],
            base_rate=sample_calculation_data['base_rate'],
            margin=sample_calculation_data['margin'],
            final_rate=sample_calculation_data['final_rate'],
            rate_change=sample_calculation_data['rate_change'],
            exchange_rate_data=sample_calculation_data['exchange_rate_data'],
            manager_name=sample_calculation_data['manager_name']
        )
        
        # Проверяем отрицательную наценку
        assert '-2.5%' in message
    
    def test_format_private_message(self, sample_calculation_data):
        """Тест форматирования сообщения для ЛС"""
        message = ChannelPublisher.format_private_message(
            pair_info=sample_calculation_data['pair_info'],
            base_rate=sample_calculation_data['base_rate'],
            margin=sample_calculation_data['margin'],
            final_rate=sample_calculation_data['final_rate'],
            rate_change=sample_calculation_data['rate_change'],
            exchange_rate_data=sample_calculation_data['exchange_rate_data'],
            manager_name=sample_calculation_data['manager_name']
        )
        
        # Проверяем наличие ключевых элементов
        assert 'РЕЖИМ РАЗРАБОТКИ' in message
        assert 'RUB/ZAR' in message
        assert 'Результат расчета:' in message
        assert 'Тест Менеджер' in message
        assert 'Сообщение для канала:' in message
        assert 'В продакшене это сообщение будет отправлено в канал' in message
        
        # Проверяем, что сообщение содержит вложенное сообщение для канала
        assert '<code>' in message and '</code>' in message
    
    @pytest.mark.asyncio
    async def test_publish_to_channel_success(self):
        """Тест успешной публикации в канал"""
        # Создаем мок бота
        mock_bot = AsyncMock()
        mock_message = MagicMock(spec=Message)
        mock_bot.send_message.return_value = mock_message
        
        # Тестируем публикацию
        result = await ChannelPublisher.publish_to_channel(
            bot=mock_bot,
            channel_id='@test_channel',
            message_text='Test message'
        )
        
        # Проверяем вызов
        mock_bot.send_message.assert_called_once_with(
            chat_id='@test_channel',
            text='Test message',
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        # Проверяем результат
        assert result == mock_message
    
    @pytest.mark.asyncio
    async def test_publish_to_channel_forbidden_error(self):
        """Тест ошибки прав доступа при публикации в канал"""
        # Создаем мок бота с ошибкой
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = TelegramForbiddenError(
            method='send_message',
            message='Forbidden: bot was blocked by the user'
        )
        
        # Тестируем публикацию с ошибкой
        with pytest.raises(ChannelPublisherError) as exc_info:
            await ChannelPublisher.publish_to_channel(
                bot=mock_bot,
                channel_id='@test_channel',
                message_text='Test message'
            )
        
        assert 'Нет прав для публикации в канал' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_publish_to_channel_bad_request_error(self):
        """Тест ошибки некорректного запроса при публикации в канал"""
        # Создаем мок бота с ошибкой
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = TelegramBadRequest(
            method='send_message',
            message='Bad Request: chat not found'
        )
        
        # Тестируем публикацию с ошибкой
        with pytest.raises(ChannelPublisherError) as exc_info:
            await ChannelPublisher.publish_to_channel(
                bot=mock_bot,
                channel_id='@invalid_channel',
                message_text='Test message'
            )
        
        assert 'Некорректный запрос при публикации в канал' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_to_private_chat_success(self):
        """Тест успешной отправки в ЛС"""
        # Создаем мок бота
        mock_bot = AsyncMock()
        mock_message = MagicMock(spec=Message)
        mock_bot.send_message.return_value = mock_message
        
        # Тестируем отправку
        result = await ChannelPublisher.send_to_private_chat(
            bot=mock_bot,
            user_id=123456789,
            message_text='Test private message'
        )
        
        # Проверяем вызов
        mock_bot.send_message.assert_called_once_with(
            chat_id=123456789,
            text='Test private message',
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        # Проверяем результат
        assert result == mock_message
    
    @pytest.mark.asyncio
    async def test_send_to_private_chat_forbidden_error(self):
        """Тест ошибки блокировки бота пользователем"""
        # Создаем мок бота с ошибкой
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = TelegramForbiddenError(
            method='send_message',
            message='Forbidden: bot was blocked by the user'
        )
        
        # Тестируем отправку с ошибкой
        with pytest.raises(ChannelPublisherError) as exc_info:
            await ChannelPublisher.send_to_private_chat(
                bot=mock_bot,
                user_id=123456789,
                message_text='Test message'
            )
        
        assert 'заблокировал бота' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_publish_result_development_mode(self, sample_calculation_data):
        """Тест публикации в режиме разработки"""
        # Создаем мок бота
        mock_bot = AsyncMock()
        mock_message = MagicMock(spec=Message)
        mock_bot.send_message.return_value = mock_message
        
        # Тестируем публикацию в режиме разработки
        result = await ChannelPublisher.publish_result(
            bot=mock_bot,
            pair_info=sample_calculation_data['pair_info'],
            base_rate=sample_calculation_data['base_rate'],
            margin=sample_calculation_data['margin'],
            final_rate=sample_calculation_data['final_rate'],
            rate_change=sample_calculation_data['rate_change'],
            exchange_rate_data=sample_calculation_data['exchange_rate_data'],
            manager_name=sample_calculation_data['manager_name'],
            user_id=sample_calculation_data['user_id'],
            channel_id=None,
            development_mode=True
        )
        
        # Проверяем результат
        assert result['success'] is True
        assert result['target'] == 'private_chat'
        assert 'режим разработки' in result['message']
        
        # Проверяем, что был вызван send_message для ЛС
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args[1]['chat_id'] == sample_calculation_data['user_id']
        assert 'РЕЖИМ РАЗРАБОТКИ' in call_args[1]['text']
    
    @pytest.mark.asyncio
    async def test_publish_result_production_mode(self, sample_calculation_data):
        """Тест публикации в продакшен режиме"""
        # Создаем мок бота
        mock_bot = AsyncMock()
        mock_message = MagicMock(spec=Message)
        mock_bot.send_message.return_value = mock_message
        
        # Тестируем публикацию в продакшен режиме
        result = await ChannelPublisher.publish_result(
            bot=mock_bot,
            pair_info=sample_calculation_data['pair_info'],
            base_rate=sample_calculation_data['base_rate'],
            margin=sample_calculation_data['margin'],
            final_rate=sample_calculation_data['final_rate'],
            rate_change=sample_calculation_data['rate_change'],
            exchange_rate_data=sample_calculation_data['exchange_rate_data'],
            manager_name=sample_calculation_data['manager_name'],
            user_id=sample_calculation_data['user_id'],
            channel_id='@test_channel',
            development_mode=False
        )
        
        # Проверяем результат
        assert result['success'] is True
        assert result['target'] == 'channel'
        assert 'опубликован в канал' in result['message']
        
        # Проверяем, что был вызван send_message для канала
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args[1]['chat_id'] == '@test_channel'
        assert 'RUB/ZAR' in call_args[1]['text']
        assert 'РЕЖИМ РАЗРАБОТКИ' not in call_args[1]['text']
    
    @pytest.mark.asyncio
    async def test_publish_result_error_handling(self, sample_calculation_data):
        """Тест обработки ошибок при публикации"""
        # Создаем мок бота с ошибкой
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = TelegramForbiddenError(
            method='send_message',
            message='Forbidden: bot was blocked by the user'
        )
        
        # Тестируем публикацию с ошибкой
        result = await ChannelPublisher.publish_result(
            bot=mock_bot,
            pair_info=sample_calculation_data['pair_info'],
            base_rate=sample_calculation_data['base_rate'],
            margin=sample_calculation_data['margin'],
            final_rate=sample_calculation_data['final_rate'],
            rate_change=sample_calculation_data['rate_change'],
            exchange_rate_data=sample_calculation_data['exchange_rate_data'],
            manager_name=sample_calculation_data['manager_name'],
            user_id=sample_calculation_data['user_id'],
            channel_id='@test_channel',
            development_mode=False
        )
        
        # Проверяем результат
        assert result['success'] is False
        assert result['target'] == 'error'
        assert 'Нет прав для публикации' in result['message']
    
    @pytest.mark.asyncio
    async def test_publish_result_unexpected_error(self, sample_calculation_data):
        """Тест обработки неожиданных ошибок при публикации"""
        # Создаем мок бота с неожиданной ошибкой
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = Exception('Unexpected error')
        
        # Тестируем публикацию с ошибкой
        result = await ChannelPublisher.publish_result(
            bot=mock_bot,
            pair_info=sample_calculation_data['pair_info'],
            base_rate=sample_calculation_data['base_rate'],
            margin=sample_calculation_data['margin'],
            final_rate=sample_calculation_data['final_rate'],
            rate_change=sample_calculation_data['rate_change'],
            exchange_rate_data=sample_calculation_data['exchange_rate_data'],
            manager_name=sample_calculation_data['manager_name'],
            user_id=sample_calculation_data['user_id'],
            channel_id=None,
            development_mode=True
        )
        
        # Проверяем результат
        assert result['success'] is False
        assert result['target'] == 'error'
        assert 'Неожиданная ошибка' in result['message']
    
    def test_format_channel_message_with_crypto_pair(self):
        """Тест форматирования сообщения для криптовалютной пары"""
        crypto_pair_info = {
            'name': 'BTC/USDT',
            'base': 'BTC',
            'quote': 'USDT',
            'emoji': '₿💰',
            'description': 'Биткоин к Tether USD'
        }
        
        crypto_exchange_data = {
            'timestamp': '2024-01-15T12:30:45.123456Z',
            'source': 'Rapira API',
            'rate': 42500.12345678
        }
        
        message = ChannelPublisher.format_channel_message(
            pair_info=crypto_pair_info,
            base_rate=Decimal('42500.12345678'),
            margin=Decimal('1.5'),
            final_rate=Decimal('43137.62530763'),
            rate_change=Decimal('637.50185085'),
            exchange_rate_data=crypto_exchange_data,
            manager_name='Крипто Менеджер'
        )
        
        # Проверяем специфичные для криптовалют элементы
        assert 'BTC/USDT' in message
        assert 'USDT' in message
        assert 'Крипто Менеджер' in message
        # Проверяем форматирование криптовалютных значений
        assert '43137.6253' in message  # 4 знака для USDT
    
    def test_format_private_message_structure(self, sample_calculation_data):
        """Тест структуры сообщения для ЛС"""
        message = ChannelPublisher.format_private_message(
            pair_info=sample_calculation_data['pair_info'],
            base_rate=sample_calculation_data['base_rate'],
            margin=sample_calculation_data['margin'],
            final_rate=sample_calculation_data['final_rate'],
            rate_change=sample_calculation_data['rate_change'],
            exchange_rate_data=sample_calculation_data['exchange_rate_data'],
            manager_name=sample_calculation_data['manager_name']
        )
        
        # Проверяем структуру сообщения
        lines = message.split('\n')
        
        # Должно быть достаточно строк для полного сообщения
        assert len(lines) > 10
        
        # Проверяем наличие основных секций
        message_sections = [
            'РЕЖИМ РАЗРАБОТКИ',
            'Результат расчета:',
            'Менеджер:',
            'Время расчета:',
            'Сообщение для канала:',
            'В продакшене это сообщение будет отправлено в канал'
        ]
        
        for section in message_sections:
            assert section in message, f"Секция '{section}' не найдена в сообщении"


if __name__ == '__main__':
    # Запуск тестов
    pytest.main([__file__, '-v'])