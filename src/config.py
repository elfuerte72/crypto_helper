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
    
    # Development Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Settings
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT', '30'))
    API_RETRY_COUNT: int = int(os.getenv('API_RETRY_COUNT', '3'))
    
    # Supported Currency Pairs (криптовалюты с рублем)
    SUPPORTED_PAIRS = [
        # Основные пары из Rapira API (прямые)
        'USDT/RUB', 'BTC/USDT', 'ETH/USDT', 'TON/USDT',
        
        # Поддерживаемые пары через расчет
        'RUB/BTC', 'BTC/RUB',
        'RUB/TON', 'TON/RUB',
        'RUB/USDT', 'USDT/RUB',
        'RUB/ETH', 'ETH/RUB'
    ]
    
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
    



# Create global config instance
config = Config()

# Validate configuration on import
try:
    config.validate()
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print(
        "Please check your .env file and ensure all required "
        "variables are set."
    )