#!/usr/bin/env python3
"""
Configuration Management CLI Tool
Validates configuration, manages secrets, and ensures production readiness
"""

import os
import sys
import json
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.halcytone_content_generator.config.enhanced_config import (
    ConfigurationManager,
    get_production_settings
)
from src.halcytone_content_generator.config.validation import (
    validate_configuration,
    is_production_ready,
    ValidationSeverity
)
from src.halcytone_content_generator.config.secrets_manager import (
    get_secrets_manager,
    SecretsProvider,
    SecretReference
)


class ConfigManagerCLI:
    """Command-line interface for configuration management"""

    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def validate_config(self, environment: str, config_file: str = None) -> int:
        """Validate configuration for specified environment"""
        print(f"🔍 Validating configuration for environment: {environment}")
        print()

        try:
            # Load configuration
            if config_file:
                # Load from specific file
                config_data = self._load_config_file(config_file)
            else:
                # Load using configuration manager
                manager = ConfigurationManager(environment)
                settings = await manager.load_settings()
                config_data = settings.dict()

            # Validate configuration
            issues, report = validate_configuration(config_data, environment)

            # Print report
            print(report)

            # Return appropriate exit code
            critical_count = len([i for i in issues if i.severity == ValidationSeverity.CRITICAL])
            if critical_count > 0:
                return 1  # Critical issues found
            else:
                return 0  # No critical issues

        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            print(f"❌ Configuration validation failed: {e}")
            return 2

    def _load_config_file(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file"""
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        if config_file.endswith('.json'):
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            # Load .env file
            from dotenv import dotenv_values
            return dotenv_values(config_file)

    async def check_secrets(self, provider: str = None) -> int:
        """Check secrets availability and configuration"""
        print("🔐 Checking secrets configuration...")
        print()

        try:
            # Initialize secrets manager
            if provider:
                provider_enum = SecretsProvider(provider)
                secrets_manager = get_secrets_manager(provider_enum)
            else:
                secrets_manager = get_secrets_manager()

            print(f"Using secrets provider: {secrets_manager.primary_provider.value}")
            print()

            # Test secret references
            test_secrets = [
                SecretReference("API_KEY", secrets_manager.primary_provider, required=False),
                SecretReference("CRM_API_KEY", secrets_manager.primary_provider, required=False),
                SecretReference("PLATFORM_API_KEY", secrets_manager.primary_provider, required=False),
                SecretReference("OPENAI_API_KEY", secrets_manager.primary_provider, required=False),
            ]

            # Check each secret
            all_available = True
            for secret_ref in test_secrets:
                value = await secrets_manager.get_secret(secret_ref)
                if value:
                    print(f"✅ {secret_ref.key}: Available")
                else:
                    print(f"❌ {secret_ref.key}: Not found")
                    all_available = False

            print()
            if all_available:
                print("✅ All test secrets are available")
                return 0
            else:
                print("⚠️  Some secrets are missing")
                return 1

        except Exception as e:
            self.logger.error(f"Secrets check failed: {e}")
            print(f"❌ Secrets check failed: {e}")
            return 2

    async def generate_production_template(self, output_file: str = None) -> int:
        """Generate production configuration template"""
        print("📝 Generating production configuration template...")

        try:
            # Load current configuration to understand structure
            manager = ConfigurationManager('development')
            dev_settings = await manager.load_settings()

            # Generate production template
            template_content = self._create_production_template(dev_settings.dict())

            # Write to file
            if not output_file:
                output_file = ".env.production.generated"

            with open(output_file, 'w') as f:
                f.write(template_content)

            print(f"✅ Production template generated: {output_file}")
            print()
            print("Next steps:")
            print("1. Review the generated template")
            print("2. Replace placeholder values with actual production credentials")
            print("3. Store secrets in your secrets management system")
            print("4. Validate the configuration with: python scripts/config_manager.py validate production")

            return 0

        except Exception as e:
            self.logger.error(f"Template generation failed: {e}")
            print(f"❌ Template generation failed: {e}")
            return 2

    def _create_production_template(self, dev_config: Dict[str, Any]) -> str:
        """Create production configuration template from development config"""
        template_lines = [
            "# Production Configuration Template",
            "# Generated from development configuration",
            "# Replace ALL placeholder values with actual production credentials",
            "",
            "# CRITICAL: This file contains sensitive configuration",
            "# - Never commit this file with real values",
            "# - Use secrets management for sensitive values",
            "# - Validate configuration before deployment",
            "",
        ]

        # Environment settings
        template_lines.extend([
            "# Environment Configuration",
            "ENVIRONMENT=production",
            "DEBUG=false",
            "LOG_LEVEL=WARNING",
            "",
        ])

        # Secrets with placeholders
        secrets_section = [
            "# Secrets Configuration (REPLACE WITH ACTUAL VALUES)",
            "API_KEY_ENCRYPTION_KEY=${PRODUCTION_API_KEY_ENCRYPTION_KEY}",
            "JWT_SECRET_KEY=${PRODUCTION_JWT_SECRET_KEY}",
            "API_KEY=${PRODUCTION_API_KEY}",
            "",
            "# External Service Credentials",
            "CRM_API_KEY=${PRODUCTION_CRM_API_KEY}",
            "PLATFORM_API_KEY=${PRODUCTION_PLATFORM_API_KEY}",
            "",
            "# Optional Service Credentials",
            "OPENAI_API_KEY=${PRODUCTION_OPENAI_API_KEY}",
            "GOOGLE_CREDENTIALS_JSON=${PRODUCTION_GOOGLE_CREDENTIALS_JSON}",
            "",
        ]
        template_lines.extend(secrets_section)

        # URLs with production placeholders
        urls_section = [
            "# Service URLs (REPLACE WITH PRODUCTION ENDPOINTS)",
            "CRM_BASE_URL=${PRODUCTION_CRM_BASE_URL}",
            "PLATFORM_BASE_URL=${PRODUCTION_PLATFORM_BASE_URL}",
            "",
        ]
        template_lines.extend(urls_section)

        # Production-optimized settings
        prod_settings = [
            "# Production-Optimized Settings",
            "DRY_RUN_MODE=false",
            "USE_MOCK_SERVICES=false",
            "ENABLE_METRICS=true",
            "CACHE_REDIS_ENABLED=true",
            "CACHE_REDIS_URL=${PRODUCTION_REDIS_URL}",
            "",
            "# Production Security Settings",
            "_REQUIRE_HTTPS=true",
            "_REQUIRE_SSL_VERIFICATION=true",
            "_REQUIRE_SECURE_COOKIES=true",
            "",
        ]
        template_lines.extend(prod_settings)

        # Monitoring and alerting
        monitoring_section = [
            "# Production Monitoring",
            "ALERT_EMAIL_ENABLED=true",
            "ALERT_EMAIL_RECIPIENTS=${PRODUCTION_ALERT_EMAILS}",
            "ALERT_SLACK_ENABLED=true",
            "ALERT_SLACK_WEBHOOK_URL=${PRODUCTION_SLACK_WEBHOOK}",
            "",
        ]
        template_lines.extend(monitoring_section)

        return "\n".join(template_lines)

    async def test_production_readiness(self, environment: str = "production") -> int:
        """Test if configuration is ready for production deployment"""
        print(f"🚀 Testing production readiness for environment: {environment}")
        print()

        try:
            # Load and validate configuration
            manager = ConfigurationManager(environment)
            settings = await manager.load_settings()

            # Run comprehensive validation
            config_data = settings.dict()
            issues, report = validate_configuration(config_data, environment)

            # Print validation report
            print(report)
            print()

            # Check production readiness
            if is_production_ready(issues):
                print("🎉 PRODUCTION READY: Configuration passed all critical checks!")

                # Additional production readiness checks
                production_issues = manager.validate_production_readiness(settings)
                if production_issues:
                    print()
                    print("⚠️  Additional production considerations:")
                    for issue in production_issues:
                        print(f"  • {issue}")
                    print()

                return 0
            else:
                print("❌ NOT PRODUCTION READY: Critical issues must be resolved")
                return 1

        except Exception as e:
            self.logger.error(f"Production readiness test failed: {e}")
            print(f"❌ Production readiness test failed: {e}")
            return 2

    def print_help(self):
        """Print detailed help information"""
        help_text = """
🔧 Configuration Manager - Halcytone Content Generator

This tool helps manage configuration, validate settings, and ensure production readiness.

COMMANDS:

  validate <environment> [--config-file FILE]
    Validate configuration for specified environment
    Environment: development, staging, production

  check-secrets [--provider PROVIDER]
    Check secrets availability and configuration
    Provider: azure_key_vault, aws_secrets_manager, environment, local_file

  generate-template [--output FILE]
    Generate production configuration template

  test-production [--environment ENV]
    Test production readiness (comprehensive check)

  help
    Show this help message

EXAMPLES:

  # Validate development configuration
  python scripts/config_manager.py validate development

  # Validate production configuration from specific file
  python scripts/config_manager.py validate production --config-file .env.production

  # Check if secrets are available via Azure Key Vault
  python scripts/config_manager.py check-secrets --provider azure_key_vault

  # Generate production template
  python scripts/config_manager.py generate-template --output .env.production.template

  # Test production readiness
  python scripts/config_manager.py test-production

SECRETS MANAGEMENT:

The tool supports multiple secrets providers:
  • Azure Key Vault (recommended for Azure deployments)
  • AWS Secrets Manager (recommended for AWS deployments)
  • Environment variables (for development/simple deployments)
  • Local file (development only)

Configuration is automatically detected based on available credentials and settings.

VALIDATION LEVELS:

  🚨 CRITICAL - Must be fixed before production deployment
  ⚠️  HIGH     - Should be fixed before production deployment
  ⚡ MEDIUM   - Should be addressed
  💡 LOW      - Nice to have
  ℹ️  INFO     - Informational

For more information, see docs/production-configuration.md
        """
        print(help_text)

    def run(self, args):
        """Run CLI command"""
        if len(args) < 1 or args[0] in ['help', '--help', '-h']:
            self.print_help()
            return 0

        command = args[0]

        if command == 'validate':
            if len(args) < 2:
                print("❌ Error: Environment required for validate command")
                return 1

            environment = args[1]
            config_file = None

            # Parse additional arguments
            i = 2
            while i < len(args):
                if args[i] == '--config-file' and i + 1 < len(args):
                    config_file = args[i + 1]
                    i += 2
                else:
                    i += 1

            return asyncio.run(self.validate_config(environment, config_file))

        elif command == 'check-secrets':
            provider = None

            # Parse arguments
            i = 1
            while i < len(args):
                if args[i] == '--provider' and i + 1 < len(args):
                    provider = args[i + 1]
                    i += 2
                else:
                    i += 1

            return asyncio.run(self.check_secrets(provider))

        elif command == 'generate-template':
            output_file = None

            # Parse arguments
            i = 1
            while i < len(args):
                if args[i] == '--output' and i + 1 < len(args):
                    output_file = args[i + 1]
                    i += 2
                else:
                    i += 1

            return asyncio.run(self.generate_production_template(output_file))

        elif command == 'test-production':
            environment = 'production'

            # Parse arguments
            i = 1
            while i < len(args):
                if args[i] == '--environment' and i + 1 < len(args):
                    environment = args[i + 1]
                    i += 2
                else:
                    i += 1

            return asyncio.run(self.test_production_readiness(environment))

        else:
            print(f"❌ Error: Unknown command '{command}'")
            print("Run 'python scripts/config_manager.py help' for available commands")
            return 1


def main():
    """Main entry point"""
    cli = ConfigManagerCLI()
    exit_code = cli.run(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()