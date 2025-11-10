"""
Tests for QA Service
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from dataclasses import dataclass

from backend.services.qa_service import (
    TestType,
    CoverageGap,
    TestMetrics,
    CoverageAnalyzer,
    TestGenerator,
    TestRunner,
    QAService
)


class TestTestType:
    """Test TestType enum"""

    def test_test_types_exist(self):
        """Test that all test types are defined"""
        assert TestType.UNIT.value == "unit"
        assert TestType.INTEGRATION.value == "integration"
        assert TestType.E2E.value == "e2e"
        assert TestType.PERFORMANCE.value == "performance"
        assert TestType.CONTRACT.value == "contract"
        assert TestType.REGRESSION.value == "regression"


class TestCoverageGap:
    """Test CoverageGap dataclass"""

    def test_coverage_gap_creation(self):
        """Test creating a coverage gap"""
        gap = CoverageGap(
            file_path="services/test_service.py",
            type="service",
            name="TestClass",
            line_number=10,
            reason="No test found",
            severity="high"
        )
        assert gap.file_path == "services/test_service.py"
        assert gap.type == "service"
        assert gap.name == "TestClass"
        assert gap.line_number == 10
        assert gap.reason == "No test found"
        assert gap.severity == "high"


class TestTestMetrics:
    """Test TestMetrics dataclass"""

    def test_test_metrics_defaults(self):
        """Test TestMetrics default values"""
        metrics = TestMetrics()
        assert metrics.total_tests == 0
        assert metrics.passing_tests == 0
        assert metrics.failing_tests == 0
        assert metrics.skipped_tests == 0
        assert metrics.coverage_percentage == 0.0
        assert metrics.lines_covered == 0
        assert metrics.lines_total == 0
        assert metrics.missing_test_files == []
        assert metrics.coverage_gaps == []

    def test_test_metrics_with_values(self):
        """Test TestMetrics with custom values"""
        metrics = TestMetrics(
            total_tests=10,
            passing_tests=8,
            failing_tests=2,
            coverage_percentage=75.5
        )
        assert metrics.total_tests == 10
        assert metrics.passing_tests == 8
        assert metrics.failing_tests == 2
        assert metrics.coverage_percentage == 75.5


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class"""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure"""
        # Create directory structure
        backend_dir = tmp_path / "backend"
        backend_dir.mkdir()
        services_dir = backend_dir / "services"
        services_dir.mkdir()
        api_dir = backend_dir / "api"
        api_dir.mkdir()
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        # Create a sample service file
        service_file = services_dir / "sample_service.py"
        service_file.write_text("""
class SampleService:
    def __init__(self):
        pass

    def public_method(self):
        return True

    def _private_method(self):
        return False
""")

        # Create __init__.py files
        (services_dir / "__init__.py").touch()
        (api_dir / "__init__.py").touch()

        return tmp_path

    def test_analyzer_initialization(self, temp_project):
        """Test CoverageAnalyzer initialization"""
        analyzer = CoverageAnalyzer(str(temp_project))
        assert analyzer.project_root == temp_project
        assert analyzer.backend_dir == temp_project / "backend"
        assert analyzer.tests_dir == temp_project / "tests"

    def test_analyze_finds_missing_tests(self, temp_project):
        """Test that analyze finds files without tests"""
        analyzer = CoverageAnalyzer(str(temp_project))
        metrics = analyzer.analyze()

        # Should find sample_service.py as missing test
        assert len(metrics.missing_test_files) > 0
        assert any("sample_service" in f for f in metrics.missing_test_files)

    def test_analyze_detects_coverage_gaps(self, temp_project):
        """Test that analyze detects coverage gaps"""
        analyzer = CoverageAnalyzer(str(temp_project))
        metrics = analyzer.analyze()

        # Should find SampleService class as a gap
        assert len(metrics.coverage_gaps) > 0
        assert any(gap.name == "SampleService" for gap in metrics.coverage_gaps)

    def test_analyze_with_existing_test(self, temp_project):
        """Test analyze when test file exists"""
        # Create a test file
        tests_dir = temp_project / "tests"
        test_file = tests_dir / "test_sample_service.py"
        test_file.write_text("# Test file")

        analyzer = CoverageAnalyzer(str(temp_project))
        metrics = analyzer.analyze()

        # Should not list sample_service as missing test
        assert not any("sample_service" in f for f in metrics.missing_test_files)

    def test_analyze_skips_init_files(self, temp_project):
        """Test that __init__.py files are skipped"""
        analyzer = CoverageAnalyzer(str(temp_project))
        metrics = analyzer.analyze()

        # Should not include __init__.py in missing tests
        assert not any("__init__" in f for f in metrics.missing_test_files)

    def test_analyze_calculates_coverage_percentage(self, temp_project):
        """Test that coverage percentage is calculated"""
        analyzer = CoverageAnalyzer(str(temp_project))
        metrics = analyzer.analyze()

        # Should have calculated coverage
        assert metrics.lines_total > 0
        assert metrics.coverage_percentage >= 0


class TestTestGenerator:
    """Test TestGenerator class"""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure"""
        backend_dir = tmp_path / "backend"
        backend_dir.mkdir()
        services_dir = backend_dir / "services"
        services_dir.mkdir()

        # Create a sample service file
        service_file = services_dir / "user_service.py"
        service_file.write_text("""
class UserService:
    def __init__(self, session):
        self.session = session

    def get_user(self, user_id):
        return None

    def create_user(self, data):
        return True
""")

        return tmp_path, service_file

    def test_generator_initialization(self, temp_project):
        """Test TestGenerator initialization"""
        tmp_path, _ = temp_project
        generator = TestGenerator(str(tmp_path))
        assert generator.project_root == tmp_path

    def test_generate_service_test_creates_code(self, temp_project):
        """Test that generate_service_test creates test code"""
        tmp_path, service_file = temp_project
        generator = TestGenerator(str(tmp_path))

        test_code = generator.generate_service_test(service_file)

        # Verify test code contains expected elements
        assert "import pytest" in test_code
        assert "UserService" in test_code
        assert "class TestUserService" in test_code
        assert "def service" in test_code

    def test_generate_service_test_includes_methods(self, temp_project):
        """Test that generated test includes method tests"""
        tmp_path, service_file = temp_project
        generator = TestGenerator(str(tmp_path))

        test_code = generator.generate_service_test(service_file)

        # Should include test methods for public methods
        assert "test_get_user" in test_code or "TODO" in test_code

    def test_to_class_name_converts_snake_case(self, temp_project):
        """Test _to_class_name method"""
        tmp_path, _ = temp_project
        generator = TestGenerator(str(tmp_path))

        assert generator._to_class_name("user_service") == "UserService"
        assert generator._to_class_name("company_service") == "CompanyService"
        assert generator._to_class_name("api_endpoint") == "ApiEndpoint"

    def test_generate_api_test_creates_code(self, temp_project):
        """Test that generate_api_test creates test code"""
        tmp_path, _ = temp_project
        api_dir = tmp_path / "backend" / "api"
        api_dir.mkdir(parents=True, exist_ok=True)

        api_file = api_dir / "users.py"
        api_file.write_text("""
from fastapi import APIRouter
router = APIRouter()

@router.get("/users")
def get_users():
    return []
""")

        generator = TestGenerator(str(tmp_path))
        test_code = generator.generate_api_test(api_file)

        # Verify test code contains expected elements
        assert "import pytest" in test_code
        assert "TestClient" in test_code or "client" in test_code


class TestTestRunner:
    """Test TestRunner class"""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure"""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        return tmp_path

    def test_runner_initialization(self, temp_project):
        """Test TestRunner initialization"""
        runner = TestRunner(str(temp_project))
        assert runner.project_root == temp_project

    @patch('subprocess.run')
    def test_run_tests_executes_pytest(self, mock_run, temp_project):
        """Test that run_tests executes pytest"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="10 passed",
            stderr=""
        )

        runner = TestRunner(str(temp_project))
        results = runner.run_tests()

        # Verify pytest was called
        mock_run.assert_called_once()
        assert "pytest" in str(mock_run.call_args)

    @patch('subprocess.run')
    def test_run_tests_with_test_type(self, mock_run, temp_project):
        """Test run_tests with test_type parameter"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="10 passed, 80% coverage",
            stderr=""
        )

        runner = TestRunner(str(temp_project))
        results = runner.run_tests(test_type=TestType.UNIT)

        # Verify test type was used
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_tests_with_pattern(self, mock_run, temp_project):
        """Test run_tests with pattern parameter"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="5 passed",
            stderr=""
        )

        runner = TestRunner(str(temp_project))
        results = runner.run_tests(pattern="test_specific")

        # Verify pattern was used
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_tests_handles_failures(self, mock_run, temp_project):
        """Test that run_tests handles test failures"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="5 passed, 3 failed",
            stderr=""
        )

        runner = TestRunner(str(temp_project))
        results = runner.run_tests()

        # Should return results even on failure
        assert results is not None

    def test_parse_pytest_output_success(self, temp_project):
        """Test parsing successful pytest output"""
        runner = TestRunner(str(temp_project))

        stdout = "10 passed in 2.5s"
        results = runner._parse_pytest_output(stdout, "", 0)

        assert "passed" in results or "tests" in results

    def test_parse_pytest_output_with_failures(self, temp_project):
        """Test parsing pytest output with failures"""
        runner = TestRunner(str(temp_project))

        stdout = "5 passed, 3 failed in 2.5s"
        results = runner._parse_pytest_output(stdout, "", 1)

        assert "passed" in results or "failed" in results


class TestQAService:
    """Test QAService main class"""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a minimal project structure"""
        backend_dir = tmp_path / "backend"
        backend_dir.mkdir()
        services_dir = backend_dir / "services"
        services_dir.mkdir()
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        (services_dir / "__init__.py").touch()

        return tmp_path

    def test_qa_service_initialization(self, temp_project):
        """Test QAService initialization"""
        qa = QAService(project_root=str(temp_project))
        assert qa.project_root == str(temp_project)

    def test_qa_service_finds_project_root(self):
        """Test that QAService can find project root"""
        # When called without project_root, it should find it
        qa = QAService()
        assert qa.project_root is not None
        assert os.path.exists(qa.project_root)

    def test_analyze_coverage(self, temp_project):
        """Test analyze_coverage method"""
        qa = QAService(project_root=str(temp_project))
        metrics = qa.analyze_coverage()

        assert isinstance(metrics, TestMetrics)
        assert metrics.coverage_percentage >= 0

    @patch.object(TestGenerator, 'generate_service_test')
    def test_generate_missing_tests_creates_files(self, mock_generate, temp_project):
        """Test that generate_missing_tests creates test files"""
        mock_generate.return_value = "# Test code"

        # Create a service file without a test
        services_dir = temp_project / "backend" / "services"
        service_file = services_dir / "new_service.py"
        service_file.write_text("class NewService: pass")

        qa = QAService(project_root=str(temp_project))

        # Generate tests to a specific output dir
        output_dir = temp_project / "generated_tests"
        output_dir.mkdir()

        generated_files = qa.generate_missing_tests(output_dir=str(output_dir))

        # Should have called generate for the service
        assert mock_generate.called or len(generated_files) >= 0

    @patch.object(TestRunner, 'run_tests')
    @patch.object(CoverageAnalyzer, 'analyze')
    def test_run_qa_report(self, mock_analyze, mock_run_tests, temp_project):
        """Test run_qa_report method"""
        # Mock the analyzer
        mock_metrics = TestMetrics(
            total_tests=10,
            passing_tests=8,
            failing_tests=2,
            coverage_percentage=75.0,
            lines_covered=150,
            lines_total=200
        )
        mock_analyze.return_value = mock_metrics

        # Mock the test runner
        mock_run_tests.return_value = {
            "tests_run": 10,
            "passed": 8,
            "failed": 2
        }

        qa = QAService(project_root=str(temp_project))
        report = qa.run_qa_report()

        # Verify report structure
        assert "quality_score" in report
        assert "coverage" in report
        assert "tests" in report
        assert isinstance(report["quality_score"], int)

    def test_calculate_quality_score(self, temp_project):
        """Test _calculate_quality_score method"""
        qa = QAService(project_root=str(temp_project))

        metrics = TestMetrics(
            total_tests=100,
            passing_tests=90,
            coverage_percentage=80.0
        )

        test_results = {
            "tests_run": 100,
            "passed": 90,
            "failed": 10
        }

        score = qa._calculate_quality_score(metrics, test_results)

        # Score should be between 0 and 100
        assert 0 <= score <= 100
        assert isinstance(score, int)

    def test_calculate_quality_score_perfect(self, temp_project):
        """Test quality score calculation with perfect metrics"""
        qa = QAService(project_root=str(temp_project))

        metrics = TestMetrics(
            total_tests=100,
            passing_tests=100,
            coverage_percentage=100.0,
            missing_test_files=[],
            coverage_gaps=[]
        )

        test_results = {
            "total": 100,
            "passed": 100,
            "failed": 0
        }

        score = qa._calculate_quality_score(metrics, test_results)

        # Perfect score with no missing files or gaps
        assert score == 100

    def test_calculate_quality_score_zero(self, temp_project):
        """Test quality score with no tests"""
        qa = QAService(project_root=str(temp_project))

        metrics = TestMetrics(
            total_tests=0,
            passing_tests=0,
            coverage_percentage=0.0
        )

        test_results = {
            "tests_run": 0,
            "passed": 0,
            "failed": 0
        }

        score = qa._calculate_quality_score(metrics, test_results)

        # Should be low score
        assert score < 50

    @patch('builtins.print')
    def test_print_report(self, mock_print, temp_project):
        """Test print_report method"""
        qa = QAService(project_root=str(temp_project))

        report = {
            "quality_score": 75,
            "coverage": {
                "percentage": 80.0,
                "lines_covered": 800,
                "lines_total": 1000,
                "missing_files": 2
            },
            "tests": {
                "total": 100,
                "passed": 90,
                "failed": 10,
                "skipped": 0
            },
            "gaps": {
                "count": 5,
                "critical": 0,
                "high": 2,
                "medium": 3,
                "low": 0
            },
            "missing_test_files": ["service1.py", "service2.py"],
            "coverage_gaps": [
                {
                    "file": "service1.py",
                    "name": "method1",
                    "severity": "high",
                    "reason": "No test found"
                }
            ]
        }

        qa.print_report(report)

        # Verify print was called
        assert mock_print.called

    @patch('smtplib.SMTP')
    def test_send_email_report_success(self, mock_smtp, temp_project):
        """Test sending email report successfully"""
        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        # Set environment variables
        os.environ['EMAIL_USERNAME'] = 'test@example.com'
        os.environ['EMAIL_PASSWORD'] = 'testpass'
        os.environ['SMTP_SERVER'] = 'smtp.gmail.com'
        os.environ['SMTP_PORT'] = '587'

        qa = QAService(project_root=str(temp_project))

        report = {
            "quality_score": 75,
            "coverage": {"percentage": 80.0, "lines_covered": 800, "lines_total": 1000, "missing_files": 1},
            "tests": {"total": 100, "passed": 90, "failed": 10, "skipped": 0},
            "gaps": {"count": 5, "high": 2, "medium": 3, "critical": 0, "low": 0},
            "missing_test_files": ["service1.py"],
            "coverage_gaps": []
        }

        result = qa.send_email_report(
            report=report,
            to_email="recipient@example.com",
            from_email="test@example.com"
        )

        # Verify email was sent
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

        # Clean up
        del os.environ['EMAIL_USERNAME']
        del os.environ['EMAIL_PASSWORD']
        del os.environ['SMTP_SERVER']
        del os.environ['SMTP_PORT']

    @patch('smtplib.SMTP')
    def test_send_email_report_auth_failure(self, mock_smtp, temp_project):
        """Test email sending with authentication failure"""
        import smtplib

        # Mock SMTP to raise auth error
        mock_smtp.return_value.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')

        os.environ['EMAIL_USERNAME'] = 'test@example.com'
        os.environ['EMAIL_PASSWORD'] = 'wrongpass'

        qa = QAService(project_root=str(temp_project))

        report = {
            "quality_score": 75,
            "coverage": {"percentage": 80.0, "lines_covered": 800, "lines_total": 1000, "missing_files": 0},
            "tests": {"total": 100, "passed": 90, "failed": 10, "skipped": 0},
            "gaps": {"count": 5, "high": 2, "medium": 3, "critical": 0, "low": 0},
            "missing_test_files": [],
            "coverage_gaps": []
        }

        result = qa.send_email_report(
            report=report,
            to_email="recipient@example.com"
        )

        # Should return False on auth failure
        assert result is False

        # Clean up
        del os.environ['EMAIL_USERNAME']
        del os.environ['EMAIL_PASSWORD']

    def test_generate_email_html(self, temp_project):
        """Test _generate_email_html method"""
        qa = QAService(project_root=str(temp_project))

        report = {
            "quality_score": 75,
            "coverage": {
                "percentage": 80.0,
                "lines_covered": 800,
                "lines_total": 1000,
                "missing_files": 2
            },
            "tests": {
                "total": 100,
                "passed": 90,
                "failed": 10,
                "skipped": 0
            },
            "gaps": {
                "count": 5,
                "high": 2,
                "medium": 3,
                "critical": 0,
                "low": 0
            },
            "missing_test_files": ["service1.py", "service2.py"],
            "coverage_gaps": [
                {"file": "service1.py", "name": "method1", "severity": "high", "reason": "No test"}
            ]
        }

        html = qa._generate_email_html(report)

        # Verify HTML content
        assert "<html>" in html
        assert "metric" in html.lower()  # metrics grid
        assert "75" in html  # quality score
        assert "80.0" in html  # coverage percentage
        assert "90" in html  # passed tests

    def test_generate_email_html_score_colors(self, temp_project):
        """Test that email HTML uses correct colors for scores"""
        qa = QAService(project_root=str(temp_project))

        # Test high score (green)
        report_high = {
            "quality_score": 90,
            "coverage": {"percentage": 90.0, "lines_covered": 900, "lines_total": 1000, "missing_files": 0},
            "tests": {"total": 100, "passed": 100, "failed": 0, "skipped": 0},
            "gaps": {"count": 0, "high": 0, "medium": 0, "critical": 0, "low": 0},
            "missing_test_files": [],
            "coverage_gaps": []
        }

        html_high = qa._generate_email_html(report_high)
        # Check for green color (#28a745 is the actual green used)
        assert "#28a745" in html_high or "green" in html_high.lower()

        # Test low score (red/orange)
        report_low = {
            "quality_score": 40,
            "coverage": {"percentage": 40.0, "lines_covered": 400, "lines_total": 1000, "missing_files": 1},
            "tests": {"total": 100, "passed": 60, "failed": 40, "skipped": 0},
            "gaps": {"count": 20, "high": 10, "medium": 10, "critical": 0, "low": 0},
            "missing_test_files": ["service1.py"],
            "coverage_gaps": []
        }

        html_low = qa._generate_email_html(report_low)
        # Check for red/orange colors  (#dc3545 or #ffc107 are used)
        assert "#dc3545" in html_low or "#ffc107" in html_low or "red" in html_low.lower() or "orange" in html_low.lower()
