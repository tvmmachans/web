"""
Enhanced Monitoring service for AI Social Manager Orchestrator.
Provides health checks, metrics collection, alerting, and orchestration monitoring.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import psutil
import httpx
import asyncio
from prometheus_client import Counter, Histogram, Gauge, start_http_server

from orchestrator.config.settings import settings
from orchestrator.event_bus import EventBus

logger = logging.getLogger(__name__)

class MonitoringService:
    """Enhanced service for monitoring system health, performance, and orchestration."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus

        # Prometheus metrics (keeping existing ones)
        self.trends_discovered = Counter(
            'orchestrator_trends_discovered_total',
            'Total trends discovered',
            ['source']
        )

        self.blueprints_generated = Counter(
            'orchestrator_blueprints_generated_total',
            'Total blueprints generated'
        )

        self.prediction_requests = Counter(
            'orchestrator_prediction_requests_total',
            'Total prediction requests'
        )

        self.generation_duration = Histogram(
            'orchestrator_generation_duration_seconds',
            'Time spent generating blueprints'
        )

        self.active_trends = Gauge(
            'orchestrator_active_trends',
            'Number of active trends'
        )

        self.system_cpu_usage = Gauge(
            'orchestrator_cpu_usage_percent',
            'CPU usage percentage'
        )

        self.system_memory_usage = Gauge(
            'orchestrator_memory_usage_percent',
            'Memory usage percentage'
        )

        # New orchestration metrics
        self.pipelines_started = Counter(
            'orchestrator_pipelines_started_total',
            'Total pipelines started'
        )

        self.pipelines_completed = Counter(
            'orchestrator_pipelines_completed_total',
            'Total pipelines completed'
        )

        self.pipelines_failed = Counter(
            'orchestrator_pipelines_failed_total',
            'Total pipelines failed'
        )

        self.websocket_connections = Gauge(
            'orchestrator_websocket_connections',
            'Active WebSocket connections'
        )

        self.cache_hit_rate = Gauge(
            'orchestrator_cache_hit_rate',
            'Cache hit rate percentage'
        )

        self.retry_attempts = Counter(
            'orchestrator_retry_attempts_total',
            'Total retry attempts'
        )

        # Enhanced monitoring state
        self.metrics = {
            'requests_total': 0,
            'requests_failed': 0,
            'response_time_avg': 0.0,
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            # Orchestration metrics
            'pipelines_started': 0,
            'pipelines_completed': 0,
            'pipelines_failed': 0,
            'active_websocket_connections': 0,
            'cache_hit_rate': 0.0,
            'retry_attempts': 0
        }
        self.alerts: List[Dict[str, Any]] = []
        self.service_health_history: Dict[str, List[Dict[str, Any]]] = {}
        self._monitoring = False

    async def start(self):
        """Start the monitoring service."""
        logger.info("Starting enhanced monitoring service")
        self._monitoring = True

        # Start Prometheus metrics server
        try:
            start_http_server(8002)  # Different port from main app
            logger.info("Prometheus metrics server started on port 8002")
        except Exception as e:
            logger.warning(f"Failed to start Prometheus server: {e}")

        # Start background monitoring
        asyncio.create_task(self._collect_system_metrics())

    async def stop(self):
        """Stop the monitoring service."""
        logger.info("Stopping enhanced monitoring service")
        self._monitoring = False

    async def _collect_system_metrics(self):
        """Collect system metrics periodically."""
        while self._monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.system_cpu_usage.set(cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                self.system_memory_usage.set(memory.percent)

                # Update active trends count
                await self._update_active_trends_count()

                # Update orchestration metrics
                await self._update_orchestration_metrics()

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(30)

    async def _update_active_trends_count(self):
        """Update the count of active trends."""
        try:
            from orchestrator.database.session import get_db

            async with get_db() as session:
                result = await session.execute("""
                    SELECT COUNT(*) as count
                    FROM trends
                    WHERE discovered_at > NOW() - INTERVAL '24 hours'
                """)

                count = result.first().count
                self.active_trends.set(count or 0)

        except Exception as e:
            logger.error(f"Error updating active trends count: {e}")

    async def _update_orchestration_metrics(self):
        """Update orchestration-specific metrics."""
        try:
            # Update Prometheus gauges with current values
            self.pipelines_started._value.set(self.metrics['pipelines_started'])
            self.pipelines_completed._value.set(self.metrics['pipelines_completed'])
            self.pipelines_failed._value.set(self.metrics['pipelines_failed'])
            self.websocket_connections.set(self.metrics['active_websocket_connections'])
            self.cache_hit_rate.set(self.metrics['cache_hit_rate'] * 100)  # Convert to percentage

        except Exception as e:
            logger.error(f"Error updating orchestration metrics: {e}")

    def record_trend_discovered(self, source: str):
        """Record a trend discovery."""
        self.trends_discovered.labels(source=source).inc()

    def record_blueprint_generated(self):
        """Record a blueprint generation."""
        self.blueprints_generated.inc()

    def record_prediction_request(self):
        """Record a prediction request."""
        self.prediction_requests.inc()

    def time_generation(self):
        """Decorator/context manager for timing blueprint generation."""
        return self.generation_duration.time()

    # Enhanced methods for orchestration monitoring

    async def record_request(self, response_time: float, success: bool = True):
        """Record a request metric."""
        self.metrics['requests_total'] += 1
        if not success:
            self.metrics['requests_failed'] += 1

        # Update average response time
        total_requests = self.metrics['requests_total']
        current_avg = self.metrics['response_time_avg']
        self.metrics['response_time_avg'] = (current_avg * (total_requests - 1) + response_time) / total_requests

    async def record_pipeline_event(self, event_type: str, data: Dict[str, Any]):
        """Record pipeline-related metrics."""
        if event_type == 'pipeline.started':
            self.metrics['pipelines_started'] += 1
            self.pipelines_started.inc()
        elif event_type == 'pipeline.completed':
            self.metrics['pipelines_completed'] += 1
            self.pipelines_completed.inc()
        elif event_type == 'pipeline.failed':
            self.metrics['pipelines_failed'] += 1
            self.pipelines_failed.inc()

    async def update_websocket_connections(self, count: int):
        """Update WebSocket connection count."""
        self.metrics['active_websocket_connections'] = count
        self.websocket_connections.set(count)

    async def update_cache_metrics(self, hits: int, misses: int):
        """Update cache hit rate."""
        total = hits + misses
        if total > 0:
            hit_rate = hits / total
            self.metrics['cache_hit_rate'] = hit_rate
            self.cache_hit_rate.set(hit_rate * 100)

    async def update_retry_metrics(self, attempts: int):
        """Update retry attempts count."""
        self.metrics['retry_attempts'] += attempts
        self.retry_attempts.inc(attempts)

    async def create_alert(self, alert_type: str, message: str,
                          metadata: Dict[str, Any] = None):
        """Create an alert with enhanced metadata."""
        alert = {
            'id': f"{alert_type}_{int(datetime.utcnow().timestamp())}",
            'type': alert_type,
            'message': message,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat(),
            'resolved': False,
            'severity': metadata.get('severity', 'info') if metadata else 'info'
        }

        self.alerts.append(alert)
        logger.warning(f"Alert created: {alert_type} - {message}")

        # Publish to event bus if available
        if self.event_bus:
            await self.event_bus.publish('system.alert_created', {
                'alert_id': alert['id'],
                'type': alert_type,
                'message': message,
                'severity': alert['severity']
            })

        # Keep only last 200 alerts
        if len(self.alerts) > 200:
            self.alerts = self.alerts[-200:]

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status including orchestration components."""
        try:
            # Database connectivity check
            db_healthy = await self._check_database_health()

            # External service checks
            services_healthy = await self._check_external_services()

            # System resources
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Collect current system metrics
            system_metrics = {
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count(),
                'memory_percent': memory.percent,
                'memory_used': memory.used,
                'memory_total': memory.total,
                'disk_percent': disk.percent,
                'disk_used': disk.used,
                'disk_total': disk.total,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Check critical services
            services_health = []
            critical_services = [
                ('backend', f"{settings.BACKEND_BASE_URL}/health"),
                ('agent', f"{settings.AGENT_BASE_URL}/health"),
                ('frontend', "http://frontend:3000/api/health"),
            ]

            for service_name, endpoint in critical_services:
                health = await self._check_service_health(service_name, endpoint)
                services_health.append(health)

            # Determine overall status
            unhealthy_services = [s for s in services_health if s.get('status') in ['unhealthy', 'critical']]
            high_cpu = system_metrics['cpu_percent'] > settings.CPU_CRITICAL_THRESHOLD
            high_memory = system_metrics['memory_percent'] > settings.MEMORY_CRITICAL_THRESHOLD
            high_disk = system_metrics['disk_percent'] > settings.DISK_CRITICAL_THRESHOLD

            if unhealthy_services or high_cpu or high_memory or high_disk:
                overall_status = 'unhealthy'
            elif any(s.get('status') == 'degraded' for s in services_health):
                overall_status = 'degraded'
            else:
                overall_status = 'healthy'

            status = {
                "overall_status": overall_status,
                "database": "healthy" if db_healthy else "unhealthy",
                "external_services": "healthy" if services_healthy else "unhealthy",
                "system": system_metrics,
                "services": services_health,
                "orchestration_metrics": {
                    'pipelines_started': self.metrics['pipelines_started'],
                    'pipelines_completed': self.metrics['pipelines_completed'],
                    'pipelines_failed': self.metrics['pipelines_failed'],
                    'active_websocket_connections': self.metrics['active_websocket_connections'],
                    'cache_hit_rate': self.metrics['cache_hit_rate'],
                    'retry_attempts': self.metrics['retry_attempts']
                },
                "active_alerts": len([a for a in self.alerts if not a.get('resolved', False)]),
                "timestamp": time.time()
            }

            return status

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "overall_status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }

    async def _check_service_health(self, service_name: str, endpoint: str,
                                   timeout: float = 5.0) -> Dict[str, Any]:
        """Check health of a specific service with enhanced monitoring."""
        try:
            start_time = time.time()

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(endpoint)

            response_time = time.time() - start_time

            health_status = {
                'service': service_name,
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response_time,
                'status_code': response.status_code,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Store in history (keep last 10 checks)
            if service_name not in self.service_health_history:
                self.service_health_history[service_name] = []

            self.service_health_history[service_name].append(health_status)
            if len(self.service_health_history[service_name]) > 10:
                self.service_health_history[service_name].pop(0)

            return health_status

        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")

            health_status = {
                'service': service_name,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

            # Store failed check
            if service_name not in self.service_health_history:
                self.service_health_history[service_name] = []
            self.service_health_history[service_name].append(health_status)

            return health_status

    async def _check_database_health(self) -> bool:
        """Check database connectivity."""
        try:
            from orchestrator.database.session import get_db

            async with get_db() as session:
                await session.execute("SELECT 1")
                return True

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def _check_external_services(self) -> bool:
        """Check external service connectivity."""
        services = [
            f"{settings.BACKEND_BASE_URL}/health",
            f"{settings.VOICE_ENGINE_URL}/health"
        ]

        for service_url in services:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(service_url)
                    if response.status_code != 200:
                        return False
            except Exception as e:
                logger.warning(f"Service check failed for {service_url}: {e}")
                return False

        return True

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics including orchestration metrics."""
        return dict(self.metrics)

    def get_alerts(self, resolved: bool = False, severity: str = None) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering."""
        alerts = [alert for alert in self.alerts if alert.get('resolved', False) == resolved]
        if severity:
            alerts = [alert for alert in alerts if alert.get('severity') == severity]
        return alerts

    def get_service_health_history(self, service_name: str) -> List[Dict[str, Any]]:
        """Get health history for a specific service."""
        return self.service_health_history.get(service_name, [])
