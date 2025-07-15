#!/usr/bin/env python3
"""
Fiat Rates Service for Crypto Helper Bot
Получает курсы фиатных валют из APILayer
"""

import asyncio
import aiohttp
import json
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import random

try:
    from ..config import config
    from ..utils.logger import get_api_logger
    from .models import ExchangeRate, APILayerError
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config
    from utils.logger import get_api_logger
    from services.models import ExchangeRate, APILayerError

logger = get_api_logger()


# Используем APILayerError из models.py


class FiatRatesService:
    """Сервис для получения курсов фиатных валют через APILayer"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.API_LAYER_URL
        self.api_key = config.API_LAYER_KEY
        self.timeout = aiohttp.ClientTimeout(total=30)
        self._rate_limit_delay = 1.0
        self._last_request_time = 0.0
        
        # Поддерживаемые фиатные валюты
        self.supported_currencies = {
            'USD', 'EUR', 'RUB', 'ZAR', 'THB', 'AED', 'IDR',
            'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
    
    async def start_session(self):
        """Инициализация HTTP сессии"""
        if not self.session:
            headers = {
                'User-Agent': 'CryptoHelper-Bot/1.0',
                'Accept': 'application/json',
                'apikey': self.api_key  # APILayer использует apikey в header
            }
            
            connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout,
                connector=connector,
                raise_for_status=False
            )
            logger.info("APILayer fiat rates session initialized")
    
    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("APILayer fiat rates session closed")
    
    async def _rate_limit(self):
        """Rate limiting"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._rate_limit_delay:
            sleep_time = self._rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def get_rates_from_base(self, base_currency: str) -> Optional[Dict[str, float]]:
        """
        Получает курсы всех валют относительно базовой через APILayer
        
        Args:
            base_currency: Базовая валюта (например, 'USD')
        
        Returns:
            Словарь курсов {валюта: курс} или None
        """
        if not self.session:
            await self.start_session()
        
        await self._rate_limit()
        
        # APILayer endpoint для получения курсов
        url = f"{self.base_url}/latest"
        params = {
            'base': base_currency,
            'symbols': ','.join(self.supported_currencies)
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # APILayer возвращает структуру:
                    # {
                    #   "success": true,
                    #   "timestamp": 1234567890,
                    #   "base": "USD",
                    #   "date": "2024-01-01",
                    #   "rates": {
                    #     "EUR": 0.85,
                    #     "RUB": 75.5
                    #   }
                    # }
                    
                    if data.get('success') and 'rates' in data:
                        rates = data['rates']
                        logger.debug(f"Got {len(rates)} rates from {base_currency} via APILayer")
                        return rates
                    else:
                        error_msg = data.get('error', {}).get('info', 'Unknown error')
                        logger.error(f"APILayer API error: {error_msg}")
                        raise APILayerError(f"APILayer error: {error_msg}")
                
                elif response.status == 401:
                    logger.error("APILayer authentication failed - check API key")
                    raise APILayerError("Invalid API key", response.status)
                
                elif response.status == 429:
                    logger.warning("APILayer rate limit exceeded")
                    raise APILayerError("Rate limit exceeded", response.status)
                
                else:
                    error_text = await response.text()
                    logger.error(f"APILayer API error {response.status}: {error_text}")
                    raise APILayerError(f"API error {response.status}: {error_text}", response.status)
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error getting fiat rates from {base_currency}: {e}")
            raise APILayerError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting fiat rates from {base_currency}: {e}")
            raise APILayerError(f"Unexpected error: {str(e)}")
    
    async def get_fiat_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Получает курс между двумя фиатными валютами
        
        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта
        
        Returns:
            Курс или None
        """
        logger.info(f"Getting fiat rate for {from_currency}/{to_currency}")
        
        # Проверяем поддержку валют
        if from_currency not in self.supported_currencies or to_currency not in self.supported_currencies:
            logger.warning(f"Unsupported currency pair: {from_currency}/{to_currency}")
            return None
        
        # Если валюты одинаковые
        if from_currency == to_currency:
            return 1.0
        
        try:
            # Получаем курсы относительно исходной валюты
            rates = await self.get_rates_from_base(from_currency)
            
            if rates and to_currency in rates:
                rate = rates[to_currency]
                logger.debug(f"Direct fiat rate {from_currency}/{to_currency}: {rate}")
                return rate
            
            # Если прямого курса нет, пытаемся через USD
            if from_currency != 'USD' and to_currency != 'USD':
                usd_rates = await self.get_rates_from_base('USD')
                
                if usd_rates and from_currency in usd_rates and to_currency in usd_rates:
                    # USD/from -> from/USD (инвертируем)
                    from_usd_rate = 1.0 / usd_rates[from_currency]
                    # USD/to -> прямой курс
                    to_usd_rate = usd_rates[to_currency]
                    
                    # from -> USD -> to
                    cross_rate = from_usd_rate * to_usd_rate
                    
                    logger.debug(f"Cross fiat rate {from_currency}/{to_currency} via USD: {cross_rate}")
                    return cross_rate
            
            logger.warning(f"Could not calculate fiat rate for {from_currency}/{to_currency}")
            return None
            
        except APILayerError as e:
            logger.error(f"APILayer error getting rate {from_currency}/{to_currency}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting rate {from_currency}/{to_currency}: {e}")
            return None
    
    async def create_fiat_exchange_rate(
        self, 
        from_currency: str, 
        to_currency: str, 
        rate: float
    ) -> ExchangeRate:
        """
        Создает объект ExchangeRate для фиатной пары
        
        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта
            rate: Курс
        
        Returns:
            ExchangeRate объект
        """
        pair = f"{from_currency}/{to_currency}"
        
        return ExchangeRate(
            pair=pair,
            rate=round(rate, 6),
            timestamp=datetime.now().isoformat(),
            source='apilayer'
        )
    
    async def get_fiat_exchange_rate(self, pair: str) -> Optional[ExchangeRate]:
        """
        Получает ExchangeRate для фиатной пары
        
        Args:
            pair: Валютная пара (например, 'USD/ZAR')
        
        Returns:
            ExchangeRate объект или None
        """
        try:
            from_currency, to_currency = pair.split('/')
            
            rate = await self.get_fiat_rate(from_currency, to_currency)
            
            if rate is not None:
                return await self.create_fiat_exchange_rate(from_currency, to_currency, rate)
            
            return None
            
        except ValueError:
            logger.error(f"Invalid fiat pair format: {pair}")
            return None
        except Exception as e:
            logger.error(f"Error getting fiat exchange rate for {pair}: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья APILayer API
        
        Returns:
            Словарь с результатами проверки
        """
        logger.info("Performing APILayer health check")
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'service': 'apilayer_fiat_rates',
            'status': 'unknown',
            'response_time_ms': None,
            'api_url': self.base_url,
            'has_api_key': bool(self.api_key),
            'session_active': self.session is not None and not self.session.closed
        }
        
        # Выполняем тестовый запрос к APILayer
        start_time = asyncio.get_event_loop().time()
        try:
            # Простой запрос для проверки
            rate = await self.get_fiat_rate('USD', 'EUR')
            
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000
            
            health_data['response_time_ms'] = round(response_time, 2)
            
            if rate is not None:
                health_data.update({
                    'status': 'healthy',
                    'message': f'APILayer responding normally (USD/EUR: {rate:.6f})',
                    'sample_rate': rate
                })
            else:
                health_data.update({
                    'status': 'degraded',
                    'message': 'APILayer returned no rate data'
                })
                
        except APILayerError as e:
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000
            health_data.update({
                'response_time_ms': round(response_time, 2),
                'status': 'unhealthy',
                'message': f'APILayer error: {str(e)}',
                'error': str(e)
            })
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000
            health_data.update({
                'response_time_ms': round(response_time, 2),
                'status': 'unhealthy',
                'message': f'Health check failed: {str(e)}',
                'error': str(e)
            })
        
        logger.info(f"APILayer health check completed: {health_data['status']} ({health_data.get('response_time_ms', 'N/A')}ms)")
        return health_data


# Глобальный экземпляр сервиса
fiat_rates_service = FiatRatesService()