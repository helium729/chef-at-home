# FamilyChef Testing Documentation

This document outlines the comprehensive testing strategy implemented in Phase 6 of the FamilyChef project.

## Testing Overview

FamilyChef uses a multi-layered testing approach to ensure reliability and quality:

- **Backend Coverage**: 84%+ unit and integration tests
- **End-to-End Testing**: 20% of testing effort on critical user workflows  
- **Progressive Web App (PWA) Testing**: Offline functionality and installation
- **Real-time Features**: WebSocket and background task testing
- **Security Testing**: Automated vulnerability scanning

## Test Categories

### 1. Unit Tests
**Location**: `core/tests.py`  
**Purpose**: Test individual components in isolation

- **Model Tests**: Database models, relationships, and constraints
- **API Tests**: REST endpoints, authentication, and data validation
- **Serializer Tests**: Data transformation and validation logic
- **Utility Tests**: Helper functions and WebSocket utilities

### 2. Integration Tests  
**Location**: `core/tests.py`  
**Purpose**: Test component interactions

- **Order Workflow**: Menu → Order → Chef → Stock Deduction
- **Alert System**: Low stock detection → Alert creation → Shopping list
- **Family Isolation**: Multi-tenant data security
- **Authentication Flow**: Login → API access → Permissions

### 3. End-to-End Tests
**Location**: `tests/`  
**Purpose**: Test complete user workflows

- **User Workflows** (`test_user_workflows.py`):
  - Menu browsing and order creation
  - Chef dashboard and order management
  - Pantry stock management
  - Shopping list functionality

- **PWA Functionality** (`test_pwa_functionality.py`):
  - Service worker registration and caching
  - Offline functionality
  - Responsive design across devices
  - Install prompt handling
  - Dark mode support

### 4. Background Task Tests
**Location**: `core/tests.py` - `CeleryTaskTests`  
**Purpose**: Test scheduled and async operations

- Low stock alert generation
- Expired item detection
- Shopping list auto-generation
- Task error handling

### 5. WebSocket Tests
**Location**: `core/tests.py` - `WebSocketTests`  
**Purpose**: Test real-time features

- Order update notifications
- Shopping list updates
- Authentication requirements
- Room group management

## Running Tests

### Prerequisites
```bash
# Install all dependencies
pip install -r requirements-dev.txt

# Install Playwright browsers (for e2e tests)
playwright install chromium
```

### Unit and Integration Tests
```bash
# Run all Django tests
python manage.py test

# Run with coverage reporting
coverage run --source='.' manage.py test
coverage report --show-missing
coverage html  # Generate HTML report

# Run specific test classes
python manage.py test core.tests.APITests
python manage.py test core.tests.PWATests
python manage.py test core.tests.WebSocketTests
python manage.py test core.tests.CeleryTaskTests
```

### End-to-End Tests
```bash
# Start the Django development server
python manage.py runserver &

# Run e2e tests
cd tests
pytest -v --tb=short

# Run specific e2e test categories
pytest -v -m "workflow"  # User workflow tests
pytest -v -m "pwa"       # PWA functionality tests

# Run against staging environment
E2E_BASE_URL=https://staging-url.com pytest -v
```

### Coverage Validation
```bash
# Ensure 80%+ backend coverage (Phase 6 requirement)
coverage report --fail-under=80

# Generate detailed coverage report
coverage html
open htmlcov/index.html  # View in browser
```

## Test Configuration

### Pytest Configuration
**File**: `pytest.ini`  
**Purpose**: E2E test configuration and markers

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = familychef.settings
python_files = tests.py test_*.py *_tests.py
addopts = --tb=short --strict-markers
markers =
    e2e: End-to-end tests
    pwa: PWA functionality tests  
    workflow: User workflow tests
```

### E2E Test Base Configuration
**File**: `tests/conftest.py`  
**Purpose**: Shared e2e test utilities

- Browser configuration (mobile-first viewport)
- Authentication helpers
- API response waiting utilities
- Base URL configuration

## CI/CD Testing Pipeline

### Continuous Integration (`.github/workflows/ci.yml`)

1. **Unit/Integration Tests**:
   - Run Django tests on Python 3.11 and 3.12
   - PostgreSQL and Redis service containers
   - Coverage reporting with 80% threshold

2. **End-to-End Tests**:
   - Playwright browser installation
   - Django server startup
   - E2E test execution
   - Test result artifacts

3. **Code Quality**:
   - Black formatting checks
   - isort import organization
   - flake8 linting
   - Security scanning (bandit, safety)

### Staging Deployment Pipeline (`.github/workflows/staging-deploy.yml`)

1. **Automated Deployment**:
   - Docker image building
   - Container registry publishing
   - Staging environment deployment

2. **Post-Deployment Testing**:
   - Health check validation
   - E2E tests against staging
   - Deployment verification

## Test Data and Fixtures

### Database Setup
- SQLite in-memory database for fast test execution
- Automatic migrations during test setup
- Isolated test data per test method

### Test Users and Families
- Programmatic test user creation
- Family isolation testing
- Role-based permission validation

### Mock and Stub Strategy
- WebSocket utilities skip during testing
- Celery tasks run synchronously in tests
- External service mocking (Redis, email)

## Writing New Tests

### Adding Unit Tests
1. Add test methods to existing test classes in `core/tests.py`
2. Follow naming convention: `test_<functionality>_<expected_behavior>`
3. Use Django's `TestCase` for database tests
4. Use `APITestCase` for API endpoint tests

### Adding E2E Tests
1. Create new test files in `tests/` directory
2. Inherit from `E2ETestBase` in `conftest.py`
3. Use Playwright page objects and expect assertions
4. Add appropriate pytest markers

### Test Checklist
- [ ] Test covers both success and error cases
- [ ] Authentication/authorization properly tested
- [ ] Family isolation respected
- [ ] Database transactions properly isolated
- [ ] Appropriate assertions and error messages
- [ ] Documentation updated if needed

## Performance and Optimization

### Test Execution Speed
- In-memory SQLite database
- Minimal test data creation
- Parallel test execution where possible
- CI job parallelization

### Coverage Optimization
- Focus on critical business logic
- Exclude migration files and third-party code
- Target 80%+ meaningful coverage
- Regular coverage review and improvement

## Debugging Tests

### Local Debugging
```bash
# Run specific failing test with verbose output
python manage.py test core.tests.APITests.test_specific_method --verbosity=2

# Use Python debugger
import pdb; pdb.set_trace()  # Add to test code

# E2E test debugging
pytest -v -s --tb=long tests/test_user_workflows.py::TestUserWorkflows::test_menu_browsing_workflow
```

### CI Debugging
- Check GitHub Actions logs
- Download test artifacts
- Review coverage reports
- Examine error stack traces

## Maintenance

### Regular Tasks
- Review and update test coverage
- Update e2e tests for UI changes
- Maintain test data and fixtures
- Update browser versions for e2e tests

### Monitoring
- CI/CD pipeline success rates
- Test execution time trends
- Coverage percentage tracking
- Flaky test identification and fixes

---

This testing strategy ensures FamilyChef meets Phase 6 requirements for robust, reliable, and maintainable code with comprehensive test coverage and automated quality assurance.