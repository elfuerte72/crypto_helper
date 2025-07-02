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
    
    # Admin Configuration
    ADMIN_CHANNEL_ID: int = int(os.getenv('ADMIN_CHANNEL_ID', '0'))
    
    # Rapira API Configuration
    RAPIRA_API_KEY: str = os.getenv('RAPIRA_API_KEY', '')
    RAPIRA_API_URL: str = os.getenv(
        'RAPIRA_API_URL', 
        'https://api.rapira.net/open/market/rates'
    )
    
    # Development Settings
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Settings
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT', '30'))
    API_RETRY_COUNT: int = int(os.getenv('API_RETRY_COUNT', '3'))
    
    # Supported Currency Pairs
    SUPPORTED_PAIRS = [
        # Основные криптовалютные пары из Rapira API
        'USDT/RUB', 'RUB/USDT',
        'BTC/USDT', 'USDT/BTC',
        'ETH/USDT', 'USDT/ETH',
        'ETH/BTC', 'BTC/ETH',
        'LTC/USDT', 'USDT/LTC',
        'TRX/USDT', 'USDT/TRX',
        'BNB/USDT', 'USDT/BNB',
        'TON/USDT', 'USDT/TON',
        'DOGE/USDT', 'USDT/DOGE',
        'SOL/USDT', 'USDT/SOL',
        'NOT/USDT', 'USDT/NOT',
        'USDC/USDT', 'USDT/USDC',
        'DAI/USDT', 'USDT/DAI',
        'ETC/USDT', 'USDT/ETC',
        'OP/USDT', 'USDT/OP',
        'XMR/USDT', 'USDT/XMR',
        
        # Кросс-курсы для фиатных валют (будут вычисляться через USDT/RUB)
        'RUB/ZAR', 'ZAR/RUB',
        'RUB/THB', 'THB/RUB',
        'RUB/AED', 'AED/RUB',
        'RUB/IDR', 'IDR/RUB',
        'USDT/ZAR', 'ZAR/USDT',
        'USDT/THB', 'THB/USDT',
        'USDT/AED', 'AED/USDT',
        'USDT/IDR', 'IDR/USDT'
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
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return cls.DEBUG_MODE


# Create global config instance
config = Config()

# Validate configuration on import
try:
    config.validate()
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print(
        "Please check your .env file and ensure all required variables are set."
    )