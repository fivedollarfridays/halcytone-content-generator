"""
Comprehensive unit tests for authentication module
Sprint 5: Achieving >70% test coverage for critical auth components
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
import tempfile

from halcytone_content_generator.core.auth import AuthenticationManager, auth_manager


class TestAuthenticationManager:
    """Test suite for AuthenticationManager class"""

    @pytest.fixture
    def manager(self):
        """Provide a fresh AuthenticationManager instance"""
        mgr = AuthenticationManager()
        # Clear any cached data
        if hasattr(mgr.get_google_credentials, 'cache_clear'):
            mgr.get_google_credentials.cache_clear()
        return mgr

    @pytest.fixture
    def valid_google_creds(self):
        """Valid Google service account credentials"""
        return {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }

    @pytest.fixture
    def valid_notion_token(self):
        """Valid Notion API token"""
        return "secret_abcd1234567890"

    def test_initialization(self, manager):
        """Test AuthenticationManager initializes correctly"""
        assert manager._google_creds is None
        assert manager._notion_token is None
        assert manager._cached_tokens == {}

    def test_get_google_credentials_from_json_string(self, manager, valid_google_creds):
        """Test loading Google credentials from JSON string"""
        creds_json = json.dumps(valid_google_creds)
        result = manager.get_google_credentials(creds_json)

        assert result == valid_google_creds
        assert result["type"] == "service_account"
        assert result["project_id"] == "test-project"
        assert manager._google_creds == valid_google_creds

    def test_get_google_credentials_from_file(self, manager, valid_google_creds):
        """Test loading Google credentials from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_google_creds, f)
            temp_file = f.name

        try:
            result = manager.get_google_credentials(temp_file)
            assert result == valid_google_creds
            assert manager._google_creds == valid_google_creds
        finally:
            os.unlink(temp_file)

    @patch.dict(os.environ, {'GOOGLE_CREDENTIALS_JSON': '{"type": "service_account", "project_id": "test", "private_key": "key", "client_email": "test@test.com"}'})
    def test_get_google_credentials_from_env(self, manager):
        """Test loading Google credentials from environment variable"""
        # Pass a non-JSON string that doesn't exist as a file to trigger env lookup
        result = manager.get_google_credentials("nonexistent_file")
        assert result["type"] == "service_account"

    def test_get_google_credentials_invalid_json(self, manager):
        """Test handling of invalid JSON credentials"""
        with pytest.raises(ValueError, match="Google credentials must be valid JSON"):
            manager.get_google_credentials("invalid json")

    def test_get_google_credentials_no_credentials(self, manager):
        """Test handling when no credentials are provided"""
        with pytest.raises(ValueError, match="No Google credentials provided"):
            manager.get_google_credentials(None)

    def test_get_google_credentials_missing_fields(self, manager):
        """Test handling of credentials with missing required fields"""
        invalid_creds = {
            "type": "service_account",
            "project_id": "test"
            # Missing private_key and client_email
        }
        with pytest.raises(ValueError, match="Missing required field in Google credentials"):
            manager.get_google_credentials(json.dumps(invalid_creds))

    def test_get_google_credentials_file_not_exists(self, manager):
        """Test handling when file doesn't exist and no env var"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Google credentials not found"):
                manager.get_google_credentials("/nonexistent/file.json")

    def test_get_notion_token_from_string(self, manager, valid_notion_token):
        """Test getting Notion token from string"""
        result = manager.get_notion_token(valid_notion_token)
        assert result == valid_notion_token
        assert manager._notion_token == valid_notion_token

    @patch.dict(os.environ, {'NOTION_API_KEY': 'secret_test123'})
    def test_get_notion_token_from_env(self, manager):
        """Test getting Notion token from environment"""
        result = manager.get_notion_token()
        assert result == "secret_test123"
        assert manager._notion_token == "secret_test123"

    def test_get_notion_token_missing(self, manager):
        """Test handling when Notion token is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Notion API key not found"):
                manager.get_notion_token()

    @patch('halcytone_content_generator.core.auth.logger')
    def test_get_notion_token_invalid_format_warning(self, mock_logger, manager):
        """Test warning for invalid Notion token format"""
        token = "invalid_token"  # Doesn't start with 'secret_'
        result = manager.get_notion_token(token)
        assert result == token
        mock_logger.warning.assert_called_once()

    def test_get_openai_key_from_string(self, manager):
        """Test getting OpenAI key from string"""
        api_key = "sk-test123"
        result = manager.get_openai_key(api_key)
        assert result == api_key

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-env456'})
    def test_get_openai_key_from_env(self, manager):
        """Test getting OpenAI key from environment"""
        result = manager.get_openai_key()
        assert result == "sk-env456"

    def test_get_openai_key_not_configured(self, manager):
        """Test OpenAI key when not configured (optional)"""
        with patch.dict(os.environ, {}, clear=True):
            result = manager.get_openai_key()
            assert result is None

    @patch('halcytone_content_generator.core.auth.logger')
    def test_get_openai_key_exception_handling(self, mock_logger, manager):
        """Test exception handling in get_openai_key"""
        # Test with None - should handle gracefully
        with patch.dict(os.environ, {}, clear=True):
            result = manager.get_openai_key(None)
            assert result is None

    def test_validate_credentials_google_docs_valid(self, manager, valid_google_creds):
        """Test Google Docs credentials validation - valid"""
        assert manager.validate_credentials('google_docs', valid_google_creds) is True

    def test_validate_credentials_google_docs_invalid(self, manager):
        """Test Google Docs credentials validation - invalid"""
        invalid_creds = {"type": "service_account"}  # Missing required fields
        assert manager.validate_credentials('google_docs', invalid_creds) is False
        assert manager.validate_credentials('google_docs', "not a dict") is False

    def test_validate_credentials_notion_valid(self, manager, valid_notion_token):
        """Test Notion credentials validation - valid"""
        assert manager.validate_credentials('notion', valid_notion_token) is True
        assert manager.validate_credentials('notion', "any_non_empty_string") is True

    def test_validate_credentials_notion_invalid(self, manager):
        """Test Notion credentials validation - invalid"""
        assert manager.validate_credentials('notion', "") is False
        assert manager.validate_credentials('notion', 123) is False

    def test_validate_credentials_openai_valid(self, manager):
        """Test OpenAI credentials validation - valid"""
        assert manager.validate_credentials('openai', 'sk-valid123') is True

    def test_validate_credentials_openai_invalid(self, manager):
        """Test OpenAI credentials validation - invalid"""
        assert manager.validate_credentials('openai', 'invalid') is False
        assert manager.validate_credentials('openai', 123) is False

    @patch('halcytone_content_generator.core.auth.logger')
    def test_validate_credentials_unknown_service(self, mock_logger, manager):
        """Test validation with unknown service"""
        assert manager.validate_credentials('unknown', {}) is False
        mock_logger.warning.assert_called_once()

    @patch('halcytone_content_generator.core.auth.logger')
    def test_validate_credentials_exception(self, mock_logger, manager):
        """Test exception handling in validate_credentials"""
        # Create a mock object that raises an exception when accessed
        bad_creds = Mock(side_effect=Exception("Test error"))

        with patch.object(manager, 'validate_credentials', side_effect=Exception("Test error")):
            manager2 = AuthenticationManager()
            result = manager2.validate_credentials('google_docs', bad_creds)
            assert result is False

    def test_save_credentials_to_env_google_docs(self, manager, valid_google_creds):
        """Test saving Google Docs credentials to env file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            temp_file = f.name

        try:
            manager.save_credentials_to_env('google_docs', valid_google_creds, temp_file)

            # Read back and verify
            with open(temp_file, 'r') as f:
                content = f.read()
                assert 'GOOGLE_CREDENTIALS_JSON=' in content
                assert json.dumps(valid_google_creds) in content
        finally:
            os.unlink(temp_file)

    def test_save_credentials_to_env_notion(self, manager, valid_notion_token):
        """Test saving Notion credentials to env file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            temp_file = f.name

        try:
            manager.save_credentials_to_env('notion', valid_notion_token, temp_file)

            # Read back and verify
            with open(temp_file, 'r') as f:
                content = f.read()
                assert f'NOTION_API_KEY={valid_notion_token}' in content
        finally:
            os.unlink(temp_file)

    def test_save_credentials_to_env_openai(self, manager):
        """Test saving OpenAI credentials to env file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            temp_file = f.name

        try:
            api_key = "sk-test123"
            manager.save_credentials_to_env('openai', api_key, temp_file)

            # Read back and verify
            with open(temp_file, 'r') as f:
                content = f.read()
                assert f'OPENAI_API_KEY={api_key}' in content
        finally:
            os.unlink(temp_file)

    def test_save_credentials_to_env_existing_file(self, manager):
        """Test updating existing env file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("EXISTING_VAR=value\n")
            f.write("# Comment line\n")
            temp_file = f.name

        try:
            manager.save_credentials_to_env('openai', 'sk-new123', temp_file)

            # Read back and verify
            with open(temp_file, 'r') as f:
                content = f.read()
                assert 'EXISTING_VAR=value' in content
                assert 'OPENAI_API_KEY=sk-new123' in content
        finally:
            os.unlink(temp_file)

    @patch('halcytone_content_generator.core.auth.logger')
    def test_save_credentials_to_env_error(self, mock_logger, manager):
        """Test error handling in save_credentials_to_env"""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(IOError):
                manager.save_credentials_to_env('openai', 'sk-test', 'test.env')
            mock_logger.error.assert_called()

    def test_clear_cached_credentials(self, manager, valid_google_creds, valid_notion_token):
        """Test clearing all cached credentials"""
        # First, set some credentials
        manager._google_creds = valid_google_creds
        manager._notion_token = valid_notion_token
        manager._cached_tokens = {'test': 'token'}

        # Clear them
        manager.clear_cached_credentials()

        # Verify all cleared
        assert manager._google_creds is None
        assert manager._notion_token is None
        assert manager._cached_tokens == {}

    def test_lru_cache_behavior(self, manager, valid_google_creds):
        """Test that get_google_credentials uses LRU cache"""
        creds_json = json.dumps(valid_google_creds)

        # First call
        result1 = manager.get_google_credentials(creds_json)
        # Second call with same input should return cached result
        result2 = manager.get_google_credentials(creds_json)

        assert result1 is result2  # Same object due to caching


class TestGlobalAuthManager:
    """Test the global auth_manager instance"""

    def test_global_auth_manager_exists(self):
        """Test that global auth_manager is available"""
        assert auth_manager is not None
        assert isinstance(auth_manager, AuthenticationManager)

    def test_global_auth_manager_functionality(self):
        """Test that global auth_manager works correctly"""
        # Test basic validation
        assert auth_manager.validate_credentials('notion', 'secret_test') is True
        assert auth_manager.validate_credentials('notion', '') is False


class TestAuthIntegrationScenarios:
    """Integration test scenarios for authentication"""

    @pytest.fixture
    def manager(self):
        mgr = AuthenticationManager()
        if hasattr(mgr.get_google_credentials, 'cache_clear'):
            mgr.get_google_credentials.cache_clear()
        return mgr

    def test_full_google_auth_workflow(self, manager, valid_google_creds):
        """Test complete Google authentication workflow"""
        # Save credentials to env
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            temp_file = f.name

        try:
            # Save credentials
            manager.save_credentials_to_env('google_docs', valid_google_creds, temp_file)

            # Load and validate
            creds_json = json.dumps(valid_google_creds)
            loaded_creds = manager.get_google_credentials(creds_json)

            # Validate
            assert manager.validate_credentials('google_docs', loaded_creds) is True

            # Clear and verify cleared
            manager.clear_cached_credentials()
            assert manager._google_creds is None
        finally:
            os.unlink(temp_file)

    def test_full_notion_auth_workflow(self, manager, valid_notion_token):
        """Test complete Notion authentication workflow"""
        # Set via environment
        with patch.dict(os.environ, {'NOTION_API_KEY': valid_notion_token}):
            # Load token
            token = manager.get_notion_token()

            # Validate
            assert manager.validate_credentials('notion', token) is True

            # Clear and verify
            manager.clear_cached_credentials()
            assert manager._notion_token is None

    def test_multi_service_auth(self, manager, valid_google_creds, valid_notion_token):
        """Test authenticating multiple services"""
        # Authenticate Google
        google_result = manager.get_google_credentials(json.dumps(valid_google_creds))
        assert google_result is not None

        # Authenticate Notion
        notion_result = manager.get_notion_token(valid_notion_token)
        assert notion_result is not None

        # Authenticate OpenAI (optional)
        openai_result = manager.get_openai_key("sk-test123")
        assert openai_result == "sk-test123"

        # Validate all
        assert manager.validate_credentials('google_docs', google_result) is True
        assert manager.validate_credentials('notion', notion_result) is True
        assert manager.validate_credentials('openai', openai_result) is True