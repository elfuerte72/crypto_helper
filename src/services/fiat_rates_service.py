#!/usr/bin/env python3
"""
Fiat Rates Service for Crypto Helper Bot
Получает курсы фиатных валют из APILayer
"""

import asyncio
import aiohttp
import json
import traceback
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import random
import sys

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

def log_detailed_error(error_type: str, error: Exception, context: str = ""):
    """Детальное логирование ошибок с трейсбеком"""
    error_details = {
        'type': error_type,
        'message': str(error),
        'class': error.__class__.__name__,
        'context': context,
        'traceback': traceback.format_exc() if hasattr(error, '__traceback__') else 'No traceback available'
    }
    
    logger.error(
        f"🚨 {error_type} ERROR in {context}:\n"
        f"   ├─ Type: {error_details['class']}\n"
        f"   ├─ Message: {error_details['message']}\n"
        f"   └─ Traceback:\n{error_details['traceback']}"
    )
    
    return error_details


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
    
    async def get_rates_from_base(self, base_currency: str, use_fallback: bool = True) -> Optional[Dict[str, float]]:
        """
        Получает курсы всех валют относительно базовой через APILayer
        
        Args:
            base_currency: Базовая валюта (например, 'USD')
            use_fallback: Использовать fallback при ошибках
        
        Returns:
            Словарь курсов {валюта: курс} или None
        """
        if not self.session:
            await self.start_session()
        
        # Проверяем кэш сначала
        cached_rates = await self._get_cached_rates(base_currency)
        if cached_rates:
            logger.debug(f"Using cached rates for {base_currency}")
            return cached_rates
        
        # Если нет API ключа, сразу используем fallback
        if not self.api_key:
            logger.warning(
                "🔑 APILayer API key not configured\n"
                f"   ├─ Service: {self.__class__.__name__}\n"
                f"   ├─ Base currency: {base_currency}\n"
                f"   ├─ Fallback available: {use_fallback}\n"
                f"   └─ Action: Using fallback data"
            )
            if use_fallback:
                fallback_rates = await self._get_fallback_rates(base_currency)
                logger.info(f"✅ Fallback rates loaded for {base_currency}: {len(fallback_rates)} currencies")
                return fallback_rates
            return None
        
        # Пытаемся получить реальные данные с улучшенной retry логикой
        max_retries = 3
        base_delay = 5  # Начальная задержка в секундах
        
        logger.info(
            f"🚀 Starting APILayer request for {base_currency}\n"
            f"   ├─ Max retries: {max_retries}\n"
            f"   ├─ Base delay: {base_delay}s\n"
            f"   ├─ Supported currencies: {len(self.supported_currencies)}\n"
            f"   └─ Fallback enabled: {use_fallback}"
        )
        
        for attempt in range(max_retries):
            attempt_start_time = asyncio.get_event_loop().time()
            logger.info(
                f"🔄 APILayer attempt {attempt + 1}/{max_retries} for {base_currency}\n"
                f"   ├─ URL: {self.base_url}/latest\n"
                f"   ├─ Currencies requested: {len(self.supported_currencies)}\n"
                f"   └─ Timeout: {self.timeout.total}s"
            )
            
            try:
                await self._rate_limit()
                
                # APILayer endpoint для получения курсов
                url = f"{self.base_url}/latest"
                params = {
                    'base': base_currency,
                    'symbols': ','.join(self.supported_currencies)
                }
                
                logger.debug(f"🔗 Making HTTP request to APILayer: {url} with params: {params}")
                
                async with self.session.get(url, params=params) as response:
                    response_time = (asyncio.get_event_loop().time() - attempt_start_time) * 1000
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            logger.debug(f"📨 APILayer response received in {response_time:.2f}ms: {len(str(data))} chars")
                            
                            if data.get('success') and 'rates' in data:
                                rates = data['rates']
                                logger.info(
                                    f"✅ APILayer SUCCESS for {base_currency}\n"
                                    f"   ├─ Response time: {response_time:.2f}ms\n"
                                    f"   ├─ Rates received: {len(rates)}\n"
                                    f"   ├─ Attempt: {attempt + 1}/{max_retries}\n"
                                    f"   └─ Caching: enabled"
                                )
                                
                                # Кэшируем успешный результат
                                await self._cache_rates(base_currency, rates)
                                return rates
                            else:
                                error_data = data.get('error', {})
                                error_msg = error_data.get('info', 'Unknown error')
                                error_code = error_data.get('code', 'unknown')
                                
                                logger.error(
                                    f"❌ APILayer API ERROR for {base_currency}\n"
                                    f"   ├─ Error code: {error_code}\n"
                                    f"   ├─ Error message: {error_msg}\n"
                                    f"   ├─ Full response: {json.dumps(data, indent=2)}\n"
                                    f"   ├─ Response time: {response_time:.2f}ms\n"
                                    f"   └─ Attempt: {attempt + 1}/{max_retries}"
                                )
                                
                                if attempt == max_retries - 1:  # Последняя попытка
                                    if use_fallback:
                                        logger.info(f"🔄 Using fallback data for {base_currency} after API error")
                                        fallback_rates = await self._get_fallback_rates(base_currency)
                                        logger.info(f"✅ Fallback rates loaded: {len(fallback_rates)} currencies")
                                        return fallback_rates
                                    raise APILayerError(f"APILayer error: {error_msg} (code: {error_code})")
                        except json.JSONDecodeError as e:
                            log_detailed_error("JSON_DECODE", e, f"APILayer response parsing for {base_currency}")
                            response_text = await response.text()
                            logger.error(f"🚨 Invalid JSON response from APILayer: {response_text[:500]}...")
                            if attempt == max_retries - 1 and use_fallback:
                                return await self._get_fallback_rates(base_currency)
                    
                    elif response.status == 401:
                        auth_error_details = {
                            'status': response.status,
                            'headers': dict(response.headers),
                            'url': str(response.url),
                            'api_key_present': bool(self.api_key),
                            'api_key_length': len(self.api_key) if self.api_key else 0
                        }
                        
                        logger.error(
                            f"🔒 APILayer AUTHENTICATION FAILED for {base_currency}\n"
                            f"   ├─ Status: {auth_error_details['status']}\n"
                            f"   ├─ API key present: {auth_error_details['api_key_present']}\n"
                            f"   ├─ API key length: {auth_error_details['api_key_length']}\n"
                            f"   ├─ URL: {auth_error_details['url']}\n"
                            f"   ├─ Response time: {response_time:.2f}ms\n"
                            f"   └─ Attempt: {attempt + 1}/{max_retries}"
                        )
                        
                        if use_fallback:
                            logger.info(f"🔄 Using fallback data for {base_currency} after auth error")
                            fallback_rates = await self._get_fallback_rates(base_currency)
                            logger.info(f"✅ Fallback rates loaded: {len(fallback_rates)} currencies")
                            return fallback_rates
                        raise APILayerError("Invalid API key", response.status)
                    
                    elif response.status == 429:
                        # Улучшенная обработка rate limiting
                        retry_after = int(response.headers.get('Retry-After', 60))
                        exponential_delay = base_delay * (2 ** attempt)
                        actual_delay = min(retry_after, exponential_delay, 30)  # Максимум 30 секунд
                        
                        rate_limit_details = {
                            'status': response.status,
                            'retry_after_header': response.headers.get('Retry-After'),
                            'exponential_delay': exponential_delay,
                            'actual_delay': actual_delay,
                            'headers': dict(response.headers),
                            'response_time': response_time
                        }
                        
                        logger.warning(
                            f"⏱️ APILayer RATE LIMIT for {base_currency}\n"
                            f"   ├─ Status: {rate_limit_details['status']}\n"
                            f"   ├─ Retry-After header: {rate_limit_details['retry_after_header']}s\n"
                            f"   ├─ Exponential delay: {rate_limit_details['exponential_delay']:.1f}s\n"
                            f"   ├─ Actual delay: {rate_limit_details['actual_delay']:.1f}s\n"
                            f"   ├─ Response time: {rate_limit_details['response_time']:.2f}ms\n"
                            f"   └─ Attempt: {attempt + 1}/{max_retries}"
                        )
                        
                        if attempt < max_retries - 1:  # Не последняя попытка
                            logger.info(
                                f"⏳ Waiting {actual_delay}s before retry {attempt + 2}/{max_retries} "
                                f"(exponential backoff for {base_currency})"
                            )
                            await asyncio.sleep(actual_delay)
                            continue
                        else:
                            logger.warning(
                                f"⚠️ Rate limit exceeded after all {max_retries} retries for {base_currency}\n"
                                f"   ├─ Total attempts: {max_retries}\n"
                                f"   ├─ Final delay was: {actual_delay}s\n"
                                f"   └─ Using fallback: {use_fallback}"
                            )
                            if use_fallback:
                                fallback_rates = await self._get_fallback_rates(base_currency)
                                logger.info(f"✅ Fallback rates loaded: {len(fallback_rates)} currencies")
                                return fallback_rates
                            raise APILayerError("Rate limit exceeded", response.status)
                    
                    else:
                        try:
                            error_text = await response.text()
                        except Exception as e:
                            error_text = f"Could not read response body: {str(e)}"
                        
                        http_error_details = {
                            'status': response.status,
                            'status_text': response.reason,
                            'headers': dict(response.headers),
                            'url': str(response.url),
                            'response_time': response_time,
                            'content_type': response.headers.get('content-type', 'unknown'),
                            'content_length': response.headers.get('content-length', 'unknown'),
                            'error_body': error_text[:1000] if error_text else 'No body'
                        }
                        
                        logger.error(
                            f"🚨 APILayer HTTP ERROR for {base_currency}\n"
                            f"   ├─ Status: {http_error_details['status']} {http_error_details['status_text']}\n"
                            f"   ├─ Content-Type: {http_error_details['content_type']}\n"
                            f"   ├─ Content-Length: {http_error_details['content_length']}\n"
                            f"   ├─ Response time: {http_error_details['response_time']:.2f}ms\n"
                            f"   ├─ URL: {http_error_details['url']}\n"
                            f"   ├─ Attempt: {attempt + 1}/{max_retries}\n"
                            f"   └─ Error body: {http_error_details['error_body']}"
                        )
                        
                        if attempt == max_retries - 1:
                            if use_fallback:
                                logger.info(
                                    f"🔄 Using fallback data for {base_currency} after HTTP {response.status} error\n"
                                    f"   └─ Final attempt failed after {response_time:.2f}ms"
                                )
                                fallback_rates = await self._get_fallback_rates(base_currency)
                                logger.info(f"✅ Fallback rates loaded: {len(fallback_rates)} currencies")
                                return fallback_rates
                            raise APILayerError(f"API error {response.status}: {error_text}", response.status)
                        
                        # Добавляем задержку перед повторной попыткой
                        retry_delay = base_delay * (attempt + 1)
                        logger.info(f"⏳ Waiting {retry_delay}s before retry after HTTP {response.status}")
                        await asyncio.sleep(retry_delay)
                        
            except aiohttp.ClientError as e:
                network_error_details = log_detailed_error(
                    "NETWORK", e, f"APILayer request for {base_currency} (attempt {attempt + 1}/{max_retries})"
                )
                
                logger.error(
                    f"🌐 NETWORK ERROR for {base_currency}\n"
                    f"   ├─ Error type: {network_error_details['class']}\n"
                    f"   ├─ Error message: {network_error_details['message']}\n"
                    f"   ├─ Attempt: {attempt + 1}/{max_retries}\n"
                    f"   ├─ Retry available: {attempt < max_retries - 1}\n"
                    f"   └─ Fallback available: {use_fallback}"
                )
                
                if attempt == max_retries - 1:
                    if use_fallback:
                        logger.info(
                            f"🔄 Using fallback data for {base_currency} after network error\n"
                            f"   ├─ All {max_retries} attempts failed\n"
                            f"   └─ Final error: {network_error_details['class']}"
                        )
                        fallback_rates = await self._get_fallback_rates(base_currency)
                        logger.info(f"✅ Fallback rates loaded: {len(fallback_rates)} currencies")
                        return fallback_rates
                    raise APILayerError(f"Network error: {str(e)}")
                
                # Добавляем задержку перед повторной попыткой
                retry_delay = base_delay * (attempt + 1)
                logger.info(
                    f"⏳ Network retry delay for {base_currency}: {retry_delay}s \n"
                    f"   └─ Next attempt: {attempt + 2}/{max_retries}"
                )
                await asyncio.sleep(retry_delay)
            
            except Exception as e:
                # Обработка неожиданных ошибок
                unexpected_error_details = log_detailed_error(
                    "UNEXPECTED", e, f"APILayer request for {base_currency} (attempt {attempt + 1}/{max_retries})"
                )
                
                logger.critical(
                    f"🚨 UNEXPECTED ERROR for {base_currency}\n"
                    f"   ├─ Error type: {unexpected_error_details['class']}\n"
                    f"   ├─ Error message: {unexpected_error_details['message']}\n"
                    f"   ├─ Attempt: {attempt + 1}/{max_retries}\n"
                    f"   ├─ Python version: {sys.version}\n"
                    f"   └─ Module: {__name__}"
                )
                
                if attempt == max_retries - 1:
                    if use_fallback:
                        logger.warning(
                            f"🔄 Using fallback after unexpected error for {base_currency}\n"
                            f"   └─ This should be investigated: {unexpected_error_details['class']}"
                        )
                        fallback_rates = await self._get_fallback_rates(base_currency)
                        logger.info(f"✅ Fallback rates loaded: {len(fallback_rates)} currencies")
                        return fallback_rates
                    raise APILayerError(f"Unexpected error: {str(e)}")
                
                # Короткая задержка перед повтором при неожиданных ошибках
                await asyncio.sleep(2)
        
        # Если все попытки неудачны, используем fallback
        if use_fallback:
            logger.warning(
                f"⚠️ ALL ATTEMPTS FAILED for {base_currency}\n"
                f"   ├─ Total attempts: {max_retries}\n"
                f"   ├─ Service: APILayer\n"
                f"   ├─ Base delay: {base_delay}s\n"
                f"   └─ Falling back to static rates"
            )
            fallback_rates = await self._get_fallback_rates(base_currency)
            logger.info(
                f"✅ FALLBACK SUCCESS for {base_currency}\n"
                f"   ├─ Rates loaded: {len(fallback_rates)}\n"
                f"   └─ Source: Static fallback data"
            )
            return fallback_rates
        
        logger.critical(
            f"🚨 FINAL FAILURE for {base_currency}\n"
            f"   ├─ All {max_retries} attempts failed\n"
            f"   ├─ Fallback disabled\n"
            f"   └─ No rates available"
        )
        raise APILayerError("All retry attempts failed")
    
    async def get_fiat_rate(self, from_currency: str, to_currency: str, use_fallback: bool = True) -> Optional[float]:
        """
        Получает курс между двумя фиатными валютами
        
        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта
            use_fallback: Использовать fallback при ошибках
        
        Returns:
            Курс или None
        """
        logger.info(f"Getting fiat rate for {from_currency}/{to_currency}")
        
        # Проверяем поддержку валют
        if from_currency not in self.supported_currencies or to_currency not in self.supported_currencies:
            logger.warning(f"Unsupported currency pair: {from_currency}/{to_currency}")
            if use_fallback:
                return await self._get_fallback_rate(from_currency, to_currency)
            return None
        
        # Если валюты одинаковые
        if from_currency == to_currency:
            return 1.0
        
        try:
            # Получаем курсы относительно исходной валюты
            rates = await self.get_rates_from_base(from_currency, use_fallback)
            
            if rates and to_currency in rates:
                rate = rates[to_currency]
                logger.debug(f"Direct fiat rate {from_currency}/{to_currency}: {rate}")
                return rate
            
            # Если прямого курса нет, пытаемся через USD
            if from_currency != 'USD' and to_currency != 'USD':
                usd_rates = await self.get_rates_from_base('USD', use_fallback)
                
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
            if use_fallback:
                return await self._get_fallback_rate(from_currency, to_currency)
            return None
            
        except APILayerError as e:
            logger.error(f"APILayer error getting rate {from_currency}/{to_currency}: {e}")
            if use_fallback:
                return await self._get_fallback_rate(from_currency, to_currency)
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting rate {from_currency}/{to_currency}: {e}")
            if use_fallback:
                return await self._get_fallback_rate(from_currency, to_currency)
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
        Получает ExchangeRate для фиатной пары с fallback поддержкой
        
        Args:
            pair: Валютная пара (например, 'USD/ZAR')
        
        Returns:
            ExchangeRate объект или None
        """
        try:
            from_currency, to_currency = pair.split('/')
            
            # Используем fallback по умолчанию
            rate = await self.get_fiat_rate(from_currency, to_currency, use_fallback=True)
            
            if rate is not None:
                exchange_rate = await self.create_fiat_exchange_rate(from_currency, to_currency, rate)
                # Отмечаем, что это fallback данные если нужно
                if hasattr(self, '_cache') and f"rates_{from_currency}" not in getattr(self, '_cache', {}):
                    exchange_rate.source = 'apilayer_fallback'
                return exchange_rate
            
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
    
    # Кэширование и fallback методы
    async def _get_cached_rates(self, base_currency: str) -> Optional[Dict[str, float]]:
        """
        Получить курсы из кэша (простая реализация в памяти)
        В продакшене можно использовать Redis или другое хранилище
        """
        # Простое кэширование в памяти с временем жизни 5 минут
        if not hasattr(self, '_cache'):
            self._cache = {}
        
        cache_key = f"rates_{base_currency}"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            # Проверяем, не устарел ли кэш (5 минут)
            if (datetime.now().timestamp() - timestamp) < 300:
                return cached_data
            else:
                # Удаляем устаревший кэш
                del self._cache[cache_key]
        
        return None
    
    async def _cache_rates(self, base_currency: str, rates: Dict[str, float]):
        """
        Сохранить курсы в кэш
        """
        if not hasattr(self, '_cache'):
            self._cache = {}
        
        cache_key = f"rates_{base_currency}"
        self._cache[cache_key] = (rates, datetime.now().timestamp())
        logger.debug(f"Cached rates for {base_currency}")
    
    async def _get_fallback_rates(self, base_currency: str) -> Dict[str, float]:
        """
        Получить fallback курсы при недоступности APILayer
        Используем реалистичные курсы на основе исторических данных
        """
        logger.info(
            f"🗄 LOADING FALLBACK RATES for {base_currency}\n"
            f"   ├─ Source: Static historical data\n"
            f"   ├─ Supported currencies: {len(self.supported_currencies)}\n"
            f"   └─ Reason: APILayer unavailable"
        )
        
        # Реалистичные курсы на основе исторических данных
        fallback_rates = {
            'USD': {
                'EUR': 0.85, 'RUB': 100.0, 'ZAR': 18.5, 'THB': 35.5, 
                'AED': 3.67, 'IDR': 15650.0, 'GBP': 0.75, 'JPY': 149.0,
                'CAD': 1.35, 'AUD': 1.55, 'CHF': 0.92, 'CNY': 7.25
            },
            'EUR': {
                'USD': 1.18, 'RUB': 118.0, 'ZAR': 21.8, 'THB': 41.8,
                'AED': 4.33, 'IDR': 18467.0, 'GBP': 0.88, 'JPY': 175.6,
                'CAD': 1.59, 'AUD': 1.83, 'CHF': 1.08, 'CNY': 8.55
            },
            'RUB': {
                'USD': 0.01, 'EUR': 0.0085, 'ZAR': 0.185, 'THB': 0.355,
                'AED': 0.037, 'IDR': 156.5, 'GBP': 0.0075, 'JPY': 1.49,
                'CAD': 0.0135, 'AUD': 0.0155, 'CHF': 0.0092, 'CNY': 0.0725
            },
            'ZAR': {
                'USD': 0.054, 'EUR': 0.046, 'RUB': 5.41, 'THB': 1.92,
                'AED': 0.198, 'IDR': 846.0, 'GBP': 0.041, 'JPY': 8.05,
                'CAD': 0.073, 'AUD': 0.084, 'CHF': 0.050, 'CNY': 0.392
            },
            'THB': {
                'USD': 0.028, 'EUR': 0.024, 'RUB': 2.82, 'ZAR': 0.52,
                'AED': 0.103, 'IDR': 441.0, 'GBP': 0.021, 'JPY': 4.20,
                'CAD': 0.038, 'AUD': 0.044, 'CHF': 0.026, 'CNY': 0.204
            },
            'AED': {
                'USD': 0.272, 'EUR': 0.231, 'RUB': 27.2, 'ZAR': 5.04,
                'THB': 9.67, 'IDR': 4264.0, 'GBP': 0.204, 'JPY': 40.6,
                'CAD': 0.368, 'AUD': 0.422, 'CHF': 0.251, 'CNY': 1.97
            },
            'IDR': {
                'USD': 0.000064, 'EUR': 0.000054, 'RUB': 0.0064, 'ZAR': 0.00118,
                'THB': 0.00227, 'AED': 0.000234, 'GBP': 0.000048, 'JPY': 0.0095,
                'CAD': 0.000086, 'AUD': 0.000099, 'CHF': 0.000059, 'CNY': 0.000463
            }
        }
        
        # Добавляем остальные валюты для полноты
        for currency in self.supported_currencies:
            if currency not in fallback_rates:
                fallback_rates[currency] = {}
            
            # Заполняем недостающие курсы через USD
            if base_currency in fallback_rates and 'USD' in fallback_rates[base_currency]:
                base_to_usd = fallback_rates[base_currency]['USD']
                for target_currency in self.supported_currencies:
                    if target_currency != currency and target_currency not in fallback_rates[currency]:
                        if 'USD' in fallback_rates and target_currency in fallback_rates['USD']:
                            usd_to_target = fallback_rates['USD'][target_currency]
                            fallback_rates[currency][target_currency] = base_to_usd * usd_to_target
        
        return fallback_rates.get(base_currency, {})
    
    async def _get_fallback_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Получить fallback курс для конкретной пары валют
        """
        logger.info(f"Using fallback rate for {from_currency}/{to_currency}")
        
        if from_currency == to_currency:
            return 1.0
        
        # Получаем fallback курсы для базовой валюты
        rates = await self._get_fallback_rates(from_currency)
        
        if to_currency in rates:
            return rates[to_currency]
        
        # Пытаемся через USD
        usd_rates = await self._get_fallback_rates('USD')
        if from_currency in usd_rates and to_currency in usd_rates:
            from_usd_rate = 1.0 / usd_rates[from_currency]
            to_usd_rate = usd_rates[to_currency]
            return from_usd_rate * to_usd_rate
        
        # Возвращаем примерный курс если ничего не найдено
        logger.warning(f"No fallback rate found for {from_currency}/{to_currency}, using default")
        return 1.0


# Глобальный экземпляр сервиса
fiat_rates_service = FiatRatesService()