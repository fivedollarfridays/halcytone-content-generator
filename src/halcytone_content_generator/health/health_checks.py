"""
Core health check implementation
"""
import asyncio
import time
import psutil
import os
from typing import Dict, Optional, List, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, asdict

from .schemas import (
    HealthStatus,
    ComponentStatus,
    DependencyHealth,
    MetricsSnapshot
)

logger = logging.getLogger(__name__)

# Global instance
_health_manager: Optional['HealthCheckManager'] = None


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    status: HealthStatus
    message: Optional[str] = None
    response_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ComponentHealth:
    """Component health information"""
    name: str
    status: HealthStatus
    last_check: datetime
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    message: Optional[str] = None
    response_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class HealthCheckManager:
    """Manages all health checks for the application"""

    def __init__(self, app_start_time: Optional[datetime] = None):
        self.app_start_time = app_start_time or datetime.utcnow()
        self.components: Dict[str, ComponentHealth] = {}
        self.checks: Dict[str, Callable] = {}
        self.cache: Dict[str, tuple[datetime, Any]] = {}
        self.cache_ttl = timedelta(seconds=5)
        self.failure_threshold = 3
        self.success_threshold = 1
        self._lock = asyncio.Lock()

    def register_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.checks[name] = check_func
        self.components[name] = ComponentHealth(
            name=name,
            status=HealthStatus.UNKNOWN,
            last_check=datetime.utcnow()
        )

    async def check_database(self) -> HealthCheckResult:
        """Check database connectivity"""
        try:
            start_time = time.time()

            # Import here to avoid circular dependency
            from ..database import get_database

            db = get_database()
            if not db:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message="Database not configured (development mode)"
                )

            health = await db.health_check()
            response_time = (time.time() - start_time) * 1000

            if health.get("status") == "connected":
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message="Database connection healthy",
                    response_time_ms=response_time,
                    metadata=health
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message="Database connection failed",
                    response_time_ms=response_time,
                    error=health.get("error")
                )

        except ImportError:
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Database module not available"
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Database check failed",
                error=str(e)
            )

    async def check_cache(self) -> HealthCheckResult:
        """Check cache connectivity"""
        try:
            start_time = time.time()

            # Import here to avoid circular dependency
            from ..core.cache import get_cache_manager

            cache_manager = get_cache_manager()
            if not cache_manager:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message="Cache not configured"
                )

            # Try to set and get a test value
            test_key = f"health_check_{datetime.utcnow().timestamp()}"
            test_value = "healthy"

            await cache_manager.set(test_key, test_value, ttl=5)
            retrieved = await cache_manager.get(test_key)
            await cache_manager.delete(test_key)

            response_time = (time.time() - start_time) * 1000

            if retrieved == test_value:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message="Cache connection healthy",
                    response_time_ms=response_time
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message="Cache partially working",
                    response_time_ms=response_time
                )

        except ImportError:
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Cache module not available"
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="Cache check failed",
                error=str(e)
            )

    async def check_external_services(self) -> HealthCheckResult:
        """Check external service connectivity"""
        try:
            start_time = time.time()

            # Import here to avoid circular dependency
            from ..core.services import validate_all_services

            results = await validate_all_services()
            response_time = (time.time() - start_time) * 1000

            all_healthy = all(
                result.get("status") in ["connected", "configured", "mocked"]
                for result in results.values()
            )

            unhealthy_services = [
                name for name, result in results.items()
                if result.get("status") not in ["connected", "configured", "mocked"]
            ]

            if all_healthy:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message="All external services healthy",
                    response_time_ms=response_time,
                    metadata=results
                )
            elif len(unhealthy_services) < len(results) / 2:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message=f"Some services unhealthy: {', '.join(unhealthy_services)}",
                    response_time_ms=response_time,
                    metadata=results
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Multiple services unhealthy: {', '.join(unhealthy_services)}",
                    response_time_ms=response_time,
                    metadata=results
                )

        except ImportError:
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Service validation not available"
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message="External service check failed",
                error=str(e)
            )

    async def check_disk_space(self) -> HealthCheckResult:
        """Check available disk space"""
        try:
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024 ** 3)
            percent_used = disk_usage.percent

            if percent_used > 90:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Critical disk space: {percent_used:.1f}% used, {free_gb:.1f}GB free",
                    metadata={"percent_used": percent_used, "free_gb": free_gb}
                )
            elif percent_used > 80:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message=f"Low disk space: {percent_used:.1f}% used, {free_gb:.1f}GB free",
                    metadata={"percent_used": percent_used, "free_gb": free_gb}
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message=f"Disk space healthy: {percent_used:.1f}% used, {free_gb:.1f}GB free",
                    metadata={"percent_used": percent_used, "free_gb": free_gb}
                )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="Could not check disk space",
                error=str(e)
            )

    async def check_memory(self) -> HealthCheckResult:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process(os.getpid())
            process_memory_mb = process.memory_info().rss / (1024 * 1024)

            if memory.percent > 90:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Critical memory usage: {memory.percent:.1f}% used",
                    metadata={
                        "system_percent": memory.percent,
                        "process_mb": process_memory_mb,
                        "available_mb": memory.available / (1024 * 1024)
                    }
                )
            elif memory.percent > 80:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message=f"High memory usage: {memory.percent:.1f}% used",
                    metadata={
                        "system_percent": memory.percent,
                        "process_mb": process_memory_mb,
                        "available_mb": memory.available / (1024 * 1024)
                    }
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message=f"Memory usage healthy: {memory.percent:.1f}% used",
                    metadata={
                        "system_percent": memory.percent,
                        "process_mb": process_memory_mb,
                        "available_mb": memory.available / (1024 * 1024)
                    }
                )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="Could not check memory",
                error=str(e)
            )

    async def check_cpu(self) -> HealthCheckResult:
        """Check CPU usage"""
        try:
            # Get CPU percent over 1 second interval
            cpu_percent = psutil.cpu_percent(interval=1)
            process = psutil.Process(os.getpid())
            process_cpu = process.cpu_percent()

            if cpu_percent > 90:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Critical CPU usage: {cpu_percent:.1f}%",
                    metadata={
                        "system_percent": cpu_percent,
                        "process_percent": process_cpu,
                        "cpu_count": psutil.cpu_count()
                    }
                )
            elif cpu_percent > 75:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message=f"High CPU usage: {cpu_percent:.1f}%",
                    metadata={
                        "system_percent": cpu_percent,
                        "process_percent": process_cpu,
                        "cpu_count": psutil.cpu_count()
                    }
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message=f"CPU usage healthy: {cpu_percent:.1f}%",
                    metadata={
                        "system_percent": cpu_percent,
                        "process_percent": process_cpu,
                        "cpu_count": psutil.cpu_count()
                    }
                )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="Could not check CPU",
                error=str(e)
            )

    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check"""
        # Check cache first
        if name in self.cache:
            cache_time, cached_result = self.cache[name]
            if datetime.utcnow() - cache_time < self.cache_ttl:
                return cached_result

        # Run the check
        check_func = self.checks.get(name)
        if not check_func:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"Check '{name}' not registered"
            )

        try:
            result = await check_func()

            # Update cache
            self.cache[name] = (datetime.utcnow(), result)

            # Update component health
            async with self._lock:
                component = self.components[name]
                component.status = result.status
                component.last_check = datetime.utcnow()
                component.message = result.message
                component.response_time_ms = result.response_time_ms
                component.metadata = result.metadata

                # Update consecutive counts
                if result.status in [HealthStatus.HEALTHY]:
                    component.consecutive_successes += 1
                    component.consecutive_failures = 0
                else:
                    component.consecutive_failures += 1
                    component.consecutive_successes = 0

            return result

        except Exception as e:
            logger.error(f"Health check '{name}' failed: {e}")
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed with error",
                error=str(e)
            )

    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks"""
        tasks = {name: self.run_check(name) for name in self.checks}
        results = {}

        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                results[name] = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message="Check failed",
                    error=str(e)
                )

        return results

    def get_overall_status(self) -> HealthStatus:
        """Get overall health status based on component health"""
        if not self.components:
            return HealthStatus.UNKNOWN

        statuses = [c.status for c in self.components.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNKNOWN

    def get_uptime_seconds(self) -> float:
        """Get application uptime in seconds"""
        return (datetime.utcnow() - self.app_start_time).total_seconds()

    async def get_system_metrics(self) -> MetricsSnapshot:
        """Get current system metrics"""
        try:
            process = psutil.Process(os.getpid())

            return MetricsSnapshot(
                timestamp=datetime.utcnow(),
                memory_usage_percent=psutil.virtual_memory().percent,
                cpu_usage_percent=psutil.cpu_percent(interval=0.1),
                disk_usage_percent=psutil.disk_usage('/').percent,
                active_connections=len(process.connections()),
                # These would need to be tracked separately:
                requests_per_second=0,
                average_response_time_ms=0,
                error_rate=0,
                queue_depth=0
            )
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return MetricsSnapshot()

    def should_check_component(self, component: ComponentHealth) -> bool:
        """Determine if a component should be checked based on failure/success thresholds"""
        # If component is healthy and has enough consecutive successes, check less frequently
        if component.status == HealthStatus.HEALTHY and component.consecutive_successes >= self.success_threshold:
            # Check every 5th time to reduce load
            return component.consecutive_successes % 5 == 0

        # If component is failing, always check
        return True


def get_health_manager() -> HealthCheckManager:
    """Get or create the global health check manager"""
    global _health_manager

    if _health_manager is None:
        _health_manager = HealthCheckManager()

        # Register default checks
        _health_manager.register_check("database", _health_manager.check_database)
        _health_manager.register_check("cache", _health_manager.check_cache)
        _health_manager.register_check("external_services", _health_manager.check_external_services)
        _health_manager.register_check("disk_space", _health_manager.check_disk_space)
        _health_manager.register_check("memory", _health_manager.check_memory)
        _health_manager.register_check("cpu", _health_manager.check_cpu)

    return _health_manager