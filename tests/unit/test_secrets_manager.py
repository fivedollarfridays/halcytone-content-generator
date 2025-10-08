"""
Unit tests for Secrets Manager.

Tests cover all secrets management providers including Azure Key Vault,
AWS Secrets Manager, environment variables, and local file storage.
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock, mock_open
from pathlib import Path

from halcytone_content_generator.config.secrets_manager import (
    SecretsProvider,
    SecretReference,
    BaseSecretsManager,
    EnvironmentSecretsManager,
    AzureKeyVaultSecretsManager,
    AWSSecretsManager,
    LocalFileSecretsManager,
    SecretsManagerFactory,
    get_secrets_manager
)


class TestSecretsProvider:
    """Test SecretsProvider enum."""

    def test_provider_values(self):
        """Test provider enum values."""
        assert SecretsProvider.AZURE_KEY_VAULT == "azure_key_vault"
        assert SecretsProvider.AWS_SECRETS_MANAGER == "aws_secrets_manager"
        assert SecretsProvider.ENVIRONMENT == "environment"
        assert SecretsProvider.LOCAL_FILE == "local_file"


class TestSecretReference:
    """Test SecretReference dataclass."""

    def test_create_basic_reference(self):
        """Test creating a basic secret reference."""
        ref = SecretReference(
            key="test_secret",
            provider=SecretsProvider.ENVIRONMENT
        )

        assert ref.key == "test_secret"
        assert ref.provider == SecretsProvider.ENVIRONMENT
        assert ref.vault_name is None
        assert ref.region is None
        assert ref.default_value is None
        assert ref.required is True

    def test_create_full_reference(self):
        """Test creating a secret reference with all fields."""
        ref = SecretReference(
            key="test_secret",
            provider=SecretsProvider.AZURE_KEY_VAULT,
            vault_name="my-vault",
            region="us-east-1",
            default_value="default",
            required=False
        )

        assert ref.key == "test_secret"
        assert ref.vault_name == "my-vault"
        assert ref.region == "us-east-1"
        assert ref.default_value == "default"
        assert ref.required is False


class TestEnvironmentSecretsManager:
    """Test EnvironmentSecretsManager."""

    @pytest.fixture
    def manager(self):
        """Create environment secrets manager."""
        return EnvironmentSecretsManager()

    @pytest.mark.asyncio
    async def test_get_secret_exists(self, manager):
        """Test getting an existing secret from environment."""
        with patch.dict(os.environ, {"TEST_SECRET": "test_value"}):
            result = await manager.get_secret("TEST_SECRET")
            assert result == "test_value"

    @pytest.mark.asyncio
    async def test_get_secret_not_exists(self, manager):
        """Test getting a non-existent secret."""
        with patch.dict(os.environ, {}, clear=True):
            result = await manager.get_secret("NONEXISTENT_SECRET")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_multiple_secrets(self, manager):
        """Test getting multiple secrets."""
        env_vars = {
            "SECRET_1": "value1",
            "SECRET_2": "value2",
            "SECRET_3": "value3"
        }

        with patch.dict(os.environ, env_vars):
            result = await manager.get_secrets(["SECRET_1", "SECRET_2", "SECRET_3"])

            assert result == {
                "SECRET_1": "value1",
                "SECRET_2": "value2",
                "SECRET_3": "value3"
            }

    @pytest.mark.asyncio
    async def test_get_mixed_secrets(self, manager):
        """Test getting mix of existing and non-existing secrets."""
        with patch.dict(os.environ, {"SECRET_1": "value1"}):
            result = await manager.get_secrets(["SECRET_1", "SECRET_2"])

            assert result["SECRET_1"] == "value1"
            assert result["SECRET_2"] is None

    def test_is_available(self, manager):
        """Test that environment manager is always available."""
        assert manager.is_available() is True


class TestAzureKeyVaultSecretsManager:
    """Test AzureKeyVaultSecretsManager."""

    @pytest.fixture
    def mock_azure_client(self):
        """Create mock Azure Key Vault client."""
        client = Mock()
        client.get_secret = Mock()
        return client

    @pytest.fixture
    def mock_credential(self):
        """Create mock Azure credential."""
        return Mock()

    def test_init_with_vault_url(self, mock_credential):
        """Test initialization with vault URL."""
        manager = AzureKeyVaultSecretsManager(
            vault_url="https://test-vault.vault.azure.net",
            credential=mock_credential
        )

        assert manager.vault_url == "https://test-vault.vault.azure.net"
        assert manager.credential == mock_credential
        assert manager._client is None

    def test_init_from_environment(self):
        """Test initialization from environment variable."""
        with patch.dict(os.environ, {"AZURE_KEY_VAULT_URL": "https://env-vault.vault.azure.net"}):
            manager = AzureKeyVaultSecretsManager()
            assert manager.vault_url == "https://env-vault.vault.azure.net"

    @patch('halcytone_content_generator.config.secrets_manager.SecretClient')
    @patch('halcytone_content_generator.config.secrets_manager.DefaultAzureCredential')
    def test_get_client_lazy_initialization(self, mock_credential_class, mock_client_class):
        """Test lazy initialization of Azure client."""
        mock_credential = Mock()
        mock_client = Mock()
        mock_credential_class.return_value = mock_credential
        mock_client_class.return_value = mock_client

        manager = AzureKeyVaultSecretsManager(vault_url="https://test-vault.vault.azure.net")

        # Client should not be initialized yet
        assert manager._client is None

        # Get client
        client = manager._get_client()

        # Client should now be initialized
        assert manager._client is not None
        assert client == mock_client
        mock_client_class.assert_called_once()

    def test_get_client_no_vault_url(self):
        """Test getting client without vault URL raises error."""
        manager = AzureKeyVaultSecretsManager()

        with pytest.raises(ValueError, match="Azure Key Vault URL not configured"):
            manager._get_client()

    @pytest.mark.asyncio
    @patch('halcytone_content_generator.config.secrets_manager.SecretClient')
    @patch('halcytone_content_generator.config.secrets_manager.DefaultAzureCredential')
    async def test_get_secret_success(self, mock_credential_class, mock_client_class):
        """Test successfully getting a secret from Azure Key Vault."""
        mock_secret = Mock()
        mock_secret.value = "secret_value"

        mock_client = Mock()
        mock_client.get_secret.return_value = mock_secret
        mock_client_class.return_value = mock_client

        manager = AzureKeyVaultSecretsManager(vault_url="https://test-vault.vault.azure.net")

        result = await manager.get_secret("test-secret")

        assert result == "secret_value"
        mock_client.get_secret.assert_called_once_with("test-secret")

    def test_is_available_with_url(self):
        """Test availability check with vault URL."""
        manager = AzureKeyVaultSecretsManager(vault_url="https://test-vault.vault.azure.net")
        assert manager.is_available() is True

    def test_is_available_without_url(self):
        """Test availability check without vault URL."""
        with patch.dict(os.environ, {}, clear=True):
            manager = AzureKeyVaultSecretsManager()
            assert manager.is_available() is False


class TestAWSSecretsManager:
    """Test AWSSecretsManager."""

    @pytest.fixture
    def mock_boto3_client(self):
        """Create mock boto3 client."""
        client = Mock()
        client.get_secret_value = Mock()
        return client

    def test_init_with_region(self):
        """Test initialization with region."""
        manager = AWSSecretsManager(region_name="us-west-2")
        assert manager.region_name == "us-west-2"
        assert manager._client is None

    def test_init_from_environment(self):
        """Test initialization from environment."""
        with patch.dict(os.environ, {"AWS_DEFAULT_REGION": "eu-west-1"}):
            manager = AWSSecretsManager()
            assert manager.region_name == "eu-west-1"

    @patch('boto3.client')
    def test_get_client_lazy_initialization(self, mock_boto3):
        """Test lazy initialization of AWS client."""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        manager = AWSSecretsManager(region_name="us-east-1")

        # Client should not be initialized yet
        assert manager._client is None

        # Get client
        client = manager._get_client()

        # Client should now be initialized
        assert manager._client is not None
        assert client == mock_client
        mock_boto3.assert_called_once_with('secretsmanager', region_name='us-east-1')

    @pytest.mark.asyncio
    @patch('boto3.client')
    async def test_get_secret_string_success(self, mock_boto3):
        """Test getting a string secret from AWS Secrets Manager."""
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            "SecretString": "my_secret_value"
        }
        mock_boto3.return_value = mock_client

        manager = AWSSecretsManager(region_name="us-east-1")

        result = await manager.get_secret("test-secret")

        assert result == "my_secret_value"
        mock_client.get_secret_value.assert_called_once_with(SecretId="test-secret")

    @pytest.mark.asyncio
    @patch('boto3.client')
    async def test_get_secret_binary_success(self, mock_boto3):
        """Test getting a binary secret from AWS Secrets Manager."""
        mock_client = Mock()
        mock_client.get_secret_value.return_value = {
            "SecretBinary": b"binary_secret"
        }
        mock_boto3.return_value = mock_client

        manager = AWSSecretsManager(region_name="us-east-1")

        result = await manager.get_secret("test-secret")

        assert result == "binary_secret"

    @pytest.mark.asyncio
    @patch('boto3.client')
    async def test_get_secret_not_found(self, mock_boto3):
        """Test handling of secret not found."""
        from botocore.exceptions import ClientError

        mock_client = Mock()
        error_response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_client.get_secret_value.side_effect = ClientError(error_response, "GetSecretValue")
        mock_boto3.return_value = mock_client

        manager = AWSSecretsManager(region_name="us-east-1")

        result = await manager.get_secret("nonexistent-secret")

        assert result is None

    def test_is_available(self):
        """Test availability check."""
        manager = AWSSecretsManager(region_name="us-east-1")
        assert manager.is_available() is True


class TestLocalFileSecretsManager:
    """Test LocalFileSecretsManager."""

    @pytest.fixture
    def temp_secrets_file(self, tmp_path):
        """Create temporary secrets file."""
        secrets_file = tmp_path / "secrets.json"
        secrets = {
            "secret1": "value1",
            "secret2": "value2",
            "secret3": "value3"
        }
        secrets_file.write_text(json.dumps(secrets))
        return str(secrets_file)

    def test_init_with_file_path(self, temp_secrets_file):
        """Test initialization with file path."""
        manager = LocalFileSecretsManager(file_path=temp_secrets_file)
        assert manager.file_path == temp_secrets_file

    @pytest.mark.asyncio
    async def test_get_secret_success(self, temp_secrets_file):
        """Test getting a secret from local file."""
        manager = LocalFileSecretsManager(file_path=temp_secrets_file)

        result = await manager.get_secret("secret1")

        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_secret_not_found(self, temp_secrets_file):
        """Test getting a non-existent secret."""
        manager = LocalFileSecretsManager(file_path=temp_secrets_file)

        result = await manager.get_secret("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_multiple_secrets(self, temp_secrets_file):
        """Test getting multiple secrets."""
        manager = LocalFileSecretsManager(file_path=temp_secrets_file)

        result = await manager.get_secrets(["secret1", "secret2", "nonexistent"])

        assert result == {
            "secret1": "value1",
            "secret2": "value2",
            "nonexistent": None
        }

    @pytest.mark.asyncio
    async def test_get_secret_file_not_found(self):
        """Test handling of missing file."""
        manager = LocalFileSecretsManager(file_path="/nonexistent/path/secrets.json")

        result = await manager.get_secret("secret1")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_secret_invalid_json(self, tmp_path):
        """Test handling of invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json")

        manager = LocalFileSecretsManager(file_path=str(bad_file))

        result = await manager.get_secret("secret1")

        assert result is None

    def test_is_available_exists(self, temp_secrets_file):
        """Test availability when file exists."""
        manager = LocalFileSecretsManager(file_path=temp_secrets_file)
        assert manager.is_available() is True

    def test_is_available_not_exists(self):
        """Test availability when file doesn't exist."""
        manager = LocalFileSecretsManager(file_path="/nonexistent/secrets.json")
        assert manager.is_available() is False


class TestSecretsManagerFactory:
    """Test SecretsManagerFactory."""

    def test_create_environment_manager(self):
        """Test creating environment secrets manager."""
        manager = SecretsManagerFactory.create(SecretsProvider.ENVIRONMENT)

        assert isinstance(manager, EnvironmentSecretsManager)

    def test_create_azure_manager(self):
        """Test creating Azure Key Vault manager."""
        manager = SecretsManagerFactory.create(
            SecretsProvider.AZURE_KEY_VAULT,
            vault_url="https://test-vault.vault.azure.net"
        )

        assert isinstance(manager, AzureKeyVaultSecretsManager)
        assert manager.vault_url == "https://test-vault.vault.azure.net"

    def test_create_aws_manager(self):
        """Test creating AWS Secrets Manager."""
        manager = SecretsManagerFactory.create(
            SecretsProvider.AWS_SECRETS_MANAGER,
            region_name="us-east-1"
        )

        assert isinstance(manager, AWSSecretsManager)
        assert manager.region_name == "us-east-1"

    def test_create_local_file_manager(self):
        """Test creating local file manager."""
        manager = SecretsManagerFactory.create(
            SecretsProvider.LOCAL_FILE,
            file_path="/path/to/secrets.json"
        )

        assert isinstance(manager, LocalFileSecretsManager)
        assert manager.file_path == "/path/to/secrets.json"

    def test_create_invalid_provider(self):
        """Test creating manager with invalid provider."""
        with pytest.raises(ValueError, match="Unknown secrets provider"):
            SecretsManagerFactory.create("invalid_provider")


class TestGetSecretsManager:
    """Test get_secrets_manager function."""

    def test_get_default_manager(self):
        """Test getting default secrets manager."""
        with patch.dict(os.environ, {}, clear=True):
            manager = get_secrets_manager()
            assert isinstance(manager, EnvironmentSecretsManager)

    def test_get_azure_manager_from_env(self):
        """Test getting Azure manager from environment."""
        with patch.dict(os.environ, {
            "SECRETS_PROVIDER": "azure_key_vault",
            "AZURE_KEY_VAULT_URL": "https://test-vault.vault.azure.net"
        }):
            manager = get_secrets_manager()
            assert isinstance(manager, AzureKeyVaultSecretsManager)

    def test_get_aws_manager_from_env(self):
        """Test getting AWS manager from environment."""
        with patch.dict(os.environ, {
            "SECRETS_PROVIDER": "aws_secrets_manager",
            "AWS_DEFAULT_REGION": "us-east-1"
        }):
            manager = get_secrets_manager()
            assert isinstance(manager, AWSSecretsManager)

    def test_get_local_file_manager_from_env(self):
        """Test getting local file manager from environment."""
        with patch.dict(os.environ, {
            "SECRETS_PROVIDER": "local_file",
            "SECRETS_FILE_PATH": "/path/to/secrets.json"
        }):
            manager = get_secrets_manager()
            assert isinstance(manager, LocalFileSecretsManager)

    def test_get_manager_with_explicit_provider(self):
        """Test getting manager with explicit provider."""
        manager = get_secrets_manager(provider=SecretsProvider.ENVIRONMENT)
        assert isinstance(manager, EnvironmentSecretsManager)
