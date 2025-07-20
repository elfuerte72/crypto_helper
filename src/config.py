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
    
    # Bot Configuration - приоритет LOCAL_BOT_TOKEN для разработки
    BOT_TOKEN: str = os.getenv('LOCAL_BOT_TOKEN') or os.getenv('BOT_TOKEN', '')
    
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
    
    # API Settings
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT', '30'))
    API_RETRY_COUNT: int = int(os.getenv('API_RETRY_COUNT', '3'))
    
    # Telegram Bot Settings - новые параметры для callback timeout fix
    CALLBACK_API_TIMEOUT: int = int(os.getenv('CALLBACK_API_TIMEOUT', '3'))  # Быстрые API запросы для callback
    CALLBACK_ANSWER_TIMEOUT: int = int(os.getenv('CALLBACK_ANSWER_TIMEOUT', '2'))  # Время на ответ callback
    MAX_MESSAGE_EDIT_ATTEMPTS: int = int(os.getenv('MAX_MESSAGE_EDIT_ATTEMPTS', '3'))  # Попытки редактирования
    
    # Development Settings
    USE_MOCK_DATA: bool = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'
    
    # Environment Detection
    IS_LOCAL_DEVELOPMENT: bool = bool(os.getenv('LOCAL_BOT_TOKEN'))
    
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
        print("🤖 Using LOCAL_BOT_TOKEN for testing")
    else:
        print("🤖 Using BOT_TOKEN for production")
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print(
        "Please check your .env file and ensure all required "
        "variables are set."
    )