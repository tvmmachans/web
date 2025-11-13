"""
Health Monitor - Heartbeat checks every 5 minutes with self-healing.
Monitors system health and performs automatic recovery actions.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import psutil
import httpx

from orchestrator.event_bus import EventBus

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

@dataclass
class ServiceHealth:
    """Health information for a service."""
    name: str
    status: HealthStatus
    last_check: datetime
    response_time: float
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    total_checks: int = 0
    successful_checks: int = 0

@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_connections: int
    timestamp: datetime

class HealthMonitor:
    """Monitors system and service health with self-healing capabilities."""

    def __init__(self, event_bus: EventBus, check_interval: int = 300):  # 5 minutes default
        self.event_bus = event_bus
        self.check_interval = check_interval
        self.services: Dict[str, ServiceHealth] = {}
        self.system_history: List[SystemMetrics] = []
        self._running = False
        self._last_system_check = datetime.utcnow()

        # Recovery actions
        self.recovery_actions: Dict[str, List[Callable]] = {}

        # Health thresholds
        self.thresholds = {
            'cpu_critical': 90.0,
            'cpu_degraded': 70.0,
            'memory_critical': 90.0,
            'memory_degraded': 80.0,
            'disk_critical': 95.0,
            'disk_degraded': 85.0,
            'max_consecutive_failures': 3,
            'response_time_degraded': 5.0,  # seconds
            'response_time_critical': 15.0  # seconds
        }

    async def start(self):
        """Start the health monitoring."""
        self._running = True

        # Register default services to monitor
        await self.register_service("backend", "http://backend:8000/health")
        await self.register_service("agent", "http://agent:8001/health")
        await self.register_service("frontend", "http://frontend:3000/api/health")
        await self.register_service("redis", "redis://redis:6379", check_type="redis")
        await self.register_service("database", "postgresql://db:5432", check_type="database")

        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())

        logger.info("HealthMonitor started")

    async def stop(self):
        """Stop the health monitoring."""
        self._running = False
        logger.info("HealthMonitor stopped")

    async def register_service(self, name: str, endpoint: str,
                             check_type: str = "http", timeout: float = 5.0):
        """Register a service for health monitoring."""
        self.services[name] = ServiceHealth(
            name=name,
            status=HealthStatus.HEALTHY,
            last_check=datetime.utcnow(),
            response_time=0.0
        )

        # Store check configuration
        self.services[name].__dict__.update({
            'endpoint': endpoint,
            'check_type': check_type,
            'timeout': timeout
        })

        logger.info(f"Registered service for monitoring: {name} ({endpoint})")

    async def unregister_service(self, name: str):
        """Unregister a service from monitoring."""
        if name in self.services:
            del self.services[name]
            logger.info(f"Unregistered service from monitoring: {name}")

    def register_recovery_action(self, service_name: str, action: Callable):
        """Register a recovery action for a service."""
        if service_name not in self.recovery_actions:
            self.recovery_actions[service_name] = []

        self.recovery_actions[service_name].append(action)
        logger.info(f"Registered recovery action for service: {service_name}")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                # Perform health checks
                await self._perform_health_checks()

                # Check system resources
                await self._check_system_resources()

                # Perform self-healing if needed
                await self._perform_self_healing()

                # Publish health status
                await self._publish_health_status()

                # Wait for next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def _perform_health_checks(self):
        """Perform health checks on all registered services."""
        for service_name, service in self.services.items():
            try:
                start_time = time.time()

                if service.__dict__.get('check_type') == 'http':
                    await self._check_http_service(service)
                elif service.__dict__.get('check_type') == 'redis':
                    await self._check_redis_service(service)
                elif service.__dict__.get('check_type') == 'database':
                    await self._check_database_service(service)
                else:
                    await self._check_http_service(service)  # Default to HTTP

                response_time = time.time() - start_time
                service.response_time = response_time
                service.last_check = datetime.utcnow()
                service.total_checks += 1

                # Determine status based on response time and failures
                old_status = service.status
                service.status = self._determine_service_status(service)

                # Handle status changes
                if service.status != old_status:
                    await self._handle_status_change(service, old_status)

            except Exception as e:
                await self._handle_service_failure(service, str(e))

    async def _check_http_service(self, service: ServiceHealth):
        """Check HTTP service health."""
        timeout = service.__dict__.get('timeout', 5.0)
        endpoint = service.__dict__.get('endpoint')

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{endpoint}")

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

            # Check response content for health indicators
            data = response.json()
            if not data.get('status') == 'healthy':
                raise Exception(f"Service reported unhealthy status: {data}")

    async def _check_redis_service(self, service: ServiceHealth):
        """Check Redis service health."""
        import redis.asyncio as redis

        endpoint = service.__dict__.get('endpoint', 'redis://localhost:6379/0')

        try:
            r = redis.from_url(endpoint)
            await r.ping()
            await r.close()
        except Exception as e:
            raise Exception(f"Redis connection failed: {e}")

    async def _check_database_service(self, service: ServiceHealth):
        """Check database service health."""
        # This would integrate with actual database connection
        # For now, just mark as healthy
        pass

    def _determine_service_status(self, service: ServiceHealth) -> HealthStatus:
        """Determine the health status of a service."""
        # Check consecutive failures
        if service.consecutive_failures >= self.thresholds['max_consecutive_failures']:
            return HealthStatus.CRITICAL

        # Check response time
        if service.response_time >= self.thresholds['response_time_critical']:
            return HealthStatus.CRITICAL
        elif service.response_time >= self.thresholds['response_time_degraded']:
            return HealthStatus.DEGRADED

        # Check success rate
        if service.total_checks > 0:
            success_rate = service.successful_checks / service.total_checks
            if success_rate < 0.5:
                return HealthStatus.UNHEALTHY
            elif success_rate < 0.8:
                return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    async def _handle_service_failure(self, service: ServiceHealth, error: str):
        """Handle service health check failure."""
        service.consecutive_failures += 1
        service.error_message = error
        service.last_check = datetime.utcnow()
        service.total_checks += 1

        old_status = service.status
        service.status = HealthStatus.CRITICAL

        logger.warning(f"Service {service.name} health check failed: {error}")

        # Publish failure event
        await self.event_bus.publish('system.service_down', {
            'service': service.name,
            'error': error,
            'consecutive_failures': service.consecutive_failures
        })

        # Trigger recovery if status changed
        if service.status != old_status:
            await self._handle_status_change(service, old_status)

    async def _handle_status_change(self, service: ServiceHealth, old_status: HealthStatus):
        """Handle service status changes."""
        logger.info(f"Service {service.name} status changed: {old_status.value} -> {service.status.value}")

        # Publish status change event
        await self.event_bus.publish('system.service_status_changed', {
            'service': service.name,
            'old_status': old_status.value,
            'new_status': service.status.value,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Reset consecutive failures on recovery
        if service.status == HealthStatus.HEALTHY:
            service.consecutive_failures = 0
            service.error_message = None
            service.successful_checks += 1

    async def _check_system_resources(self):
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent

            # Network connections
            network_connections = len(psutil.net_connections())

            # Create metrics
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_connections=network_connections,
                timestamp=datetime.utcnow()
            )

            # Store in history (keep last 100 entries)
            self.system_history.append(metrics)
            if len(self.system_history) > 100:
                self.system_history.pop(0)

            # Check thresholds and alert if needed
            await self._check_resource_thresholds(metrics)

            self._last_system_check = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error checking system resources: {e}")

    async def _check_resource_thresholds(self, metrics: SystemMetrics):
        """Check if system resources exceed thresholds."""
        alerts = []

        if metrics.cpu_percent >= self.thresholds['cpu_critical']:
            alerts.append(('cpu', 'critical', metrics.cpu_percent))
        elif metrics.cpu_percent >= self.thresholds['cpu_degraded']:
            alerts.append(('cpu', 'degraded', metrics.cpu_percent))

        if metrics.memory_percent >= self.thresholds['memory_critical']:
            alerts.append(('memory', 'critical', metrics.memory_percent))
        elif metrics.memory_percent >= self.thresholds['memory_degraded']:
            alerts.append(('memory', 'degraded', metrics.memory_percent))

        if metrics.disk_usage_percent >= self.thresholds['disk_critical']:
            alerts.append(('disk', 'critical', metrics.disk_usage_percent))
        elif metrics.disk_usage_percent >= self.thresholds['disk_degraded']:
            alerts.append(('disk', 'degraded', metrics.disk_usage_percent))

        for resource, level, value in alerts:
            await self.event_bus.publish('system.resource_alert', {
                'resource': resource,
                'level': level,
                'value': value,
                'threshold': self.thresholds[f'{resource}_{level}'],
                'timestamp': metrics.timestamp.isoformat()
            })

    async def _perform_self_healing(self):
        """Perform self-healing actions for unhealthy services."""
        for service_name, service in self.services.items():
            if service.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                if service_name in self.recovery_actions:
                    logger.info(f"Attempting self-healing for service: {service_name}")

                    for action in self.recovery_actions[service_name]:
                        try:
                            await action(service)
                            logger.info(f"Executed recovery action for {service_name}")

                            # Wait a bit before checking again
                            await asyncio.sleep(10)

                            # Re-check service health
                            await self._perform_single_health_check(service)

                            if service.status == HealthStatus.HEALTHY:
                                logger.info(f"Self-healing successful for {service_name}")
                                break

                        except Exception as e:
                            logger.error(f"Recovery action failed for {service_name}: {e}")

    async def _perform_single_health_check(self, service: ServiceHealth):
        """Perform a single health check on a service."""
        try:
            if service.__dict__.get('check_type') == 'http':
                await self._check_http_service(service)
            # Add other check types as needed

            service.consecutive_failures = 0
            service.error_message = None
            service.status = HealthStatus.HEALTHY
            service.successful_checks += 1

        except Exception as e:
            service.consecutive_failures += 1
            service.error_message = str(e)
            service.status = HealthStatus.CRITICAL

    async def _publish_health_status(self):
        """Publish overall health status."""
        overall_status = self._calculate_overall_health()

        health_data = {
            'overall_status': overall_status.value,
            'services': {
                name: {
                    'status': service.status.value,
                    'last_check': service.last_check.isoformat(),
                    'response_time': service.response_time,
                    'consecutive_failures': service.consecutive_failures,
                    'error_message': service.error_message
                }
                for name, service in self.services.items()
            },
            'system': self._get_latest_system_metrics(),
            'timestamp': datetime.utcnow().isoformat()
        }

        await self.event_bus.publish('system.health_check', health_data)

    def _calculate_overall_health(self) -> HealthStatus:
        """Calculate overall system health."""
        critical_count = sum(1 for s in self.services.values() if s.status == HealthStatus.CRITICAL)
        unhealthy_count = sum(1 for s in self.services.values() if s.status == HealthStatus.UNHEALTHY)

        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif any(s.status == HealthStatus.DEGRADED for s in self.services.values()):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def _get_latest_system_metrics(self) -> Dict[str, Any]:
        """Get the latest system metrics."""
        if not self.system_history:
            return {}

        latest = self.system_history[-1]
        return {
            'cpu_percent': latest.cpu_percent,
            'memory_percent': latest.memory_percent,
            'disk_usage_percent': latest.disk_usage_percent,
            'network_connections': latest.network_connections,
            'timestamp': latest.timestamp.isoformat()
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            'overall_status': self._calculate_overall_health().value,
            'services': {
                name: {
                    'status': service.status.value,
                    'last_check': service.last_check.isoformat(),
                    'response_time': service.response_time,
                    'consecutive_failures': service.consecutive_failures
                }
                for name, service in self.services.items()
            },
            'system': self._get_latest_system_metrics(),
            'last_check': self._last_system_check.isoformat()
        }

    def get_service_health(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get health status for a specific service."""
        if service_name not in self.services:
            return None

        service = self.services[service_name]
        return {
            'name': service.name,
            'status': service.status.value,
            'last_check': service.last_check.isoformat(),
            'response_time': service.response_time,
            'consecutive_failures': service.consecutive_failures,
            'total_checks': service.total_checks,
            'successful_checks': service.successful_checks,
            'error_message': service.error_message
        }
