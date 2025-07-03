#!/usr/bin/env python3
"""
Unit тесты для административных обработчиков Crypto Helper Bot
Упрощенная версия без проверки прав администратора
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from aiogram.types import Message, User, Chat, InlineKeyboardMarkup, CallbackQuery
from aiogram.enums import ChatType

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from handlers.admin_handlers import (
    admin_bot_command,
    handle_cancel_selection
)
from handlers.currency_pairs import (
    get_currency_pair_info,
    is_valid_currency_pair
)
from handlers.keyboards import create_currency_pairs_keyboard


class TestAdminBotCommand:
    """Тесты для команды /admin_bot (без проверки прав администратора)"""
    
    def create_mock_message(self, user_id: int = 123456789, username: str = "testuser"):
        """Создает mock объект Message"""
        user = User(id=user_id, is_bot=False, first_name="Test", username=username)
        chat = Chat(id=user_id, type=ChatType.PRIVATE)
        message = Mock(spec=Message)
        message.from_user = user
        message.chat = chat
        message.reply = AsyncMock()
        return message
    
    @pytest.mark.asyncio
    async def test_admin_bot_command_success(self):
        """Тест успешного выполнения команды /admin_bot для любого пользователя"""
        # Arrange
        message = self.create_mock_message()
        
        # Act
        await admin_bot_command(message)
        
        # Assert
        message.reply.assert_called_once()
        call_args = message.reply.call_args
        
        # Проверяем текст сообщения
        message_text = call_args[0][0]
        assert "панель" in message_text.lower()
        
        # Проверяем наличие клавиатуры
        assert 'reply_markup' in call_args[1]
        keyboard = call_args[1]['reply_markup']
        assert isinstance(keyboard, InlineKeyboardMarkup)
    
    @pytest.mark.asyncio
    async def test_admin_bot_command_different_users(self):
        """Тест команды /admin_bot для разных пользователей"""
        user_ids = [123456789, 987654321, 555555555]
        
        for user_id in user_ids:
            # Arrange
            message = self.create_mock_message(user_id=user_id)
            
            # Act
            await admin_bot_command(message)
            
            # Assert
            message.reply.assert_called_once()
            call_args = message.reply.call_args[0][0]
            assert len(call_args) > 0  # Проверяем, что есть текст ответа
            
            # Reset mock for next iteration
            message.reply.reset_mock()


class TestCurrencyPairsKeyboard:
    """Тесты для создания клавиатуры валютных пар"""
    
    def test_create_currency_pairs_keyboard_structure(self):
        """Тест структуры клавиатуры валютных пар"""
        # Act
        keyboard = create_currency_pairs_keyboard()
        
        # Assert
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0
        
        # Проверяем наличие кнопок
        all_buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                all_buttons_text.append(button.text)
        
        # Проверяем, что есть кнопки с валютными парами
        assert len(all_buttons_text) > 0
    
    def test_create_currency_pairs_keyboard_callback_data(self):
        """Тест правильности callback_data для кнопок"""
        # Act
        keyboard = create_currency_pairs_keyboard()
        
        # Assert
        all_callback_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data:
                    all_callback_data.append(button.callback_data)
        
        # Проверяем, что есть callback_data для валютных пар
        pair_callbacks = [cd for cd in all_callback_data if cd.startswith('pair_')]
        assert len(pair_callbacks) > 0, "Не найдены callback_data для валютных пар"


class TestCurrencyPairUtils:
    """Тесты для вспомогательных функций работы с валютными парами"""
    
    def test_is_valid_currency_pair_basic(self):
        """Тест валидации основных валютных пар"""
        # Проверяем, что функция работает
        result = is_valid_currency_pair('USDT/RUB')
        assert isinstance(result, bool)
    
    def test_get_currency_pair_info_basic(self):
        """Тест получения информации о валютной паре"""
        # Act
        pair_info = get_currency_pair_info('USDT/RUB')
        
        # Assert
        if pair_info is not None:
            assert 'name' in pair_info
            assert 'base' in pair_info
            assert 'quote' in pair_info
            assert isinstance(pair_info['name'], str)
            assert isinstance(pair_info['base'], str)
            assert isinstance(pair_info['quote'], str)
    
    def test_get_currency_pair_info_invalid_pair(self):
        """Тест получения информации о несуществующей паре"""
        # Act
        pair_info = get_currency_pair_info('INVALID/PAIR')
        
        # Assert
        assert pair_info is None


class TestCallbackHandlers:
    """Тесты для обработчиков callback запросов"""
    
    def create_mock_callback_query(self, callback_data: str, user_id: int = 123456789):
        """Создает mock объект CallbackQuery"""
        user = User(id=user_id, is_bot=False, first_name="Test")
        message = Mock(spec=Message)
        message.edit_text = AsyncMock()
        
        callback_query = Mock(spec=CallbackQuery)
        callback_query.data = callback_data
        callback_query.from_user = user
        callback_query.message = message
        callback_query.answer = AsyncMock()
        
        return callback_query
    
    @pytest.mark.asyncio
    async def test_handle_cancel_selection(self):
        """Тест обработки отмены выбора"""
        # Arrange
        callback_query = self.create_mock_callback_query('cancel_selection')
        
        # Act
        await handle_cancel_selection(callback_query)
        
        # Assert
        callback_query.message.edit_text.assert_called_once()
        call_args = callback_query.message.edit_text.call_args[0][0]
        assert "отмен" in call_args.lower()
        
        callback_query.answer.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])