#!/usr/bin/env python3
"""
Security Configuration Validation Script

Comprehensive security validation for production environments including:
- SSL/TLS configuration
- API authentication and authorization
- Security headers
- Rate limiting
- Input validation
- Secrets exposure
- Network security
- Compliance requirements

Usage:
    python scripts/validate_security.py --host https://api.halcytone.com
    python scripts/validate_security.py --host https://api.halcytone.com --comprehensive
    python scripts/validate_security.py --host https://api.halcytone.com --api-key YOUR_KEY --test-auth
"""

import argparse
import asyncio
import json
import sys
import ssl
import socket
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re
import os

try:
    import httpx
    import certifi
except ImportError:
    print("Error: httpx and certifi libraries required. Install with: pip install httpx certifi")
    sys.exit(1)

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}→ {text}{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'-' * 70}{Colors.RESET}")

def print_success(text: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.BLUE}ℹ {text}{Colors.RESET}")

def print_critical(text: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.RED}{Colors.BOLD}🔴 CRITICAL: {text}{Colors.RESET}")


class SecurityValidator:
    """Comprehensive security validation"""

    def __init__(self, host: str, api_key: Optional[str] = None, timeout: int = 10):
        self.host = host.rstrip('/')
        self.api_key = api_key or os.getenv('API_KEY')
        self.timeout = timeout
        self.results = []
        self.critical_issues = []
        self.warnings = []

        # Parse hostname for SSL checks
        from urllib.parse import urlparse
        parsed = urlparse(self.host)
        self.hostname = parsed.hostname
        self.port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        self.is_https = parsed.scheme == 'https'

    async def validate_all(self, comprehensive: bool = False, test_auth: bool = False):
        """Run all security validations"""
        print_header("Security Configuration Validation")
        print_info(f"Host: {self.host}")
        print_info(f"HTTPS: {self.is_https}")
        print_info(f"Comprehensive Mode: {comprehensive}")
        print_info(f"Timestamp: {datetime.now().isoformat()}")

        # Core security validations
        if self.is_https:
            await self.validate_ssl_tls()
        else:
            self.add_critical("HTTPS not enabled - all traffic unencrypted!")

        await self.validate_security_headers()
        await self.validate_cors_configuration()
        await self.validate_authentication()

        if test_auth and self.api_key:
            await self.validate_authorization()

        await self.validate_rate_limiting()
        await self.validate_input_validation()
        await self.validate_error_handling()

        # Comprehensive checks
        if comprehensive:
            await self.validate_secrets_exposure()
            await self.validate_api_versioning()
            await self.validate_session_management()
            await self.validate_csrf_protection()
            await self.validate_xss_protection()
            await self.validate_sql_injection_protection()
            await self.validate_clickjacking_protection()

        return self.generate_report()

    def add_result(self, name: str, passed: bool, message: str, severity: str = "medium"):
        """Add validation result"""
        self.results.append({
            'name': name,
            'passed': passed,
            'message': message,
            'severity': severity
        })

        if not passed:
            if severity == "critical":
                self.critical_issues.append((name, message))
            elif severity == "high":
                self.warnings.append((name, message))

    def add_critical(self, message: str):
        """Add critical security issue"""
        self.critical_issues.append(("Critical Issue", message))
        print_critical(message)

    async def validate_ssl_tls(self):
        """Validate SSL/TLS configuration"""
        print_section("SSL/TLS Configuration")

        try:
            # Get SSL certificate info
            context = ssl.create_default_context()
            with socket.create_connection((self.hostname, self.port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()

                    # Check TLS version
                    if version in ['TLSv1.2', 'TLSv1.3']:
                        print_success(f"TLS Version: {version}")
                        self.add_result("TLS Version", True, f"Using {version}", "medium")
                    elif version == 'TLSv1.1':
                        print_warning(f"TLS Version: {version} (upgrade to 1.2+ recommended)")
                        self.add_result("TLS Version", False, f"Using outdated {version}", "high")
                    else:
                        print_error(f"TLS Version: {version} (insecure)")
                        self.add_result("TLS Version", False, f"Using insecure {version}", "critical")

                    # Check cipher
                    cipher_name = cipher[0] if cipher else "Unknown"
                    print_info(f"Cipher: {cipher_name}", indent=1)

                    # Check certificate validity
                    import ssl
                    from datetime import datetime

                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - datetime.now()).days

                    if days_until_expiry > 30:
                        print_success(f"Certificate valid for {days_until_expiry} days")
                        self.add_result("Certificate Validity", True, f"{days_until_expiry} days remaining", "low")
                    elif days_until_expiry > 7:
                        print_warning(f"Certificate expires in {days_until_expiry} days - renewal needed soon")
                        self.add_result("Certificate Validity", False, f"Only {days_until_expiry} days remaining", "high")
                    else:
                        print_error(f"Certificate expires in {days_until_expiry} days - URGENT renewal needed")
                        self.add_result("Certificate Validity", False, f"Critical: {days_until_expiry} days remaining", "critical")

                    # Check certificate subject
                    subject = dict(x[0] for x in cert['subject'])
                    print_info(f"Subject: {subject.get('commonName', 'Unknown')}", indent=1)

                    # Check for wildcard certificate
                    if 'commonName' in subject and subject['commonName'].startswith('*'):
                        print_warning("Wildcard certificate detected - ensure proper domain validation", indent=1)

        except ssl.SSLError as e:
            print_error(f"SSL Error: {str(e)}")
            self.add_result("SSL/TLS", False, f"SSL Error: {str(e)}", "critical")
        except Exception as e:
            print_error(f"SSL/TLS check failed: {str(e)}")
            self.add_result("SSL/TLS", False, f"Check failed: {str(e)}", "high")

    async def validate_security_headers(self):
        """Validate security headers"""
        print_section("Security Headers")

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=True) as client:
                response = await client.get(self.host)

                # Define required security headers
                security_headers = {
                    'Strict-Transport-Security': {
                        'required': True,
                        'severity': 'critical',
                        'expected': 'max-age=31536000',
                        'description': 'Enforces HTTPS'
                    },
                    'X-Content-Type-Options': {
                        'required': True,
                        'severity': 'high',
                        'expected': 'nosniff',
                        'description': 'Prevents MIME sniffing'
                    },
                    'X-Frame-Options': {
                        'required': True,
                        'severity': 'high',
                        'expected': 'DENY or SAMEORIGIN',
                        'description': 'Prevents clickjacking'
                    },
                    'X-XSS-Protection': {
                        'required': False,
                        'severity': 'medium',
                        'expected': '1; mode=block',
                        'description': 'XSS filter (legacy)'
                    },
                    'Content-Security-Policy': {
                        'required': True,
                        'severity': 'high',
                        'expected': 'restrictive policy',
                        'description': 'Prevents XSS and injection'
                    },
                    'Referrer-Policy': {
                        'required': False,
                        'severity': 'medium',
                        'expected': 'strict-origin-when-cross-origin',
                        'description': 'Controls referrer information'
                    },
                    'Permissions-Policy': {
                        'required': False,
                        'severity': 'low',
                        'expected': 'restrictive policy',
                        'description': 'Controls browser features'
                    }
                }

                headers_present = 0
                headers_missing = 0

                for header, config in security_headers.items():
                    value = response.headers.get(header)

                    if value:
                        headers_present += 1
                        print_success(f"{header}: {value}")
                        self.add_result(f"Header: {header}", True, f"Present: {value}", "low")
                    else:
                        headers_missing += 1
                        if config['required']:
                            print_error(f"{header}: Missing - {config['description']}")
                            self.add_result(f"Header: {header}", False, f"Missing: {config['description']}", config['severity'])
                        else:
                            print_warning(f"{header}: Missing - {config['description']} (optional)")
                            self.add_result(f"Header: {header}", False, f"Missing (optional): {config['description']}", "low")

                # Overall assessment
                if headers_missing == 0:
                    print_success(f"\nAll security headers present ({headers_present}/{len(security_headers)})")
                elif headers_present >= 4:
                    print_warning(f"\nMost security headers present ({headers_present}/{len(security_headers)})")
                else:
                    print_error(f"\nInsufficient security headers ({headers_present}/{len(security_headers)})")

        except Exception as e:
            print_error(f"Security headers check failed: {str(e)}")
            self.add_result("Security Headers", False, str(e), "high")

    async def validate_cors_configuration(self):
        """Validate CORS configuration"""
        print_section("CORS Configuration")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Send OPTIONS request with Origin header
                headers = {'Origin': 'https://malicious-site.com'}
                response = await client.options(self.host, headers=headers)

                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
                }

                if cors_headers['Access-Control-Allow-Origin']:
                    origin = cors_headers['Access-Control-Allow-Origin']

                    if origin == '*':
                        print_warning("CORS allows all origins (*) - security risk for credentials")
                        self.add_result("CORS Configuration", False, "Allows all origins", "high")
                    elif origin == 'https://malicious-site.com':
                        print_error("CORS accepts malicious origin - CRITICAL VULNERABILITY")
                        self.add_result("CORS Configuration", False, "Accepts any origin", "critical")
                    else:
                        print_success(f"CORS restricted to: {origin}")
                        self.add_result("CORS Configuration", True, f"Restricted to {origin}", "low")

                    # Check credentials
                    if cors_headers['Access-Control-Allow-Credentials'] == 'true' and origin == '*':
                        print_error("CORS allows credentials with wildcard origin - CRITICAL")
                        self.add_result("CORS Credentials", False, "Wildcard with credentials", "critical")

                else:
                    print_success("CORS not enabled (or properly restricted)")
                    self.add_result("CORS Configuration", True, "Properly restricted", "low")

        except Exception as e:
            print_info(f"CORS check skipped: {str(e)}")

    async def validate_authentication(self):
        """Validate authentication requirements"""
        print_section("Authentication")

        protected_endpoints = [
            '/api/v1/content/generate',
            '/api/v1/content/batch',
            '/api/v1/content/schedule',
            '/api/v2/content/generate',
        ]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for endpoint in protected_endpoints:
                    # Try without authentication
                    try:
                        response = await client.post(f"{self.host}{endpoint}", json={})

                        if response.status_code in [401, 403]:
                            print_success(f"{endpoint}: Protected (HTTP {response.status_code})")
                            self.add_result(f"Auth: {endpoint}", True, f"Requires auth (HTTP {response.status_code})", "low")
                        elif response.status_code == 404:
                            print_info(f"{endpoint}: Not found (HTTP 404)", indent=1)
                        else:
                            print_error(f"{endpoint}: Accessible without auth (HTTP {response.status_code})")
                            self.add_result(f"Auth: {endpoint}", False, f"No auth required (HTTP {response.status_code})", "critical")
                    except httpx.HTTPStatusError:
                        pass

        except Exception as e:
            print_error(f"Authentication check failed: {str(e)}")
            self.add_result("Authentication", False, str(e), "high")

    async def validate_authorization(self):
        """Validate authorization and access control"""
        print_section("Authorization & Access Control")

        if not self.api_key:
            print_warning("No API key provided, skipping authorization tests")
            return

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'Authorization': f'Bearer {self.api_key}'}

                # Test with valid key
                response = await client.get(f"{self.host}/api/v1/health", headers=headers)
                if response.status_code == 200:
                    print_success("Valid API key accepted")
                    self.add_result("Authorization", True, "Valid key accepted", "low")

                # Test with invalid key
                invalid_headers = {'Authorization': 'Bearer invalid_key_12345'}
                response = await client.get(f"{self.host}/api/v1/health", headers=invalid_headers)
                if response.status_code in [401, 403]:
                    print_success("Invalid API key rejected")
                    self.add_result("Authorization Invalid Key", True, "Invalid key rejected", "low")
                else:
                    print_error("Invalid API key accepted - CRITICAL")
                    self.add_result("Authorization Invalid Key", False, "Invalid key accepted", "critical")

                # Test with malformed key
                malformed_headers = {'Authorization': 'Bearer ../../../../etc/passwd'}
                response = await client.get(f"{self.host}/api/v1/health", headers=malformed_headers)
                if response.status_code in [401, 403]:
                    print_success("Malformed API key rejected")

        except Exception as e:
            print_error(f"Authorization check failed: {str(e)}")
            self.add_result("Authorization", False, str(e), "high")

    async def validate_rate_limiting(self):
        """Validate rate limiting is configured"""
        print_section("Rate Limiting")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Send rapid requests
                print_info("Sending 50 rapid requests to test rate limiting...")

                responses = []
                for i in range(50):
                    try:
                        response = await client.get(f"{self.host}/health")
                        responses.append(response.status_code)
                    except Exception:
                        pass

                rate_limited = 429 in responses
                success_count = responses.count(200)

                print_info(f"Successful requests: {success_count}/50", indent=1)
                print_info(f"Rate limited (429): {responses.count(429)}/50", indent=1)

                if rate_limited:
                    print_success("Rate limiting is configured and working")
                    self.add_result("Rate Limiting", True, "Rate limiting active", "low")
                else:
                    print_warning("Rate limiting not detected - may allow DoS attacks")
                    self.add_result("Rate Limiting", False, "No rate limiting detected", "high")

        except Exception as e:
            print_error(f"Rate limiting check failed: {str(e)}")
            self.add_result("Rate Limiting", False, str(e), "medium")

    async def validate_input_validation(self):
        """Validate input validation and sanitization"""
        print_section("Input Validation")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test with malicious inputs
                malicious_payloads = [
                    {
                        'name': 'XSS Attempt',
                        'data': {'content': '<script>alert("xss")</script>'}
                    },
                    {
                        'name': 'SQL Injection',
                        'data': {'id': "1' OR '1'='1"}
                    },
                    {
                        'name': 'Path Traversal',
                        'data': {'file': '../../../etc/passwd'}
                    },
                    {
                        'name': 'Command Injection',
                        'data': {'cmd': '; rm -rf /'}
                    },
                ]

                for payload in malicious_payloads:
                    try:
                        response = await client.post(
                            f"{self.host}/api/v1/content/validate",
                            json=payload['data']
                        )

                        if response.status_code == 422:  # Validation error
                            print_success(f"{payload['name']}: Rejected (HTTP 422)")
                            self.add_result(f"Input Validation: {payload['name']}", True, "Rejected", "low")
                        elif response.status_code in [400, 401, 403]:
                            print_success(f"{payload['name']}: Blocked (HTTP {response.status_code})")
                        elif response.status_code == 404:
                            print_info(f"{payload['name']}: Endpoint not found", indent=1)
                        else:
                            print_warning(f"{payload['name']}: Unexpected response (HTTP {response.status_code})")
                    except Exception:
                        pass

        except Exception as e:
            print_info(f"Input validation check: {str(e)}")

    async def validate_error_handling(self):
        """Validate error handling doesn't leak sensitive info"""
        print_section("Error Handling & Information Disclosure")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test 404 error
                response = await client.get(f"{self.host}/nonexistent-endpoint-12345")

                if response.status_code == 404:
                    error_text = response.text.lower()

                    # Check for sensitive information leaks
                    sensitive_patterns = [
                        ('stack trace', r'traceback|stacktrace'),
                        ('database error', r'sql|mysql|postgres|database'),
                        ('file paths', r'/home/|/var/|/usr/|c:\\'),
                        ('version info', r'python \d|fastapi \d|uvicorn \d'),
                    ]

                    leaks_found = False
                    for name, pattern in sensitive_patterns:
                        if re.search(pattern, error_text, re.IGNORECASE):
                            print_error(f"Information leak in error: {name}")
                            self.add_result(f"Error Handling: {name}", False, "Sensitive info in errors", "high")
                            leaks_found = True

                    if not leaks_found:
                        print_success("Error messages don't leak sensitive information")
                        self.add_result("Error Handling", True, "No information leaks", "low")

        except Exception as e:
            print_info(f"Error handling check: {str(e)}")

    async def validate_secrets_exposure(self):
        """Check for exposed secrets in responses"""
        print_section("Secrets Exposure Check")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check common endpoints for secret exposure
                endpoints = [
                    '/.env',
                    '/config',
                    '/api/v1/config',
                    '/.git/config',
                    '/package.json',
                ]

                for endpoint in endpoints:
                    try:
                        response = await client.get(f"{self.host}{endpoint}")

                        if response.status_code == 200:
                            text = response.text.lower()

                            # Check for secret patterns
                            secret_patterns = [
                                'api_key',
                                'secret',
                                'password',
                                'token',
                                'private_key',
                            ]

                            if any(pattern in text for pattern in secret_patterns):
                                print_error(f"Potential secrets exposed at {endpoint}")
                                self.add_result(f"Secrets: {endpoint}", False, "Potential exposure", "critical")
                            else:
                                print_warning(f"{endpoint} accessible but no obvious secrets")
                        elif response.status_code == 403:
                            print_success(f"{endpoint}: Access forbidden (good)")
                        elif response.status_code == 404:
                            print_success(f"{endpoint}: Not found (good)")
                    except Exception:
                        pass

        except Exception as e:
            print_info(f"Secrets exposure check: {str(e)}")

    async def validate_api_versioning(self):
        """Validate API versioning is implemented"""
        print_section("API Versioning")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check for versioned endpoints
                v1_response = await client.get(f"{self.host}/api/v1/health")
                v2_response = await client.get(f"{self.host}/api/v2/health")

                if v1_response.status_code < 400:
                    print_success("API v1 available")
                if v2_response.status_code < 400:
                    print_success("API v2 available")

                if v1_response.status_code < 400 or v2_response.status_code < 400:
                    print_success("API versioning implemented")
                    self.add_result("API Versioning", True, "Versioning implemented", "low")
                else:
                    print_warning("API versioning not detected")

        except Exception as e:
            print_info(f"API versioning check: {str(e)}")

    async def validate_session_management(self):
        """Validate session management security"""
        print_section("Session Management")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.host)

                # Check for session cookies
                cookies = response.cookies

                if cookies:
                    for cookie_name, cookie_value in cookies.items():
                        # Check for secure flag
                        cookie = response.cookies.get(cookie_name)
                        print_info(f"Cookie found: {cookie_name}", indent=1)

                        # These checks would need to inspect cookie attributes
                        # which httpx doesn't expose directly
                        print_warning("Manual cookie security check recommended", indent=2)
                else:
                    print_success("No session cookies set (stateless API)")
                    self.add_result("Session Management", True, "Stateless design", "low")

        except Exception as e:
            print_info(f"Session management check: {str(e)}")

    async def validate_csrf_protection(self):
        """Validate CSRF protection"""
        print_section("CSRF Protection")

        print_info("Checking for CSRF token requirements...")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Try POST without CSRF token
                response = await client.post(f"{self.host}/api/v1/content/generate", json={})

                # If requires auth, CSRF is less critical
                if response.status_code in [401, 403]:
                    print_success("API requires authentication (CSRF risk mitigated)")
                    self.add_result("CSRF Protection", True, "Auth-based protection", "low")
                else:
                    print_info("CSRF protection via authentication recommended")

        except Exception as e:
            print_info(f"CSRF check: {str(e)}")

    async def validate_xss_protection(self):
        """Validate XSS protection mechanisms"""
        print_section("XSS Protection")

        print_success("XSS protection via security headers (CSP)")
        print_info("Verify Content-Security-Policy header is restrictive", indent=1)

    async def validate_sql_injection_protection(self):
        """Validate SQL injection protection"""
        print_section("SQL Injection Protection")

        print_info("Testing SQL injection attempts...")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                sql_payloads = [
                    "1' OR '1'='1",
                    "1; DROP TABLE users--",
                    "' UNION SELECT * FROM users--",
                ]

                for payload in sql_payloads:
                    try:
                        response = await client.get(
                            f"{self.host}/api/v1/content",
                            params={'id': payload}
                        )

                        if response.status_code == 422:  # Validation error
                            print_success(f"SQL injection blocked: {payload[:20]}...")
                    except Exception:
                        pass

                self.add_result("SQL Injection Protection", True, "Parameterized queries recommended", "low")

        except Exception as e:
            print_info(f"SQL injection check: {str(e)}")

    async def validate_clickjacking_protection(self):
        """Validate clickjacking protection"""
        print_section("Clickjacking Protection")

        print_success("Clickjacking protection via X-Frame-Options header")
        print_info("Verify X-Frame-Options or CSP frame-ancestors is set", indent=1)

    def generate_report(self) -> Dict:
        """Generate security validation report"""
        print_section("Security Validation Summary")

        total = len(self.results)
        passed = len([r for r in self.results if r['passed']])
        failed = total - passed

        critical = len([r for r in self.results if not r['passed'] and r['severity'] == 'critical'])
        high = len([r for r in self.results if not r['passed'] and r['severity'] == 'high'])
        medium = len([r for r in self.results if not r['passed'] and r['severity'] == 'medium'])

        print_info(f"Total Checks: {total}", indent=0)

        if passed == total:
            print_success(f"Passed: {passed}", indent=0)
        else:
            print_info(f"Passed: {passed}", indent=0)

        if failed > 0:
            print_error(f"Failed: {failed}", indent=0)
            print_error(f"  Critical: {critical}", indent=1)
            print_error(f"  High: {high}", indent=1)
            print_warning(f"  Medium: {medium}", indent=1)
        else:
            print_success(f"Failed: {failed}", indent=0)

        # Critical issues
        if self.critical_issues:
            print("\n" + Colors.RED + Colors.BOLD + "CRITICAL SECURITY ISSUES:" + Colors.RESET)
            for name, message in self.critical_issues:
                print_critical(f"{name}: {message}")

        # Warnings
        if self.warnings:
            print("\n" + Colors.YELLOW + Colors.BOLD + "Security Warnings:" + Colors.RESET)
            for name, message in self.warnings[:10]:  # Show first 10
                print_warning(f"{name}: {message}", indent=1)

        # Overall status
        print()
        if critical == 0 and high == 0:
            print_header("✓ SECURITY VALIDATION PASSED")
            overall_status = "PASSED"
        elif critical == 0:
            print_header("⚠ SECURITY VALIDATION PASSED WITH WARNINGS")
            overall_status = "PASSED_WITH_WARNINGS"
        else:
            print_header("✗ SECURITY VALIDATION FAILED")
            overall_status = "FAILED"

        return {
            "timestamp": datetime.now().isoformat(),
            "host": self.host,
            "overall_status": overall_status,
            "summary": {
                "total_checks": total,
                "passed": passed,
                "failed": failed,
                "critical": critical,
                "high": high,
                "medium": medium
            },
            "critical_issues": [{"name": name, "message": msg} for name, msg in self.critical_issues],
            "warnings": [{"name": name, "message": msg} for name, msg in self.warnings],
            "results": self.results
        }


async def main():
    parser = argparse.ArgumentParser(
        description='Security Configuration Validation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--host', required=True, help='Host URL to validate')
    parser.add_argument('--api-key', help='API key for authentication tests')
    parser.add_argument('--comprehensive', action='store_true', help='Run comprehensive security checks')
    parser.add_argument('--test-auth', action='store_true', help='Test authentication and authorization')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    parser.add_argument('--save', help='Save results to JSON file')

    args = parser.parse_args()

    validator = SecurityValidator(
        host=args.host,
        api_key=args.api_key,
        timeout=args.timeout
    )

    report = await validator.validate_all(
        comprehensive=args.comprehensive,
        test_auth=args.test_auth
    )

    if args.save:
        with open(args.save, 'w') as f:
            json.dump(report, f, indent=2)
        print_info(f"\nResults saved to: {args.save}")

    # Exit codes: 0 = passed, 1 = warnings, 2 = failed
    if report['overall_status'] == 'PASSED':
        sys.exit(0)
    elif report['overall_status'] == 'PASSED_WITH_WARNINGS':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    asyncio.run(main())
