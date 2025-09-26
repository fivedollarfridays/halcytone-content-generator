"""
Configuration Validation and Security Checks
Comprehensive validation for production deployment safety
"""

import re
import os
import json
import logging
import secrets
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation issue severity levels"""
    CRITICAL = "critical"      # Must be fixed before deployment
    HIGH = "high"             # Should be fixed before deployment
    MEDIUM = "medium"         # Should be addressed
    LOW = "low"              # Nice to have
    INFO = "info"            # Informational


@dataclass
class ValidationIssue:
    """Represents a configuration validation issue"""
    key: str
    severity: ValidationSeverity
    message: str
    recommendation: Optional[str] = None
    current_value: Optional[str] = None
    expected_pattern: Optional[str] = None


class ConfigurationValidator:
    """Validates configuration for security and production readiness"""

    def __init__(self):
        self.issues: List[ValidationIssue] = []

    def validate_all(self, config: Dict[str, Any], environment: str = "development") -> List[ValidationIssue]:
        """Run all validation checks"""
        self.issues = []

        # Run all validation methods
        self._validate_secrets(config, environment)
        self._validate_urls(config, environment)
        self._validate_environment_settings(config, environment)
        self._validate_security_settings(config, environment)
        self._validate_external_services(config, environment)
        self._validate_monitoring_config(config, environment)
        self._validate_cache_config(config, environment)
        self._validate_database_config(config, environment)
        self._validate_alert_config(config, environment)

        return self.issues

    def _add_issue(self, key: str, severity: ValidationSeverity, message: str,
                   recommendation: Optional[str] = None, current_value: Optional[str] = None):
        """Add a validation issue"""
        issue = ValidationIssue(
            key=key,
            severity=severity,
            message=message,
            recommendation=recommendation,
            current_value=current_value
        )
        self.issues.append(issue)
        logger.log(
            logging.CRITICAL if severity == ValidationSeverity.CRITICAL else
            logging.ERROR if severity == ValidationSeverity.HIGH else
            logging.WARNING,
            f"Config validation [{severity.value}] {key}: {message}"
        )

    def _validate_secrets(self, config: Dict[str, Any], environment: str):
        """Validate secret configuration"""
        secret_keys = [
            'API_KEY_ENCRYPTION_KEY',
            'JWT_SECRET_KEY',
            'API_KEY',
            'CRM_API_KEY',
            'PLATFORM_API_KEY',
        ]

        for key in secret_keys:
            value = config.get(key, '')
            if not value:
                severity = ValidationSeverity.CRITICAL if environment == 'production' else ValidationSeverity.HIGH
                self._add_issue(
                    key, severity,
                    f"Required secret '{key}' is not configured",
                    f"Set {key} via secrets manager or environment variable"
                )
                continue

            # Check for development placeholders
            dev_patterns = [
                'dev-', 'development', 'test-', 'replace-in-production',
                'your-', 'example', 'localhost', 'changeme'
            ]

            for pattern in dev_patterns:
                if pattern in value.lower():
                    severity = ValidationSeverity.CRITICAL if environment == 'production' else ValidationSeverity.HIGH
                    self._add_issue(
                        key, severity,
                        f"Secret contains development placeholder: '{pattern}'",
                        f"Replace {key} with production-grade secret",
                        current_value=value[:10] + "..." if len(value) > 10 else value
                    )
                    break

            # Check secret strength
            if key in ['API_KEY_ENCRYPTION_KEY', 'JWT_SECRET_KEY']:
                if len(value) < 32:
                    severity = ValidationSeverity.CRITICAL if environment == 'production' else ValidationSeverity.HIGH
                    self._add_issue(
                        key, severity,
                        f"Secret is too short ({len(value)} characters, minimum 32)",
                        f"Generate a stronger {key} with at least 32 random characters"
                    )

                # Check entropy (basic check)
                if len(set(value)) < 8:  # Too few unique characters
                    self._add_issue(
                        key, ValidationSeverity.MEDIUM,
                        "Secret appears to have low entropy",
                        f"Generate a more random {key} with higher entropy"
                    )

            # Check for common weak patterns
            if key == 'API_KEY':
                if len(value) < 16:
                    self._add_issue(
                        key, ValidationSeverity.HIGH,
                        f"API key is too short ({len(value)} characters)",
                        "Generate a longer API key (minimum 16 characters)"
                    )

    def _validate_urls(self, config: Dict[str, Any], environment: str):
        """Validate URL configuration"""
        url_keys = [
            ('CRM_BASE_URL', True),
            ('PLATFORM_BASE_URL', True),
            ('AZURE_KEY_VAULT_URL', False),
            ('CACHE_REDIS_URL', False),
            ('DATABASE_URL', False),
        ]

        for key, required in url_keys:
            value = config.get(key, '')

            if not value:
                if required:
                    severity = ValidationSeverity.CRITICAL if environment == 'production' else ValidationSeverity.HIGH
                    self._add_issue(
                        key, severity,
                        f"Required URL '{key}' is not configured",
                        f"Set {key} to the appropriate service endpoint"
                    )
                continue

            # Parse URL
            try:
                parsed = urlparse(value)
            except Exception as e:
                self._add_issue(
                    key, ValidationSeverity.HIGH,
                    f"Invalid URL format: {e}",
                    f"Ensure {key} is a valid URL",
                    current_value=value
                )
                continue

            # Check HTTPS requirement for production
            if environment == 'production' and key in ['CRM_BASE_URL', 'PLATFORM_BASE_URL']:
                if parsed.scheme != 'https':
                    self._add_issue(
                        key, ValidationSeverity.CRITICAL,
                        f"Production URL must use HTTPS, found: {parsed.scheme}",
                        f"Update {key} to use HTTPS protocol",
                        current_value=value
                    )

            # Check for localhost/development URLs in production
            if environment == 'production':
                dev_hosts = ['localhost', '127.0.0.1', '0.0.0.0', 'host.docker.internal']
                if parsed.hostname in dev_hosts:
                    self._add_issue(
                        key, ValidationSeverity.CRITICAL,
                        f"Production URL points to development host: {parsed.hostname}",
                        f"Update {key} to point to production endpoint",
                        current_value=value
                    )

            # Check for missing hostname
            if not parsed.hostname:
                self._add_issue(
                    key, ValidationSeverity.HIGH,
                    "URL missing hostname",
                    f"Ensure {key} includes a valid hostname",
                    current_value=value
                )

    def _validate_environment_settings(self, config: Dict[str, Any], environment: str):
        """Validate environment-specific settings"""
        env_value = config.get('ENVIRONMENT', 'development')

        if env_value != environment:
            self._add_issue(
                'ENVIRONMENT', ValidationSeverity.MEDIUM,
                f"Environment mismatch: config says '{env_value}', runtime is '{environment}'",
                f"Ensure ENVIRONMENT variable matches deployment target"
            )

        # Production-specific validations
        if environment == 'production':
            prod_settings = {
                'DEBUG': (False, "DEBUG must be disabled in production"),
                'DRY_RUN_MODE': (False, "DRY_RUN_MODE must be disabled in production"),
                'USE_MOCK_SERVICES': (False, "USE_MOCK_SERVICES must be disabled in production"),
            }

            for key, (expected, message) in prod_settings.items():
                value = config.get(key, False)
                if isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes', 'on')

                if value != expected:
                    self._add_issue(
                        key, ValidationSeverity.CRITICAL,
                        message,
                        f"Set {key}={expected}",
                        current_value=str(value)
                    )

    def _validate_security_settings(self, config: Dict[str, Any], environment: str):
        """Validate security configuration"""
        if environment == 'production':
            # Check HTTPS enforcement
            if not config.get('_REQUIRE_HTTPS', True):
                self._add_issue(
                    '_REQUIRE_HTTPS', ValidationSeverity.CRITICAL,
                    "HTTPS enforcement is disabled in production",
                    "Enable HTTPS enforcement for production deployment"
                )

            # Check secure cookies
            if not config.get('_REQUIRE_SECURE_COOKIES', True):
                self._add_issue(
                    '_REQUIRE_SECURE_COOKIES', ValidationSeverity.HIGH,
                    "Secure cookies are disabled in production",
                    "Enable secure cookie settings for production"
                )

        # Check CORS settings
        cors_origins = config.get('CORS_ORIGINS', '')
        if cors_origins == '*' and environment == 'production':
            self._add_issue(
                'CORS_ORIGINS', ValidationSeverity.HIGH,
                "CORS is configured to allow all origins in production",
                "Restrict CORS origins to specific domains for production"
            )

    def _validate_service_endpoints(self, config: Dict[str, Any], environment: str):
        """Validate external service endpoint configuration"""
        # CRM service validation
        crm_url = config.get('CRM_BASE_URL') or config.get('external_services', {}).get('CRM_BASE_URL')
        crm_key = config.get('CRM_API_KEY') or config.get('external_services', {}).get('CRM_API_KEY')

        if not crm_url:
            self._add_issue(
                'CRM_BASE_URL', ValidationSeverity.CRITICAL,
                "CRM_BASE_URL is required",
                "Set CRM_BASE_URL to the production CRM service endpoint"
            )
        else:
            if environment == 'production' and not crm_url.startswith('https://'):
                self._add_issue(
                    'CRM_BASE_URL', ValidationSeverity.CRITICAL,
                    "CRM_BASE_URL must use HTTPS in production",
                    "Update CRM_BASE_URL to use HTTPS protocol"
                )

            if 'localhost' in crm_url and environment == 'production':
                self._add_issue(
                    'CRM_BASE_URL', ValidationSeverity.CRITICAL,
                    "CRM_BASE_URL cannot be localhost in production",
                    "Update CRM_BASE_URL to production service endpoint"
                )

        if not crm_key:
            self._add_issue(
                'CRM_API_KEY', ValidationSeverity.CRITICAL,
                "CRM_API_KEY is required",
                "Set CRM_API_KEY via secrets management"
            )
        elif environment == 'production':
            if len(crm_key) < 16:
                self._add_issue(
                    'CRM_API_KEY', ValidationSeverity.HIGH,
                    "CRM_API_KEY should be at least 16 characters in production",
                    "Use a stronger CRM API key for production"
                )

            if any(pattern in crm_key.lower() for pattern in ['dev', 'test', 'mock', 'example']):
                self._add_issue(
                    'CRM_API_KEY', ValidationSeverity.CRITICAL,
                    "CRM_API_KEY appears to be a development placeholder",
                    "Replace with production CRM API key"
                )

        # Platform service validation
        platform_url = config.get('PLATFORM_BASE_URL') or config.get('external_services', {}).get('PLATFORM_BASE_URL')
        platform_key = config.get('PLATFORM_API_KEY') or config.get('external_services', {}).get('PLATFORM_API_KEY')

        if not platform_url:
            self._add_issue(
                'PLATFORM_BASE_URL', ValidationSeverity.CRITICAL,
                "PLATFORM_BASE_URL is required",
                "Set PLATFORM_BASE_URL to the production platform service endpoint"
            )
        else:
            if environment == 'production' and not platform_url.startswith('https://'):
                self._add_issue(
                    'PLATFORM_BASE_URL', ValidationSeverity.CRITICAL,
                    "PLATFORM_BASE_URL must use HTTPS in production",
                    "Update PLATFORM_BASE_URL to use HTTPS protocol"
                )

            if 'localhost' in platform_url and environment == 'production':
                self._add_issue(
                    'PLATFORM_BASE_URL', ValidationSeverity.CRITICAL,
                    "PLATFORM_BASE_URL cannot be localhost in production",
                    "Update PLATFORM_BASE_URL to production service endpoint"
                )

        if not platform_key:
            self._add_issue(
                'PLATFORM_API_KEY', ValidationSeverity.CRITICAL,
                "PLATFORM_API_KEY is required",
                "Set PLATFORM_API_KEY via secrets management"
            )
        elif environment == 'production':
            if len(platform_key) < 16:
                self._add_issue(
                    'PLATFORM_API_KEY', ValidationSeverity.HIGH,
                    "PLATFORM_API_KEY should be at least 16 characters in production",
                    "Use a stronger platform API key for production"
                )

            if any(pattern in platform_key.lower() for pattern in ['dev', 'test', 'mock', 'example']):
                self._add_issue(
                    'PLATFORM_API_KEY', ValidationSeverity.CRITICAL,
                    "PLATFORM_API_KEY appears to be a development placeholder",
                    "Replace with production platform API key"
                )

    def _validate_external_services(self, config: Dict[str, Any], environment: str):
        """Validate external service configuration"""
        # Enhanced service endpoint validation
        self._validate_service_endpoints(config, environment)
        # Check timeout settings
        timeout_keys = [
            ('CRM_TIMEOUT', 30),
            ('PLATFORM_TIMEOUT', 30),
            ('DATABASE_TIMEOUT', 30),
        ]

        for key, default in timeout_keys:
            value = config.get(key, default)
            try:
                timeout = int(value)
                if timeout < 5:
                    self._add_issue(
                        key, ValidationSeverity.MEDIUM,
                        f"Timeout is very short ({timeout}s)",
                        f"Consider increasing {key} for production stability"
                    )
                elif timeout > 300:  # 5 minutes
                    self._add_issue(
                        key, ValidationSeverity.MEDIUM,
                        f"Timeout is very long ({timeout}s)",
                        f"Consider reducing {key} to avoid blocking operations"
                    )
            except ValueError:
                self._add_issue(
                    key, ValidationSeverity.HIGH,
                    f"Invalid timeout value: {value}",
                    f"Set {key} to a numeric value in seconds"
                )

        # Check retry settings
        retry_keys = ['CRM_MAX_RETRIES', 'PLATFORM_MAX_RETRIES', 'MAX_RETRIES']
        for key in retry_keys:
            value = config.get(key)
            if value is not None:
                try:
                    retries = int(value)
                    if retries < 1:
                        self._add_issue(
                            key, ValidationSeverity.MEDIUM,
                            f"Retry count is too low ({retries})",
                            f"Set {key} to at least 1 for resilience"
                        )
                    elif retries > 10:
                        self._add_issue(
                            key, ValidationSeverity.MEDIUM,
                            f"Retry count is very high ({retries})",
                            f"Consider reducing {key} to avoid excessive delays"
                        )
                except ValueError:
                    self._add_issue(
                        key, ValidationSeverity.HIGH,
                        f"Invalid retry value: {value}",
                        f"Set {key} to a numeric value"
                    )

    def _validate_monitoring_config(self, config: Dict[str, Any], environment: str):
        """Validate monitoring configuration"""
        if environment == 'production':
            # Ensure metrics are enabled
            if not config.get('ENABLE_METRICS', True):
                self._add_issue(
                    'ENABLE_METRICS', ValidationSeverity.HIGH,
                    "Metrics are disabled in production",
                    "Enable metrics for production monitoring"
                )

        # Check log level
        log_level = config.get('LOG_LEVEL', 'INFO').upper()
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

        if log_level not in valid_levels:
            self._add_issue(
                'LOG_LEVEL', ValidationSeverity.HIGH,
                f"Invalid log level: {log_level}",
                f"Set LOG_LEVEL to one of: {', '.join(valid_levels)}"
            )

        # Production log level recommendations
        if environment == 'production' and log_level == 'DEBUG':
            self._add_issue(
                'LOG_LEVEL', ValidationSeverity.MEDIUM,
                "DEBUG logging in production may impact performance",
                "Consider using INFO or WARNING level for production"
            )

    def _validate_cache_config(self, config: Dict[str, Any], environment: str):
        """Validate cache configuration"""
        if config.get('CACHE_REDIS_ENABLED', False):
            redis_url = config.get('CACHE_REDIS_URL')
            if not redis_url:
                self._add_issue(
                    'CACHE_REDIS_URL', ValidationSeverity.HIGH,
                    "Redis caching enabled but CACHE_REDIS_URL not configured",
                    "Set CACHE_REDIS_URL or disable Redis caching"
                )

        # Check cache TTL
        cache_ttl = config.get('CACHE_TTL')
        if cache_ttl is not None:
            try:
                ttl = int(cache_ttl)
                if ttl < 60 and environment == 'production':
                    self._add_issue(
                        'CACHE_TTL', ValidationSeverity.MEDIUM,
                        f"Cache TTL is very short ({ttl}s) for production",
                        "Consider longer cache TTL for production efficiency"
                    )
            except ValueError:
                self._add_issue(
                    'CACHE_TTL', ValidationSeverity.HIGH,
                    f"Invalid cache TTL value: {cache_ttl}",
                    "Set CACHE_TTL to a numeric value in seconds"
                )

    def _validate_database_config(self, config: Dict[str, Any], environment: str):
        """Validate database configuration if applicable"""
        db_url = config.get('DATABASE_URL')
        if db_url:
            try:
                parsed = urlparse(db_url)

                # Check SSL mode for production
                if environment == 'production':
                    ssl_mode = config.get('DATABASE_SSL_MODE', 'prefer')
                    if ssl_mode not in ['require', 'verify-ca', 'verify-full']:
                        self._add_issue(
                            'DATABASE_SSL_MODE', ValidationSeverity.HIGH,
                            f"Database SSL mode '{ssl_mode}' not secure for production",
                            "Set DATABASE_SSL_MODE to 'require' or stronger for production"
                        )

                # Check connection pool settings
                min_conn = config.get('DATABASE_MIN_CONNECTIONS', 5)
                max_conn = config.get('DATABASE_MAX_CONNECTIONS', 20)

                try:
                    min_conn = int(min_conn)
                    max_conn = int(max_conn)

                    if min_conn >= max_conn:
                        self._add_issue(
                            'DATABASE_MIN_CONNECTIONS', ValidationSeverity.HIGH,
                            f"Min connections ({min_conn}) >= max connections ({max_conn})",
                            "Ensure DATABASE_MIN_CONNECTIONS < DATABASE_MAX_CONNECTIONS"
                        )

                    if max_conn > 100:
                        self._add_issue(
                            'DATABASE_MAX_CONNECTIONS', ValidationSeverity.MEDIUM,
                            f"Very high max connections ({max_conn})",
                            "Consider if DATABASE_MAX_CONNECTIONS is appropriate for your database"
                        )

                except ValueError:
                    self._add_issue(
                        'DATABASE_CONNECTIONS', ValidationSeverity.HIGH,
                        "Invalid database connection pool configuration",
                        "Ensure DATABASE_MIN_CONNECTIONS and DATABASE_MAX_CONNECTIONS are numeric"
                    )

            except Exception as e:
                self._add_issue(
                    'DATABASE_URL', ValidationSeverity.HIGH,
                    f"Invalid database URL: {e}",
                    "Check DATABASE_URL format"
                )

    def _validate_alert_config(self, config: Dict[str, Any], environment: str):
        """Validate alerting configuration"""
        if environment == 'production':
            # Check if any alerting is configured
            email_enabled = config.get('ALERT_EMAIL_ENABLED', False)
            slack_enabled = config.get('ALERT_SLACK_ENABLED', False)

            if not email_enabled and not slack_enabled:
                self._add_issue(
                    'ALERTING', ValidationSeverity.HIGH,
                    "No alerting configured for production",
                    "Enable email or Slack alerts for production monitoring"
                )

        # Validate email alerting
        if config.get('ALERT_EMAIL_ENABLED', False):
            email_recipients = config.get('ALERT_EMAIL_RECIPIENTS', [])
            if isinstance(email_recipients, str):
                try:
                    email_recipients = json.loads(email_recipients)
                except json.JSONDecodeError:
                    email_recipients = []

            if not email_recipients:
                self._add_issue(
                    'ALERT_EMAIL_RECIPIENTS', ValidationSeverity.HIGH,
                    "Email alerting enabled but no recipients configured",
                    "Set ALERT_EMAIL_RECIPIENTS to list of email addresses"
                )

        # Validate Slack alerting
        if config.get('ALERT_SLACK_ENABLED', False):
            webhook_url = config.get('ALERT_SLACK_WEBHOOK_URL')
            if not webhook_url:
                self._add_issue(
                    'ALERT_SLACK_WEBHOOK_URL', ValidationSeverity.HIGH,
                    "Slack alerting enabled but no webhook URL configured",
                    "Set ALERT_SLACK_WEBHOOK_URL to your Slack webhook"
                )
            elif not webhook_url.startswith('https://hooks.slack.com/'):
                self._add_issue(
                    'ALERT_SLACK_WEBHOOK_URL', ValidationSeverity.MEDIUM,
                    "Slack webhook URL format may be invalid",
                    "Ensure ALERT_SLACK_WEBHOOK_URL is a valid Slack webhook"
                )

    def generate_report(self, issues: List[ValidationIssue]) -> str:
        """Generate a human-readable validation report"""
        if not issues:
            return "✅ Configuration validation passed with no issues!"

        report = ["🔍 Configuration Validation Report", "=" * 40, ""]

        # Group by severity
        by_severity = {}
        for issue in issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)

        # Report by severity
        severity_icons = {
            ValidationSeverity.CRITICAL: "🚨",
            ValidationSeverity.HIGH: "⚠️",
            ValidationSeverity.MEDIUM: "⚡",
            ValidationSeverity.LOW: "💡",
            ValidationSeverity.INFO: "ℹ️"
        }

        for severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH,
                        ValidationSeverity.MEDIUM, ValidationSeverity.LOW, ValidationSeverity.INFO]:
            if severity in by_severity:
                icon = severity_icons[severity]
                report.append(f"{icon} {severity.value.upper()} Issues ({len(by_severity[severity])})")
                report.append("-" * 30)

                for issue in by_severity[severity]:
                    report.append(f"• {issue.key}: {issue.message}")
                    if issue.recommendation:
                        report.append(f"  → {issue.recommendation}")
                    if issue.current_value:
                        report.append(f"  Current: {issue.current_value}")
                    report.append("")

                report.append("")

        # Summary
        critical_count = len(by_severity.get(ValidationSeverity.CRITICAL, []))
        high_count = len(by_severity.get(ValidationSeverity.HIGH, []))

        report.append("📊 Summary")
        report.append("-" * 20)
        report.append(f"Total issues: {len(issues)}")
        report.append(f"Critical: {critical_count}")
        report.append(f"High: {high_count}")

        if critical_count > 0:
            report.append("")
            report.append("❌ DEPLOYMENT BLOCKED: Critical issues must be resolved before production deployment")
        elif high_count > 0:
            report.append("")
            report.append("⚠️  WARNING: High-priority issues should be resolved before production deployment")
        else:
            report.append("")
            report.append("✅ No critical or high-priority issues found")

        return "\n".join(report)


def validate_configuration(config_dict: Dict[str, Any], environment: str = "development") -> Tuple[List[ValidationIssue], str]:
    """Validate configuration and return issues and report"""
    validator = ConfigurationValidator()
    issues = validator.validate_all(config_dict, environment)
    report = validator.generate_report(issues)
    return issues, report


def is_production_ready(issues: List[ValidationIssue]) -> bool:
    """Check if configuration is ready for production deployment"""
    critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
    return len(critical_issues) == 0