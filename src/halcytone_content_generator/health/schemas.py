"""
Health check response schemas
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentStatus(BaseModel):
    """Individual component health status"""
    name: str = Field(..., description="Component name")
    status: HealthStatus = Field(..., description="Component health status")
    message: Optional[str] = Field(None, description="Status message")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last check timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class HealthResponse(BaseModel):
    """Basic health check response"""
    status: HealthStatus = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment name")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response with component status"""
    components: Dict[str, ComponentStatus] = Field(default_factory=dict, description="Component health status")
    checks_passed: int = Field(0, description="Number of passed health checks")
    checks_failed: int = Field(0, description="Number of failed health checks")
    checks_total: int = Field(0, description="Total number of health checks")
    response_time_ms: float = Field(..., description="Total response time in milliseconds")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    errors: List[str] = Field(default_factory=list, description="Error messages")


class ReadinessCheck(BaseModel):
    """Individual readiness check"""
    name: str = Field(..., description="Check name")
    ready: bool = Field(..., description="Whether the check passed")
    message: Optional[str] = Field(None, description="Check message")
    required: bool = Field(True, description="Whether this check is required for readiness")


class ReadinessResponse(BaseModel):
    """Readiness check response"""
    ready: bool = Field(..., description="Overall readiness status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    checks: List[ReadinessCheck] = Field(default_factory=list, description="Individual readiness checks")
    total_checks: int = Field(0, description="Total number of checks")
    passed_checks: int = Field(0, description="Number of passed checks")
    failed_checks: int = Field(0, description="Number of failed checks")
    required_checks_passed: bool = Field(True, description="Whether all required checks passed")


class LivenessResponse(BaseModel):
    """Liveness probe response"""
    alive: bool = Field(True, description="Whether the service is alive")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    pid: Optional[int] = Field(None, description="Process ID")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_percent: Optional[float] = Field(None, description="CPU usage percentage")
    thread_count: Optional[int] = Field(None, description="Number of active threads")


class DependencyHealth(BaseModel):
    """External dependency health status"""
    name: str = Field(..., description="Dependency name")
    type: str = Field(..., description="Dependency type (database, api, cache, etc)")
    status: HealthStatus = Field(..., description="Dependency health status")
    latency_ms: Optional[float] = Field(None, description="Latency in milliseconds")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last check timestamp")
    error: Optional[str] = Field(None, description="Error message if any")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MetricsSnapshot(BaseModel):
    """System metrics snapshot"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Snapshot timestamp")
    requests_per_second: float = Field(0, description="Current requests per second")
    average_response_time_ms: float = Field(0, description="Average response time")
    error_rate: float = Field(0, description="Error rate percentage")
    active_connections: int = Field(0, description="Number of active connections")
    queue_depth: int = Field(0, description="Request queue depth")
    memory_usage_percent: float = Field(0, description="Memory usage percentage")
    cpu_usage_percent: float = Field(0, description="CPU usage percentage")
    disk_usage_percent: float = Field(0, description="Disk usage percentage")


class HealthCheckConfig(BaseModel):
    """Health check configuration"""
    enabled: bool = Field(True, description="Whether health checks are enabled")
    interval_seconds: int = Field(30, description="Check interval in seconds")
    timeout_seconds: int = Field(10, description="Check timeout in seconds")
    failure_threshold: int = Field(3, description="Consecutive failures before marking unhealthy")
    success_threshold: int = Field(1, description="Consecutive successes before marking healthy")
    cache_ttl_seconds: int = Field(5, description="Cache TTL for health check results")
    include_details: bool = Field(False, description="Include detailed component status")
    check_dependencies: bool = Field(True, description="Check external dependencies")
    check_database: bool = Field(True, description="Check database connectivity")
    check_cache: bool = Field(True, description="Check cache connectivity")
    check_external_apis: bool = Field(True, description="Check external API connectivity")