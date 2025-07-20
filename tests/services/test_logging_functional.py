#!/usr/bin/env python3
"""
Функциональные тесты для проверки улучшенного логирования в FiatRatesService
Tests TASK-CRYPTO-003: Улучшение логирования API ошибок
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch
from io import StringIO

# Настройка для импорта модулей
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.fiat_rates_service import FiatRatesService, log_detailed_error


class TestLoggingFunctional:
    """Функциональные тесты для проверки улучшенного логирования"""
    
    @pytest.mark.asyncio
    async def test_api_key_missing_scenario(self):
        """Функциональный тест: сценарий отсутствия API ключа"""
        service = FiatRatesService()
        service.api_key = None  # Намеренно убираем API ключ
        
        captured_logs = []
        
        def capture_log(msg):
            captured_logs.append(msg)
        
        with patch('src.services.fiat_rates_service.logger') as mock_logger:
            mock_logger.warning = Mock(side_effect=capture_log)
            mock_logger.info = Mock(side_effect=capture_log)
            
            # Тестируем получение курсов без API ключа
            result = await service.get_rates_from_base("USD")
            
            # Проверяем, что получили fallback данные
            assert result is not None
            assert isinstance(result, dict)
            assert len(result) > 0
            
            # Проверяем логирование
            log_messages = ' '.join(captured_logs)
            assert "🔑 APILayer API key not configured" in log_messages
            assert "Service: FiatRatesService" in log_messages
            assert "✅ Fallback rates loaded" in log_messages
    
    @pytest.mark.asyncio
    async def test_fallback_rates_detailed_logging(self):
        """Функциональный тест: детальное логирование fallback rates"""
        service = FiatRatesService()
        
        captured_logs = []
        
        def capture_log(msg):
            captured_logs.append(msg)
        
        with patch('src.services.fiat_rates_service.logger') as mock_logger:
            mock_logger.info = Mock(side_effect=capture_log)
            
            # Тестируем загрузку fallback курсов
            result = await service._get_fallback_rates("USD")
            
            # Проверяем результат
            assert result is not None
            assert isinstance(result, dict)
            assert "EUR" in result
            assert "GBP" in result
            assert "RUB" in result
            
            # Проверяем логирование
            log_messages = ' '.join(captured_logs)
            assert "🗄 LOADING FALLBACK RATES for USD" in log_messages
            assert "Source: Static historical data" in log_messages
            assert "Reason: APILayer unavailable" in log_messages
    
    @pytest.mark.asyncio
    async def test_get_fiat_rate_with_logging(self):
        """Функциональный тест: получение курса валют с логированием"""
        service = FiatRatesService()
        
        captured_logs = []
        
        def capture_log(msg):
            captured_logs.append(msg)
        
        with patch('src.services.fiat_rates_service.logger') as mock_logger:
            mock_logger.info = Mock(side_effect=capture_log)
            mock_logger.warning = Mock(side_effect=capture_log)
            
            # Тестируем получение курса USD/EUR
            rate = await service.get_fiat_rate("USD", "EUR")
            
            # Проверяем результат
            assert rate is not None
            assert isinstance(rate, float)
            assert rate > 0
            
            # Проверяем логирование
            log_messages = ' '.join(captured_logs)
            assert "Getting fiat rate for USD/EUR" in log_messages
    
    @pytest.mark.asyncio
    async def test_health_check_with_logging(self):
        """Функциональный тест: health check с логированием"""
        service = FiatRatesService()
        
        captured_logs = []
        
        def capture_log(msg):
            captured_logs.append(msg)
        
        with patch('src.services.fiat_rates_service.logger') as mock_logger:
            mock_logger.info = Mock(side_effect=capture_log)
            
            # Тестируем health check
            result = await service.health_check()
            
            # Проверяем результат
            assert result is not None
            assert 'status' in result
            assert 'timestamp' in result
            assert 'service' in result
            assert result['service'] == 'apilayer_fiat_rates'
            
            # Проверяем логирование
            log_messages = ' '.join(captured_logs)
            assert "Performing APILayer health check" in log_messages
            assert "APILayer health check completed" in log_messages
    
    def test_detailed_error_logging_function(self):
        """Функциональный тест: функция детального логирования ошибок"""
        captured_logs = []
        
        def capture_log(msg):
            captured_logs.append(msg)
        
        with patch('src.services.fiat_rates_service.logger') as mock_logger:
            mock_logger.error = Mock(side_effect=capture_log)
            
            # Создаем реальную ошибку
            try:
                raise ConnectionError("Network connection failed")
            except ConnectionError as e:
                # Тестируем детальное логирование
                result = log_detailed_error("NETWORK", e, "APILayer request")
                
                # Проверяем результат
                assert result['type'] == "NETWORK"
                assert result['class'] == "ConnectionError"
                assert result['message'] == "Network connection failed"
                assert result['context'] == "APILayer request"
                assert 'traceback' in result
                
                # Проверяем логирование
                log_messages = ' '.join(captured_logs)
                assert "🚨 NETWORK ERROR in APILayer request:" in log_messages
                assert "Type: ConnectionError" in log_messages
                assert "Message: Network connection failed" in log_messages
                assert "└─ Traceback:" in log_messages
    
    @pytest.mark.asyncio
    async def test_exchange_rate_object_creation(self):
        """Функциональный тест: создание объекта ExchangeRate"""
        service = FiatRatesService()
        
        # Тестируем создание ExchangeRate объекта
        exchange_rate = await service.create_fiat_exchange_rate("USD", "EUR", 0.85)
        
        # Проверяем результат
        assert exchange_rate is not None
        assert exchange_rate.pair == "USD/EUR"
        assert exchange_rate.rate == 0.85
        assert exchange_rate.source == 'apilayer'
        assert exchange_rate.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_get_fiat_exchange_rate_with_fallback(self):
        """Функциональный тест: получение ExchangeRate с fallback"""
        service = FiatRatesService()
        
        # Тестируем получение ExchangeRate объекта
        exchange_rate = await service.get_fiat_exchange_rate("USD/EUR")
        
        # Проверяем результат
        assert exchange_rate is not None
        assert exchange_rate.pair == "USD/EUR"
        assert exchange_rate.rate > 0
        assert exchange_rate.source in ['apilayer', 'apilayer_fallback']
        assert exchange_rate.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_multiple_currency_pairs(self):
        """Функциональный тест: получение курсов для множества валютных пар"""
        service = FiatRatesService()
        
        currency_pairs = [
            ("USD", "EUR"),
            ("EUR", "GBP"), 
            ("USD", "RUB"),
            ("GBP", "USD")
        ]
        
        captured_logs = []
        
        def capture_log(msg):
            captured_logs.append(msg)
        
        with patch('src.services.fiat_rates_service.logger') as mock_logger:
            mock_logger.info = Mock(side_effect=capture_log)
            mock_logger.warning = Mock(side_effect=capture_log)
            
            # Тестируем получение курсов для всех пар
            for from_curr, to_curr in currency_pairs:
                rate = await service.get_fiat_rate(from_curr, to_curr)
                
                # Проверяем результат
                assert rate is not None
                assert isinstance(rate, float)
                assert rate > 0
                
                # Проверяем логирование
                expected_log = f"Getting fiat rate for {from_curr}/{to_curr}"
                log_messages = ' '.join(captured_logs)
                assert expected_log in log_messages
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self):
        """Функциональный тест: функциональность кэширования"""
        service = FiatRatesService()
        
        # Тестируем кэширование
        test_rates = {"EUR": 0.85, "GBP": 0.75}
        await service._cache_rates("USD", test_rates)
        
        # Получаем из кэша
        cached_rates = await service._get_cached_rates("USD")
        
        # Проверяем результат
        assert cached_rates is not None
        assert cached_rates == test_rates
        
        # Тестируем истечение кэша (симулируем)
        import time
        time.sleep(0.1)  # Небольшая задержка
        
        # Кэш все еще должен быть активен (время жизни 5 минут)
        cached_rates_2 = await service._get_cached_rates("USD")
        assert cached_rates_2 is not None


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])