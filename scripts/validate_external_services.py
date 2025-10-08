#!/usr/bin/env python3
"""
External Service Connectivity Validation Script

Validates connectivity and authentication with all external services
used by the Halcytone Content Generator.

Usage:
    python scripts/validate_external_services.py --all
    python scripts/validate_external_services.py --service google_docs
    python scripts/validate_external_services.py --service openai --service crm
"""

import os
import sys
import argparse
import json
import time
from typing import Dict, List, Tuple
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


class ServiceValidator:
    """Base class for service validators"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None

    def validate(self) -> Tuple[bool, str, Dict]:
        """
        Validate service connectivity
        Returns: (success, message, metadata)
        """
        raise NotImplementedError

    def get_duration(self) -> float:
        """Get validation duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


class GoogleDocsValidator(ServiceValidator):
    """Validate Google Docs API connectivity"""

    def __init__(self):
        super().__init__("Google Docs API")

    def validate(self) -> Tuple[bool, str, Dict]:
        self.start_time = time.time()

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError

            # Get credentials
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if not creds_json:
                return False, "GOOGLE_CREDENTIALS_JSON not set", {}

            # Parse credentials
            try:
                if os.path.exists(creds_json):
                    creds = service_account.Credentials.from_service_account_file(
                        creds_json,
                        scopes=['https://www.googleapis.com/auth/documents.readonly']
                    )
                else:
                    creds_info = json.loads(creds_json)
                    creds = service_account.Credentials.from_service_account_info(
                        creds_info,
                        scopes=['https://www.googleapis.com/auth/documents.readonly']
                    )
            except json.JSONDecodeError:
                return False, "Invalid JSON in GOOGLE_CREDENTIALS_JSON", {}
            except Exception as e:
                return False, f"Failed to parse credentials: {str(e)}", {}

            # Test API connection
            service = build('docs', 'v1', credentials=creds)

            # Get living doc ID
            doc_id = os.getenv('LIVING_DOC_ID')
            if not doc_id:
                return False, "LIVING_DOC_ID not set", {}

            # Try to fetch document metadata
            doc = service.documents().get(documentId=doc_id).execute()

            self.end_time = time.time()

            metadata = {
                'document_id': doc_id,
                'document_title': doc.get('title', 'Unknown'),
                'service_account': creds_info.get('client_email') if not os.path.exists(creds_json) else 'from_file',
                'response_time_ms': int((self.end_time - self.start_time) * 1000)
            }

            return True, f"Successfully connected to document: {doc.get('title')}", metadata

        except HttpError as e:
            self.end_time = time.time()
            if e.resp.status == 404:
                return False, f"Document not found: {doc_id}", {}
            elif e.resp.status == 403:
                return False, "Permission denied. Ensure service account has access to document", {}
            else:
                return False, f"HTTP error: {e.resp.status} - {str(e)}", {}
        except ImportError:
            self.end_time = time.time()
            return False, "Google API libraries not installed (google-auth, google-api-python-client)", {}
        except Exception as e:
            self.end_time = time.time()
            return False, f"Unexpected error: {str(e)}", {}


class NotionValidator(ServiceValidator):
    """Validate Notion API connectivity"""

    def __init__(self):
        super().__init__("Notion API")

    def validate(self) -> Tuple[bool, str, Dict]:
        self.start_time = time.time()

        try:
            import httpx

            api_key = os.getenv('NOTION_API_KEY')
            database_id = os.getenv('NOTION_DATABASE_ID')

            if not api_key:
                return False, "NOTION_API_KEY not set", {}
            if not database_id:
                return False, "NOTION_DATABASE_ID not set", {}

            # Test API connection
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Notion-Version': '2022-06-28',
                'Content-Type': 'application/json'
            }

            url = f'https://api.notion.com/v1/databases/{database_id}'

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)

            self.end_time = time.time()

            if response.status_code == 200:
                data = response.json()
                metadata = {
                    'database_id': database_id,
                    'database_title': data.get('title', [{}])[0].get('plain_text', 'Unknown'),
                    'response_time_ms': int((self.end_time - self.start_time) * 1000)
                }
                return True, f"Successfully connected to database: {metadata['database_title']}", metadata
            elif response.status_code == 404:
                return False, f"Database not found: {database_id}", {}
            elif response.status_code == 401:
                return False, "Unauthorized. Check NOTION_API_KEY", {}
            else:
                return False, f"HTTP {response.status_code}: {response.text}", {}

        except ImportError:
            self.end_time = time.time()
            return False, "httpx library not installed", {}
        except Exception as e:
            self.end_time = time.time()
            return False, f"Unexpected error: {str(e)}", {}


class OpenAIValidator(ServiceValidator):
    """Validate OpenAI API connectivity"""

    def __init__(self):
        super().__init__("OpenAI API")

    def validate(self) -> Tuple[bool, str, Dict]:
        self.start_time = time.time()

        try:
            import httpx

            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return False, "OPENAI_API_KEY not set", {}

            # Test API connection with models endpoint
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.get('https://api.openai.com/v1/models', headers=headers)

            self.end_time = time.time()

            if response.status_code == 200:
                data = response.json()
                models = [model['id'] for model in data.get('data', []) if 'gpt' in model['id']]

                metadata = {
                    'available_models': len(data.get('data', [])),
                    'gpt_models': models[:5],  # First 5 GPT models
                    'response_time_ms': int((self.end_time - self.start_time) * 1000)
                }
                return True, f"Successfully connected. {len(models)} GPT models available", metadata
            elif response.status_code == 401:
                return False, "Unauthorized. Check OPENAI_API_KEY", {}
            else:
                return False, f"HTTP {response.status_code}: {response.text}", {}

        except ImportError:
            self.end_time = time.time()
            return False, "httpx library not installed", {}
        except Exception as e:
            self.end_time = time.time()
            return False, f"Unexpected error: {str(e)}", {}


class CRMValidator(ServiceValidator):
    """Validate CRM Service connectivity"""

    def __init__(self):
        super().__init__("CRM Service")

    def validate(self) -> Tuple[bool, str, Dict]:
        self.start_time = time.time()

        try:
            import httpx

            base_url = os.getenv('CRM_BASE_URL')
            api_key = os.getenv('CRM_API_KEY')

            if not base_url:
                return False, "CRM_BASE_URL not set", {}
            if not api_key:
                return False, "CRM_API_KEY not set", {}

            # Test health endpoint
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            health_url = f"{base_url.rstrip('/')}/health"

            with httpx.Client(timeout=10.0) as client:
                response = client.get(health_url, headers=headers)

            self.end_time = time.time()

            if response.status_code == 200:
                metadata = {
                    'base_url': base_url,
                    'response_time_ms': int((self.end_time - self.start_time) * 1000),
                    'status': 'healthy'
                }
                return True, f"Successfully connected to {base_url}", metadata
            elif response.status_code == 401:
                return False, "Unauthorized. Check CRM_API_KEY", {}
            else:
                return False, f"HTTP {response.status_code}: {response.text}", {}

        except httpx.ConnectError:
            self.end_time = time.time()
            return False, f"Connection failed. Is {base_url} accessible?", {}
        except ImportError:
            self.end_time = time.time()
            return False, "httpx library not installed", {}
        except Exception as e:
            self.end_time = time.time()
            return False, f"Unexpected error: {str(e)}", {}


class PlatformValidator(ServiceValidator):
    """Validate Platform Service connectivity"""

    def __init__(self):
        super().__init__("Platform Service")

    def validate(self) -> Tuple[bool, str, Dict]:
        self.start_time = time.time()

        try:
            import httpx

            base_url = os.getenv('PLATFORM_BASE_URL')
            api_key = os.getenv('PLATFORM_API_KEY')

            if not base_url:
                return False, "PLATFORM_BASE_URL not set", {}
            if not api_key:
                return False, "PLATFORM_API_KEY not set", {}

            # Test health endpoint
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            health_url = f"{base_url.rstrip('/')}/health"

            with httpx.Client(timeout=10.0) as client:
                response = client.get(health_url, headers=headers)

            self.end_time = time.time()

            if response.status_code == 200:
                metadata = {
                    'base_url': base_url,
                    'response_time_ms': int((self.end_time - self.start_time) * 1000),
                    'status': 'healthy'
                }
                return True, f"Successfully connected to {base_url}", metadata
            elif response.status_code == 401:
                return False, "Unauthorized. Check PLATFORM_API_KEY", {}
            else:
                return False, f"HTTP {response.status_code}: {response.text}", {}

        except httpx.ConnectError:
            self.end_time = time.time()
            return False, f"Connection failed. Is {base_url} accessible?", {}
        except ImportError:
            self.end_time = time.time()
            return False, "httpx library not installed", {}
        except Exception as e:
            self.end_time = time.time()
            return False, f"Unexpected error: {str(e)}", {}


class DatabaseValidator(ServiceValidator):
    """Validate Database connectivity"""

    def __init__(self):
        super().__init__("Database")

    def validate(self) -> Tuple[bool, str, Dict]:
        self.start_time = time.time()

        try:
            import psycopg2
            from urllib.parse import urlparse

            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                return False, "DATABASE_URL not set", {}

            # Parse database URL
            parsed = urlparse(database_url)

            # Test connection
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                connect_timeout=10,
                sslmode=os.getenv('DATABASE_SSL_MODE', 'prefer')
            )

            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]

            cursor.execute('SELECT pg_database_size(current_database());')
            size_bytes = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            self.end_time = time.time()

            metadata = {
                'host': parsed.hostname,
                'database': parsed.path.lstrip('/'),
                'version': version.split()[0:2],
                'size_mb': round(size_bytes / (1024 * 1024), 2),
                'response_time_ms': int((self.end_time - self.start_time) * 1000)
            }

            return True, f"Successfully connected to {parsed.hostname}", metadata

        except ImportError:
            self.end_time = time.time()
            return False, "psycopg2 library not installed", {}
        except Exception as e:
            self.end_time = time.time()
            return False, f"Connection failed: {str(e)}", {}


class RedisValidator(ServiceValidator):
    """Validate Redis connectivity"""

    def __init__(self):
        super().__init__("Redis Cache")

    def validate(self) -> Tuple[bool, str, Dict]:
        self.start_time = time.time()

        try:
            import redis
            from urllib.parse import urlparse

            redis_url = os.getenv('CACHE_REDIS_URL', os.getenv('REDIS_URL'))
            if not redis_url:
                return False, "REDIS_URL not set", {}

            # Parse Redis URL
            parsed = urlparse(redis_url)

            # Test connection
            r = redis.Redis(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 6379,
                password=parsed.password,
                db=int(parsed.path.lstrip('/')) if parsed.path else 0,
                socket_connect_timeout=10
            )

            # Test ping
            r.ping()

            # Get info
            info = r.info()

            self.end_time = time.time()

            metadata = {
                'host': parsed.hostname or 'localhost',
                'version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_mb': round(info.get('used_memory', 0) / (1024 * 1024), 2),
                'response_time_ms': int((self.end_time - self.start_time) * 1000)
            }

            return True, f"Successfully connected to Redis {info.get('redis_version')}", metadata

        except ImportError:
            self.end_time = time.time()
            return False, "redis library not installed", {}
        except Exception as e:
            self.end_time = time.time()
            return False, f"Connection failed: {str(e)}", {}


def main():
    parser = argparse.ArgumentParser(
        description='Validate external service connectivity',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--service',
        action='append',
        choices=['google_docs', 'notion', 'openai', 'crm', 'platform', 'database', 'redis'],
        help='Service to validate (can specify multiple times)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Validate all services'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    parser.add_argument(
        '--env-file',
        help='Path to .env file to load'
    )

    args = parser.parse_args()

    # Load environment file if specified
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file)
        print_info(f"Loaded environment from: {args.env_file}")

    # Determine which services to validate
    if args.all:
        services_to_validate = ['google_docs', 'notion', 'openai', 'crm', 'platform', 'database', 'redis']
    elif args.service:
        services_to_validate = args.service
    else:
        print_error("Please specify --all or --service")
        parser.print_help()
        sys.exit(1)

    # Service validator mapping
    validators = {
        'google_docs': GoogleDocsValidator(),
        'notion': NotionValidator(),
        'openai': OpenAIValidator(),
        'crm': CRMValidator(),
        'platform': PlatformValidator(),
        'database': DatabaseValidator(),
        'redis': RedisValidator()
    }

    # Run validations
    results = {}
    total_success = 0
    total_failed = 0

    if not args.json:
        print_header("External Service Connectivity Validation")
        print_info(f"Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
        print_info(f"Timestamp: {datetime.now().isoformat()}")

    for service_name in services_to_validate:
        validator = validators[service_name]

        if not args.json:
            print(f"\n{Colors.BOLD}Testing {validator.name}...{Colors.RESET}")

        success, message, metadata = validator.validate()

        results[service_name] = {
            'success': success,
            'message': message,
            'metadata': metadata,
            'duration_ms': int(validator.get_duration() * 1000)
        }

        if success:
            total_success += 1
            if not args.json:
                print_success(message)
                if metadata:
                    for key, value in metadata.items():
                        print(f"  {key}: {value}")
        else:
            total_failed += 1
            if not args.json:
                print_error(message)

    # Print summary
    if args.json:
        print(json.dumps({
            'timestamp': datetime.now().isoformat(),
            'environment': os.getenv('ENVIRONMENT', 'unknown'),
            'total_validated': len(services_to_validate),
            'total_success': total_success,
            'total_failed': total_failed,
            'results': results
        }, indent=2))
    else:
        print_header("Validation Summary")
        print(f"Total Services Validated: {len(services_to_validate)}")
        print_success(f"Successful: {total_success}")
        if total_failed > 0:
            print_error(f"Failed: {total_failed}")
        else:
            print(f"Failed: {total_failed}")

        if total_failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All services validated successfully!{Colors.RESET}")
            sys.exit(0)
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ Some services failed validation{Colors.RESET}")
            sys.exit(1)


if __name__ == '__main__':
    main()
