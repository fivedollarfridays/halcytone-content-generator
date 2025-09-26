"""
Secrets Management for Halcytone Content Generator
Supports Azure Key Vault, AWS Secrets Manager, and local development
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecretsProvider(str, Enum):
    """Supported secrets management providers"""
    AZURE_KEY_VAULT = "azure_key_vault"
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    ENVIRONMENT = "environment"
    LOCAL_FILE = "local_file"


@dataclass
class SecretReference:
    """Reference to a secret in a secrets management system"""
    key: str
    provider: SecretsProvider
    vault_name: Optional[str] = None
    region: Optional[str] = None
    default_value: Optional[str] = None
    required: bool = True


class BaseSecretsManager(ABC):
    """Base class for all secrets managers"""

    @abstractmethod
    async def get_secret(self, key: str, **kwargs) -> Optional[str]:
        """Retrieve a secret by key"""
        pass

    @abstractmethod
    async def get_secrets(self, keys: list[str], **kwargs) -> Dict[str, Optional[str]]:
        """Retrieve multiple secrets"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this secrets manager is available/configured"""
        pass


class EnvironmentSecretsManager(BaseSecretsManager):
    """Secrets manager that reads from environment variables"""

    async def get_secret(self, key: str, **kwargs) -> Optional[str]:
        """Get secret from environment variable"""
        return os.getenv(key)

    async def get_secrets(self, keys: list[str], **kwargs) -> Dict[str, Optional[str]]:
        """Get multiple secrets from environment variables"""
        return {key: os.getenv(key) for key in keys}

    def is_available(self) -> bool:
        """Environment variables are always available"""
        return True


class AzureKeyVaultSecretsManager(BaseSecretsManager):
    """Secrets manager for Azure Key Vault"""

    def __init__(self, vault_url: Optional[str] = None, credential=None):
        self.vault_url = vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        self.credential = credential
        self._client = None

    def _get_client(self):
        """Get Azure Key Vault client (lazy initialization)"""
        if self._client is None:
            try:
                from azure.keyvault.secrets import SecretClient
                from azure.identity import DefaultAzureCredential

                if not self.credential:
                    self.credential = DefaultAzureCredential()

                if not self.vault_url:
                    raise ValueError("Azure Key Vault URL not configured")

                self._client = SecretClient(vault_url=self.vault_url, credential=self.credential)
            except ImportError:
                logger.error("Azure SDK not installed. Install with: pip install azure-keyvault-secrets azure-identity")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Azure Key Vault client: {e}")
                raise

        return self._client

    async def get_secret(self, key: str, **kwargs) -> Optional[str]:
        """Get secret from Azure Key Vault"""
        try:
            client = self._get_client()
            secret = client.get_secret(key)
            return secret.value
        except Exception as e:
            logger.warning(f"Failed to retrieve secret '{key}' from Azure Key Vault: {e}")
            return None

    async def get_secrets(self, keys: list[str], **kwargs) -> Dict[str, Optional[str]]:
        """Get multiple secrets from Azure Key Vault"""
        results = {}
        for key in keys:
            results[key] = await self.get_secret(key)
        return results

    def is_available(self) -> bool:
        """Check if Azure Key Vault is configured and available"""
        try:
            return bool(self.vault_url) and bool(self._get_client())
        except Exception:
            return False


class AWSSecretsManager(BaseSecretsManager):
    """Secrets manager for AWS Secrets Manager"""

    def __init__(self, region_name: Optional[str] = None):
        self.region_name = region_name or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self._client = None

    def _get_client(self):
        """Get AWS Secrets Manager client (lazy initialization)"""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client('secretsmanager', region_name=self.region_name)
            except ImportError:
                logger.error("AWS SDK not installed. Install with: pip install boto3")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize AWS Secrets Manager client: {e}")
                raise

        return self._client

    async def get_secret(self, key: str, **kwargs) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            client = self._get_client()
            response = client.get_secret_value(SecretId=key)

            # Handle both string and JSON secrets
            secret_value = response.get('SecretString')
            if secret_value:
                try:
                    # Try to parse as JSON and extract specific key if provided
                    secret_data = json.loads(secret_value)
                    if isinstance(secret_data, dict):
                        # If a sub-key is specified (e.g., "secret-name/api-key")
                        if '/' in key:
                            _, sub_key = key.rsplit('/', 1)
                            return secret_data.get(sub_key)
                        # Return the first value if it's a simple key-value JSON
                        if len(secret_data) == 1:
                            return list(secret_data.values())[0]
                        return json.dumps(secret_data)
                    return secret_value
                except json.JSONDecodeError:
                    # Not JSON, return as string
                    return secret_value

            # Handle binary secrets
            binary_secret = response.get('SecretBinary')
            if binary_secret:
                return binary_secret.decode('utf-8')

            return None

        except Exception as e:
            logger.warning(f"Failed to retrieve secret '{key}' from AWS Secrets Manager: {e}")
            return None

    async def get_secrets(self, keys: list[str], **kwargs) -> Dict[str, Optional[str]]:
        """Get multiple secrets from AWS Secrets Manager"""
        results = {}
        for key in keys:
            results[key] = await self.get_secret(key)
        return results

    def is_available(self) -> bool:
        """Check if AWS Secrets Manager is configured and available"""
        try:
            client = self._get_client()
            # Test with a simple list operation
            client.list_secrets(MaxResults=1)
            return True
        except Exception:
            return False


class LocalFileSecretsManager(BaseSecretsManager):
    """Secrets manager that reads from local JSON files (development only)"""

    def __init__(self, secrets_file: str = "secrets.json"):
        self.secrets_file = secrets_file
        self._secrets_cache = None

    def _load_secrets(self) -> Dict[str, str]:
        """Load secrets from local file"""
        if self._secrets_cache is None:
            try:
                if os.path.exists(self.secrets_file):
                    with open(self.secrets_file, 'r') as f:
                        self._secrets_cache = json.load(f)
                else:
                    logger.warning(f"Secrets file {self.secrets_file} not found")
                    self._secrets_cache = {}
            except Exception as e:
                logger.error(f"Failed to load secrets from {self.secrets_file}: {e}")
                self._secrets_cache = {}

        return self._secrets_cache

    async def get_secret(self, key: str, **kwargs) -> Optional[str]:
        """Get secret from local file"""
        secrets = self._load_secrets()
        return secrets.get(key)

    async def get_secrets(self, keys: list[str], **kwargs) -> Dict[str, Optional[str]]:
        """Get multiple secrets from local file"""
        secrets = self._load_secrets()
        return {key: secrets.get(key) for key in keys}

    def is_available(self) -> bool:
        """Check if local secrets file exists"""
        return os.path.exists(self.secrets_file)


class SecretsManagerFactory:
    """Factory for creating appropriate secrets managers"""

    @staticmethod
    def create_manager(provider: SecretsProvider, **kwargs) -> BaseSecretsManager:
        """Create a secrets manager based on provider type"""
        if provider == SecretsProvider.AZURE_KEY_VAULT:
            return AzureKeyVaultSecretsManager(**kwargs)
        elif provider == SecretsProvider.AWS_SECRETS_MANAGER:
            return AWSSecretsManager(**kwargs)
        elif provider == SecretsProvider.ENVIRONMENT:
            return EnvironmentSecretsManager()
        elif provider == SecretsProvider.LOCAL_FILE:
            return LocalFileSecretsManager(**kwargs)
        else:
            raise ValueError(f"Unknown secrets provider: {provider}")

    @staticmethod
    def detect_available_provider() -> SecretsProvider:
        """Detect which secrets provider is available in the current environment"""
        # Check for Azure Key Vault configuration
        if os.getenv("AZURE_KEY_VAULT_URL"):
            try:
                manager = AzureKeyVaultSecretsManager()
                if manager.is_available():
                    return SecretsProvider.AZURE_KEY_VAULT
            except Exception:
                pass

        # Check for AWS Secrets Manager configuration
        if os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION"):
            try:
                manager = AWSSecretsManager()
                if manager.is_available():
                    return SecretsProvider.AWS_SECRETS_MANAGER
            except Exception:
                pass

        # Check for local secrets file (development)
        if os.path.exists("secrets.json"):
            return SecretsProvider.LOCAL_FILE

        # Fall back to environment variables
        return SecretsProvider.ENVIRONMENT


class UnifiedSecretsManager:
    """Unified interface for managing secrets across multiple providers"""

    def __init__(self, primary_provider: Optional[SecretsProvider] = None, fallback_to_env: bool = True):
        self.fallback_to_env = fallback_to_env
        self.providers = {}

        # Set up primary provider
        if primary_provider:
            self.primary_provider = primary_provider
        else:
            self.primary_provider = SecretsManagerFactory.detect_available_provider()

        # Initialize managers
        self._init_managers()

    def _init_managers(self):
        """Initialize secrets managers for available providers"""
        try:
            self.providers[self.primary_provider] = SecretsManagerFactory.create_manager(
                self.primary_provider
            )
        except Exception as e:
            logger.error(f"Failed to initialize primary secrets provider {self.primary_provider}: {e}")

        # Always have environment fallback
        if self.fallback_to_env and self.primary_provider != SecretsProvider.ENVIRONMENT:
            self.providers[SecretsProvider.ENVIRONMENT] = EnvironmentSecretsManager()

    async def get_secret(self, secret_ref: Union[str, SecretReference]) -> Optional[str]:
        """Get a secret, trying providers in order"""
        if isinstance(secret_ref, str):
            secret_ref = SecretReference(key=secret_ref, provider=self.primary_provider)

        # Try the specified provider first
        if secret_ref.provider in self.providers:
            try:
                value = await self.providers[secret_ref.provider].get_secret(
                    secret_ref.key,
                    vault_name=secret_ref.vault_name,
                    region=secret_ref.region
                )
                if value:
                    return value
            except Exception as e:
                logger.warning(f"Failed to get secret from {secret_ref.provider}: {e}")

        # Fall back to environment if enabled and different from primary
        if (self.fallback_to_env and
            secret_ref.provider != SecretsProvider.ENVIRONMENT and
            SecretsProvider.ENVIRONMENT in self.providers):
            try:
                value = await self.providers[SecretsProvider.ENVIRONMENT].get_secret(secret_ref.key)
                if value:
                    logger.info(f"Retrieved secret '{secret_ref.key}' from environment fallback")
                    return value
            except Exception as e:
                logger.warning(f"Environment fallback failed for secret '{secret_ref.key}': {e}")

        # Use default value if provided
        if secret_ref.default_value is not None:
            logger.info(f"Using default value for secret '{secret_ref.key}'")
            return secret_ref.default_value

        # Log error if secret is required
        if secret_ref.required:
            logger.error(f"Required secret '{secret_ref.key}' not found in any provider")

        return None

    async def get_secrets_batch(self, secret_refs: list[SecretReference]) -> Dict[str, Optional[str]]:
        """Get multiple secrets efficiently"""
        results = {}

        # Group by provider for batch operations
        provider_groups = {}
        for ref in secret_refs:
            if ref.provider not in provider_groups:
                provider_groups[ref.provider] = []
            provider_groups[ref.provider].append(ref)

        # Process each provider group
        for provider, refs in provider_groups.items():
            if provider in self.providers:
                keys = [ref.key for ref in refs]
                try:
                    provider_results = await self.providers[provider].get_secrets(keys)
                    for ref in refs:
                        if ref.key in provider_results and provider_results[ref.key]:
                            results[ref.key] = provider_results[ref.key]
                        elif self.fallback_to_env and provider != SecretsProvider.ENVIRONMENT:
                            # Individual environment fallback
                            env_value = await self.providers[SecretsProvider.ENVIRONMENT].get_secret(ref.key)
                            results[ref.key] = env_value or ref.default_value
                        else:
                            results[ref.key] = ref.default_value
                except Exception as e:
                    logger.warning(f"Batch secret retrieval failed for provider {provider}: {e}")
                    # Fall back to individual secret retrieval
                    for ref in refs:
                        results[ref.key] = await self.get_secret(ref)

        return results


# Global secrets manager instance
_secrets_manager: Optional[UnifiedSecretsManager] = None


def get_secrets_manager(
    provider: Optional[SecretsProvider] = None,
    fallback_to_env: bool = True
) -> UnifiedSecretsManager:
    """Get the global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = UnifiedSecretsManager(provider, fallback_to_env)
    return _secrets_manager


def reset_secrets_manager():
    """Reset the global secrets manager (for testing)"""
    global _secrets_manager
    _secrets_manager = None