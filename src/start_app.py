#!/usr/bin/env python3
"""
Application starter script for Heroku deployment
Starts both health check server and Telegram bot with internal keep-alive
"""

import asyncio
import sys
import os
import aiohttp
import logging
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import after path setup
from main import main  # noqa: E402
from health_check import start_health_server  # noqa: E402

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def internal_keep_alive():
    """Internal keep-alive mechanism - pings own health endpoint every 25 minutes"""
    port = os.environ.get('PORT', '8080')
    health_url = f"http://localhost:{port}/health/live"
    
    # Wait 2 minutes before starting pings (let server start)
    logger.info("🔄 Internal keep-alive: Starting in 2 minutes...")
    await asyncio.sleep(120)
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        logger.info(f"✅ Internal keep-alive: {data.get('status', 'unknown')} - {timestamp}")
                    else:
                        logger.warning(f"⚠️ Internal keep-alive: HTTP {response.status}")
        except Exception as e:
            logger.error(f"❌ Internal keep-alive failed: {e}")
        
        # Wait 25 minutes before next ping
        logger.info("⏰ Internal keep-alive: Next ping in 25 minutes...")
        await asyncio.sleep(25 * 60)


async def run_all():
    """Run health server, bot, and internal keep-alive concurrently"""
    try:
        await asyncio.gather(
            start_health_server(),
            main(),
            internal_keep_alive()
        )
    except Exception as e:
        print(f"❌ Error running application: {e}")
        raise


if __name__ == '__main__':
    print("🚀 Starting Crypto Helper Bot with health server and internal keep-alive...")
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1) 