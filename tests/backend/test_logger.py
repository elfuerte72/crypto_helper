#!/usr/bin/env python3
"""
Unit tests for logger utilities
Tests logging configuration and functionality
"""

import unittest
import logging
import sys
import os
from unittest.mock import patch, MagicMock
from io import StringIO

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.logger import setup_logger, get_bot_logger, get_api_logger, get_handler_logger


class TestLogger(unittest.TestCase):
    """Test cases for logger utilities"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear any existing loggers to avoid interference
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.WARNING)
    
    def tearDown(self):
        """Clean up test environment"""
        # Clear loggers after each test
        for name in list(logging.Logger.manager.loggerDict.keys()):
            if name.startswith('crypto_helper') or name.startswith('test_'):
                logger = logging.getLogger(name)
                logger.handlers.clear()
                logger.setLevel(logging.NOTSET)
    
    def test_setup_logger_basic(self):
        """Test basic logger setup"""
        logger = setup_logger('test_logger')
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'test_logger')
        self.assertTrue(len(logger.handlers) > 0)
    
    def test_setup_logger_with_level(self):
        """Test logger setup with custom level"""
        logger = setup_logger('test_logger', level=logging.DEBUG)
        
        self.assertEqual(logger.level, logging.DEBUG)
    
    @patch('src.config.config.get_log_level')
    def test_setup_logger_uses_config_level(self, mock_get_log_level):
        """Test that logger uses config log level by default"""
        mock_get_log_level.return_value = logging.WARNING
        
        logger = setup_logger('test_logger')
        
        mock_get_log_level.assert_called_once()
        self.assertEqual(logger.level, logging.WARNING)
    
    def test_setup_logger_console_handler(self):
        """Test that console handler is properly configured"""
        logger = setup_logger('test_logger')
        
        # Should have at least one handler
        self.assertTrue(len(logger.handlers) >= 1)
        
        # Find console handler
        console_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                console_handler = handler
                break
        
        self.assertIsNotNone(console_handler)
        self.assertEqual(console_handler.stream, sys.stdout)
    
    def test_setup_logger_formatter(self):
        """Test logger formatter configuration"""
        logger = setup_logger('test_logger')
        
        handler = logger.handlers[0]
        formatter = handler.formatter
        
        self.assertIsNotNone(formatter)
        
        # Test formatter format
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        self.assertIn('test message', formatted)
        self.assertIn('INFO', formatted)
        self.assertIn('test', formatted)
    
    def test_setup_logger_no_duplicate_handlers(self):
        """Test that calling setup_logger twice doesn't create duplicate handlers"""
        logger1 = setup_logger('test_logger')
        initial_handler_count = len(logger1.handlers)
        
        logger2 = setup_logger('test_logger')
        
        self.assertEqual(logger1, logger2)
        self.assertEqual(len(logger2.handlers), initial_handler_count)
    
    def test_logger_output(self):
        """Test actual logger output"""
        # Capture stdout
        captured_output = StringIO()
        
        # Create logger with custom handler
        logger = logging.getLogger('test_output_logger')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(captured_output)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Test logging
        logger.info('Test info message')
        logger.warning('Test warning message')
        
        output = captured_output.getvalue()
        self.assertIn('INFO - Test info message', output)
        self.assertIn('WARNING - Test warning message', output)
    
    def test_get_bot_logger(self):
        """Test get_bot_logger function"""
        logger = get_bot_logger()
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'crypto_helper_bot')
    
    def test_get_api_logger(self):
        """Test get_api_logger function"""
        logger = get_api_logger()
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'crypto_helper_api')
    
    def test_get_handler_logger(self):
        """Test get_handler_logger function"""
        logger = get_handler_logger()
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'crypto_helper_handlers')
    
    def test_different_loggers_are_separate(self):
        """Test that different logger functions return separate loggers"""
        bot_logger = get_bot_logger()
        api_logger = get_api_logger()
        handler_logger = get_handler_logger()
        
        self.assertNotEqual(bot_logger, api_logger)
        self.assertNotEqual(api_logger, handler_logger)
        self.assertNotEqual(bot_logger, handler_logger)
        
        self.assertNotEqual(bot_logger.name, api_logger.name)
        self.assertNotEqual(api_logger.name, handler_logger.name)
        self.assertNotEqual(bot_logger.name, handler_logger.name)
    
    @patch('pathlib.Path.mkdir')
    @patch('logging.FileHandler')
    def test_setup_logger_with_file(self, mock_file_handler, mock_mkdir):
        """Test logger setup with file handler"""
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler
        
        logger = setup_logger('test_logger', log_file='/tmp/test.log')
        
        # Should create directory
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # Should create file handler
        mock_file_handler.assert_called_once_with('/tmp/test.log', encoding='utf-8')
        
        # Should add file handler to logger
        self.assertIn(mock_handler, logger.handlers)
    
    @patch('logging.FileHandler')
    def test_setup_logger_file_error_handling(self, mock_file_handler):
        """Test file handler error handling"""
        # Mock file handler to raise exception
        mock_file_handler.side_effect = Exception("File error")
        
        # Should not raise exception, but should log warning
        logger = setup_logger('test_logger', log_file='/invalid/path/test.log')
        
        # Logger should still be created successfully
        self.assertIsInstance(logger, logging.Logger)
        self.assertTrue(len(logger.handlers) > 0)


if __name__ == '__main__':
    unittest.main()