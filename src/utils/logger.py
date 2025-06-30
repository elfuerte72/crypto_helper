#!/usr/bin/env python3
"""
Logging utilities for Crypto Helper Telegram Bot
Centralized logging configuration
"""

import logging
import sys
from typing import Optional
from pathlib import Path

try:
    from ..config import config
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import config


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[int] = None
) -> logging.Logger:
    """
    Setup logger with consistent formatting
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Optional log level override
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = level or config.get_log_level()
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            # Create logs directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not setup file logging: {e}")
    
    return logger


def get_bot_logger() -> logging.Logger:
    """Get the main bot logger"""
    return setup_logger('crypto_helper_bot')


def get_api_logger() -> logging.Logger:
    """Get the API service logger"""
    return setup_logger('crypto_helper_api')


def get_handler_logger() -> logging.Logger:
    """Get the handlers logger"""
    return setup_logger('crypto_helper_handlers')