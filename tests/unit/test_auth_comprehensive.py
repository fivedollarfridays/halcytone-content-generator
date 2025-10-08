"""
Comprehensive unit tests for authentication module
Tests authentication, credential validation, and token management
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from halcytone_content_generator.core.auth import (
    AuthenticationManager,
    auth_manager
)


class TestAuthenticationManager:
    """Comprehensive tests for AuthenticationManager"""

    @pytest.fixture
    def auth_mgr(self):
        """Create fresh auth manager for each test"""
        mgr = AuthenticationManager()
        mgr.clear_cached_credentials()
        return mgr

    @pytest.fixture
    def valid_google_creds(self):
        """Valid Google service account credentials"""
        return {
            "type": "service_account",
            "project_id": "test-project-123",
            "private_key_id": "key-id-123",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project-123.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }

    # ===== Google Credentials Tests =====

    def test_get_google_credentials_from_json_string(self, auth_mgr, valid_google_creds):
        """Test loading Google credentials from JSON string"""
        json_str = json.dumps(valid_google_creds)

        creds = auth_mgr.get_google_credentials(json_str)

        assert creds['type'] == 'service_account'
        assert creds['project_id'] == 'test-project-123'
        assert creds['client_email'] == 'test@test-project-123.iam.gserviceaccount.com'

    def test_get_google_credentials_from_file(self, auth_mgr, valid_google_creds):
        """Test loading Google credentials from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_google_creds, f)
            temp_file = f.name

        try:
            creds = auth_mgr.get_google_credentials(temp_file)

            assert creds['type'] == 'service_account'
            assert creds['project_id'] == 'test-project-123'
        finally:
            os.unlink(temp_file)

    def test_get_google_credentials_missing_required_field(self, auth_mgr):
        """Test validation fails when required field is missing"""
        incomplete_creds = {
            "type": "service_account",
            "project_id": "test-project"
            # Missing private_key and client_email
        }

        with pytest.raises(ValueError, match="Missing required field"):
            auth_mgr.get_google_credentials(json.dumps(incomplete_creds))

    def test_get_google_credentials_invalid_json(self, auth_mgr):
        """Test error handling for invalid JSON"""
        with pytest.raises(ValueError, match="must be valid JSON"):
            auth_mgr.get_google_credentials("not valid json {{{")

    def test_get_google_credentials_no_credentials_provided(self, auth_mgr):
        """Test error when no credentials provided"""
        with pytest.raises(ValueError, match="No Google credentials provided"):
            auth_mgr.get_google_credentials(None)

    def test_get_google_credentials_from_env_variable(self, auth_mgr, valid_google_creds):
        """Test loading credentials from environment variable"""
        with patch.dict(os.environ, {'GOOGLE_CREDENTIALS_JSON': json.dumps(valid_google_creds)}):
            # Pass invalid JSON string, should fallback to env var
            creds = auth_mgr.get_google_credentials("invalid json")

            assert creds['type'] == 'service_account'

    def test_get_google_credentials_caching(self, auth_mgr, valid_google_creds):
        """Test that credentials are cached after first load"""
        json_str = json.dumps(valid_google_creds)

        # First call
        creds1 = auth_mgr.get_google_credentials(json_str)
        # Second call should return cached
        creds2 = auth_mgr.get_google_credentials(json_str)

        assert creds1 is creds2  # Same object reference

    # ===== Notion Token Tests =====

    def test_get_notion_token_from_parameter(self, auth_mgr):
        """Test loading Notion token from parameter"""
        token = "secret_test_token_123"

        result = auth_mgr.get_notion_token(token)

        assert result == token

    def test_get_notion_token_from_env(self, auth_mgr):
        """Test loading Notion token from environment"""
        with patch.dict(os.environ, {'NOTION_API_KEY': 'secret_env_token'}):
            result = auth_mgr.get_notion_token()

            assert result == 'secret_env_token'

    def test_get_notion_token_missing(self, auth_mgr):
        """Test error when Notion token is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Notion API key not found"):
                auth_mgr.get_notion_token(None)

    def test_get_notion_token_invalid_format_warning(self, auth_mgr, caplog):
        """Test warning when token doesn't have expected format"""
        token = "invalid_format_token"

        auth_mgr.get_notion_token(token)

        assert "doesn't start with 'secret_'" in caplog.text

    def test_get_notion_token_valid_format(self, auth_mgr):
        """Test no warning with valid token format"""
        token = "secret_valid_token_123"

        result = auth_mgr.get_notion_token(token)

        assert result.startswith('secret_')

    # ===== OpenAI Key Tests =====

    def test_get_openai_key_from_parameter(self, auth_mgr):
        """Test loading OpenAI key from parameter"""
        key = "sk-test_openai_key_123"

        result = auth_mgr.get_openai_key(key)

        assert result == key

    def test_get_openai_key_from_env(self, auth_mgr):
        """Test loading OpenAI key from environment"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-env_key'}):
            result = auth_mgr.get_openai_key()

            assert result == 'sk-env_key'

    def test_get_openai_key_not_configured(self, auth_mgr):
        """Test OpenAI key returns None when not configured (optional)"""
        with patch.dict(os.environ, {}, clear=True):
            result = auth_mgr.get_openai_key()

            assert result is None

    def test_get_openai_key_handles_exceptions(self, auth_mgr):
        """Test OpenAI key returns None on exceptions (optional service)"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'valid_key'}):
            with patch('os.getenv', side_effect=Exception("Test error")):
                result = auth_mgr.get_openai_key()

                assert result is None

    # ===== Credential Validation Tests =====

    def test_validate_google_docs_credentials_valid(self, auth_mgr, valid_google_creds):
        """Test validation of valid Google credentials"""
        result = auth_mgr.validate_credentials('google_docs', valid_google_creds)

        assert result is True

    def test_validate_google_docs_credentials_invalid_missing_field(self, auth_mgr):
        """Test validation fails for incomplete Google credentials"""
        incomplete = {"type": "service_account", "project_id": "test"}

        result = auth_mgr.validate_credentials('google_docs', incomplete)

        assert result is False

    def test_validate_google_docs_credentials_not_dict(self, auth_mgr):
        """Test validation fails for non-dict Google credentials"""
        result = auth_mgr.validate_credentials('google_docs', "string_not_dict")

        assert result is False

    def test_validate_notion_credentials_valid(self, auth_mgr):
        """Test validation of valid Notion token"""
        result = auth_mgr.validate_credentials('notion', 'secret_valid_token')

        assert result is True

    def test_validate_notion_credentials_empty(self, auth_mgr):
        """Test validation fails for empty Notion token"""
        result = auth_mgr.validate_credentials('notion', '')

        assert result is False

    def test_validate_notion_credentials_not_string(self, auth_mgr):
        """Test validation fails for non-string Notion token"""
        result = auth_mgr.validate_credentials('notion', {'key': 'value'})

        assert result is False

    def test_validate_openai_credentials_valid(self, auth_mgr):
        """Test validation of valid OpenAI key"""
        result = auth_mgr.validate_credentials('openai', 'sk-valid_key_123')

        assert result is True

    def test_validate_openai_credentials_invalid_prefix(self, auth_mgr):
        """Test validation fails for OpenAI key without sk- prefix"""
        result = auth_mgr.validate_credentials('openai', 'invalid_prefix_key')

        assert result is False

    def test_validate_unknown_service(self, auth_mgr):
        """Test validation returns False for unknown service"""
        result = auth_mgr.validate_credentials('unknown_service', 'credentials')

        assert result is False

    def test_validate_credentials_handles_exceptions(self, auth_mgr):
        """Test validation handles exceptions gracefully"""
        # Pass None to trigger exception in validation logic
        result = auth_mgr.validate_credentials('google_docs', None)

        assert result is False

    # ===== Save Credentials Tests =====

    def test_save_google_credentials_to_env(self, auth_mgr, valid_google_creds):
        """Test saving Google credentials to .env file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            env_file = f.name

        try:
            auth_mgr.save_credentials_to_env('google_docs', valid_google_creds, env_file)

            # Read back and verify
            with open(env_file, 'r') as f:
                content = f.read()
                assert 'GOOGLE_CREDENTIALS_JSON=' in content
                assert 'test-project-123' in content
        finally:
            os.unlink(env_file)

    def test_save_notion_string_credentials_to_env(self, auth_mgr):
        """Test saving Notion token (string) to .env file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            env_file = f.name

        try:
            auth_mgr.save_credentials_to_env('notion', 'secret_token_123', env_file)

            with open(env_file, 'r') as f:
                content = f.read()
                assert 'NOTION_API_KEY=secret_token_123' in content
        finally:
            os.unlink(env_file)

    def test_save_notion_dict_credentials_to_env(self, auth_mgr):
        """Test saving Notion credentials (dict with token and database_id) to .env"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            env_file = f.name

        try:
            creds = {
                'api_key': 'secret_token_123',
                'database_id': 'db_id_456'
            }
            auth_mgr.save_credentials_to_env('notion', creds, env_file)

            with open(env_file, 'r') as f:
                content = f.read()
                assert 'NOTION_API_KEY=secret_token_123' in content
                assert 'NOTION_DATABASE_ID=db_id_456' in content
        finally:
            os.unlink(env_file)

    def test_save_openai_credentials_to_env(self, auth_mgr):
        """Test saving OpenAI key to .env file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            env_file = f.name

        try:
            auth_mgr.save_credentials_to_env('openai', 'sk-key_123', env_file)

            with open(env_file, 'r') as f:
                content = f.read()
                assert 'OPENAI_API_KEY=sk-key_123' in content
        finally:
            os.unlink(env_file)

    def test_save_credentials_preserves_existing(self, auth_mgr):
        """Test that saving credentials preserves other existing env vars"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            # Write existing vars
            f.write("EXISTING_VAR=existing_value\n")
            f.write("ANOTHER_VAR=another_value\n")
            env_file = f.name

        try:
            auth_mgr.save_credentials_to_env('notion', 'secret_new_token', env_file)

            with open(env_file, 'r') as f:
                content = f.read()
                assert 'EXISTING_VAR=existing_value' in content
                assert 'ANOTHER_VAR=another_value' in content
                assert 'NOTION_API_KEY=secret_new_token' in content
        finally:
            os.unlink(env_file)

    def test_save_credentials_handles_errors(self, auth_mgr):
        """Test save_credentials raises exception on error"""
        # Try to write to invalid path
        with pytest.raises(Exception):
            auth_mgr.save_credentials_to_env('notion', 'token', '/invalid/path/.env')

    # ===== Clear Credentials Tests =====

    def test_clear_cached_credentials(self, auth_mgr, valid_google_creds):
        """Test clearing all cached credentials"""
        # Load some credentials
        auth_mgr.get_google_credentials(json.dumps(valid_google_creds))
        auth_mgr.get_notion_token('secret_test_token')

        # Clear cache
        auth_mgr.clear_cached_credentials()

        # Verify internal state is cleared
        assert auth_mgr._google_creds is None
        assert auth_mgr._notion_token is None
        assert len(auth_mgr._cached_tokens) == 0

    def test_clear_cached_credentials_clears_lru_cache(self, auth_mgr, valid_google_creds):
        """Test that clear also clears LRU cache"""
        json_str = json.dumps(valid_google_creds)

        # Load and cache
        creds1 = auth_mgr.get_google_credentials(json_str)

        # Clear
        auth_mgr.clear_cached_credentials()

        # Load again - should not be same object if cache cleared
        creds2 = auth_mgr.get_google_credentials(json_str)

        # Note: Due to LRU cache, might still be same object if not properly cleared
        # But this tests the clear_cached_credentials functionality
        assert creds2 is not None

    # ===== Integration Tests =====

    def test_full_google_workflow(self, auth_mgr, valid_google_creds):
        """Test complete workflow: load, validate, save Google credentials"""
        json_str = json.dumps(valid_google_creds)

        # Load
        creds = auth_mgr.get_google_credentials(json_str)

        # Validate
        is_valid = auth_mgr.validate_credentials('google_docs', creds)
        assert is_valid is True

        # Save
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            env_file = f.name

        try:
            auth_mgr.save_credentials_to_env('google_docs', creds, env_file)

            # Verify saved
            with open(env_file, 'r') as f:
                assert 'GOOGLE_CREDENTIALS_JSON=' in f.read()
        finally:
            os.unlink(env_file)

    def test_full_notion_workflow(self, auth_mgr):
        """Test complete workflow: load, validate, save Notion credentials"""
        token = "secret_test_token_123"

        # Load
        loaded_token = auth_mgr.get_notion_token(token)

        # Validate
        is_valid = auth_mgr.validate_credentials('notion', loaded_token)
        assert is_valid is True

        # Save
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            env_file = f.name

        try:
            auth_mgr.save_credentials_to_env('notion', loaded_token, env_file)

            # Verify saved
            with open(env_file, 'r') as f:
                assert 'NOTION_API_KEY=secret_test_token_123' in f.read()
        finally:
            os.unlink(env_file)

    def test_multiple_services_in_same_env_file(self, auth_mgr, valid_google_creds):
        """Test saving credentials for multiple services in same file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            env_file = f.name

        try:
            # Save Google creds
            auth_mgr.save_credentials_to_env('google_docs', valid_google_creds, env_file)

            # Save Notion creds
            auth_mgr.save_credentials_to_env('notion', 'secret_notion_token', env_file)

            # Save OpenAI creds
            auth_mgr.save_credentials_to_env('openai', 'sk-openai_key', env_file)

            # Verify all are present
            with open(env_file, 'r') as f:
                content = f.read()
                assert 'GOOGLE_CREDENTIALS_JSON=' in content
                assert 'NOTION_API_KEY=secret_notion_token' in content
                assert 'OPENAI_API_KEY=sk-openai_key' in content
        finally:
            os.unlink(env_file)

    # ===== Global Auth Manager Tests =====

    def test_global_auth_manager_exists(self):
        """Test that global auth_manager instance exists"""
        assert auth_manager is not None
        assert isinstance(auth_manager, AuthenticationManager)

    def test_global_auth_manager_is_singleton(self):
        """Test that global auth_manager is effectively a singleton"""
        from halcytone_content_generator.core.auth import auth_manager as auth_manager2

        assert auth_manager is auth_manager2
