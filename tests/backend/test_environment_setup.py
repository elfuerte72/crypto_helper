#!/usr/bin/env python3
"""
Unit tests for environment setup task
Tests that all components are properly configured and working
"""

import unittest
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestEnvironmentSetup(unittest.TestCase):
    """Test cases for environment setup task completion"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent.parent
        self.src_dir = self.project_root / 'src'
    
    def test_project_structure_exists(self):
        """Test that all required directories exist"""
        required_dirs = [
            self.src_dir,
            self.src_dir / 'handlers',
            self.src_dir / 'services',
            self.src_dir / 'utils',
            self.project_root / 'tests',
            self.project_root / 'tests' / 'backend'
        ]
        
        for dir_path in required_dirs:
            self.assertTrue(dir_path.exists(), f"Directory {dir_path} should exist")
            self.assertTrue(dir_path.is_dir(), f"{dir_path} should be a directory")
    
    def test_required_files_exist(self):
        """Test that all required files exist"""
        required_files = [
            self.src_dir / '__init__.py',
            self.src_dir / 'config.py',
            self.src_dir / 'bot.py',
            self.src_dir / 'main.py',
            self.src_dir / 'handlers' / '__init__.py',
            self.src_dir / 'services' / '__init__.py',
            self.src_dir / 'services' / 'api_service.py',
            self.src_dir / 'utils' / '__init__.py',
            self.src_dir / 'utils' / 'logger.py',
            self.project_root / '.env',
            self.project_root / '.env.example',
            self.project_root / 'requirements.txt'
        ]
        
        for file_path in required_files:
            self.assertTrue(file_path.exists(), f"File {file_path} should exist")
            self.assertTrue(file_path.is_file(), f"{file_path} should be a file")
    
    def test_config_module_imports(self):
        """Test that config module can be imported and has required attributes"""
        try:
            from config import Config, config
            
            # Test that Config class has required attributes
            required_attrs = [
                'BOT_TOKEN', 'RAPIRA_API_KEY', 'RAPIRA_API_URL',
                'ADMIN_CHANNEL_ID', 'DEBUG_MODE', 'LOG_LEVEL',
                'API_TIMEOUT', 'API_RETRY_COUNT', 'SUPPORTED_PAIRS'
            ]
            
            for attr in required_attrs:
                self.assertTrue(hasattr(Config, attr), f"Config should have {attr} attribute")
            
            # Test that config instance exists
            self.assertIsNotNone(config)
            
        except ImportError as e:
            self.fail(f"Could not import config module: {e}")
    
    def test_logger_module_imports(self):
        """Test that logger module can be imported"""
        try:
            from utils.logger import setup_logger, get_bot_logger, get_api_logger, get_handler_logger
            
            # Test that functions exist and are callable
            self.assertTrue(callable(setup_logger))
            self.assertTrue(callable(get_bot_logger))
            self.assertTrue(callable(get_api_logger))
            self.assertTrue(callable(get_handler_logger))
            
        except ImportError as e:
            self.fail(f"Could not import logger module: {e}")
    
    def test_api_service_module_imports(self):
        """Test that API service module can be imported"""
        try:
            from services.api_service import APIService, ExchangeRate, api_service
            
            # Test that classes exist
            self.assertTrue(hasattr(APIService, '__init__'))
            self.assertTrue(hasattr(ExchangeRate, '__dataclass_fields__'))
            self.assertIsNotNone(api_service)
            
        except ImportError as e:
            self.fail(f"Could not import API service module: {e}")
    
    def test_bot_module_imports(self):
        """Test that bot module can be imported"""
        try:
            from bot import CryptoHelperBot
            
            # Test that bot class exists
            self.assertTrue(hasattr(CryptoHelperBot, '__init__'))
            self.assertTrue(hasattr(CryptoHelperBot, 'start'))
            
        except ImportError as e:
            self.fail(f"Could not import bot module: {e}")
    
    def test_environment_file_structure(self):
        """Test that .env file has required structure"""
        env_file = self.project_root / '.env'
        
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        # Check for required environment variables
        required_vars = [
            'BOT_TOKEN',
            'RAPIRA_API_URL',
            'ADMIN_CHANNEL_ID',
            'DEBUG_MODE',
            'LOG_LEVEL'
        ]
        
        for var in required_vars:
            self.assertIn(var, env_content, f"Environment variable {var} should be in .env file")
    
    def test_supported_currency_pairs(self):
        """Test that supported currency pairs are properly configured"""
        try:
            from config import Config
            
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
                self.assertIn(pair, Config.SUPPORTED_PAIRS, f"Currency pair {pair} should be supported")
            
            # Check total count
            self.assertEqual(len(Config.SUPPORTED_PAIRS), 16, "Should support exactly 16 currency pairs")
            
        except ImportError as e:
            self.fail(f"Could not test currency pairs: {e}")
    
    def test_requirements_file_content(self):
        """Test that requirements.txt has required dependencies"""
        requirements_file = self.project_root / 'requirements.txt'
        
        with open(requirements_file, 'r') as f:
            requirements_content = f.read()
        
        required_packages = ['aiogram', 'aiohttp', 'python-dotenv']
        
        for package in required_packages:
            self.assertIn(package, requirements_content, f"Package {package} should be in requirements.txt")
    
    def test_package_init_files(self):
        """Test that all __init__.py files have proper content"""
        init_files = [
            self.src_dir / '__init__.py',
            self.src_dir / 'handlers' / '__init__.py',
            self.src_dir / 'services' / '__init__.py',
            self.src_dir / 'utils' / '__init__.py'
        ]
        
        for init_file in init_files:
            with open(init_file, 'r') as f:
                content = f.read()
            
            self.assertGreater(len(content.strip()), 0, f"{init_file} should not be empty")
            self.assertIn('"""', content, f"{init_file} should have docstring")


if __name__ == '__main__':
    unittest.main()