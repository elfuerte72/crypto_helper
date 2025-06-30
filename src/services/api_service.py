#!/usr/bin/env python3
"""
API Service for Crypto Helper Bot
Handles all external API communications, primarily with Rapira API
"""

import asyncio
import aiohttp
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

try:
    from ..config import config
    from ..utils.logger import get_api_logger
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config
    from utils.logger import get_api_logger

logger = get_api_logger()


@dataclass
class ExchangeRate:
    """Data class for exchange rate information"""
    pair: str
    rate: float
    timestamp: str
    source: str = "rapira"


class APIService:
    """Service for handling external API calls"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.RAPIRA_API_URL
        self.api_key = config.RAPIRA_API_KEY
        self.timeout = aiohttp.ClientTimeout(total=config.API_TIMEOUT)
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
    
    async def start_session(self):
        """Initialize HTTP session"""
        if not self.session:
            headers = {
                'User-Agent': 'CryptoHelper-Bot/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout
            )
            logger.info("API session initialized")
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("API session closed")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_count: int = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            retry_count: Number of retries
        
        Returns:
            Tuple of (success, response_data)
        """
        if not self.session:
            await self.start_session()
        
        retry_count = retry_count or config.API_RETRY_COUNT
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        for attempt in range(retry_count + 1):
            try:
                logger.debug(f"API request: {method} {url} (attempt {attempt + 1})")
                
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data
                ) as response:
                    
                    if response.status == 200:
                        response_data = await response.json()
                        logger.debug(f"API success: {response.status}")
                        return True, response_data
                    
                    elif response.status in [429, 500, 502, 503, 504]:
                        # Retryable errors
                        logger.warning(f"API error {response.status}, retrying...")
                        if attempt < retry_count:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                    
                    else:
                        # Non-retryable errors
                        error_text = await response.text()
                        logger.error(f"API error {response.status}: {error_text}")
                        return False, None
            
            except asyncio.TimeoutError:
                logger.warning(f"API timeout (attempt {attempt + 1})")
                if attempt < retry_count:
                    await asyncio.sleep(2 ** attempt)
                    continue
            
            except Exception as e:
                logger.error(f"API request error: {e}")
                if attempt < retry_count:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        logger.error(f"API request failed after {retry_count + 1} attempts")
        return False, None
    
    async def get_exchange_rate(self, pair: str) -> Optional[ExchangeRate]:
        """
        Get exchange rate for a currency pair
        
        Args:
            pair: Currency pair (e.g., 'RUB/ZAR')
        
        Returns:
            ExchangeRate object or None if failed
        """
        logger.info(f"Getting exchange rate for {pair}")
        
        # Validate pair
        if pair not in config.SUPPORTED_PAIRS:
            logger.error(f"Unsupported currency pair: {pair}")
            return None
        
        # For MVP - mock implementation since we don't have real Rapira API access
        if config.DEBUG_MODE:
            return await self._get_mock_rate(pair)
        
        # Real API call structure (to be implemented when API is available)
        success, data = await self._make_request(
            method='GET',
            endpoint=f'/rates/{pair.replace("/", "")}',
            params={'format': 'json'}
        )
        
        if success and data:
            try:
                return ExchangeRate(
                    pair=pair,
                    rate=float(data.get('rate', 0)),
                    timestamp=data.get('timestamp', ''),
                    source='rapira'
                )
            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing API response: {e}")
        
        return None
    
    async def _get_mock_rate(self, pair: str) -> ExchangeRate:
        """
        Generate mock exchange rate for development/testing
        
        Args:
            pair: Currency pair
        
        Returns:
            Mock ExchangeRate object
        """
        from datetime import datetime
        import random
        
        # Mock rates for different pairs
        mock_rates = {
            'RUB/ZAR': 0.18,
            'ZAR/RUB': 5.56,
            'RUB/THB': 0.35,
            'THB/RUB': 2.86,
            'RUB/AED': 0.037,
            'AED/RUB': 27.03,
            'RUB/IDR': 156.78,
            'IDR/RUB': 0.0064,
            'USDT/ZAR': 18.45,
            'ZAR/USDT': 0.054,
            'USDT/THB': 35.67,
            'THB/USDT': 0.028,
            'USDT/AED': 3.67,
            'AED/USDT': 0.27,
            'USDT/IDR': 15678.90,
            'IDR/USDT': 0.000064
        }
        
        base_rate = mock_rates.get(pair, 1.0)
        # Add small random variation (±2%)
        variation = random.uniform(-0.02, 0.02)
        final_rate = base_rate * (1 + variation)
        
        logger.debug(f"Generated mock rate for {pair}: {final_rate}")
        
        return ExchangeRate(
            pair=pair,
            rate=round(final_rate, 6),
            timestamp=datetime.now().isoformat(),
            source='mock'
        )
    
    async def health_check(self) -> bool:
        """
        Check API service health
        
        Returns:
            True if service is healthy, False otherwise
        """
        logger.info("Performing API health check")
        
        if config.DEBUG_MODE:
            # In debug mode, always return healthy
            logger.info("Health check: OK (debug mode)")
            return True
        
        success, data = await self._make_request(
            method='GET',
            endpoint='/health',
            retry_count=1
        )
        
        result = success and data and data.get('status') == 'ok'
        logger.info(f"Health check: {'OK' if result else 'FAILED'}")
        return result


# Global API service instance
api_service = APIService()