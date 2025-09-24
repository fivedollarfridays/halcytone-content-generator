#!/usr/bin/env python3
"""
Security Auditor for Halcytone Content Generator
Scans repository for exposed credentials and security issues.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class SecurityFinding:
    """Represents a security issue found during audit"""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW


class SecurityAuditor:
    """Audit repository for security issues"""

    def __init__(self):
        self.sensitive_patterns = {
            'google_api_key': {
                'pattern': r'AIza[0-9A-Za-z\-_]{35}',
                'description': 'Google API Key',
                'severity': 'CRITICAL'
            },
            'notion_token': {
                'pattern': r'ntn_[0-9A-Za-z]{50}',
                'description': 'Notion Integration Token',
                'severity': 'CRITICAL'
            },
            'openai_key': {
                'pattern': r'sk-[a-zA-Z0-9]{48}',
                'description': 'OpenAI API Key',
                'severity': 'CRITICAL'
            },
            'bearer_token': {
                'pattern': r'Bearer\s+[A-Za-z0-9\-._~+/]+',
                'description': 'Bearer Token',
                'severity': 'HIGH'
            },
            'aws_access_key': {
                'pattern': r'AKIA[0-9A-Z]{16}',
                'description': 'AWS Access Key ID',
                'severity': 'CRITICAL'
            },
            'private_key': {
                'pattern': r'-----BEGIN [A-Z ]+PRIVATE KEY-----',
                'description': 'Private Key',
                'severity': 'CRITICAL'
            },
            'password_in_url': {
                'pattern': r'[a-zA-Z][a-zA-Z0-9+.-]*://[^:]+:[^@]+@',
                'description': 'Password in URL',
                'severity': 'HIGH'
            },
            'hardcoded_secret': {
                'pattern': r'(?i)(secret|password|pwd|token|key)\s*[=:]\s*["\'][^"\']{8,}["\']',
                'description': 'Hardcoded Secret',
                'severity': 'MEDIUM'
            }
        }

        self.ignore_dirs = {'.git', '__pycache__', 'node_modules', '.pytest_cache',
                           'venv', '.venv', 'env', '.env_backup', 'dist', 'build'}
        self.ignore_extensions = {'.pyc', '.pyo', '.jpg', '.png', '.gif', '.ico',
                                '.pdf', '.zip', '.tar', '.gz', '.exe', '.dll'}

    def scan_repository(self, root_path: str = '.') -> List[SecurityFinding]:
        """Scan all files for exposed credentials and security issues"""
        findings = []
        root = Path(root_path)

        for file_path in self._get_scannable_files(root):
            try:
                findings.extend(self._scan_file(file_path))
            except Exception as e:
                print(f"Warning: Could not scan {file_path}: {e}", file=sys.stderr)

        return findings

    def _get_scannable_files(self, root: Path) -> List[Path]:
        """Get list of files to scan, excluding ignored directories and extensions"""
        scannable_files = []

        for item in root.rglob('*'):
            if not item.is_file():
                continue

            # Skip ignored directories
            if any(ignored_dir in item.parts for ignored_dir in self.ignore_dirs):
                continue

            # Skip ignored extensions
            if item.suffix.lower() in self.ignore_extensions:
                continue

            # Skip very large files (>1MB)
            try:
                if item.stat().st_size > 1024 * 1024:
                    continue
            except OSError:
                continue

            scannable_files.append(item)

        return scannable_files

    def _scan_file(self, file_path: Path) -> List[SecurityFinding]:
        """Scan a single file for security issues"""
        findings = []

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                findings.extend(self._scan_line(file_path, line_num, line))

        except Exception as e:
            print(f"Error scanning {file_path}: {e}", file=sys.stderr)

        return findings

    def _scan_line(self, file_path: Path, line_num: int, line: str) -> List[SecurityFinding]:
        """Scan a single line for security issues"""
        findings = []

        for issue_type, pattern_info in self.sensitive_patterns.items():
            matches = re.finditer(pattern_info['pattern'], line)

            for match in matches:
                # Skip if it's in a comment explaining the pattern
                if self._is_in_documentation(line, match):
                    continue

                finding = SecurityFinding(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type=issue_type,
                    description=pattern_info['description'],
                    severity=pattern_info['severity']
                )
                findings.append(finding)

        return findings

    def _is_in_documentation(self, line: str, match) -> bool:
        """Check if the match is in documentation/comments"""
        line_before_match = line[:match.start()].strip()

        # Skip if it's in a comment
        if line_before_match.startswith('#') or line_before_match.startswith('//'):
            return True

        # Skip if it's in example documentation
        if any(keyword in line.lower() for keyword in
               ['example', 'placeholder', 'your-', 'template', 'sample']):
            return True

        return False

    def generate_report(self, findings: List[SecurityFinding]) -> str:
        """Generate a security audit report"""
        if not findings:
            return "SUCCESS: No security issues found in repository scan."

        report = []
        report.append("SECURITY AUDIT REPORT")
        report.append("=" * 50)
        report.append(f"Total issues found: {len(findings)}")
        report.append("")

        # Group by severity
        by_severity = {}
        for finding in findings:
            if finding.severity not in by_severity:
                by_severity[finding.severity] = []
            by_severity[finding.severity].append(finding)

        # Report by severity
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if severity not in by_severity:
                continue

            report.append(f"{severity} ISSUES ({len(by_severity[severity])})")
            report.append("-" * 30)

            for finding in by_severity[severity]:
                report.append(f"  File: {finding.file_path}:{finding.line_number}")
                report.append(f"  Issue: {finding.description}")
                report.append(f"  Type: {finding.issue_type}")
                report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("1. Revoke all exposed API keys immediately")
        report.append("2. Generate new credentials from respective services")
        report.append("3. Update .env files with new credentials")
        report.append("4. Ensure .env files are in .gitignore")
        report.append("5. Run this audit script regularly")

        return "\n".join(report)


def main():
    """Run security audit"""
    auditor = SecurityAuditor()
    findings = auditor.scan_repository()
    report = auditor.generate_report(findings)

    print(report)

    # Exit with error code if critical issues found
    critical_count = sum(1 for f in findings if f.severity == 'CRITICAL')
    if critical_count > 0:
        print(f"\nFAILED: {critical_count} critical security issues found!")
        sys.exit(1)
    else:
        print("\nSUCCESS: Security audit passed - no critical issues found.")
        sys.exit(0)


if __name__ == "__main__":
    main()