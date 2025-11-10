# 🧪 QA Sub-Agent Documentation

## Overview

The QA Sub-Agent is an autonomous testing and quality assurance system that analyzes test coverage, generates missing tests, and ensures code quality through comprehensive test suites.

## Current Status

**Initial Quality Score: 1/100**
- Coverage: 2.8%
- 15 files missing tests
- 82 coverage gaps

**After QA Sub-Agent Implementation:**
- ✅ Comprehensive test suites created
- ✅ Automated test generation
- ✅ Performance testing framework
- ✅ E2E testing framework
- ✅ API contract testing

## Features

### 1. **Coverage Analysis**
- Identifies untested services and APIs
- Detects coverage gaps
- Calculates quality scores

### 2. **Automated Test Generation**
- Generates test files for missing coverage
- Creates boilerplate tests for services and APIs
- Saves time on test setup

### 3. **Test Suites**

#### **Unit Tests**
- Service-level business logic testing
- Mock-based isolated testing
- Fast execution

#### **Integration Tests**
- Database integration testing
- Service interaction testing
- Real database scenarios

#### **API Contract Tests**
- Endpoint schema validation
- Status code verification
- Response structure testing
- Error handling verification

#### **Performance Tests**
- Response time benchmarks
- Load testing
- Memory usage monitoring
- Concurrent request handling

#### **E2E Tests**
- Complete user workflows
- Cross-entity interactions
- Data consistency verification
- Real user journey simulation

### 4. **Quality Metrics**
- Test coverage percentage
- Pass/fail rates
- Missing test file tracking
- Coverage gap analysis

## Usage

### Run QA Analysis

```bash
# Full QA analysis
python3 backend/services/qa_service.py

# Generate JSON report
python3 backend/services/qa_service.py --json

# Generate missing tests
python3 backend/services/qa_service.py --generate
```

### Run Specific Test Types

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# API contract tests
pytest tests/test_api_contracts.py -v

# Performance tests
pytest -m performance

# E2E tests
pytest -m e2e

# Exclude slow tests
pytest -m "not slow"
```

### Run Tests with Coverage

```bash
# Run all tests with coverage report
pytest --cov=backend --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Test Structure

```
tests/
├── test_api.py                # Existing API tests
├── test_similar_companies.py  # Existing service tests
├── test_security.py           # Security tests
├── test_company_service.py    # NEW: Company service tests
├── test_stats_service.py      # NEW: Stats service tests
├── test_api_contracts.py      # NEW: API contract tests
├── test_performance.py        # NEW: Performance tests
├── test_e2e.py                # NEW: E2E tests
└── generated/                 # Auto-generated tests
    ├── test_*_service.py
    └── test_*_api.py
```

## Test Markers

Configure test execution with pytest markers:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Database integration tests
- `@pytest.mark.e2e` - End-to-end workflows
- `@pytest.mark.performance` - Performance benchmarks
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.regression` - Regression tests for bugs

## CI/CD Integration

The QA Sub-Agent runs automatically on every push/PR via GitHub Actions.

### Viewing QA Reports

1. Go to **Actions** tab in GitHub
2. Select workflow run
3. View **QA Analysis** job
4. Download **qa-report** artifact

### Quality Score Breakdown

- **0-40 points**: Coverage score (based on code coverage %)
- **0-30 points**: Test pass rate
- **0-20 points**: Missing file penalty
- **0-10 points**: Coverage gap penalty

**Thresholds:**
- **80-100**: Excellent quality
- **60-79**: Good quality
- **40-59**: Needs improvement
- **<40**: Poor quality (CI will warn)

## Test Coverage Targets

| Category | Current | Target |
|----------|---------|--------|
| Overall Coverage | 2.8% | 80%+ |
| Services | ~0% | 90%+ |
| API Endpoints | ~30% | 95%+ |
| Business Logic | ~0% | 85%+ |

## Writing New Tests

### Unit Test Example

```python
import pytest
from backend.services.company_service import CompanyService
from unittest.mock import Mock

class TestCompanyService:
    @pytest.fixture
    def service(self):
        return CompanyService(session=Mock())

    def test_method_name(self, service):
        # Arrange
        test_data = {...}

        # Act
        result = service.some_method(test_data)

        # Assert
        assert result == expected_value
```

### Integration Test Example

```python
@pytest.mark.integration
class TestCompanyServiceIntegration:
    @pytest.fixture
    def db_service(self, db_session):
        return CompanyService(session=db_session)

    def test_with_real_db(self, db_service):
        companies, total = db_service.get_companies({}, limit=10, offset=0)
        assert isinstance(companies, list)
```

### E2E Test Example

```python
@pytest.mark.e2e
class TestUserWorkflow:
    def test_complete_workflow(self, client):
        # Step 1
        stats = client.get("/api/stats").json()

        # Step 2
        companies = client.get("/api/companies").json()

        # Step 3
        assert len(companies) <= stats["total_companies"]
```

## Performance Benchmarks

| Endpoint | Target | Current |
|----------|--------|---------|
| /health | <100ms | TBD |
| /api/stats | <2s | TBD |
| /api/companies (100) | <3s | TBD |
| /api/companies (search) | <3s | TBD |

## Best Practices

### For Developers

1. **Write tests first** (TDD) when adding new features
2. **Run tests locally** before committing
   ```bash
   pytest tests/ -v
   ```
3. **Check coverage** for new code
   ```bash
   pytest --cov=backend --cov=src
   ```
4. **Use appropriate markers** for test categorization
5. **Mock external dependencies** in unit tests
6. **Test edge cases** and error handling

### For QA

1. **Review QA reports** weekly
2. **Monitor quality score** trends
3. **Generate missing tests** for new code
   ```bash
   python3 backend/services/qa_service.py --generate
   ```
4. **Update performance benchmarks** quarterly
5. **Add regression tests** for reported bugs

## Automated Test Generation

The QA Sub-Agent can automatically generate test templates:

```bash
# Generate tests for all missing coverage
python3 backend/services/qa_service.py --generate

# Review generated tests
ls tests/generated/

# Customize and move to main tests folder
mv tests/generated/test_foo_service.py tests/
```

**Note:** Generated tests are templates. You must:
- Add specific assertions
- Implement test logic
- Add edge cases
- Verify behavior

## Troubleshooting

### Tests Failing Locally

```bash
# Check database connection
pytest tests/test_company_service.py -v

# Run without coverage (faster)
pytest tests/ --no-cov

# Run specific test
pytest tests/test_company_service.py::TestCompanyService::test_method_name -v
```

### Low Coverage Score

1. Run QA analysis to identify gaps
   ```bash
   python3 backend/services/qa_service.py
   ```

2. Review missing test files

3. Generate test templates
   ```bash
   python3 backend/services/qa_service.py --generate
   ```

4. Implement tests for critical paths first

### Performance Tests Failing

- Check database query optimization
- Review N+1 query issues
- Consider adding indexes
- Use query profiling tools

## Future Enhancements

- [ ] Mutation testing
- [ ] Visual regression testing
- [ ] API load testing (locust/k6)
- [ ] Test data factories
- [ ] Snapshot testing
- [ ] Automated flaky test detection
- [ ] Test impact analysis
- [ ] AI-powered test generation

## Configuration

Create `.qa.yml` for custom configuration:

```yaml
qa:
  coverage_target: 80
  fail_on_coverage_drop: true

  test_types:
    unit: true
    integration: true
    e2e: true
    performance: true

  performance_targets:
    health_endpoint: 100  # ms
    stats_endpoint: 2000  # ms
    list_endpoint: 3000   # ms
```

## Metrics Dashboard

View QA metrics in CI/CD:
- Quality score trend
- Coverage over time
- Test execution time
- Flaky test rate
- Coverage by module

## Support

For questions or issues:
- Check this documentation
- Review test examples in `tests/`
- Open GitHub issue with `qa` label

---

**Quality Score Target**: 80/100
**Coverage Target**: 80%+
**Last Updated**: 2025-11-10
**Version**: 1.0.0
