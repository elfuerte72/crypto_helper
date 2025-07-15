#!/usr/bin/env python3
"""
Unit tests for configuration module
Tests environment variable loading and validation
"""

import unittest
import os
from unittest.mock import patch
import sys
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class"""
    
    def setUp(self):
        """Set up test environment"""
        # Store original environment
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Clean up test environment"""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_config_with_valid_bot_token(self):
        """Test config validation with valid BOT_TOKEN"""
        with patch.dict(os.environ, {'BOT_TOKEN': 'test_token_123'}):
            # Reload config
            from importlib import reload
            import config
            reload(config)
            
            # Should not raise exception
            self.assertTrue(config.Config.validate())
    
    def test_config_bot_token_required(self):
        """Test that BOT_TOKEN is required and present"""
        with patch.dict(os.environ, {'BOT_TOKEN': 'test_token'}):
            from importlib import reload
            import config
            reload(config)
            
            # Should validate successfully with BOT_TOKEN
            self.assertTrue(config.Config.validate())
            self.assertNotEqual(config.Config.BOT_TOKEN, '')
            self.assertTrue(len(config.Config.BOT_TOKEN) > 0)
    
    def test_config_default_values(self):
        """Test config default values"""
        with patch.dict(os.environ, {'BOT_TOKEN': 'test_token'}):
            from importlib import reload
            import config
            reload(config)
            
            cfg = config.Config()
            
            # Test defaults
            self.assertEqual(cfg.RAPIRA_API_URL, 'https://api.rapira.net/open/market/rates')
            self.assertEqual(cfg.API_TIMEOUT, 30)
            self.assertEqual(cfg.API_RETRY_COUNT, 3)
            self.assertEqual(cfg.LOG_LEVEL, 'INFO')  # Default log level
    
    def test_config_log_level_mapping(self):
        """Test log level string to logging level mapping"""
        test_cases = [
            ('DEBUG', logging.DEBUG),
            ('INFO', logging.INFO),
            ('WARNING', logging.WARNING),
            ('ERROR', logging.ERROR),
            ('CRITICAL', logging.CRITICAL),
            ('invalid', logging.INFO)  # Default
        ]
        
        for log_level, expected in test_cases:
            with patch.dict(os.environ, {
                'BOT_TOKEN': 'test_token',
                'LOG_LEVEL': log_level
            }):
                from importlib import reload
                import config
                reload(config)
                
                actual = config.Config.get_log_level()
                self.assertEqual(actual, expected,
                               f"LOG_LEVEL='{log_level}' should map to {expected}")
    
    def test_supported_currency_pairs(self):
        """Test that all expected currency pairs are supported"""
        with patch.dict(os.environ, {'BOT_TOKEN': 'test_token'}):
            from importlib import reload
            import config
            reload(config)
            
            # Проверяем, что есть основные криптовалютные пары
            expected_base_pairs = [
                'USDT/RUB', 'BTC/USDT', 'ETH/USDT', 'TON/USDT',
                'RUB/BTC', 'BTC/RUB', 'RUB/TON', 'TON/RUB',
                'RUB/USDT', 'USDT/RUB', 'RUB/ETH', 'ETH/RUB'
            ]
            
            for pair in expected_base_pairs:
                self.assertIn(pair, config.Config.SUPPORTED_PAIRS,
                            f"Currency pair {pair} should be supported")
            
            # Проверяем, что есть поддерживаемые пары
            self.assertGreater(len(config.Config.SUPPORTED_PAIRS), 0)
    
    def test_config_api_settings(self):
        """Test API-related configuration settings"""
        with patch.dict(os.environ, {
            'BOT_TOKEN': 'test_token',
            'API_TIMEOUT': '45',
            'API_RETRY_COUNT': '5'
        }):
            from importlib import reload
            import config
            reload(config)
            
            cfg = config.Config()
            
            # Test API settings
            self.assertEqual(cfg.API_TIMEOUT, 45)
            self.assertEqual(cfg.API_RETRY_COUNT, 5)
    
    def test_config_rapira_api_settings(self):
        """Test Rapira API specific settings"""
        with patch.dict(os.environ, {
            'BOT_TOKEN': 'test_token',
            'RAPIRA_API_KEY': 'test_api_key',
            'RAPIRA_API_URL': 'https://custom.api.url'
        }):
            from importlib import reload
            import config
            reload(config)
            
            cfg = config.Config()
            
            # Test Rapira API settings
            self.assertEqual(cfg.RAPIRA_API_KEY, 'test_api_key')
            self.assertEqual(cfg.RAPIRA_API_URL, 'https://custom.api.url')


if __name__ == '__main__':
    unittest.main()