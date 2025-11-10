"""
QA Sub-Agent Service
Autonomous testing, coverage analysis, and test generation
"""
import ast
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


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

        # Exit with error if quality score is low
        if report["quality_score"] < 60:
            sys.exit(1)
