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
    
    def test_config_missing_bot_token(self):
        """Test config validation with missing BOT_TOKEN"""
        with patch.dict(os.environ, {}, clear=True):
            # Create fresh config instance without BOT_TOKEN
            from config import Config
            test_config = Config()
            test_config.BOT_TOKEN = ''  # Explicitly set to empty
            
            # Should raise ValueError
            with self.assertRaises(ValueError) as context:
                test_config.validate()
            
            self.assertIn('BOT_TOKEN', str(context.exception))
    
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
            self.assertFalse(cfg.DEBUG_MODE)  # Default should be False
    
    def test_config_debug_mode_parsing(self):
        """Test DEBUG_MODE boolean parsing"""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('', False),
            ('invalid', False)
        ]
        
        for debug_value, expected in test_cases:
            with patch.dict(os.environ, {
                'BOT_TOKEN': 'test_token',
                'DEBUG_MODE': debug_value
            }):
                from importlib import reload
                import config
                reload(config)
                
                self.assertEqual(config.Config.DEBUG_MODE, expected,
                               f"DEBUG_MODE='{debug_value}' should be {expected}")
    
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
            
            expected_pairs = [
                'RUB/ZAR', 'ZAR/RUB',
                'RUB/THB', 'THB/RUB',
                'RUB/AED', 'AED/RUB',
                'RUB/IDR', 'IDR/RUB',
                'USDT/ZAR', 'ZAR/USDT',
                'USDT/THB', 'THB/USDT',
                'USDT/AED', 'AED/USDT',
                'USDT/IDR', 'IDR/USDT'
            ]
            
            for pair in expected_pairs:
                self.assertIn(pair, config.Config.SUPPORTED_PAIRS,
                            f"Currency pair {pair} should be supported")
            
            # Check total count
            self.assertEqual(len(config.Config.SUPPORTED_PAIRS), 16)
    
    def test_config_is_development(self):
        """Test is_development method"""
        # Test development mode
        with patch.dict(os.environ, {
            'BOT_TOKEN': 'test_token',
            'DEBUG_MODE': 'true'
        }):
            from importlib import reload
            import config
            reload(config)
            
            self.assertTrue(config.Config.is_development())
        
        # Test production mode
        with patch.dict(os.environ, {
            'BOT_TOKEN': 'test_token',
            'DEBUG_MODE': 'false'
        }):
            from importlib import reload
            import config
            reload(config)
            
            self.assertFalse(config.Config.is_development())


if __name__ == '__main__':
    unittest.main()