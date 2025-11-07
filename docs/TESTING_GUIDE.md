# Testing Guide

This document describes the testing infrastructure for the documentation-helper application.

## Overview

The project uses a comprehensive automated testing setup with:
- **Backend**: pytest + FastAPI TestClient
- **Frontend**: Vitest + React Testing Library
- **CI/CD**: GitHub Actions for automated test execution

## Backend Testing

### Framework
- **pytest**: Main testing framework
- **FastAPI TestClient**: For API endpoint testing
- **SQLite in-memory**: Test database (session-scoped)
- **Coverage**: pytest-cov for code coverage reporting

### Running Tests

```bash
# Install dependencies
pipenv install --dev pytest pytest-cov httpx faker

# Run all tests
pipenv run pytest

# Run with coverage
pipenv run pytest --cov=backend --cov=src --cov-report=html

# Run specific test file
pipenv run pytest tests/test_api.py

# Run tests with specific marker
pipenv run pytest -m regression
pipenv run pytest -m slow
```

### Test Structure

```
tests/
├── __init__.py           # Package initialization
├── conftest.py          # Shared fixtures
└── test_api.py          # API endpoint tests
```

### Key Fixtures (conftest.py)

- `test_db_engine`: Session-scoped SQLite in-memory database
- `db_session`: Function-scoped database session with automatic rollback
- `sample_pe_firm`: Test PE firm data
- `sample_company`: Test company data
- `sample_investment`: Test investment data
- `api_client`: FastAPI TestClient instance
- `admin_token`: JWT token for authenticated endpoints

### Test Categories

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test API endpoints end-to-end (marked with `@pytest.mark.integration`)
3. **Regression Tests**: Prevent previously fixed bugs (marked with `@pytest.mark.regression`)
4. **Slow Tests**: Tests that take longer to run (marked with `@pytest.mark.slow`)

### Example Test

```python
def test_companies_filter_by_country(api_client, sample_company):
    response = api_client.get("/api/companies?country=United States")
    assert response.status_code == 200
    data = response.json()
    assert all(c["country"] == "United States" for c in data["companies"])
```

## Frontend Testing

### Framework
- **Vitest**: Fast unit test framework for Vite projects
- **React Testing Library**: User-centric component testing
- **@testing-library/user-event**: User interaction simulation
- **jsdom**: DOM environment for Node.js

### Running Tests

```bash
# Install dependencies
cd frontend-react
npm install --save-dev vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom jsdom @vitest/ui

# Run all tests
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### Test Structure

```
frontend-react/
├── tests/
│   ├── setup.ts                    # Test setup and global config
│   └── HorizontalFilters.test.tsx  # Component tests
└── vitest.config.ts                # Vitest configuration
```

### Writing Component Tests

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import MyComponent from '../src/components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    const queryClient = new QueryClient()
    render(
      <QueryClientProvider client={queryClient}>
        <MyComponent />
      </QueryClientProvider>
    )
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```

### Best Practices

1. **Test user behavior, not implementation details**
   - Use `screen.getByRole`, `screen.getByLabelText` instead of test IDs
   - Test what users see and interact with

2. **Mock React Query**
   - Create fresh QueryClient for each test
   - Set `retry: false` in defaultOptions

3. **Use waitFor for async operations**
   ```typescript
   await waitFor(() => {
     expect(screen.getByText('Loaded Data')).toBeInTheDocument()
   })
   ```

4. **Clean up after tests**
   - Automatically handled by setup.ts
   - Clear mocks in beforeEach: `mockFn.mockClear()`

## CI/CD Pipeline

### GitHub Actions Workflow

The `.github/workflows/tests.yml` file defines the automated testing pipeline:

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to any branch

**Jobs**:

1. **backend-tests**
   - Python 3.9 environment
   - Install dependencies via pipenv
   - Run pytest with coverage
   - Upload coverage to Codecov

2. **frontend-tests**
   - Node.js 18 environment
   - Install dependencies via npm
   - Run Vitest with coverage
   - Upload coverage to Codecov

3. **lint**
   - Run flake8 (Python)
   - Run black --check (Python formatting)
   - Run ESLint (TypeScript/React)

### Coverage Reports

Coverage reports are automatically:
- Generated locally in HTML format
- Uploaded to Codecov on CI runs
- Displayed in terminal output

**Viewing Coverage Locally**:
```bash
# Backend
pipenv run pytest --cov=backend --cov-report=html
# Open htmlcov/index.html

# Frontend
npm run test:coverage
# Open coverage/index.html
```

## Regression Tests

Specific tests prevent previously fixed bugs:

### California Filter Bug
```python
@pytest.mark.regression
def test_california_filter_only_shows_us_companies(api_client, db_session):
    """
    REGRESSION: California filter was showing companies from other countries
    because state filtering didn't enforce country='United States'
    """
    # Test that California filter only returns US companies
```

### Pagination Count Bug
```python
@pytest.mark.regression
def test_pagination_shows_filtered_count_not_total(api_client, db_session):
    """
    REGRESSION: Pagination was showing total count instead of filtered count
    """
    # Test that pagination uses filtered count
```

### Multiple Filter Selection Bug
```python
@pytest.mark.regression
def test_multiple_filter_selection(api_client, sample_company):
    """
    REGRESSION: Dropdowns were closing/options disappearing after first selection
    """
    # Test that multiple filters can be selected simultaneously
```

## Test Database

Backend tests use SQLite in-memory database:
- **Session-scoped engine**: Created once per test session
- **Function-scoped session**: New session with rollback per test
- **Automatic schema creation**: Tables created from SQLAlchemy models
- **Isolated tests**: Each test gets clean database state

## Writing New Tests

### Backend Test Checklist

- [ ] Use appropriate fixtures from conftest.py
- [ ] Test happy path and error cases
- [ ] Verify response status codes
- [ ] Validate response structure and data types
- [ ] Test filtering, pagination, and search
- [ ] Add regression test for bug fixes
- [ ] Mark slow tests with `@pytest.mark.slow`

### Frontend Test Checklist

- [ ] Wrap component in QueryClientProvider
- [ ] Test user interactions (clicks, typing, etc.)
- [ ] Verify component renders correctly
- [ ] Test conditional rendering
- [ ] Mock API calls if needed
- [ ] Use `waitFor` for async updates
- [ ] Test accessibility (ARIA roles, labels)

## Continuous Integration

Every commit triggers:
1. ✅ Backend unit tests
2. ✅ Frontend unit tests
3. ✅ Code linting (Python + TypeScript)
4. ✅ Coverage reporting

**Pull Request Requirements**:
- All tests must pass
- Code must pass linting
- Coverage should not decrease significantly

## Troubleshooting

### Backend Tests Failing

```bash
# Check database schema
pipenv run python -c "from backend.database import Base; print(Base.metadata.tables.keys())"

# Run single test with verbose output
pipenv run pytest tests/test_api.py::test_name -vv

# Check fixture availability
pipenv run pytest --fixtures
```

### Frontend Tests Failing

```bash
# Clear cache
npm run test -- --clearCache

# Run in UI mode for debugging
npm run test:ui

# Check for missing mocks
# Ensure QueryClient is provided in test
```

### CI/CD Failures

1. Check GitHub Actions logs
2. Verify dependencies are installed correctly
3. Ensure environment variables are set
4. Check for race conditions in async tests

## Future Enhancements

- [ ] Add E2E tests with Playwright/Cypress
- [ ] Increase coverage target to 90%+
- [ ] Add performance benchmarking
- [ ] Add visual regression testing
- [ ] Add mutation testing
- [ ] Set up test data factories
