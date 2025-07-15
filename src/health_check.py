#!/usr/bin/env python3
"""
Health Check Endpoint for Crypto Helper Telegram Bot
Provides HTTP endpoint for monitoring container health
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from aiohttp import web, ClientSession
from aiohttp.web_response import Response

try:
    from .config import config
    from .utils.logger import get_api_logger
    from .services.api_service import api_service
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from config import config
    from utils.logger import get_api_logger
    from services.api_service import api_service

logger = get_api_logger()


class HealthCheckServer:
    """HTTP server for health checks and metrics"""
    
    def __init__(self, port: int = None):
        # Порт может быть задан через переменную окружения
        import os
        self.port = port or int(os.getenv('PORT', 8080))
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/health/live', self.liveness_check)
        self.app.router.add_get('/health/ready', self.readiness_check)
        self.app.router.add_get('/metrics', self.metrics)
        self.app.router.add_get('/', self.root)
    
    async def root(self, request: web.Request) -> Response:
        """Root endpoint with basic info"""
        info = {
            'service': 'crypto-helper-bot',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'health': '/health',
                'liveness': '/health/live',
                'readiness': '/health/ready',
                'metrics': '/metrics'
            }
        }
        return web.json_response(info)
    
    async def health_check(self, request: web.Request) -> Response:
        """Comprehensive health check"""
        try:
            # Check API service health
            api_health = await api_service.health_check()
            
            # Overall health status
            is_healthy = api_health['status'] == 'healthy'
            
            health_data = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'checks': {
                    'api_service': api_health,
                    'configuration': self._check_configuration(),
                    'system': self._check_system()
                }
            }
            
            status_code = 200 if is_healthy else 503
            return web.json_response(health_data, status=status_code)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            error_data = {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
            return web.json_response(error_data, status=500)
    
    async def liveness_check(self, request: web.Request) -> Response:
        """Liveness probe - checks if container is alive"""
        try:
            # Simple check that the application is running
            liveness_data = {
                'status': 'alive',
                'timestamp': datetime.now().isoformat(),
                'uptime': self._get_uptime()
            }
            return web.json_response(liveness_data)
            
        except Exception as e:
            logger.error(f"Liveness check failed: {e}")
            return web.json_response({
                'status': 'dead',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }, status=500)
    
    async def readiness_check(self, request: web.Request) -> Response:
        """Readiness probe - checks if container is ready to serve traffic"""
        try:
            # Check if all dependencies are ready
            checks = {
                'config': self._check_configuration(),
                'api_connectivity': await self._check_api_connectivity()
            }
            
            is_ready = all(check['status'] == 'ok' for check in checks.values())
            
            readiness_data = {
                'status': 'ready' if is_ready else 'not_ready',
                'timestamp': datetime.now().isoformat(),
                'checks': checks
            }
            
            status_code = 200 if is_ready else 503
            return web.json_response(readiness_data, status=status_code)
            
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return web.json_response({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }, status=500)
    
    async def metrics(self, request: web.Request) -> Response:
        """Metrics endpoint (Prometheus format)"""
        try:
            # Basic metrics
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    'app_info': {
                        'name': 'crypto_helper_bot',
                        'version': '1.0.0'
                    },
                    'system': self._get_system_metrics(),
                    'api': await self._get_api_metrics()
                }
            }
            
            return web.json_response(metrics_data)
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return web.json_response({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=500)
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity"""
        try:
            config.validate()
            return {
                'status': 'ok',
                'message': 'Configuration is valid',
                'has_bot_token': bool(config.BOT_TOKEN),
                'has_api_key': bool(config.RAPIRA_API_KEY)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Configuration error: {str(e)}'
            }
    
    def _check_system(self) -> Dict[str, Any]:
        """Check system resources"""
        try:
            import psutil
            return {
                'status': 'ok',
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
        except ImportError:
            return {
                'status': 'ok',
                'message': 'System monitoring not available (psutil not installed)'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'System check failed: {str(e)}'
            }
    
    async def _check_api_connectivity(self) -> Dict[str, Any]:
        """Check API connectivity"""
        try:
            # Simple connection test
            async with ClientSession() as session:
                async with session.get(
                    config.RAPIRA_API_URL,
                    timeout=5
                ) as response:
                    if response.status == 200:
                        return {
                            'status': 'ok',
                            'message': 'API is reachable',
                            'response_time_ms': 0  # Could measure actual time
                        }
                    else:
                        return {
                            'status': 'warning',
                            'message': f'API returned status {response.status}'
                        }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'API connectivity check failed: {str(e)}'
            }
    
    def _get_uptime(self) -> str:
        """Get application uptime"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            uptime_seconds = (datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds()
            return f"{uptime_seconds:.0f} seconds"
        except:
            return "unknown"
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        try:
            import psutil
            return {
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_total': psutil.disk_usage('/').total,
                'disk_free': psutil.disk_usage('/').free
            }
        except ImportError:
            return {'status': 'metrics_not_available'}
        except Exception as e:
            return {'error': str(e)}
    
    async def _get_api_metrics(self) -> Dict[str, Any]:
        """Get API-related metrics"""
        try:
            # Could track API call statistics here
            return {
                'total_requests': 0,  # Placeholder
                'successful_requests': 0,  # Placeholder
                'failed_requests': 0,  # Placeholder
                'average_response_time': 0  # Placeholder
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def start(self):
        """Start the health check server"""
        logger.info(f"Starting health check server on port {self.port}")
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        logger.info(f"Health check server started on http://0.0.0.0:{self.port}")
        return runner


async def start_health_server():
    """Start the health check server as a background task"""
    import os
    port = int(os.getenv('PORT', 8080))
    health_server = HealthCheckServer(port=port)
    return await health_server.start()


if __name__ == '__main__':
    # Run health check server standalone
    async def main():
        runner = await start_health_server()
        try:
            await asyncio.Event().wait()  # Run forever
        finally:
            await runner.cleanup()
    
    asyncio.run(main())