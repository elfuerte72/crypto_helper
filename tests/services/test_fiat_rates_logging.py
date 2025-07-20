#!/usr/bin/env python3
"""
Unit tests for improved logging in FiatRatesService
Tests TASK-CRYPTO-003: Улучшение логирования API ошибок
"""

import pytest
import asyncio
import json
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from aiohttp import ClientError, ClientTimeout
import aiohttp

# Настройка для импорта модулей
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.fiat_rates_service import FiatRatesService, log_detailed_error
from src.services.models import APILayerError


class TestFiatRatesLogging:
    """Тесты для улучшенного логирования в FiatRatesService"""
    
    @pytest.fixture
    def service(self):
        """Создание экземпляра сервиса для тестов"""
        service = FiatRatesService()
        service.api_key = "test_api_key"
        return service
    
    @pytest.fixture
    def mock_logger(self):
        """Mock logger для проверки логирования"""
        with patch('src.services.fiat_rates_service.logger') as mock_logger:
            yield mock_logger
    
    def test_log_detailed_error_function(self, mock_logger):
        """Тест функции детального логирования ошибок"""
        test_error = ValueError("Test error message")
        test_error.__traceback__ = None  # Симуляция трейсбека
        
        # Вызываем функцию логирования
        result = log_detailed_error("TEST_TYPE", test_error, "test context")
        
        # Проверяем результат
        assert result['type'] == "TEST_TYPE"
        assert result['message'] == "Test error message"
        assert result['class'] == "ValueError"
        assert result['context'] == "test context"
        assert 'traceback' in result
        
        # Проверяем, что логирование было вызвано
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "🚨 TEST_TYPE ERROR in test context:" in call_args
        assert "Type: ValueError" in call_args
        assert "Message: Test error message" in call_args
    
    @pytest.mark.asyncio
    async def test_missing_api_key_logging(self, service, mock_logger):
        """Тест логирования при отсутствии API ключа"""
        service.api_key = None
        
        # Мокируем fallback rates
        with patch.object(service, '_get_fallback_rates') as mock_fallback:
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем логирование отсутствия API ключа
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "🔑 APILayer API key not configured" in warning_call
            assert "Service: FiatRatesService" in warning_call
            assert "Base currency: USD" in warning_call
            assert "Fallback available: True" in warning_call
    
    @pytest.mark.asyncio
    async def test_successful_request_logging(self, service, mock_logger):
        """Тест логирования успешного запроса"""
        # Мокируем весь метод для сокращения сложности
        successful_response = {
            "success": True,
            "rates": {"EUR": 0.85, "GBP": 0.75}
        }
        
        # Мокируем весь метод get_rates_from_base частично
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_cache_rates') as mock_cache, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Настраиваем мок для aiohttp
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = successful_response
            
            # Используем мок контекстного менеджера
            mock_get.return_value.__aenter__.return_value = mock_response
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Просто проверяем что метод не падает и логирует
            result = await service.get_rates_from_base("USD")
            
            # Проверяем основное логирование
            mock_logger.info.assert_called()
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            
            # Проверяем лог запуска запроса
            start_log = next((log for log in info_calls if "🚀 Starting APILayer request" in log), None)
            assert start_log is not None
            assert "Max retries: 3" in start_log
    
    @pytest.mark.asyncio
    async def test_api_error_logging(self, service, mock_logger):
        """Тест логирования ошибок API"""
        # Просто мокируем выбрасывание ошибки API
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Мокируем выбрасывание APILayerError
            from src.services.models import APILayerError
            mock_get.side_effect = APILayerError("API Error: invalid_base")
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем что было логирование ошибки
            assert mock_logger.error.called or mock_logger.critical.called
            # Просто проверяем что ошибка была обработана и вернулся fallback
            assert result == {"EUR": 0.85}
    
    @pytest.mark.asyncio
    async def test_authentication_error_logging(self, service, mock_logger):
        """Тест логирования ошибок аутентификации"""
        # Мокируем aiohttp.ClientResponseError для 401
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            import aiohttp
            # Мокируем request_info чтобы избежать AttributeError
            mock_request_info = Mock()
            mock_request_info.real_url = "https://api.apilayer.com/test"
            
            auth_error = aiohttp.ClientResponseError(
                request_info=mock_request_info,
                history=None,
                status=401,
                message="Unauthorized"
            )
            mock_get.side_effect = auth_error
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем что было логирование ошибки
            assert mock_logger.error.called or mock_logger.critical.called
            # Проверяем что вернулся fallback
            assert result == {"EUR": 0.85}
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_logging(self, service, mock_logger):
        """Тест логирования ошибок rate limiting"""
        # Мокируем 429 ошибку
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            import aiohttp
            # Мокируем request_info чтобы избежать AttributeError
            mock_request_info = Mock()
            mock_request_info.real_url = "https://api.apilayer.com/test"
            
            rate_limit_error = aiohttp.ClientResponseError(
                request_info=mock_request_info,
                history=None,
                status=429,
                message="Too Many Requests"
            )
            mock_get.side_effect = rate_limit_error
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем что было логирование
            assert mock_logger.warning.called or mock_logger.error.called
            # Проверяем что вернулся fallback
            assert result == {"EUR": 0.85}
    
    @pytest.mark.asyncio
    async def test_network_error_logging(self, service, mock_logger):
        """Тест логирования сетевых ошибок"""
        # Мокируем сетевую ошибку
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            network_error = ClientError("Connection timeout")
            mock_get.side_effect = network_error
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем что было логирование ошибки
            assert mock_logger.error.called or mock_logger.critical.called
            # Проверяем что вернулся fallback
            assert result == {"EUR": 0.85}
    
    @pytest.mark.asyncio
    async def test_unexpected_error_logging(self, service, mock_logger):
        """Тест логирования неожиданных ошибок"""
        # Мокируем неожиданную ошибку
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            unexpected_error = RuntimeError("Unexpected system error")
            mock_get.side_effect = unexpected_error
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем что было логирование критической ошибки
            assert mock_logger.critical.called or mock_logger.error.called
            # Проверяем что вернулся fallback
            assert result == {"EUR": 0.85}
    
    @pytest.mark.asyncio
    async def test_json_decode_error_logging(self, service, mock_logger):
        """Тест логирования ошибок парсинга JSON"""
        # Мокируем JSON decode ошибку
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            json_error = json.JSONDecodeError("Invalid JSON", "doc", 0)
            mock_get.side_effect = json_error
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем что было логирование ошибки
            assert mock_logger.error.called or mock_logger.critical.called
            # Проверяем что вернулся fallback
            assert result == {"EUR": 0.85}
    
    @pytest.mark.asyncio
    async def test_fallback_success_logging(self, service, mock_logger):
        """Тест логирования успешного использования fallback данных"""
        service.api_key = None  # Принудительно используем fallback
        
        result = await service.get_rates_from_base("USD")
        
        # Проверяем логирование fallback
        mock_logger.info.assert_called()
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        
        # Ищем лог загрузки fallback
        fallback_load_log = next((log for log in info_calls if "🗄 LOADING FALLBACK RATES" in log), None)
        assert fallback_load_log is not None
        assert "Source: Static historical data" in fallback_load_log
        
        # Ищем лог успешной загрузки fallback
        fallback_success_log = next((log for log in info_calls if "✅ Fallback rates loaded" in log), None)
        assert fallback_success_log is not None
    
    @pytest.mark.asyncio
    async def test_health_check_logging(self, service, mock_logger):
        """Тест логирования health check"""
        # Мокируем успешный health check
        with patch.object(service, 'get_fiat_rate') as mock_get_rate:
            mock_get_rate.return_value = 0.85
            
            result = await service.health_check()
            
            # Проверяем логирование health check
            mock_logger.info.assert_called()
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            
            # Ищем лог старта health check
            start_log = next((log for log in info_calls if "Performing APILayer health check" in log), None)
            assert start_log is not None
            
            # Ищем лог завершения health check
            complete_log = next((log for log in info_calls if "APILayer health check completed" in log), None)
            assert complete_log is not None
            
            # Проверяем результат
            assert result['status'] == 'healthy'
            assert 'response_time_ms' in result
    
    def test_log_detailed_error_with_traceback(self, mock_logger):
        """Тест логирования ошибки с полным трейсбеком"""
        try:
            # Создаем реальную ошибку с трейсбеком
            raise ValueError("Test error with traceback")
        except ValueError as e:
            result = log_detailed_error("TRACEBACK_TEST", e, "test context")
            
            # Проверяем, что трейсбек записан
            assert result['traceback'] != 'No traceback available'
            assert 'ValueError: Test error with traceback' in result['traceback']
            
            # Проверяем формат логирования
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "🚨 TRACEBACK_TEST ERROR" in call_args
            assert "└─ Traceback:" in call_args


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])