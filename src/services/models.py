#!/usr/bin/env python3
"""
Общие модели данных для сервисов API
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ExchangeRate:
    """Data class for exchange rate information"""
    pair: str
    rate: float
    timestamp: str
    source: str = "unknown"
    bid: Optional[float] = None
    ask: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def is_valid(self) -> bool:
        """Check if exchange rate data is valid"""
        return (
            self.rate > 0 and
            self.pair and
            self.timestamp and
            len(self.pair.split('/')) == 2
        )


class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RapiraAPIError(APIError):
    """Custom exception for Rapira API errors"""
    pass


class APILayerError(APIError):
    """Custom exception for APILayer errors"""
    pass