#!/usr/bin/env python3
"""
Fiat Rates Service for Crypto Helper Bot
Получает курсы фиатных валют из ExchangeRate-API
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
    from .api_service import ExchangeRate, RapiraAPIError
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config
    from utils.logger import get_api_logger
    from services.api_service import ExchangeRate, RapiraAPIError

logger = get_api_logger()


class FiatRatesService:
    """Сервис для получения курсов фиатных валют"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        # Используем бесплатный ExchangeRate-API
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
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
                'Accept': 'application/json'
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
            logger.info("Fiat rates session initialized")
    
    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Fiat rates session closed")
    
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
        Получает курсы всех валют относительно базовой
        
        Args:
            base_currency: Базовая валюта (например, 'USD')
        
        Returns:
            Словарь курсов {валюта: курс} или None
        """
        if not self.session:
            await self.start_session()
        
        await self._rate_limit()
        
        url = f"{self.base_url}/{base_currency}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'rates' in data and isinstance(data['rates'], dict):
                        logger.debug(f"Got {len(data['rates'])} rates from {base_currency}")
                        return data['rates']
                    else:
                        logger.error(f"Invalid response format from fiat API: {data}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"Fiat API error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting fiat rates from {base_currency}: {e}")
            return None
    
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
            source='exchangerate-api'
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


# Глобальный экземпляр сервиса
fiat_rates_service = FiatRatesService()