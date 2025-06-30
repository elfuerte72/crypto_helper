#!/usr/bin/env python3
"""
Unit тесты для административных обработчиков Crypto Helper Bot
Тестирует проверку прав администратора и обработку команды /admin_bot
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from aiogram.types import Message, User, Chat, InlineKeyboardMarkup, CallbackQuery
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

# Import modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from handlers.admin_handlers import (
    check_admin_permissions,
    create_currency_pairs_keyboard,
    admin_bot_command,
    handle_currency_pair_selection,
    handle_cancel_selection,
    AdminPermissionError
)


class TestAdminPermissions:
    """Тесты для проверки прав администратора"""
    
    @pytest.mark.asyncio
    async def test_check_admin_permissions_success_creator(self):
        """Тест успешной проверки прав для создателя канала"""
        # Arrange
        bot_mock = AsyncMock()
        chat_member_mock = Mock()
        chat_member_mock.status = ChatMemberStatus.CREATOR
        bot_mock.get_chat_member.return_value = chat_member_mock
        
        # Act
        result = await check_admin_permissions(bot_mock, -1001234567890, 123456789)
        
        # Assert
        assert result is True
        bot_mock.get_chat_member.assert_called_once_with(
            chat_id=-1001234567890,
            user_id=123456789
        )
    
    @pytest.mark.asyncio
    async def test_check_admin_permissions_success_administrator(self):
        """Тест успешной проверки прав для администратора канала"""
        # Arrange
        bot_mock = AsyncMock()
        chat_member_mock = Mock()
        chat_member_mock.status = ChatMemberStatus.ADMINISTRATOR
        bot_mock.get_chat_member.return_value = chat_member_mock
        
        # Act
        result = await check_admin_permissions(bot_mock, -1001234567890, 123456789)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_admin_permissions_failure_member(self):
        """Тест неуспешной проверки прав для обычного участника"""
        # Arrange
        bot_mock = AsyncMock()
        chat_member_mock = Mock()
        chat_member_mock.status = ChatMemberStatus.MEMBER
        bot_mock.get_chat_member.return_value = chat_member_mock
        
        # Act
        result = await check_admin_permissions(bot_mock, -1001234567890, 123456789)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_admin_permissions_failure_left(self):
        """Тест неуспешной проверки прав для покинувшего канал"""
        # Arrange
        bot_mock = AsyncMock()
        chat_member_mock = Mock()
        chat_member_mock.status = ChatMemberStatus.LEFT
        bot_mock.get_chat_member.return_value = chat_member_mock
        
        # Act
        result = await check_admin_permissions(bot_mock, -1001234567890, 123456789)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_admin_permissions_telegram_bad_request(self):
        """Тест обработки ошибки TelegramBadRequest"""
        # Arrange
        bot_mock = AsyncMock()
        bot_mock.get_chat_member.side_effect = TelegramBadRequest(
            method="getChatMember",
            message="Bad Request: user not found"
        )
        
        # Act & Assert
        with pytest.raises(AdminPermissionError) as exc_info:
            await check_admin_permissions(bot_mock, -1001234567890, 123456789)
        
        assert "Не удалось проверить права доступа" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_check_admin_permissions_telegram_forbidden(self):
        """Тест обработки ошибки TelegramForbiddenError"""
        # Arrange
        bot_mock = AsyncMock()
        bot_mock.get_chat_member.side_effect = TelegramForbiddenError(
            method="getChatMember",
            message="Forbidden: bot is not a member of the supergroup chat"
        )
        
        # Act & Assert
        with pytest.raises(AdminPermissionError) as exc_info:
            await check_admin_permissions(bot_mock, -1001234567890, 123456789)
        
        assert "Бот не имеет доступа к информации о канале" in str(exc_info.value)


class TestCurrencyPairsKeyboard:
    """Тесты для создания клавиатуры валютных пар"""
    
    def test_create_currency_pairs_keyboard_structure(self):
        """Тест структуры клавиатуры валютных пар"""
        # Act
        keyboard = create_currency_pairs_keyboard()
        
        # Assert
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0
        
        # Проверяем наличие всех ожидаемых пар
        all_buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                all_buttons_text.append(button.text)
        
        # Проверяем наличие основных валютных пар
        expected_pairs = [
            'RUB/ZAR', 'RUB/THB', 'RUB/AED', 'RUB/IDR',
            'USDT/ZAR', 'USDT/THB', 'USDT/AED', 'USDT/IDR',
            'ZAR/RUB', 'THB/RUB', 'AED/RUB', 'IDR/RUB',
            'ZAR/USDT', 'THB/USDT', 'AED/USDT', 'IDR/USDT'
        ]
        
        for pair in expected_pairs:
            assert pair in all_buttons_text
        
        # Проверяем наличие кнопки отмены
        assert '❌ Отмена' in all_buttons_text
    
    def test_create_currency_pairs_keyboard_callback_data(self):
        """Тест правильности callback_data для кнопок"""
        # Act
        keyboard = create_currency_pairs_keyboard()
        
        # Assert
        all_callback_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data and not button.callback_data.startswith('header_'):
                    all_callback_data.append(button.callback_data)
        
        # Проверяем наличие ожидаемых callback_data
        expected_callbacks = [
            'rub_zar', 'rub_thb', 'rub_aed', 'rub_idr',
            'usdt_zar', 'usdt_thb', 'usdt_aed', 'usdt_idr',
            'zar_rub', 'thb_rub', 'aed_rub', 'idr_rub',
            'zar_usdt', 'thb_usdt', 'aed_usdt', 'idr_usdt',
            'cancel_selection'
        ]
        
        for callback in expected_callbacks:
            assert callback in all_callback_data


class TestAdminBotCommand:
    """Тесты для команды /admin_bot"""
    
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
    @patch('handlers.admin_handlers.config')
    async def test_admin_bot_command_no_channel_configured(self, mock_config):
        """Тест команды /admin_bot без настроенного канала"""
        # Arrange
        mock_config.ADMIN_CHANNEL_ID = ""
        message = self.create_mock_message()
        bot_mock = AsyncMock()
        
        # Act
        await admin_bot_command(message, bot_mock)
        
        # Assert
        message.reply.assert_called_once()
        call_args = message.reply.call_args[0][0]
        assert "Ошибка конфигурации" in call_args
        assert "канал для проверки прав администратора не настроен" in call_args.lower()
    
    @pytest.mark.asyncio
    @patch('handlers.admin_handlers.config')
    @patch('handlers.admin_handlers.check_admin_permissions')
    async def test_admin_bot_command_not_admin(self, mock_check_admin, mock_config):
        """Тест команды /admin_bot для не-администратора"""
        # Arrange
        mock_config.ADMIN_CHANNEL_ID = "-1001234567890"
        mock_check_admin.return_value = False
        message = self.create_mock_message()
        bot_mock = AsyncMock()
        
        # Act
        await admin_bot_command(message, bot_mock)
        
        # Assert
        message.reply.assert_called_once()
        call_args = message.reply.call_args[0][0]
        assert "Доступ запрещен" in call_args
        assert "только администраторам канала" in call_args
    
    @pytest.mark.asyncio
    @patch('handlers.admin_handlers.config')
    @patch('handlers.admin_handlers.check_admin_permissions')
    async def test_admin_bot_command_admin_success(self, mock_check_admin, mock_config):
        """Тест успешного выполнения команды /admin_bot для администратора"""
        # Arrange
        mock_config.ADMIN_CHANNEL_ID = "-1001234567890"
        mock_check_admin.return_value = True
        message = self.create_mock_message()
        bot_mock = AsyncMock()
        
        # Act
        await admin_bot_command(message, bot_mock)
        
        # Assert
        message.reply.assert_called_once()
        call_args = message.reply.call_args
        
        # Проверяем текст сообщения
        message_text = call_args[0][0]
        assert "Административная панель" in message_text
        assert "Выберите валютную пару" in message_text
        
        # Проверяем наличие клавиатуры
        assert 'reply_markup' in call_args[1]
        keyboard = call_args[1]['reply_markup']
        assert isinstance(keyboard, InlineKeyboardMarkup)
    
    @pytest.mark.asyncio
    @patch('handlers.admin_handlers.config')
    @patch('handlers.admin_handlers.check_admin_permissions')
    async def test_admin_bot_command_permission_error(self, mock_check_admin, mock_config):
        """Тест обработки ошибки проверки прав"""
        # Arrange
        mock_config.ADMIN_CHANNEL_ID = "-1001234567890"
        mock_check_admin.side_effect = AdminPermissionError("Test error")
        message = self.create_mock_message()
        bot_mock = AsyncMock()
        
        # Act
        await admin_bot_command(message, bot_mock)
        
        # Assert
        message.reply.assert_called_once()
        call_args = message.reply.call_args[0][0]
        assert "Ошибка проверки прав" in call_args
        assert "Test error" in call_args


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
        assert "Операция отменена" in call_args
        
        callback_query.answer.assert_called_once_with("Операция отменена", show_alert=False)
    
    @pytest.mark.asyncio
    async def test_handle_currency_pair_selection_rub_zar(self):
        """Тест выбора валютной пары RUB/ZAR"""
        # Arrange
        callback_query = self.create_mock_callback_query('rub_zar')
        
        # Act
        await handle_currency_pair_selection(callback_query)
        
        # Assert
        callback_query.message.edit_text.assert_called_once()
        call_args = callback_query.message.edit_text.call_args[0][0]
        assert "Валютная пара выбрана" in call_args
        assert "RUB/ZAR" in call_args
        
        callback_query.answer.assert_called_once()
        answer_args = callback_query.answer.call_args[0][0]
        assert "RUB/ZAR" in answer_args
    
    @pytest.mark.asyncio
    async def test_handle_currency_pair_selection_usdt_thb(self):
        """Тест выбора валютной пары USDT/THB"""
        # Arrange
        callback_query = self.create_mock_callback_query('usdt_thb')
        
        # Act
        await handle_currency_pair_selection(callback_query)
        
        # Assert
        callback_query.message.edit_text.assert_called_once()
        call_args = callback_query.message.edit_text.call_args[0][0]
        assert "USDT/THB" in call_args
        
        callback_query.answer.assert_called_once()
        answer_args = callback_query.answer.call_args[0][0]
        assert "USDT/THB" in answer_args
    
    @pytest.mark.asyncio
    async def test_handle_currency_pair_selection_reverse_pair(self):
        """Тест выбора обратной валютной пары ZAR/RUB"""
        # Arrange
        callback_query = self.create_mock_callback_query('zar_rub')
        
        # Act
        await handle_currency_pair_selection(callback_query)
        
        # Assert
        callback_query.message.edit_text.assert_called_once()
        call_args = callback_query.message.edit_text.call_args[0][0]
        assert "ZAR/RUB" in call_args
        
        callback_query.answer.assert_called_once()
        answer_args = callback_query.answer.call_args[0][0]
        assert "ZAR/RUB" in answer_args


if __name__ == '__main__':
    pytest.main([__file__, '-v'])