"""
Security Sub-Agent Service
Autonomous security scanning and monitoring for OWASP Top 10 vulnerabilities
"""
import ast
import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class SecurityLevel(Enum):
    """Security issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityIssue:
    """Represents a security vulnerability or issue"""
    category: str
    severity: SecurityLevel
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "category": self.category,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "recommendation": self.recommendation,
            "cwe_id": self.cwe_id
        }


class SecurityScanner:
    """Base class for security scanners"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[SecurityIssue] = []

    def scan(self) -> List[SecurityIssue]:
        """Run security scan - to be implemented by subclasses"""
        raise NotImplementedError

    def add_issue(self, issue: SecurityIssue):
        """Add a security issue to the list"""
        self.issues.append(issue)


class AuthenticationScanner(SecurityScanner):
    """
    Scans for authentication/authorization vulnerabilities
    OWASP A01:2021 - Broken Access Control
    """

    def scan(self) -> List[SecurityIssue]:
        """Scan API endpoints for missing authentication"""
        self.issues = []

        # Find all API route files
        api_dir = self.project_root / "backend" / "api"
        if not api_dir.exists():
            return self.issues

        for api_file in api_dir.glob("*.py"):
            if api_file.name == "__init__.py":
                continue

            self._scan_file(api_file)

        return self.issues

    def _scan_file(self, file_path: Path):
        """Scan a single API file for authentication issues"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                tree = ast.parse(content)

            # Check for unprotected PUT/POST/DELETE/PATCH endpoints
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._check_endpoint_auth(node, file_path, content)

        except Exception as e:
            self.add_issue(SecurityIssue(
                category="Authentication",
                severity=SecurityLevel.LOW,
                title=f"Failed to parse {file_path.name}",
                description=f"Could not analyze file for security issues: {str(e)}",
                file_path=str(file_path)
            ))

    def _check_endpoint_auth(self, func_node: ast.FunctionDef, file_path: Path, content: str):
        """Check if an endpoint has proper authentication"""
        # Look for router decorators
        mutating_methods = ['put', 'post', 'delete', 'patch']

        # Endpoints that legitimately don't need auth
        public_endpoints = ['/login', '/register', '/health', '/']

        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                # Get the decorator name (e.g., router.put, router.post)
                if isinstance(decorator.func, ast.Attribute):
                    method = decorator.func.attr.lower()

                    if method in mutating_methods:
                        # Get the endpoint path from decorator args
                        endpoint_path = "unknown"
                        if decorator.args:
                            if isinstance(decorator.args[0], ast.Constant):
                                endpoint_path = decorator.args[0].value

                        # Skip public endpoints
                        if endpoint_path in public_endpoints:
                            continue

                        # Check if this endpoint has authentication
                        has_auth = self._has_authentication(func_node, decorator)

                        if not has_auth:
                            self.add_issue(SecurityIssue(
                                category="Authentication",
                                severity=SecurityLevel.HIGH,
                                title=f"Unprotected {method.upper()} endpoint",
                                description=f"Endpoint '{endpoint_path}' allows {method.upper()} operations without authentication",
                                file_path=str(file_path),
                                line_number=func_node.lineno,
                                recommendation=f"Add authentication using: dependencies=[Depends(verify_admin_token)]",
                                cwe_id="CWE-862"  # Missing Authorization
                            ))

    def _has_authentication(self, func_node: ast.FunctionDef, decorator: ast.Call) -> bool:
        """Check if endpoint has authentication via dependencies or function params"""
        # Check for dependencies in decorator
        if decorator.keywords:
            for keyword in decorator.keywords:
                if keyword.arg == "dependencies":
                    return True

        # Check for verify_admin_token or similar in function parameters
        for arg in func_node.args.args:
            if 'token' in arg.arg.lower() or 'auth' in arg.arg.lower():
                return True

        return False


class RateLimitScanner(SecurityScanner):
    """
    Scans for missing rate limiting protection
    OWASP A04:2021 - Insecure Design
    """

    def scan(self) -> List[SecurityIssue]:
        """Check if rate limiting is implemented"""
        self.issues = []

        # Check main.py for rate limiting middleware
        main_file = self.project_root / "backend" / "main.py"
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()

            # Check for common rate limiting libraries
            rate_limit_keywords = [
                'slowapi', 'ratelimit', 'rate_limit',
                'RateLimitMiddleware', 'Limiter'
            ]

            has_rate_limiting = any(keyword in content for keyword in rate_limit_keywords)

            if not has_rate_limiting:
                self.add_issue(SecurityIssue(
                    category="Rate Limiting",
                    severity=SecurityLevel.HIGH,
                    title="No rate limiting detected",
                    description="Application lacks rate limiting protection, vulnerable to brute force and DoS attacks",
                    file_path=str(main_file),
                    recommendation="Implement rate limiting using SlowAPI or similar middleware",
                    cwe_id="CWE-770"  # Allocation of Resources Without Limits
                ))

        return self.issues


class InputValidationScanner(SecurityScanner):
    """
    Scans for input validation vulnerabilities
    OWASP A03:2021 - Injection
    """

    def scan(self) -> List[SecurityIssue]:
        """Scan for potential injection vulnerabilities"""
        self.issues = []

        # Scan API files for direct SQL usage (should use ORM)
        api_dir = self.project_root / "backend" / "api"
        services_dir = self.project_root / "backend" / "services"

        for directory in [api_dir, services_dir]:
            if directory.exists():
                for py_file in directory.glob("*.py"):
                    self._scan_for_sql_injection(py_file)
                    self._scan_for_command_injection(py_file)

        return self.issues

    def _scan_for_sql_injection(self, file_path: Path):
        """Check for potential SQL injection vulnerabilities"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Look for string formatting in SQL-like statements
            dangerous_patterns = [
                (r'\.execute\([f"\'].*?%s', 'String formatting in SQL execute'),
                (r'\.execute\(f["\']', 'f-string in SQL execute'),
                (r'\.execute\(.*?\+', 'String concatenation in SQL execute'),
            ]

            for pattern, description in dangerous_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    self.add_issue(SecurityIssue(
                        category="SQL Injection",
                        severity=SecurityLevel.CRITICAL,
                        title="Potential SQL injection vulnerability",
                        description=f"{description} detected - use parameterized queries",
                        file_path=str(file_path),
                        line_number=line_num,
                        recommendation="Use SQLAlchemy ORM or parameterized queries",
                        cwe_id="CWE-89"  # SQL Injection
                    ))

        except Exception:
            pass

    def _scan_for_command_injection(self, file_path: Path):
        """Check for potential command injection vulnerabilities"""
        # Skip scanning the security service itself
        if 'security_service.py' in str(file_path):
            return

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Look for dangerous command execution patterns
            # Skip lines that are in strings or comments
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                # Skip comments and docstrings
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue

                # Check for dangerous patterns
                if 'os.system(' in line and not line.strip().startswith('#'):
                    # Check if it's in actual code (not a string)
                    if 'r\'' not in line and 'r"' not in line:  # Skip regex strings
                        self.add_issue(SecurityIssue(
                            category="Command Injection",
                            severity=SecurityLevel.CRITICAL,
                            title="Potential command injection vulnerability",
                            description="os.system() usage detected - avoid shell execution with user input",
                            file_path=str(file_path),
                            line_number=line_num,
                            recommendation="Use subprocess.run() with shell=False or sanitize input thoroughly",
                            cwe_id="CWE-78"  # OS Command Injection
                        ))

                if 'subprocess.call' in line and 'shell=True' in line:
                    self.add_issue(SecurityIssue(
                        category="Command Injection",
                        severity=SecurityLevel.CRITICAL,
                        title="Potential command injection vulnerability",
                        description="subprocess with shell=True detected - vulnerable to command injection",
                        file_path=str(file_path),
                        line_number=line_num,
                        recommendation="Use shell=False and pass arguments as a list",
                        cwe_id="CWE-78"
                    ))

        except Exception:
            pass


class SecretScanner(SecurityScanner):
    """
    Scans for exposed secrets and credentials
    OWASP A05:2021 - Security Misconfiguration
    """

    def scan(self) -> List[SecurityIssue]:
        """Scan for hardcoded secrets"""
        self.issues = []

        # Scan Python files for potential secrets
        for py_file in self.project_root.rglob("*.py"):
            # Skip virtual environments, dependencies, and test files
            path_str = str(py_file)
            skip_patterns = ['venv', 'site-packages', 'test_security.py', 'conftest.py']
            if any(pattern in path_str for pattern in skip_patterns):
                continue

            self._scan_file_for_secrets(py_file)

        return self.issues

    def _scan_file_for_secrets(self, file_path: Path):
        """Scan a file for hardcoded secrets"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Patterns for common secrets (excluding env var usage)
            secret_patterns = [
                (r'password\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded password'),
                (r'api[_-]?key\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded API key'),
                (r'secret[_-]?key\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded secret key'),
                (r'token\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded token'),
            ]

            for pattern, description in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    matched_text = match.group(0)

                    # Skip if it's using os.getenv or environment variables
                    if 'getenv' in matched_text or 'environ' in matched_text:
                        continue

                    # Skip common test/example values
                    if any(word in matched_text.lower() for word in ['test', 'example', 'dummy', 'your-']):
                        continue

                    line_num = content[:match.start()].count('\n') + 1
                    self.add_issue(SecurityIssue(
                        category="Secrets Management",
                        severity=SecurityLevel.CRITICAL,
                        title=f"{description} detected",
                        description="Hardcoded credentials found in source code",
                        file_path=str(file_path),
                        line_number=line_num,
                        recommendation="Use environment variables or a secrets manager",
                        cwe_id="CWE-798"  # Use of Hard-coded Credentials
                    ))

        except Exception:
            pass


class CORSScanner(SecurityScanner):
    """
    Scans for CORS misconfigurations
    OWASP A05:2021 - Security Misconfiguration
    """

    def scan(self) -> List[SecurityIssue]:
        """Check CORS configuration"""
        self.issues = []

        main_file = self.project_root / "backend" / "main.py"
        if main_file.exists():
            with open(main_file, 'r') as f:
                content = f.read()

            # Check for wildcard CORS origins specifically
            if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
                self.add_issue(SecurityIssue(
                    category="CORS",
                    severity=SecurityLevel.MEDIUM,
                    title="Overly permissive CORS configuration",
                    description="CORS allows all origins (*), which may expose the API to unauthorized access",
                    file_path=str(main_file),
                    recommendation="Restrict CORS to specific trusted origins",
                    cwe_id="CWE-942"  # Permissive Cross-domain Policy
                ))

            # Check for allow_credentials with wildcard origins specifically
            if 'allow_credentials=True' in content and ('allow_origins=["*"]' in content or "allow_origins=['*']" in content):
                self.add_issue(SecurityIssue(
                    category="CORS",
                    severity=SecurityLevel.HIGH,
                    title="Dangerous CORS configuration",
                    description="CORS allows credentials with wildcard origins - security vulnerability",
                    file_path=str(main_file),
                    recommendation="Never use allow_credentials=True with allow_origins=['*']",
                    cwe_id="CWE-942"
                ))

        return self.issues


class SecurityService:
    """
    Main Security Sub-Agent Service
    Orchestrates security scans and generates reports
    """

    def __init__(self, project_root: Optional[str] = None):
        """Initialize security service"""
        if project_root is None:
            # Auto-detect project root
            project_root = self._find_project_root()

        self.project_root = project_root
        self.scanners = [
            AuthenticationScanner(project_root),
            RateLimitScanner(project_root),
            InputValidationScanner(project_root),
            SecretScanner(project_root),
            CORSScanner(project_root),
        ]

    def _find_project_root(self) -> str:
        """Find project root by looking for key files"""
        current = Path(__file__).resolve()

        # Go up until we find the project root
        while current.parent != current:
            if (current / "backend").exists() and (current / "Pipfile").exists():
                return str(current)
            current = current.parent

        return str(Path.cwd())

    def run_all_scans(self) -> Dict[str, Any]:
        """Run all security scans and return report"""
        all_issues = []

        for scanner in self.scanners:
            print(f"Running {scanner.__class__.__name__}...")
            issues = scanner.scan()
            all_issues.extend(issues)

        # Generate report
        report = self._generate_report(all_issues)
        return report

    def run_scan(self, scanner_name: str) -> List[SecurityIssue]:
        """Run a specific scanner"""
        scanner_map = {
            'auth': AuthenticationScanner,
            'rate_limit': RateLimitScanner,
            'input_validation': InputValidationScanner,
            'secrets': SecretScanner,
            'cors': CORSScanner,
        }

        if scanner_name not in scanner_map:
            raise ValueError(f"Unknown scanner: {scanner_name}")

        scanner = scanner_map[scanner_name](self.project_root)
        return scanner.scan()

    def _generate_report(self, issues: List[SecurityIssue]) -> Dict[str, Any]:
        """Generate security scan report"""
        # Count issues by severity
        severity_counts = {
            SecurityLevel.CRITICAL: 0,
            SecurityLevel.HIGH: 0,
            SecurityLevel.MEDIUM: 0,
            SecurityLevel.LOW: 0,
            SecurityLevel.INFO: 0,
        }

        for issue in issues:
            severity_counts[issue.severity] += 1

        # Group issues by category
        issues_by_category = {}
        for issue in issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue.to_dict())

        # Calculate security score (0-100)
        total_issues = len(issues)
        critical_weight = 20
        high_weight = 10
        medium_weight = 5
        low_weight = 1

        deductions = (
            severity_counts[SecurityLevel.CRITICAL] * critical_weight +
            severity_counts[SecurityLevel.HIGH] * high_weight +
            severity_counts[SecurityLevel.MEDIUM] * medium_weight +
            severity_counts[SecurityLevel.LOW] * low_weight
        )

        security_score = max(0, 100 - deductions)

        return {
            "summary": {
                "total_issues": total_issues,
                "critical": severity_counts[SecurityLevel.CRITICAL],
                "high": severity_counts[SecurityLevel.HIGH],
                "medium": severity_counts[SecurityLevel.MEDIUM],
                "low": severity_counts[SecurityLevel.LOW],
                "info": severity_counts[SecurityLevel.INFO],
                "security_score": security_score
            },
            "issues_by_category": issues_by_category,
            "all_issues": [issue.to_dict() for issue in issues]
        }

    def print_report(self, report: Dict[str, Any]):
        """Print formatted security report"""
        summary = report["summary"]

        print("\n" + "="*70)
        print("🔒 SECURITY SCAN REPORT")
        print("="*70)
        print(f"\n📊 Security Score: {summary['security_score']}/100")
        print(f"\n📋 Total Issues: {summary['total_issues']}")
        print(f"   🔴 Critical: {summary['critical']}")
        print(f"   🟠 High: {summary['high']}")
        print(f"   🟡 Medium: {summary['medium']}")
        print(f"   🟢 Low: {summary['low']}")
        print(f"   ℹ️  Info: {summary['info']}")

        if summary['total_issues'] > 0:
            print("\n" + "="*70)
            print("📝 ISSUES BY CATEGORY")
            print("="*70)

            for category, issues in report["issues_by_category"].items():
                print(f"\n🔍 {category} ({len(issues)} issues)")
                print("-" * 70)

                for issue in issues:
                    severity_icon = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🟢",
                        "info": "ℹ️"
                    }[issue['severity']]

                    print(f"\n{severity_icon} {issue['title']}")
                    print(f"   Description: {issue['description']}")

                    if issue['file_path']:
                        location = f"{issue['file_path']}"
                        if issue['line_number']:
                            location += f":{issue['line_number']}"
                        print(f"   Location: {location}")

                    if issue['recommendation']:
                        print(f"   💡 Recommendation: {issue['recommendation']}")

                    if issue['cwe_id']:
                        print(f"   🏷️  {issue['cwe_id']}")

        print("\n" + "="*70)


if __name__ == "__main__":
    """Run security scans from command line"""
    import sys
    import json

    service = SecurityService()

    # Check if specific scanner requested (non-flag argument)
    scanner_name = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            scanner_name = arg
            break

    if scanner_name:
        # Run specific scanner
        issues = service.run_scan(scanner_name)
        report = service._generate_report(issues)
    else:
        # Run all scans
        report = service.run_all_scans()

    # Print report
    service.print_report(report)

    # Optionally save to JSON
    if "--json" in sys.argv:
        with open("security_report.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n✅ Report saved to security_report.json")

    # Exit with error code if critical/high issues found
    if report["summary"]["critical"] > 0 or report["summary"]["high"] > 0:
        sys.exit(1)
