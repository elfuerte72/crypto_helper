#!/usr/bin/env python3
"""
Unit tests for API service
Tests external API communication and data handling
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock
import aiohttp

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.api_service import APIService, ExchangeRate


class TestAPIService(unittest.TestCase):
    """Test cases for APIService class"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_service = APIService()
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'api_service'):
            # Clean up session if it exists
            if self.api_service.session and not self.api_service.session.closed:
                asyncio.run(self.api_service.close_session())
    
    def test_exchange_rate_dataclass(self):
        """Test ExchangeRate dataclass creation"""
        rate = ExchangeRate(
            pair='RUB/ZAR',
            rate=0.18,
            timestamp='2024-12-01T12:00:00Z',
            source='test'
        )
        
        self.assertEqual(rate.pair, 'RUB/ZAR')
        self.assertEqual(rate.rate, 0.18)
        self.assertEqual(rate.timestamp, '2024-12-01T12:00:00Z')
        self.assertEqual(rate.source, 'test')
    
    def test_exchange_rate_default_source(self):
        """Test ExchangeRate default source value"""
        rate = ExchangeRate(
            pair='RUB/ZAR',
            rate=0.18,
            timestamp='2024-12-01T12:00:00Z'
        )
        
        self.assertEqual(rate.source, 'rapira')
    
    async def test_session_lifecycle(self):
        """Test HTTP session initialization and cleanup"""
        # Session should start as None
        self.assertIsNone(self.api_service.session)
        
        # Start session
        await self.api_service.start_session()
        self.assertIsNotNone(self.api_service.session)
        self.assertIsInstance(self.api_service.session, aiohttp.ClientSession)
        
        # Close session
        await self.api_service.close_session()
        self.assertIsNone(self.api_service.session)
    
    async def test_context_manager(self):
        """Test async context manager functionality"""
        async with self.api_service as service:
            self.assertIsNotNone(service.session)
            self.assertIsInstance(service.session, aiohttp.ClientSession)
        
        # Session should be closed after context
        self.assertIsNone(self.api_service.session)
    
    @patch('src.config.config.DEBUG_MODE', True)
    async def test_get_mock_rate(self):
        """Test mock rate generation in debug mode"""
        # Test all supported pairs
        test_pairs = ['RUB/ZAR', 'USDT/THB', 'AED/RUB']
        
        for pair in test_pairs:
            rate = await self.api_service._get_mock_rate(pair)
            
            self.assertIsInstance(rate, ExchangeRate)
            self.assertEqual(rate.pair, pair)
            self.assertGreater(rate.rate, 0)
            self.assertEqual(rate.source, 'mock')
            self.assertIsNotNone(rate.timestamp)
    
    @patch('src.config.config.DEBUG_MODE', True)
    @patch('src.config.config.SUPPORTED_PAIRS', ['RUB/ZAR', 'USDT/THB'])
    async def test_get_exchange_rate_debug_mode(self):
        """Test exchange rate retrieval in debug mode"""
        # Valid pair
        rate = await self.api_service.get_exchange_rate('RUB/ZAR')
        self.assertIsNotNone(rate)
        self.assertEqual(rate.pair, 'RUB/ZAR')
        self.assertEqual(rate.source, 'mock')
        
        # Invalid pair
        rate = await self.api_service.get_exchange_rate('INVALID/PAIR')
        self.assertIsNone(rate)
    
    @patch('src.config.config.DEBUG_MODE', False)
    async def test_make_request_success(self):
        """Test successful API request"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'rate': 0.18, 'timestamp': '2024-12-01'})
        
        mock_session = AsyncMock()
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        self.api_service.session = mock_session
        
        success, data = await self.api_service._make_request('GET', '/test')
        
        self.assertTrue(success)
        self.assertIsNotNone(data)
        self.assertEqual(data['rate'], 0.18)
    
    @patch('src.config.config.DEBUG_MODE', False)
    async def test_make_request_failure(self):
        """Test failed API request"""
        # Mock failed response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value='Not Found')
        
        mock_session = AsyncMock()
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        self.api_service.session = mock_session
        
        success, data = await self.api_service._make_request('GET', '/test')
        
        self.assertFalse(success)
        self.assertIsNone(data)
    
    @patch('src.config.config.DEBUG_MODE', False)
    async def test_make_request_retry_logic(self):
        """Test API request retry logic"""
        # Mock retryable error (500) then success
        mock_response_fail = AsyncMock()
        mock_response_fail.status = 500
        
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.json = AsyncMock(return_value={'status': 'ok'})
        
        mock_session = AsyncMock()
        mock_session.request.return_value.__aenter__.side_effect = [
            mock_response_fail,
            mock_response_success
        ]
        
        self.api_service.session = mock_session
        
        # Patch sleep to speed up test
        with patch('asyncio.sleep', return_value=None):
            success, data = await self.api_service._make_request('GET', '/test', retry_count=1)
        
        self.assertTrue(success)
        self.assertEqual(data['status'], 'ok')
        # Should have made 2 requests (1 fail + 1 success)
        self.assertEqual(mock_session.request.call_count, 2)
    
    @patch('src.config.config.DEBUG_MODE', True)
    async def test_health_check_debug_mode(self):
        """Test health check in debug mode"""
        result = await self.api_service.health_check()
        self.assertTrue(result)
    
    @patch('src.config.config.DEBUG_MODE', False)
    async def test_health_check_api_mode(self):
        """Test health check with real API"""
        # Mock successful health check
        with patch.object(self.api_service, '_make_request') as mock_request:
            mock_request.return_value = (True, {'status': 'ok'})
            
            result = await self.api_service.health_check()
            self.assertTrue(result)
            
            # Verify the correct endpoint was called
            mock_request.assert_called_once_with('GET', '/health', retry_count=1)
        
        # Mock failed health check
        with patch.object(self.api_service, '_make_request') as mock_request:
            mock_request.return_value = (False, None)
            
            result = await self.api_service.health_check()
            self.assertFalse(result)


class AsyncTestCase(unittest.TestCase):
    """Base class for async test cases"""
    
    def run_async(self, coro):
        """Helper to run async tests"""
        return asyncio.run(coro)


class TestAPIServiceAsync(AsyncTestCase):
    """Async test cases for APIService"""
    
    def test_session_lifecycle_async(self):
        """Test session lifecycle asynchronously"""
        self.run_async(TestAPIService().test_session_lifecycle())
    
    def test_context_manager_async(self):
        """Test context manager asynchronously"""
        self.run_async(TestAPIService().test_context_manager())
    
    def test_get_mock_rate_async(self):
        """Test mock rate generation asynchronously"""
        self.run_async(TestAPIService().test_get_mock_rate())
    
    def test_get_exchange_rate_debug_mode_async(self):
        """Test exchange rate in debug mode asynchronously"""
        self.run_async(TestAPIService().test_get_exchange_rate_debug_mode())
    
    def test_make_request_success_async(self):
        """Test successful request asynchronously"""
        self.run_async(TestAPIService().test_make_request_success())
    
    def test_make_request_failure_async(self):
        """Test failed request asynchronously"""
        self.run_async(TestAPIService().test_make_request_failure())
    
    def test_make_request_retry_logic_async(self):
        """Test retry logic asynchronously"""
        self.run_async(TestAPIService().test_make_request_retry_logic())
    
    def test_health_check_debug_mode_async(self):
        """Test health check debug mode asynchronously"""
        self.run_async(TestAPIService().test_health_check_debug_mode())
    
    def test_health_check_api_mode_async(self):
        """Test health check API mode asynchronously"""
        self.run_async(TestAPIService().test_health_check_api_mode())


if __name__ == '__main__':
    unittest.main()