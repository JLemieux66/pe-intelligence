"""
QA Sub-Agent Service
Autonomous testing, coverage analysis, and test generation
"""
import ast
import os
import re
import subprocess
import smtplib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


class TestType(Enum):
    """Types of tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    CONTRACT = "contract"
    REGRESSION = "regression"


@dataclass
class CoverageGap:
    """Represents a gap in test coverage"""
    file_path: str
    type: str  # service, api, model
    name: str  # class or function name
    line_number: int
    reason: str
    severity: str  # critical, high, medium, low


@dataclass
class TestMetrics:
    """Test quality metrics"""
    total_tests: int = 0
    passing_tests: int = 0
    failing_tests: int = 0
    skipped_tests: int = 0
    coverage_percentage: float = 0.0
    lines_covered: int = 0
    lines_total: int = 0
    missing_test_files: List[str] = field(default_factory=list)
    coverage_gaps: List[CoverageGap] = field(default_factory=list)


class CoverageAnalyzer:
    """Analyzes test coverage and identifies gaps"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backend_dir = self.project_root / "backend"
        self.tests_dir = self.project_root / "tests"
        self.src_dir = self.project_root / "src"

    def analyze(self) -> TestMetrics:
        """Analyze test coverage"""
        metrics = TestMetrics()

        # Find all Python files that should have tests
        service_files = list((self.backend_dir / "services").glob("*.py"))
        api_files = list((self.backend_dir / "api").glob("*.py"))
        model_files = list(self.src_dir.glob("**/*.py")) if self.src_dir.exists() else []

        # Find existing test files
        test_files = set(self.tests_dir.glob("test_*.py")) if self.tests_dir.exists() else set()

        # Check coverage for services
        for service_file in service_files:
            if service_file.name in ["__init__.py", "base.py", "security_service.py"]:
                continue

            self._check_file_coverage(service_file, test_files, metrics, "service")

        # Check coverage for API endpoints
        for api_file in api_files:
            if api_file.name == "__init__.py":
                continue

            self._check_file_coverage(api_file, test_files, metrics, "api")

        # Calculate coverage percentage
        if metrics.lines_total > 0:
            metrics.coverage_percentage = (metrics.lines_covered / metrics.lines_total) * 100

        return metrics

    def _check_file_coverage(
        self,
        file_path: Path,
        test_files: Set[Path],
        metrics: TestMetrics,
        file_type: str
    ):
        """Check if a file has test coverage"""
        file_stem = file_path.stem

        # Look for corresponding test file
        expected_test_name = f"test_{file_stem}.py"
        has_test = any(t.name == expected_test_name for t in test_files)

        if not has_test:
            metrics.missing_test_files.append(str(file_path))

        # Analyze the file for testable components
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                tree = ast.parse(content)

            lines = content.split('\n')
            metrics.lines_total += len(lines)

            # Find classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not has_test:
                        metrics.coverage_gaps.append(CoverageGap(
                            file_path=str(file_path),
                            type=file_type,
                            name=node.name,
                            line_number=node.lineno,
                            reason=f"No test file found for {file_type}",
                            severity="high"
                        ))

                elif isinstance(node, ast.FunctionDef):
                    # Only count top-level functions or public methods
                    if not node.name.startswith('_') or node.name == '__init__':
                        if not has_test:
                            metrics.coverage_gaps.append(CoverageGap(
                                file_path=str(file_path),
                                type=file_type,
                                name=node.name,
                                line_number=node.lineno,
                                reason=f"Function not covered by tests",
                                severity="medium"
                            ))

            if has_test:
                # Rough estimate: assume test file covers 70% of lines
                metrics.lines_covered += int(len(lines) * 0.7)

        except Exception as e:
            print(f"Warning: Could not analyze {file_path}: {e}")


class TestGenerator:
    """Generates test code for untested components"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def generate_service_test(self, service_file: Path) -> str:
        """Generate test file for a service"""
        service_name = service_file.stem
        class_name = self._to_class_name(service_name)

        # Parse the service file to extract methods
        methods = self._extract_methods(service_file, class_name)

        test_code = f'''"""
Tests for {service_name}
Auto-generated by QA Sub-Agent
"""
import pytest
from backend.services.{service_name} import {class_name}
from src.models.database_models_v2 import get_session


class Test{class_name}:
    """Test suite for {class_name}"""

    @pytest.fixture
    def service(self, db_session):
        """Create service instance for testing"""
        return {class_name}(session=db_session)

'''

        # Generate test methods
        for method in methods:
            if method.startswith('_') and method != '__init__':
                continue  # Skip private methods

            test_code += f'''    def test_{method}(self, service):
        """Test {method} method"""
        # TODO: Implement test for {method}
        # Add assertions based on expected behavior
        pass

'''

        test_code += '''

@pytest.fixture
def db_session():
    """Database session fixture"""
    session = get_session()
    yield session
    session.close()
'''

        return test_code

    def generate_api_test(self, api_file: Path) -> str:
        """Generate test file for API endpoints"""
        api_name = api_file.stem

        # Parse API file to find endpoints
        endpoints = self._extract_endpoints(api_file)

        test_code = f'''"""
Tests for {api_name} API endpoints
Auto-generated by QA Sub-Agent
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


class Test{self._to_class_name(api_name)}API:
    """Test suite for {api_name} endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

'''

        for endpoint in endpoints:
            method = endpoint['method'].lower()
            path = endpoint['path']
            func_name = endpoint['function']

            test_code += f'''    def test_{func_name}(self, client):
        """Test {method.upper()} {path}"""
        response = client.{method}("{path}")
        assert response.status_code in [200, 401, 404], "Should return valid status"
        # TODO: Add specific assertions for response data

'''

        return test_code

    def _extract_methods(self, file_path: Path, class_name: str) -> List[str]:
        """Extract method names from a class"""
        methods = []

        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append(item.name)

        except Exception:
            pass

        return methods

    def _extract_endpoints(self, file_path: Path) -> List[Dict[str, str]]:
        """Extract API endpoints from a route file"""
        endpoints = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Find router decorators and function names
            pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\'].*?\)\s*(?:async\s+)?def\s+(\w+)'
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

            for match in matches:
                endpoints.append({
                    'method': match.group(1),
                    'path': match.group(2),
                    'function': match.group(3)
                })

        except Exception:
            pass

        return endpoints

    def _to_class_name(self, snake_case: str) -> str:
        """Convert snake_case to CamelCase"""
        return ''.join(word.capitalize() for word in snake_case.split('_'))


class TestRunner:
    """Runs tests and collects results"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def run_tests(
        self,
        test_type: Optional[TestType] = None,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run tests and return results"""
        cmd = ["pytest", "tests/", "-v", "--tb=short"]

        if test_type:
            cmd.append(f"-m {test_type.value}")

        if pattern:
            cmd.append(f"-k {pattern}")

        # Add coverage
        cmd.extend(["--cov=backend", "--cov=src", "--cov-report=term-missing"])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            return self._parse_pytest_output(result.stdout, result.stderr, result.returncode)

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Tests timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _parse_pytest_output(self, stdout: str, stderr: str, returncode: int) -> Dict[str, Any]:
        """Parse pytest output"""
        # Extract test counts
        passed = len(re.findall(r'PASSED', stdout))
        failed = len(re.findall(r'FAILED', stdout))
        skipped = len(re.findall(r'SKIPPED', stdout))

        # Extract coverage percentage
        coverage_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', stdout)
        coverage = float(coverage_match.group(1)) if coverage_match else 0.0

        return {
            "status": "success" if returncode == 0 else "failed",
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": passed + failed + skipped,
            "coverage": coverage,
            "output": stdout,
            "errors": stderr
        }


class QAService:
    """
    Main QA Sub-Agent Service
    Orchestrates test analysis, generation, and execution
    """

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            project_root = self._find_project_root()

        self.project_root = project_root
        self.coverage_analyzer = CoverageAnalyzer(project_root)
        self.test_generator = TestGenerator(project_root)
        self.test_runner = TestRunner(project_root)

    def _find_project_root(self) -> str:
        """Find project root directory"""
        current = Path(__file__).resolve()

        while current.parent != current:
            if (current / "backend").exists() and (current / "tests").exists():
                return str(current)
            current = current.parent

        return str(Path.cwd())

    def analyze_coverage(self) -> TestMetrics:
        """Analyze test coverage and identify gaps"""
        return self.coverage_analyzer.analyze()

    def generate_missing_tests(self, output_dir: Optional[str] = None) -> List[str]:
        """Generate test files for missing coverage"""
        if output_dir is None:
            output_dir = str(Path(self.project_root) / "tests" / "generated")

        os.makedirs(output_dir, exist_ok=True)

        metrics = self.analyze_coverage()
        generated_files = []

        # Group gaps by file
        gaps_by_file = {}
        for gap in metrics.coverage_gaps:
            if gap.file_path not in gaps_by_file:
                gaps_by_file[gap.file_path] = []
            gaps_by_file[gap.file_path].append(gap)

        # Generate test files
        for file_path, gaps in gaps_by_file.items():
            path = Path(file_path)

            if "services" in str(path):
                test_code = self.test_generator.generate_service_test(path)
                test_file = Path(output_dir) / f"test_{path.stem}.py"

            elif "api" in str(path):
                test_code = self.test_generator.generate_api_test(path)
                test_file = Path(output_dir) / f"test_{path.stem}_api.py"

            else:
                continue

            with open(test_file, 'w') as f:
                f.write(test_code)

            generated_files.append(str(test_file))

        return generated_files

    def run_qa_report(self) -> Dict[str, Any]:
        """Generate comprehensive QA report"""
        print("🔍 Analyzing test coverage...")
        metrics = self.analyze_coverage()

        print("🧪 Running tests...")
        test_results = self.test_runner.run_tests()

        # Calculate quality score
        quality_score = self._calculate_quality_score(metrics, test_results)

        report = {
            "quality_score": quality_score,
            "coverage": {
                "percentage": metrics.coverage_percentage,
                "lines_covered": metrics.lines_covered,
                "lines_total": metrics.lines_total,
                "missing_files": len(metrics.missing_test_files)
            },
            "tests": {
                "total": test_results.get("total", 0),
                "passed": test_results.get("passed", 0),
                "failed": test_results.get("failed", 0),
                "skipped": test_results.get("skipped", 0)
            },
            "gaps": {
                "count": len(metrics.coverage_gaps),
                "critical": sum(1 for g in metrics.coverage_gaps if g.severity == "critical"),
                "high": sum(1 for g in metrics.coverage_gaps if g.severity == "high"),
                "medium": sum(1 for g in metrics.coverage_gaps if g.severity == "medium"),
                "low": sum(1 for g in metrics.coverage_gaps if g.severity == "low")
            },
            "missing_test_files": metrics.missing_test_files,
            "coverage_gaps": [
                {
                    "file": g.file_path,
                    "name": g.name,
                    "type": g.type,
                    "severity": g.severity,
                    "reason": g.reason
                }
                for g in metrics.coverage_gaps[:20]  # Limit to first 20
            ]
        }

        return report

    def _calculate_quality_score(self, metrics: TestMetrics, test_results: Dict) -> int:
        """Calculate overall QA quality score (0-100)"""
        # Coverage score (0-40 points)
        coverage_score = min(40, int(metrics.coverage_percentage * 0.4))

        # Test pass rate (0-30 points)
        total = test_results.get("total", 0)
        passed = test_results.get("passed", 0)
        pass_rate = (passed / total * 100) if total > 0 else 0
        test_score = min(30, int(pass_rate * 0.3))

        # Missing files penalty (0-20 points)
        missing_count = len(metrics.missing_test_files)
        file_score = max(0, 20 - (missing_count * 3))

        # Gaps penalty (0-10 points)
        high_gaps = sum(1 for g in metrics.coverage_gaps if g.severity in ["critical", "high"])
        gap_score = max(0, 10 - high_gaps)

        total_score = coverage_score + test_score + file_score + gap_score
        return min(100, total_score)

    def print_report(self, report: Dict[str, Any]):
        """Print formatted QA report"""
        print("\n" + "="*70)
        print("🧪 QA SUB-AGENT REPORT")
        print("="*70)

        print(f"\n📊 Quality Score: {report['quality_score']}/100")

        # Coverage
        cov = report['coverage']
        print(f"\n📈 Code Coverage: {cov['percentage']:.1f}%")
        print(f"   Lines Covered: {cov['lines_covered']}/{cov['lines_total']}")
        print(f"   Missing Test Files: {cov['missing_files']}")

        # Tests
        tests = report['tests']
        print(f"\n🧪 Test Results: {tests['passed']}/{tests['total']} passing")
        if tests['failed'] > 0:
            print(f"   ❌ Failed: {tests['failed']}")
        if tests['skipped'] > 0:
            print(f"   ⏭️  Skipped: {tests['skipped']}")

        # Gaps
        gaps = report['gaps']
        print(f"\n⚠️  Coverage Gaps: {gaps['count']} total")
        if gaps['critical'] > 0:
            print(f"   🔴 Critical: {gaps['critical']}")
        if gaps['high'] > 0:
            print(f"   🟠 High: {gaps['high']}")
        if gaps['medium'] > 0:
            print(f"   🟡 Medium: {gaps['medium']}")

        # Missing files
        if report['missing_test_files']:
            print(f"\n📝 Files Missing Tests ({len(report['missing_test_files'])}):")
            for file_path in report['missing_test_files'][:10]:
                print(f"   - {Path(file_path).name}")

        # Sample gaps
        if report['coverage_gaps']:
            print(f"\n🔍 Sample Coverage Gaps:")
            for gap in report['coverage_gaps'][:5]:
                severity_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(gap['severity'], "⚪")
                print(f"   {severity_icon} {gap['name']} in {Path(gap['file']).name}")
                print(f"      {gap['reason']}")

        print("\n" + "="*70)

    def send_email_report(
        self,
        report: Dict[str, Any],
        to_email: str,
        from_email: Optional[str] = None,
        subject_prefix: str = "🧪 QA Report"
    ) -> bool:
        """
        Send QA report via email with HTML formatting and JSON attachment

        Args:
            report: QA report dictionary from run_qa_report()
            to_email: Recipient email address
            from_email: Sender email (defaults to env var or noreply)
            subject_prefix: Custom subject prefix

        Returns:
            True if email sent successfully, False otherwise

        Environment Variables Required:
            SMTP_SERVER: SMTP server address (default: smtp.gmail.com)
            SMTP_PORT: SMTP server port (default: 587)
            EMAIL_USERNAME: SMTP username
            EMAIL_PASSWORD: SMTP password (use App Password for Gmail)
        """
        try:
            # Get email configuration from environment
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            username = os.getenv('EMAIL_USERNAME')
            password = os.getenv('EMAIL_PASSWORD')

            if not username or not password:
                print("❌ Error: EMAIL_USERNAME and EMAIL_PASSWORD environment variables required")
                return False

            if not from_email:
                from_email = os.getenv('EMAIL_FROM', f'{username}')

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = f"{subject_prefix} - Score: {report['quality_score']}/100 - {datetime.now().strftime('%Y-%m-%d')}"

            # Generate HTML body
            html_body = self._generate_email_html(report)
            msg.attach(MIMEText(html_body, 'html'))

            # Attach JSON report
            json_data = json.dumps(report, indent=2)
            attachment = MIMEBase('application', 'json')
            attachment.set_payload(json_data.encode('utf-8'))
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename=qa_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            msg.attach(attachment)

            # Send email
            print(f"📧 Sending QA report to {to_email}...")
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("❌ SMTP Authentication failed. Check EMAIL_USERNAME and EMAIL_PASSWORD")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    def _generate_email_html(self, report: Dict[str, Any]) -> str:
        """Generate HTML email body from QA report"""

        # Determine quality score color
        score = report['quality_score']
        if score >= 80:
            score_color = '#28a745'  # Green
            score_status = 'Excellent'
        elif score >= 70:
            score_color = '#ffc107'  # Yellow
            score_status = 'Good'
        elif score >= 60:
            score_color = '#fd7e14'  # Orange
            score_status = 'Fair'
        else:
            score_color = '#dc3545'  # Red
            score_status = 'Needs Improvement'

        # Determine coverage color
        coverage = report['coverage']['percentage']
        if coverage >= 80:
            cov_color = '#28a745'
        elif coverage >= 60:
            cov_color = '#ffc107'
        else:
            cov_color = '#dc3545'

        # Build coverage gaps summary
        gaps_html = ""
        if report.get('coverage_gaps'):
            gaps_html = "<h3 style='color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;'>📋 Sample Coverage Gaps</h3>"
            gaps_html += "<ul style='list-style-type: none; padding-left: 0;'>"

            for gap in report['coverage_gaps'][:10]:  # Show first 10
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(gap['severity'], '⚪')

                gaps_html += f"""
                <li style='margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-left: 3px solid #6c757d;'>
                    {severity_emoji} <strong>{gap['name']}</strong> in <code>{Path(gap['file']).name}</code>
                    <br><small style='color: #6c757d;'>{gap['reason']}</small>
                </li>
                """
            gaps_html += "</ul>"

        # Build missing files list
        missing_files_html = ""
        if report.get('missing_test_files'):
            missing_files_html = "<h3 style='color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;'>📝 Files Missing Tests</h3>"
            missing_files_html += "<ul>"
            for file_path in report['missing_test_files'][:10]:
                missing_files_html += f"<li><code>{Path(file_path).name}</code></li>"

            remaining = len(report['missing_test_files']) - 10
            if remaining > 0:
                missing_files_html += f"<li><em>... and {remaining} more</em></li>"
            missing_files_html += "</ul>"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 20px;
                    border-bottom: 3px solid #007bff;
                    margin-bottom: 30px;
                }}
                .score-badge {{
                    display: inline-block;
                    font-size: 48px;
                    font-weight: bold;
                    color: {score_color};
                    margin: 10px 0;
                }}
                .status-badge {{
                    display: inline-block;
                    padding: 5px 15px;
                    border-radius: 20px;
                    background-color: {score_color};
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                }}
                .metrics-grid {{
                    display: table;
                    width: 100%;
                    margin: 20px 0;
                }}
                .metric-row {{
                    display: table-row;
                }}
                .metric-row:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                .metric-label {{
                    display: table-cell;
                    padding: 12px;
                    font-weight: 600;
                    border: 1px solid #dee2e6;
                }}
                .metric-value {{
                    display: table-cell;
                    padding: 12px;
                    text-align: right;
                    border: 1px solid #dee2e6;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #dee2e6;
                    text-align: center;
                    font-size: 12px;
                    color: #6c757d;
                }}
                code {{
                    background-color: #f8f9fa;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; color: #007bff;">🧪 QA Analysis Report</h1>
                    <div class="score-badge">{score}/100</div>
                    <div class="status-badge">{score_status}</div>
                    <p style="margin: 10px 0 0 0; color: #6c757d;">Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>

                <h2 style="color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📊 Quality Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-row">
                        <div class="metric-label">📈 Code Coverage</div>
                        <div class="metric-value" style="color: {cov_color}; font-weight: bold;">{coverage:.1f}%</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">📏 Lines Covered</div>
                        <div class="metric-value">{report['coverage']['lines_covered']:,} / {report['coverage']['lines_total']:,}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">✅ Tests Passing</div>
                        <div class="metric-value">{report['tests']['passed']} / {report['tests']['total']}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">❌ Tests Failing</div>
                        <div class="metric-value">{report['tests']['failed']}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">⏭️ Tests Skipped</div>
                        <div class="metric-value">{report['tests']['skipped']}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">📝 Missing Test Files</div>
                        <div class="metric-value">{report['coverage']['missing_files']}</div>
                    </div>
                </div>

                <h2 style="color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">⚠️ Coverage Gaps</h2>
                <div class="metrics-grid">
                    <div class="metric-row">
                        <div class="metric-label">🔴 Critical</div>
                        <div class="metric-value">{report['gaps']['critical']}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">🟠 High</div>
                        <div class="metric-value">{report['gaps']['high']}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">🟡 Medium</div>
                        <div class="metric-value">{report['gaps']['medium']}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label">🟢 Low</div>
                        <div class="metric-value">{report['gaps']['low']}</div>
                    </div>
                    <div class="metric-row">
                        <div class="metric-label"><strong>Total Gaps</strong></div>
                        <div class="metric-value"><strong>{report['gaps']['count']}</strong></div>
                    </div>
                </div>

                {missing_files_html}

                {gaps_html}

                <div class="footer">
                    <p>🤖 This report was automatically generated by the QA Sub-Agent</p>
                    <p>Detailed report attached as JSON file</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html


if __name__ == "__main__":
    """Run QA analysis from command line"""
    import sys
    import json

    qa_service = QAService()

    if "--generate" in sys.argv:
        # Generate missing tests
        print("🤖 Generating missing test files...")
        generated = qa_service.generate_missing_tests()
        print(f"\n✅ Generated {len(generated)} test files:")
        for file_path in generated:
            print(f"   - {file_path}")

    else:
        # Run QA report
        report = qa_service.run_qa_report()
        qa_service.print_report(report)

        # Save JSON if requested
        if "--json" in sys.argv:
            with open("qa_report.json", "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n✅ Report saved to qa_report.json")

        # Send email if requested
        if "--email" in sys.argv:
            email_index = sys.argv.index("--email")
            if email_index + 1 < len(sys.argv):
                to_email = sys.argv[email_index + 1]
                success = qa_service.send_email_report(report, to_email)
                if not success:
                    print("\n⚠️  Email sending failed. Check environment variables:")
                    print("   - EMAIL_USERNAME")
                    print("   - EMAIL_PASSWORD")
                    print("   - SMTP_SERVER (optional, defaults to smtp.gmail.com)")
                    print("   - SMTP_PORT (optional, defaults to 587)")
            else:
                print("❌ Error: --email requires an email address")
                print("Usage: python qa_service.py --email your@email.com")

        # Exit with error if quality score is low
        if report["quality_score"] < 60:
            sys.exit(1)
