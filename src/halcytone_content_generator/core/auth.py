"""
Authentication handlers for various document sources
"""
import json
import os
from typing import Dict, Optional, Any
from pathlib import Path
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """
    Manages authentication for various document sources
    """

    def __init__(self):
        """Initialize authentication manager"""
        self._google_creds = None
        self._notion_token = None
        self._cached_tokens = {}

    @lru_cache(maxsize=1)
    def get_google_credentials(self, credentials_json: Optional[str] = None) -> Dict:
        """
        Get Google service account credentials

        Args:
            credentials_json: JSON string of credentials or path to file

        Returns:
            Parsed credentials dictionary

        Raises:
            ValueError: If credentials are invalid or missing
        """
        try:
            if credentials_json:
                # Check if it's a file path first
                if os.path.exists(credentials_json):
                    with open(credentials_json, 'r') as f:
                        creds = json.load(f)
                else:
                    # Try to parse as JSON string
                    try:
                        creds = json.loads(credentials_json)
                    except json.JSONDecodeError as json_err:
                        # Try environment variable as fallback
                        env_creds = os.getenv('GOOGLE_CREDENTIALS_JSON')
                        if env_creds:
                            try:
                                creds = json.loads(env_creds)
                            except json.JSONDecodeError:
                                # Environment variable also invalid
                                raise ValueError("Google credentials must be valid JSON") from json_err
                        else:
                            # No environment variable, original JSON was invalid
                            raise ValueError("Google credentials must be valid JSON") from json_err

                # Validate required fields
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                for field in required_fields:
                    if field not in creds:
                        raise ValueError(f"Missing required field in Google credentials: {field}")

                self._google_creds = creds
                logger.info("Google credentials loaded successfully")
                return creds

            else:
                raise ValueError("No Google credentials provided")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Google credentials: {e}")
            raise ValueError("Google credentials must be valid JSON")
        except Exception as e:
            logger.error(f"Failed to load Google credentials: {e}")
            raise

    def get_notion_token(self, api_key: Optional[str] = None) -> str:
        """
        Get Notion API token

        Args:
            api_key: Notion API key

        Returns:
            Valid Notion API token

        Raises:
            ValueError: If token is invalid or missing
        """
        try:
            if api_key:
                self._notion_token = api_key
            else:
                # Try environment variable
                env_token = os.getenv('NOTION_API_KEY')
                if env_token:
                    self._notion_token = env_token
                else:
                    raise ValueError("Notion API key not found")

            # Basic validation
            if not self._notion_token.startswith('secret_'):
                logger.warning("Notion token doesn't start with 'secret_' - might be invalid")

            logger.info("Notion API key loaded successfully")
            return self._notion_token

        except Exception as e:
            logger.error(f"Failed to load Notion API key: {e}")
            raise

    def get_openai_key(self, api_key: Optional[str] = None) -> Optional[str]:
        """
        Get OpenAI API key for content enhancement (optional)

        Args:
            api_key: OpenAI API key

        Returns:
            OpenAI API key or None if not configured
        """
        try:
            if api_key:
                return api_key

            # Try environment variable
            env_key = os.getenv('OPENAI_API_KEY')
            if env_key:
                logger.info("OpenAI API key loaded")
                return env_key

            logger.info("OpenAI API key not configured (optional)")
            return None

        except Exception as e:
            logger.warning(f"Failed to load OpenAI API key: {e}")
            return None

    def validate_credentials(self, service: str, credentials: Any) -> bool:
        """
        Validate credentials for a specific service

        Args:
            service: Service name (google_docs, notion, etc.)
            credentials: Credentials to validate

        Returns:
            True if credentials are valid
        """
        try:
            if service == 'google_docs':
                if isinstance(credentials, dict):
                    required = ['type', 'project_id', 'private_key', 'client_email']
                    return all(field in credentials for field in required)
                return False

            elif service == 'notion':
                if isinstance(credentials, str):
                    return len(credentials) > 0
                return False

            elif service == 'openai':
                if isinstance(credentials, str):
                    return credentials.startswith('sk-')
                return False

            else:
                logger.warning(f"Unknown service for validation: {service}")
                return False

        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            return False

    def save_credentials_to_env(self, service: str, credentials: Any, env_file: str = '.env'):
        """
        Save credentials to environment file

        Args:
            service: Service name
            credentials: Credentials to save
            env_file: Path to .env file
        """
        try:
            env_path = Path(env_file)

            # Read existing env file
            env_vars = {}
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            env_vars[key] = value

            # Update credentials
            if service == 'google_docs':
                env_vars['GOOGLE_CREDENTIALS_JSON'] = json.dumps(credentials)
            elif service == 'notion':
                # Notion can be string (token) or dict (token + database_id)
                if isinstance(credentials, str):
                    env_vars['NOTION_API_KEY'] = credentials
                else:
                    env_vars['NOTION_API_KEY'] = credentials.get('api_key', credentials.get('token', ''))
                    env_vars['NOTION_DATABASE_ID'] = credentials.get('database_id', '')
            elif service == 'openai':
                env_vars['OPENAI_API_KEY'] = credentials

            # Write back to file
            with open(env_path, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")

            logger.info(f"Credentials for {service} saved to {env_file}")

        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise

    def clear_cached_credentials(self):
        """Clear all cached credentials"""
        self._google_creds = None
        self._notion_token = None
        self._cached_tokens.clear()
        self.get_google_credentials.cache_clear()
        logger.info("Cleared all cached credentials")


# Global auth manager instance
auth_manager = AuthenticationManager()