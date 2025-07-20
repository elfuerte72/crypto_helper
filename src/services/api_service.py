#!/usr/bin/env python3
"""
API Service for Crypto Helper Bot
Handles all external API communications, primarily with Rapira API

Features:
- Async HTTP client with connection pooling
- Exponential backoff retry logic
- Comprehensive error handling
- Mock data support for development
- Rate limiting and timeout handling
"""

import asyncio
import aiohttp
import json
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import random

try:
    from ..config import config
    from ..utils.logger import get_api_logger
    from .models import ExchangeRate, RapiraAPIError, APILayerError
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config
    from utils.logger import get_api_logger
    from services.models import ExchangeRate, RapiraAPIError, APILayerError

logger = get_api_logger()


# Импортируем модели из отдельного файла


class APIService:
    """Service for handling external API calls to Rapira API and APILayer"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.RAPIRA_API_URL
        self.api_key = config.RAPIRA_API_KEY
        self.timeout = aiohttp.ClientTimeout(total=config.API_TIMEOUT)
        self._rate_limit_delay = 1.0  # Minimum delay between requests
        self._last_request_time = 0.0
        
        # Определяем фиатные валюты
        self.fiat_currencies = {'USD', 'EUR', 'RUB', 'ZAR', 'THB', 'AED', 'IDR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY'}
        self.crypto_currencies = {'BTC', 'ETH', 'TON', 'USDT', 'USDC', 'LTC', 'TRX', 'BNB', 'DAI', 'DOGE', 'ETC', 'OP', 'XMR', 'SOL', 'NOT'}
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
    
    async def start_session(self):
        """Initialize HTTP session with connection pooling and SSL settings"""
        if not self.session:
            headers = {
                'User-Agent': 'CryptoHelper-Bot/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # Connection pooling settings
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout,
                connector=connector,
                raise_for_status=False  # Handle status codes manually
            )
            logger.info("API session initialized with connection pooling")
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("API session closed")
    
    async def _rate_limit(self):
        """Implement rate limiting to avoid overwhelming the API"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._rate_limit_delay:
            sleep_time = self._rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_count: int = None,
        timeout: Optional[float] = None
    ) -> Tuple[bool, Optional[Dict], Optional[int]]:
        """
        Make HTTP request with retry logic and comprehensive error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            retry_count: Number of retries
            timeout: Request timeout override
        
        Returns:
            Tuple of (success, response_data, status_code)
        """
        if not self.session:
            await self.start_session()
        
        await self._rate_limit()
        
        retry_count = retry_count or config.API_RETRY_COUNT
        
        # Если endpoint пустой, используем base_url напрямую
        if not endpoint or endpoint == '':
            url = self.base_url
        else:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Custom timeout for this request
        request_timeout = aiohttp.ClientTimeout(total=timeout) if timeout else self.timeout
        
        last_exception = None
        
        for attempt in range(retry_count + 1):
            try:
                logger.debug(f"API request: {method} {url} (attempt {attempt + 1}/{retry_count + 1})")
                
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=request_timeout
                ) as response:
                    
                    status_code = response.status
                    
                    # Success
                    if 200 <= status_code < 300:
                        try:
                            response_data = await response.json()
                            logger.debug(f"API success: {status_code}")
                            return True, response_data, status_code
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON response: {e}")
                            if attempt < retry_count:
                                await self._exponential_backoff(attempt)
                                continue
                            return False, None, status_code
                    
                    # Rate limiting
                    elif status_code == 429:
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            try:
                                sleep_time = float(retry_after)
                                logger.warning(f"Rate limited, sleeping for {sleep_time}s")
                                await asyncio.sleep(sleep_time)
                            except ValueError:
                                await self._exponential_backoff(attempt)
                        else:
                            await self._exponential_backoff(attempt)
                        
                        if attempt < retry_count:
                            continue
                    
                    # Server errors (retryable)
                    elif status_code in [500, 502, 503, 504]:
                        error_text = await response.text()
                        logger.warning(f"Server error {status_code}: {error_text}")
                        if attempt < retry_count:
                            await self._exponential_backoff(attempt)
                            continue
                    
                    # Client errors (non-retryable)
                    elif 400 <= status_code < 500:
                        error_text = await response.text()
                        logger.error(f"Client error {status_code}: {error_text}")
                        try:
                            error_data = await response.json()
                        except:
                            error_data = {"error": error_text}
                        return False, error_data, status_code
                    
                    # Other errors
                    else:
                        error_text = await response.text()
                        logger.error(f"Unexpected status {status_code}: {error_text}")
                        if attempt < retry_count:
                            await self._exponential_backoff(attempt)
                            continue
                        return False, None, status_code
            
            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{retry_count + 1})")
                if attempt < retry_count:
                    await self._exponential_backoff(attempt)
                    continue
            
            except aiohttp.ClientError as e:
                last_exception = e
                logger.warning(f"Client error: {e} (attempt {attempt + 1}/{retry_count + 1})")
                if attempt < retry_count:
                    await self._exponential_backoff(attempt)
                    continue
            
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error: {e} (attempt {attempt + 1}/{retry_count + 1})")
                if attempt < retry_count:
                    await self._exponential_backoff(attempt)
                    continue
        
        logger.error(f"API request failed after {retry_count + 1} attempts. Last error: {last_exception}")
        return False, None, None
    
    async def _exponential_backoff(self, attempt: int, max_delay: float = 60.0):
        """Implement exponential backoff with jitter"""
        base_delay = min(2 ** attempt, max_delay)
        jitter = random.uniform(0.1, 0.5) * base_delay
        sleep_time = base_delay + jitter
        
        logger.debug(f"Exponential backoff: sleeping for {sleep_time:.2f}s")
        await asyncio.sleep(sleep_time)
    
    async def get_all_rates(self) -> Optional[Dict[str, ExchangeRate]]:
        """
        Get all available exchange rates from Rapira API
        
        Returns:
            Dictionary mapping symbols to ExchangeRate objects or None if failed
        """
        logger.info("Getting all exchange rates from Rapira API")
        
        # Проверяем нужно ли использовать mock-данные
        if config.USE_MOCK_DATA:
            logger.info("Using mock data for development")
            return await self._get_mock_all_rates()
        
        # Real API call to Rapira - получаем все курсы одним запросом
        try:
            success, data, status_code = await self._make_request(
                method='GET',
                endpoint='',  # Используем базовый URL напрямую
                params=None
            )
            
            if success and data:
                return self._parse_all_rates_response(data)
            
            elif status_code == 404:
                logger.error("Rapira API endpoint not found")
                raise RapiraAPIError("API endpoint not found", status_code)
            
            elif status_code and 400 <= status_code < 500:
                error_msg = data.get('message', 'Client error') if data else 'Client error'
                logger.error(f"Client error: {error_msg}")
                raise RapiraAPIError(f"Client error: {error_msg}", status_code, data)
            
            else:
                logger.error("Failed to get exchange rates")
                raise RapiraAPIError("Failed to get exchange rates")
                
        except RapiraAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting rates: {e}")
            raise RapiraAPIError(f"Unexpected error: {str(e)}")
    
    async def get_exchange_rate(self, pair: str) -> Optional[ExchangeRate]:
        """
        Get exchange rate for a specific currency pair
        Uses Rapira API for crypto pairs and APILayer for fiat pairs
        
        Args:
            pair: Currency pair (e.g., 'RUB/ZAR', 'BTC/USDT')
        
        Returns:
            ExchangeRate object or None if failed
        """
        logger.info(f"Getting exchange rate for {pair}")
        
        try:
            # Определяем тип пары (крипто/фиат)
            base_currency, quote_currency = pair.split('/')
            
            # Если обе валюты фиатные - используем APILayer
            if (base_currency in self.fiat_currencies and 
                quote_currency in self.fiat_currencies):
                logger.info(f"Using APILayer for fiat pair {pair}")
                return await self._get_fiat_exchange_rate(pair)
            
            # Если есть криптовалюта - используем Rapira API
            elif (base_currency in self.crypto_currencies or 
                  quote_currency in self.crypto_currencies):
                logger.info(f"Using Rapira API for crypto pair {pair}")
                return await self._get_crypto_exchange_rate(pair)
            
            else:
                logger.error(f"Unknown currency types in pair: {pair}")
                raise RapiraAPIError(f"Unknown currency types in pair: {pair}")
                
        except ValueError:
            logger.error(f"Invalid pair format: {pair}")
            raise RapiraAPIError(f"Invalid pair format: {pair}")
        except Exception as e:
            logger.error(f"Unexpected error getting rate for {pair}: {e}")
            raise RapiraAPIError(f"Unexpected error: {str(e)}")
    
    async def _get_fiat_exchange_rate(self, pair: str) -> Optional[ExchangeRate]:
        """
        Get fiat exchange rate using APILayer
        
        Args:
            pair: Fiat currency pair (e.g., 'USD/ZAR')
        
        Returns:
            ExchangeRate object or None if failed
        """
        try:
            logger.debug(f"Getting fiat rate for {pair} via APILayer")
            
            # Ленивый импорт для избежания циклических импортов
            from .fiat_rates_service import fiat_rates_service
            
            # Используем fiat_rates_service для получения курса
            fiat_rate = await fiat_rates_service.get_fiat_exchange_rate(pair)
            
            if fiat_rate:
                logger.debug(f"Got fiat rate for {pair}: {fiat_rate.rate} (source: {fiat_rate.source})")
                return fiat_rate
            else:
                logger.warning(f"No fiat rate found for {pair} even with fallback")
                raise RapiraAPIError(f"Fiat rate for {pair} not found")
                
        except APILayerError as e:
            logger.error(f"APILayer error for {pair}: {e}")
            # Не пробрасываем ошибку, так как fallback уже обработан
            raise RapiraAPIError(f"APILayer error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting fiat rate for {pair}: {e}")
            raise RapiraAPIError(f"Unexpected error: {str(e)}")
    
    async def _get_crypto_exchange_rate(self, pair: str) -> Optional[ExchangeRate]:
        """
        Get crypto exchange rate using Rapira API
        
        Args:
            pair: Crypto currency pair (e.g., 'BTC/USDT')
        
        Returns:
            ExchangeRate object or None if failed
        """
        try:
            logger.debug(f"Getting crypto rate for {pair} via Rapira API")
            
            # Получаем все курсы из Rapira API и ищем нужный
            all_rates = await self.get_all_rates()
            if not all_rates:
                raise RapiraAPIError("Failed to get exchange rates from Rapira")
            
            # Ищем курс для запрашиваемой пары
            rate = self._find_rate_for_pair(pair, all_rates)
            if rate:
                logger.debug(f"Found direct crypto rate for {pair}: {rate.rate}")
                return rate
            
            # Если прямого курса нет, пытаемся вычислить через базовые валюты
            calculated_rate = await self._calculate_cross_rate(pair, all_rates)
            if calculated_rate:
                logger.debug(f"Calculated crypto rate for {pair}: {calculated_rate.rate}")
                return calculated_rate
            
            logger.error(f"Crypto exchange rate for {pair} not found")
            raise RapiraAPIError(f"Crypto exchange rate for {pair} not found")
                
        except RapiraAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting crypto rate for {pair}: {e}")
            raise RapiraAPIError(f"Unexpected error: {str(e)}")
    
    def _parse_all_rates_response(self, data: Dict) -> Dict[str, ExchangeRate]:
        """
        Parse Rapira API response with all rates into dictionary of ExchangeRate objects
        
        Args:
            data: API response data from Rapira
        
        Returns:
            Dictionary mapping symbols to ExchangeRate objects
        """
        try:
            rates = {}
            
            # Проверяем структуру ответа Rapira API
            if 'data' not in data or not isinstance(data['data'], list):
                raise ValueError("Invalid Rapira API response format")
            
            for item in data['data']:
                if not isinstance(item, dict) or 'symbol' not in item:
                    continue
                
                symbol = item['symbol']
                
                # Парсим данные курса
                try:
                    # Определяем основной курс (используем close, если нет - askPrice)
                    main_rate = item.get('close')
                    if main_rate is None or main_rate == 0:
                        main_rate = item.get('askPrice')
                    if main_rate is None or main_rate == 0:
                        main_rate = item.get('bidPrice')
                    
                    if main_rate is None or main_rate == 0:
                        logger.warning(f"No valid rate found for {symbol}")
                        continue
                    
                    rate_data = {
                        'rate': float(main_rate),
                        'timestamp': datetime.now().isoformat(),  # Rapira не предоставляет timestamp
                        'bid': float(item['bidPrice']) if 'bidPrice' in item and item['bidPrice'] is not None else None,
                        'ask': float(item['askPrice']) if 'askPrice' in item and item['askPrice'] is not None else None,
                        'high_24h': float(item['high']) if 'high' in item and item['high'] is not None else None,
                        'low_24h': float(item['low']) if 'low' in item and item['low'] is not None else None,
                        'change_24h': float(item['chg']) * 100 if 'chg' in item and item['chg'] is not None else None,  # Конвертируем в проценты
                    }
                    
                    # Создаем объект ExchangeRate
                    exchange_rate = ExchangeRate(
                        pair=symbol,  # Оставляем символ как есть
                        source='rapira',
                        **rate_data
                    )
                    
                    if exchange_rate.is_valid():
                        rates[symbol] = exchange_rate
                        logger.debug(f"Parsed rate for {symbol}: {exchange_rate.rate}")
                    else:
                        logger.warning(f"Invalid rate data for {symbol}: rate={exchange_rate.rate}, pair={exchange_rate.pair}")
                        
                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(f"Error parsing rate for {symbol}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(rates)} exchange rates")
            return rates
            
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Error parsing Rapira API response: {e}")
            logger.debug(f"Response data: {data}")
            raise RapiraAPIError(f"Invalid API response format: {str(e)}")
    
    def _find_rate_for_pair(self, pair: str, all_rates: Dict[str, ExchangeRate]) -> Optional[ExchangeRate]:
        """
        Find exchange rate for a specific pair from all rates
        
        Args:
            pair: Currency pair (e.g., 'RUB/ZAR')
            all_rates: Dictionary of all available rates
        
        Returns:
            ExchangeRate object or None if not found
        """
        # Проверяем разные форматы символов
        possible_symbols = [
            pair,  # RUB/ZAR
            pair.replace('/', ''),  # RUBZAR
            pair.replace('/', '_'),  # RUB_ZAR
            pair.replace('/', '-'),  # RUB-ZAR
        ]
        
        for symbol in possible_symbols:
            if symbol in all_rates:
                rate = all_rates[symbol]
                # Обновляем pair в правильном формате
                rate.pair = pair
                return rate
        
        return None
    
    async def _calculate_cross_rate(self, pair: str, all_rates: Dict[str, ExchangeRate]) -> Optional[ExchangeRate]:
        """
        Calculate cross rate for currency pair using crypto base currencies (USDT, BTC, ETH, TON)
        Specifically designed for RUB/crypto and crypto/RUB pairs
        
        Args:
            pair: Currency pair (e.g., 'RUB/BTC', 'BTC/RUB')
            all_rates: Dictionary of all available rates
        
        Returns:
            Calculated ExchangeRate object or None if cannot calculate
        """
        try:
            base_currency, quote_currency = pair.split('/')
            
            # Специальная логика для криптовалютных пар с рублем
            if (base_currency == 'RUB' and quote_currency in ['BTC', 'ETH', 'TON', 'USDT']) or \
               (quote_currency == 'RUB' and base_currency in ['BTC', 'ETH', 'TON', 'USDT']):
                
                # Для пар RUB/CRYPTO
                if base_currency == 'RUB':
                    # Специальный случай для RUB/USDT
                    if quote_currency == 'USDT':
                        usdt_rub_rate = self._find_direct_rate('USDT/RUB', all_rates)
                        if usdt_rub_rate:
                            # ВАЖНО: Для RUB/USDT возвращаем прямой курс USDT/RUB
                            # Это нужно для правильного применения наценки
                            # В calculation_logic.py логика обработает инверсию правильно
                            
                            logger.debug(f"Found {pair} base rate (USDT/RUB): {usdt_rub_rate:.2f}")
                            
                            return ExchangeRate(
                                pair=pair,
                                rate=round(usdt_rub_rate, 8),  # Возвращаем курс USDT/RUB как есть
                                timestamp=datetime.now().isoformat(),
                                source='rapira_usdt_rub_direct'
                            )
                    else:
                        # Ищем USDT/RUB и CRYPTO/USDT
                        usdt_rub_rate = self._find_direct_rate('USDT/RUB', all_rates)
                        crypto_usdt_rate = self._find_direct_rate(f'{quote_currency}/USDT', all_rates)
                        
                        if usdt_rub_rate and crypto_usdt_rate:
                            # RUB/CRYPTO = (1/USDT/RUB) / CRYPTO/USDT = RUB/USDT / CRYPTO/USDT
                            rub_usdt_rate = 1.0 / usdt_rub_rate
                            cross_rate = rub_usdt_rate / crypto_usdt_rate
                            
                            logger.debug(f"Calculated {pair} rate: {rub_usdt_rate:.6f} / {crypto_usdt_rate:.6f} = {cross_rate:.8f}")
                            
                            return ExchangeRate(
                                pair=pair,
                                rate=round(cross_rate, 8),
                                timestamp=datetime.now().isoformat(),
                                source='calculated_via_usdt_rub'
                            )
                
                # Для пар CRYPTO/RUB
                elif quote_currency == 'RUB':
                    # Ищем CRYPTO/USDT и USDT/RUB
                    crypto_usdt_rate = self._find_direct_rate(f'{base_currency}/USDT', all_rates)
                    usdt_rub_rate = self._find_direct_rate('USDT/RUB', all_rates)
                    
                    if crypto_usdt_rate and usdt_rub_rate:
                        # CRYPTO/RUB = CRYPTO/USDT * USDT/RUB
                        cross_rate = crypto_usdt_rate * usdt_rub_rate
                        
                        logger.debug(f"Calculated {pair} rate: {crypto_usdt_rate:.6f} * {usdt_rub_rate:.2f} = {cross_rate:.2f}")
                        
                        return ExchangeRate(
                            pair=pair,
                            rate=round(cross_rate, 8),
                            timestamp=datetime.now().isoformat(),
                            source='calculated_via_usdt_rub'
                        )
            
            # Попытка вычислить через USD (оригинальная логика)
            usd_base_rate = self._find_usd_rate(base_currency, all_rates)
            usd_quote_rate = self._find_usd_rate(quote_currency, all_rates)
            
            if usd_base_rate and usd_quote_rate:
                # Вычисляем кросс-курс через USD
                cross_rate = usd_base_rate / usd_quote_rate
                
                logger.debug(f"Calculated {pair} rate via USD: {cross_rate}")
                
                return ExchangeRate(
                    pair=pair,
                    rate=round(cross_rate, 8),
                    timestamp=datetime.now().isoformat(),
                    source='calculated_via_usd'
                )
            
            # Попытка вычислить через USDT (оригинальная логика)
            usdt_base_rate = self._find_usdt_rate(base_currency, all_rates)
            usdt_quote_rate = self._find_usdt_rate(quote_currency, all_rates)
            
            if usdt_base_rate and usdt_quote_rate:
                # Вычисляем кросс-курс через USDT
                cross_rate = usdt_base_rate / usdt_quote_rate
                
                logger.debug(f"Calculated {pair} rate via USDT: {cross_rate}")
                
                return ExchangeRate(
                    pair=pair,
                    rate=round(cross_rate, 8),
                    timestamp=datetime.now().isoformat(),
                    source='calculated_via_usdt'
                )
            
            logger.warning(f"Cannot calculate cross rate for {pair}")
            return None
            
        except Exception as e:
            logger.error(f"Error calculating cross rate for {pair}: {e}")
            return None
    
    def _find_usd_rate(self, currency: str, all_rates: Dict[str, ExchangeRate]) -> Optional[float]:
        """Find USD rate for a currency"""
        # Ищем прямой курс к USD
        usd_symbols = [f"{currency}/USD", f"{currency}USD", f"USD/{currency}", f"USD{currency}"]
        
        for symbol in usd_symbols:
            if symbol in all_rates:
                rate = all_rates[symbol].rate
                # Если это обратный курс (USD/XXX), инвертируем
                if symbol.startswith('USD'):
                    return 1.0 / rate if rate != 0 else None
                return rate
        
        return None
    
    def _find_usdt_rate(self, currency: str, all_rates: Dict[str, ExchangeRate]) -> Optional[float]:
        """Find USDT rate for a currency"""
        # Ищем прямой курс к USDT
        usdt_symbols = [f"{currency}/USDT", f"{currency}USDT", f"USDT/{currency}", f"USDT{currency}"]
        
        for symbol in usdt_symbols:
            if symbol in all_rates:
                rate = all_rates[symbol].rate
                # Если это обратный курс (USDT/XXX), инвертируем
                if symbol.startswith('USDT'):
                    return 1.0 / rate if rate != 0 else None
                return rate
        
        return None
    
    def _find_direct_rate(self, pair: str, all_rates: Dict[str, ExchangeRate]) -> Optional[float]:
        """Find direct rate for a specific pair format"""
        # Ищем точное совпадение пары
        possible_symbols = [
            pair,  # USDT/RUB
            pair.replace('/', ''),  # USDTRUB
            pair.replace('/', '_'),  # USDT_RUB
            pair.replace('/', '-'),  # USDT-RUB
        ]
        
        for symbol in possible_symbols:
            if symbol in all_rates:
                return all_rates[symbol].rate
        
        return None
    
    def _parse_rate_response(self, pair: str, data: Dict) -> ExchangeRate:
        """
        Parse API response into ExchangeRate object (legacy method for single rate)
        
        Args:
            pair: Currency pair
            data: API response data
        
        Returns:
            ExchangeRate object
        """
        try:
            # Handle different possible response formats
            if 'rate' in data:
                # Simple format
                rate_data = {
                    'rate': float(data['rate']),
                    'timestamp': data.get('timestamp', datetime.now().isoformat()),
                    'bid': float(data['bid']) if 'bid' in data else None,
                    'ask': float(data['ask']) if 'ask' in data else None,
                }
            elif 'data' in data and isinstance(data['data'], dict):
                # Nested format
                inner_data = data['data']
                rate_data = {
                    'rate': float(inner_data['rate']),
                    'timestamp': inner_data.get('timestamp', datetime.now().isoformat()),
                    'bid': float(inner_data['bid']) if 'bid' in inner_data else None,
                    'ask': float(inner_data['ask']) if 'ask' in inner_data else None,
                }
            else:
                raise ValueError("Invalid response format")
            
            # Add optional 24h statistics if available
            stats_fields = ['high_24h', 'low_24h', 'volume_24h', 'change_24h']
            for field in stats_fields:
                if field in data:
                    try:
                        rate_data[field] = float(data[field])
                    except (ValueError, TypeError):
                        pass
            
            exchange_rate = ExchangeRate(
                pair=pair,
                source='rapira',
                **rate_data
            )
            
            if not exchange_rate.is_valid():
                raise ValueError("Invalid exchange rate data")
            
            logger.debug(f"Parsed exchange rate for {pair}: {exchange_rate.rate}")
            return exchange_rate
            
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Error parsing API response for {pair}: {e}")
            logger.debug(f"Response data: {data}")
            raise RapiraAPIError(f"Invalid API response format: {str(e)}")
    
    async def _get_mock_all_rates(self) -> Dict[str, ExchangeRate]:
        """
        Generate realistic mock exchange rates for all supported pairs
        
        Returns:
            Dictionary mapping symbols to mock ExchangeRate objects
        """
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.2, 0.8))
        
        # Mock rates with realistic bid/ask spreads
        mock_data = {
            'USDT/RUB': {'rate': 79.3, 'spread': 0.5},
            'BTC/USDT': {'rate': 107375, 'spread': 500},
            'ETH/USDT': {'rate': 2491.7, 'spread': 10},
            'NOT/USDT': {'rate': 0.001844, 'spread': 0.00002},
            'ETH/BTC': {'rate': 0.0232, 'spread': 0.0001},
            'USDC/USDT': {'rate': 0.9994, 'spread': 0.001},
            'LTC/USDT': {'rate': 86.05, 'spread': 0.5},
            'TRX/USDT': {'rate': 0.2788, 'spread': 0.002},
            'BNB/USDT': {'rate': 657.23, 'spread': 2},
            'DAI/USDT': {'rate': 0.9999, 'spread': 0.0005},
            'TON/USDT': {'rate': 2.9381, 'spread': 0.01},
            'DOGE/USDT': {'rate': 0.1645, 'spread': 0.001},
            'ETC/USDT': {'rate': 16.547, 'spread': 0.1},
            'OP/USDT': {'rate': 0.5702, 'spread': 0.005},
            'XMR/USDT': {'rate': 313.55, 'spread': 3},
            'SOL/USDT': {'rate': 155.88, 'spread': 1},
            # Добавляем кросс-курсы для поддерживаемых пар
            'RUB/ZAR': {'rate': 0.18, 'spread': 0.002},
            'ZAR/RUB': {'rate': 5.56, 'spread': 0.05},
            'RUB/THB': {'rate': 0.35, 'spread': 0.003},
            'THB/RUB': {'rate': 2.86, 'spread': 0.03},
            'RUB/AED': {'rate': 0.037, 'spread': 0.0003},
            'AED/RUB': {'rate': 27.03, 'spread': 0.25},
            'RUB/IDR': {'rate': 156.78, 'spread': 1.5},
            'IDR/RUB': {'rate': 0.0064, 'spread': 0.00006},
            'USDT/ZAR': {'rate': 18.45, 'spread': 0.15},
            'ZAR/USDT': {'rate': 0.054, 'spread': 0.0005},
            'USDT/THB': {'rate': 35.67, 'spread': 0.30},
            'THB/USDT': {'rate': 0.028, 'spread': 0.0003},
            'USDT/AED': {'rate': 3.67, 'spread': 0.03},
            'AED/USDT': {'rate': 0.27, 'spread': 0.003},
            'USDT/IDR': {'rate': 15678.90, 'spread': 150},
            'IDR/USDT': {'rate': 0.000064, 'spread': 0.000001}
        }
        
        rates = {}
        
        for symbol, base_data in mock_data.items():
            base_rate = base_data['rate']
            spread = base_data['spread']
            
            # Add market volatility (±3%)
            market_variation = random.uniform(-0.03, 0.03)
            current_rate = base_rate * (1 + market_variation)
            
            # Calculate bid/ask with spread
            half_spread = spread / 2
            bid = current_rate - half_spread
            ask = current_rate + half_spread
            
            # Generate 24h statistics
            high_24h = current_rate * random.uniform(1.01, 1.05)
            low_24h = current_rate * random.uniform(0.95, 0.99)
            volume_24h = random.uniform(10000, 100000)
            change_24h = random.uniform(-5.0, 5.0)
            
            exchange_rate = ExchangeRate(
                pair=symbol,
                rate=round(current_rate, 8),
                bid=round(bid, 8),
                ask=round(ask, 8),
                high_24h=round(high_24h, 8),
                low_24h=round(low_24h, 8),
                volume_24h=round(volume_24h, 2),
                change_24h=round(change_24h, 2),
                timestamp=datetime.now().isoformat(),
                source='mock'
            )
            
            rates[symbol] = exchange_rate
            logger.debug(f"Generated mock rate for {symbol}: {current_rate:.6f}")
        
        logger.info(f"Generated {len(rates)} mock exchange rates")
        return rates
    
    async def _get_mock_rate(self, pair: str) -> ExchangeRate:
        """
        Generate realistic mock exchange rate for development/testing (legacy method)
        
        Args:
            pair: Currency pair
        
        Returns:
            Mock ExchangeRate object with realistic data
        """
        # Получаем все mock курсы и возвращаем нужный
        all_rates = await self._get_mock_all_rates()
        
        # Ищем курс для запрашиваемой пары
        rate = self._find_rate_for_pair(pair, all_rates)
        if rate:
            return rate
        
        # Если не нашли, генерируем базовый mock
        logger.debug(f"Generating fallback mock rate for {pair}")
        
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        base_rate = 1.0
        spread = 0.01
        
        # Add market volatility (±3%)
        market_variation = random.uniform(-0.03, 0.03)
        current_rate = base_rate * (1 + market_variation)
        
        # Calculate bid/ask with spread
        half_spread = spread / 2
        bid = current_rate - half_spread
        ask = current_rate + half_spread
        
        # Generate 24h statistics
        high_24h = current_rate * random.uniform(1.01, 1.05)
        low_24h = current_rate * random.uniform(0.95, 0.99)
        volume_24h = random.uniform(10000, 100000)
        change_24h = random.uniform(-5.0, 5.0)
        
        logger.debug(f"Generated fallback mock rate for {pair}: {current_rate:.6f}")
        
        return ExchangeRate(
            pair=pair,
            rate=round(current_rate, 8),
            bid=round(bid, 8),
            ask=round(ask, 8),
            high_24h=round(high_24h, 8),
            low_24h=round(low_24h, 8),
            volume_24h=round(volume_24h, 2),
            change_24h=round(change_24h, 2),
            timestamp=datetime.now().isoformat(),
            source='mock_fallback'
        )
    
    async def get_multiple_rates(self, pairs: list[str]) -> Dict[str, Optional[ExchangeRate]]:
        """
        Get exchange rates for multiple currency pairs concurrently
        
        Args:
            pairs: List of currency pairs
        
        Returns:
            Dictionary mapping pairs to ExchangeRate objects or None
        """
        logger.info(f"Getting exchange rates for {len(pairs)} pairs")
        
        # Create tasks for concurrent requests
        tasks = []
        for pair in pairs:
            task = asyncio.create_task(self._get_single_rate_safe(pair))
            tasks.append((pair, task))
        
        # Wait for all tasks to complete
        results = {}
        for pair, task in tasks:
            try:
                results[pair] = await task
            except Exception as e:
                logger.error(f"Error getting rate for {pair}: {e}")
                results[pair] = None
        
        successful_count = sum(1 for rate in results.values() if rate is not None)
        logger.info(f"Successfully retrieved {successful_count}/{len(pairs)} exchange rates")
        
        return results
    
    async def _get_single_rate_safe(self, pair: str) -> Optional[ExchangeRate]:
        """Safely get a single exchange rate without raising exceptions"""
        try:
            return await self.get_exchange_rate(pair)
        except Exception as e:
            logger.error(f"Error getting rate for {pair}: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check API service health with detailed information for both Rapira and APILayer
        
        Returns:
            Dictionary with health check results
        """
        logger.info("Performing comprehensive API health check")
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'service': 'unified_api_service',
            'status': 'unknown',
            'rapira_api': {},
            'apilayer_api': {}
        }
        
        # Проверяем Rapira API
        try:
            rapira_start = asyncio.get_event_loop().time()
            success, data, status_code = await self._make_request(
                method='GET',
                endpoint='',
                retry_count=1,
                timeout=10.0
            )
            
            rapira_end = asyncio.get_event_loop().time()
            rapira_time = (rapira_end - rapira_start) * 1000
            
            if success and data and 'data' in data:
                rates_count = len(data['data']) if isinstance(data['data'], list) else 0
                health_data['rapira_api'] = {
                    'status': 'healthy',
                    'response_time_ms': round(rapira_time, 2),
                    'rates_available': rates_count,
                    'message': f'Rapira API responding with {rates_count} rates'
                }
            else:
                health_data['rapira_api'] = {
                    'status': 'unhealthy',
                    'response_time_ms': round(rapira_time, 2),
                    'message': f'Rapira API failed with status {status_code}'
                }
                
        except Exception as e:
            health_data['rapira_api'] = {
                'status': 'unhealthy',
                'message': f'Rapira API error: {str(e)}'
            }
        
        # Проверяем APILayer
        try:
            from .fiat_rates_service import fiat_rates_service
            apilayer_health = await fiat_rates_service.health_check()
            health_data['apilayer_api'] = apilayer_health
                
        except Exception as e:
            health_data['apilayer_api'] = {
                'status': 'unhealthy',
                'message': f'APILayer error: {str(e)}'
            }
        
        # Определяем общий статус
        rapira_ok = health_data['rapira_api'].get('status') == 'healthy'
        apilayer_ok = health_data['apilayer_api'].get('status') == 'healthy'
        
        if rapira_ok and apilayer_ok:
            health_data['status'] = 'healthy'
            health_data['message'] = 'Both Rapira and APILayer are operational'
        elif rapira_ok or apilayer_ok:
            health_data['status'] = 'degraded'
            health_data['message'] = 'One API service is down'
        else:
            health_data['status'] = 'unhealthy'
            health_data['message'] = 'Both API services are down'
        
        logger.info(f"Health check completed: {health_data['status']}")
        return health_data
    
    async def get_supported_pairs(self) -> Optional[list[str]]:
        """
        Get list of supported currency pairs from API
        
        Returns:
            List of supported pairs or None if failed
        """
        logger.info("Getting supported currency pairs")
        
        # Всегда получаем реальные данные от API
        
        try:
            success, data, status_code = await self._make_request(
                method='GET',
                endpoint='/pairs',
                params={'format': 'json'}
            )
            
            if success and data:
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'pairs' in data:
                    return data['pairs']
                else:
                    logger.warning(f"Unexpected pairs response format: {data}")
                    return None
            else:
                logger.error(f"Failed to get supported pairs: status {status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting supported pairs: {e}")
            return None


# Global API service instance
api_service = APIService()


def determine_pair_type(pair: str) -> str:
    """
    Determine if a currency pair is crypto, fiat, or mixed
    
    Args:
        pair: Currency pair (e.g., 'BTC/USDT', 'USD/ZAR')
    
    Returns:
        str: 'crypto', 'fiat', or 'mixed'
    """
    try:
        base_currency, quote_currency = pair.split('/')
        
        fiat_currencies = {'USD', 'EUR', 'RUB', 'ZAR', 'THB', 'AED', 'IDR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY'}
        crypto_currencies = {'BTC', 'ETH', 'TON', 'USDT', 'USDC', 'LTC', 'TRX', 'BNB', 'DAI', 'DOGE', 'ETC', 'OP', 'XMR', 'SOL', 'NOT'}
        
        base_is_fiat = base_currency in fiat_currencies
        quote_is_fiat = quote_currency in fiat_currencies
        base_is_crypto = base_currency in crypto_currencies
        quote_is_crypto = quote_currency in crypto_currencies
        
        if base_is_fiat and quote_is_fiat:
            return 'fiat'
        elif base_is_crypto and quote_is_crypto:
            return 'crypto'
        elif (base_is_crypto or quote_is_crypto) and (base_is_fiat or quote_is_fiat):
            return 'mixed'
        else:
            return 'unknown'
            
    except ValueError:
        return 'invalid'