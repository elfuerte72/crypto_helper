#!/usr/bin/env python3
"""
Configuration module for Crypto Helper Telegram Bot
Centralized configuration management with environment variables
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration class"""
    
    # Bot Configuration
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # Rapira API Configuration
    RAPIRA_API_KEY: str = os.getenv('RAPIRA_API_KEY', '')
    RAPIRA_API_URL: str = os.getenv(
        'RAPIRA_API_URL', 
        'https://api.rapira.net/open/market/rates'
    )
    
    # APILayer Configuration
    API_LAYER_KEY: str = os.getenv('API_LAYER_KEY', '')
    API_LAYER_URL: str = os.getenv(
        'API_LAYER_URL',
        'https://api.apilayer.com/exchangerates_data'
    )
    
    # Development Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Settings - OPTIMIZED FOR TASK-PERF-002
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT', '10'))  # СОКРАЩЕНО: с 30s до 10s
    API_RETRY_COUNT: int = int(os.getenv('API_RETRY_COUNT', '3'))
    
    # Connection Pool Settings - TASK-PERF-002 Performance Optimization
    CONNECTION_POOL_LIMIT: int = int(os.getenv('CONNECTION_POOL_LIMIT', '200'))  # УВЕЛИЧЕНО: общий лимит
    CONNECTION_POOL_LIMIT_PER_HOST: int = int(os.getenv('CONNECTION_POOL_LIMIT_PER_HOST', '50'))  # УВЕЛИЧЕНО: лимит на хост
    CONNECTION_KEEPALIVE_TIMEOUT: int = int(os.getenv('CONNECTION_KEEPALIVE_TIMEOUT', '60'))  # УВЕЛИЧЕНО: keep-alive
    
    # Optimized Timeouts for Production - TASK-PERF-002
    CONNECT_TIMEOUT: int = int(os.getenv('CONNECT_TIMEOUT', '5'))  # Таймаут подключения
    SOCK_CONNECT_TIMEOUT: int = int(os.getenv('SOCK_CONNECT_TIMEOUT', '3'))  # Таймаут сокета
    SOCK_READ_TIMEOUT: int = int(os.getenv('SOCK_READ_TIMEOUT', '5'))  # Таймаут чтения
    
    # Preloader Settings - TASK-PERF-002
    PRELOADER_ENABLED: bool = os.getenv('PRELOADER_ENABLED', 'true').lower() == 'true'
    PRELOADER_INTERVAL_CRITICAL: int = int(os.getenv('PRELOADER_INTERVAL_CRITICAL', '60'))  # 1 минута
    PRELOADER_INTERVAL_POPULAR: int = int(os.getenv('PRELOADER_INTERVAL_POPULAR', '120'))  # 2 минуты
    
    # Circuit Breaker Settings - TASK-PERF-002
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = int(os.getenv('CIRCUIT_BREAKER_FAILURE_THRESHOLD', '5'))
    CIRCUIT_BREAKER_RESET_TIMEOUT: int = int(os.getenv('CIRCUIT_BREAKER_RESET_TIMEOUT', '60'))  # 1 минута
    
    # Telegram Bot Settings - новые параметры для callback timeout fix
    CALLBACK_API_TIMEOUT: int = int(os.getenv('CALLBACK_API_TIMEOUT', '3'))  # Быстрые API запросы для callback
    CALLBACK_ANSWER_TIMEOUT: int = int(os.getenv('CALLBACK_ANSWER_TIMEOUT', '2'))  # Время на ответ callback
    MAX_MESSAGE_EDIT_ATTEMPTS: int = int(os.getenv('MAX_MESSAGE_EDIT_ATTEMPTS', '3'))  # Попытки редактирования
    
    # Development Settings
    USE_MOCK_DATA: bool = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'
    
    # Environment Detection
    IS_LOCAL_DEVELOPMENT: bool = os.getenv('ENVIRONMENT', 'production') == 'development'
    
    # Cache Configuration - РЕШЕНИЕ MEMORY LEAK
    CACHE_MAX_SIZE: int = int(os.getenv('CACHE_MAX_SIZE', '100'))  # Максимум записей в кэше
    CACHE_DEFAULT_TTL: int = int(os.getenv('CACHE_DEFAULT_TTL', '300'))  # 5 минут TTL
    CACHE_CLEANUP_INTERVAL: int = int(os.getenv('CACHE_CLEANUP_INTERVAL', '60'))  # Очистка каждую минуту
    RATES_CACHE_TTL: int = int(os.getenv('RATES_CACHE_TTL', '300'))  # TTL для курсов валют
    API_CACHE_TTL: int = int(os.getenv('API_CACHE_TTL', '600'))  # TTL для API ответов
    
    # New Exchange Flow Configuration (Новая логика пошагового обмена)
    # Поддерживаемые исходные валюты (что отдает клиент)
    SUPPORTED_SOURCE_CURRENCIES = ['RUB', 'USDT']
    
    # Поддерживаемые целевые валюты по исходным
    TARGETS_FOR_RUB = ['USDT', 'USD', 'EUR']  # Клиент отдает RUB
    TARGETS_FOR_USDT = ['RUB']                # Клиент отдает USDT
    
    # Валидационные правила для новой логики
    MIN_MARGIN_PERCENT = 0.1   # Минимальная наценка
    MAX_MARGIN_PERCENT = 10.0  # Максимальная наценка
    MIN_EXCHANGE_AMOUNT = 1.0  # Минимальная сумма обмена
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration parameters"""
        required_fields = ['BOT_TOKEN']
        missing_fields = []
        
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_fields)}"
            )
        
        return True
    
    @classmethod
    def get_log_level(cls) -> int:
        """Get logging level from configuration"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(cls.LOG_LEVEL.upper(), logging.INFO)

    @classmethod
    def get_environment_info(cls) -> str:
        """Get current environment information"""
        if cls.IS_LOCAL_DEVELOPMENT:
            return "🔧 Local Development Environment"
        else:
            return "🚀 Production Environment"


# Create global config instance
config = Config()

# Validate configuration on import
try:
    config.validate()
    print("✅ Configuration loaded successfully")
    print(f"📍 Environment: {config.get_environment_info()}")
    if config.IS_LOCAL_DEVELOPMENT:
        print("🤖 Using development environment")
    else:
        print("🤖 Using production environment")
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print(
        "Please check your .env file and ensure all required "
        "variables are set."
    )