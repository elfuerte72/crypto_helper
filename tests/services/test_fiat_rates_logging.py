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
        # Мокируем сессию и ответ
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "success": True,
            "rates": {"EUR": 0.85, "GBP": 0.75}
        })
        
        # Создаем context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_context)
        service.session = mock_session
        
        # Мокируем rate limiting и кэширование
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_cache_rates') as mock_cache:
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем успешное логирование
            mock_logger.info.assert_called()
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            
            # Ищем лог запуска запроса
            start_log = next((log for log in info_calls if "🚀 Starting APILayer request" in log), None)
            assert start_log is not None
            assert "Max retries: 3" in start_log
            assert "Base delay: 5s" in start_log
            
            # Ищем лог успешного ответа
            success_log = next((log for log in info_calls if "✅ APILayer SUCCESS" in log), None)
            assert success_log is not None
            assert "Rates received: 2" in success_log
            assert "Attempt: 1/3" in success_log
    
    @pytest.mark.asyncio
    async def test_api_error_logging(self, service, mock_logger):
        """Тест логирования ошибок API"""
        # Мокируем сессию и ответ с ошибкой
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "success": False,
            "error": {
                "code": "invalid_base",
                "info": "Invalid base currency specified"
            }
        })
        
        # Создаем context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_context)
        service.session = mock_session
        
        # Мокируем fallback
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback:
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем логирование ошибки API
            mock_logger.error.assert_called()
            error_call = mock_logger.error.call_args[0][0]
            assert "❌ APILayer API ERROR for USD" in error_call
            assert "Error code: invalid_base" in error_call
            assert "Error message: Invalid base currency specified" in error_call
            assert "Full response:" in error_call
    
    @pytest.mark.asyncio
    async def test_authentication_error_logging(self, service, mock_logger):
        """Тест логирования ошибок аутентификации"""
        # Мокируем сессию и ответ 401
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.url = "https://api.apilayer.com/exchangerates_data/latest"
        
        # Создаем context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_context)
        service.session = mock_session
        
        # Мокируем fallback
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback:
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем логирование ошибки аутентификации
            mock_logger.error.assert_called()
            error_call = mock_logger.error.call_args[0][0]
            assert "🔒 APILayer AUTHENTICATION FAILED for USD" in error_call
            assert "Status: 401" in error_call
            assert "API key present: True" in error_call
            assert "API key length:" in error_call
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_logging(self, service, mock_logger):
        """Тест логирования ошибок rate limiting"""
        # Мокируем сессию и ответ 429
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.headers = {'Retry-After': '30', 'content-type': 'application/json'}
        
        # Создаем context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_context)
        service.session = mock_session
        
        # Мокируем fallback для финального случая
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback:
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем логирование rate limit
            mock_logger.warning.assert_called()
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            
            # Ищем лог rate limit
            rate_limit_log = next((log for log in warning_calls if "⏱️ APILayer RATE LIMIT" in log), None)
            assert rate_limit_log is not None
            assert "Status: 429" in rate_limit_log
            assert "Retry-After header: 30s" in rate_limit_log
            assert "Exponential delay:" in rate_limit_log
    
    @pytest.mark.asyncio
    async def test_network_error_logging(self, service, mock_logger):
        """Тест логирования сетевых ошибок"""
        # Мокируем сессию, которая выбрасывает ClientError
        mock_session = AsyncMock()
        network_error = ClientError("Connection timeout")
        mock_session.get.side_effect = network_error
        
        service.session = mock_session
        
        # Мокируем fallback
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback:
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем логирование сетевой ошибки
            mock_logger.error.assert_called()
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            
            # Ищем детальный лог ошибки
            detailed_error_log = next((log for log in error_calls if "🚨 NETWORK ERROR" in log), None)
            assert detailed_error_log is not None
            
            # Ищем лог сетевой ошибки
            network_error_log = next((log for log in error_calls if "🌐 NETWORK ERROR" in log), None)
            assert network_error_log is not None
            assert "Error type: ClientError" in network_error_log
            assert "Connection timeout" in network_error_log
    
    @pytest.mark.asyncio
    async def test_unexpected_error_logging(self, service, mock_logger):
        """Тест логирования неожиданных ошибок"""
        # Мокируем сессию, которая выбрасывает неожиданную ошибку
        mock_session = AsyncMock()
        unexpected_error = RuntimeError("Unexpected system error")
        mock_session.get.side_effect = unexpected_error
        
        service.session = mock_session
        
        # Мокируем fallback
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback:
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем логирование неожиданной ошибки
            mock_logger.critical.assert_called()
            critical_call = mock_logger.critical.call_args[0][0]
            assert "🚨 UNEXPECTED ERROR for USD" in critical_call
            assert "Error type: RuntimeError" in critical_call
            assert "Unexpected system error" in critical_call
            assert "Python version:" in critical_call
    
    @pytest.mark.asyncio
    async def test_json_decode_error_logging(self, service, mock_logger):
        """Тест логирования ошибок парсинга JSON"""
        # Мокируем сессию и ответ с невалидным JSON
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0))
        mock_response.text = AsyncMock(return_value="Invalid JSON response")
        
        # Создаем context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_context)
        service.session = mock_session
        
        # Мокируем fallback
        with patch.object(service, '_rate_limit') as mock_rate_limit, \
             patch.object(service, '_get_fallback_rates') as mock_fallback:
            mock_fallback.return_value = {"EUR": 0.85}
            
            result = await service.get_rates_from_base("USD")
            
            # Проверяем логирование ошибки JSON
            mock_logger.error.assert_called()
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            
            # Ищем лог JSON ошибки
            json_error_log = next((log for log in error_calls if "🚨 Invalid JSON response" in log), None)
            assert json_error_log is not None
            assert "Invalid JSON response" in json_error_log
    
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