# FamilyChef Development Guide

This guide covers setting up and developing the FamilyChef application.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional)
- PostgreSQL and Redis (for production)

## Local Development Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd chef-at-home

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Set up environment variables
cp .env.example .env
# Edit .env file with your settings
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 4. Start Development Server

```bash
# Start the development server
python manage.py runserver

# Test the setup
curl http://localhost:8000/api/health/
```

## Docker Development Setup

### Quick Start with Docker

```bash
# Build and start services
docker-compose up --build

# Run migrations (in another terminal)
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## Architecture

- **Backend**: Django 5.x + Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **Cache/Queue**: Redis + Celery
- **WebSocket**: Django Channels
- **Authentication**: Django Allauth + JWT

## Project Structure

```
familychef/
├── familychef/          # Django project settings
├── core/               # Core functionality
├── docs/               # Documentation
├── tests/              # End-to-end tests
├── templates/          # Django templates
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Docker configuration
├── Dockerfile         # Docker image definition
└── manage.py          # Django management script
```

## Code Quality and CI/CD

The project includes comprehensive CI/CD workflows with automated testing, code quality checks, and staging deployment.

### Development Tools

- **Code Formatting**: Run `black .` to format code
- **Import Sorting**: Run `isort .` to organize imports
- **Linting**: Run `flake8 .` to check for issues
- **Security**: Run `bandit -r .` and `safety scan -r requirements.txt`

### Running Tests Locally

#### Unit and Integration Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run Django tests with coverage
coverage run --source='.' manage.py test
coverage report --show-missing

# Run specific test categories
python manage.py test core.tests.APITests      # API tests
python manage.py test core.tests.PWATests      # PWA tests  
python manage.py test core.tests.CeleryTaskTests  # Background task tests
```

#### End-to-End Tests

```bash
# Install Playwright browsers
playwright install chromium

# Run e2e tests locally (requires running server)
python manage.py runserver &  # Start server in background
cd tests
pytest -v --tb=short

# Run e2e tests against staging
E2E_BASE_URL=https://your-staging-url.com pytest -v
```

#### Code Quality Checks

```bash
# Run all code quality checks
black --check .
isort --check-only .
flake8 .
bandit -r .
safety scan -r requirements.txt
```

### Continuous Integration

- **Automated Testing**: Django tests run on Python 3.11 and 3.12 with 84%+ code coverage
- **End-to-End Testing**: Playwright-based e2e tests for critical user workflows
- **Code Formatting**: Black formatter ensures consistent code style
- **Import Sorting**: isort organizes imports automatically  
- **Linting**: flake8 catches syntax errors and style issues
- **Security Scanning**: bandit and safety scan for security vulnerabilities
- **Docker Testing**: Full Docker Compose stack validation

### Staging Deployment

- **Automated Deployment**: Successful CI builds trigger staging deployment
- **Health Checks**: Post-deployment verification of all endpoints
- **Staging E2E Tests**: End-to-end testing against staging environment
- **Docker Registry**: Automated image building and publishing

## Testing Strategy

The project follows Phase 6 testing requirements:

- **Backend Coverage**: 84%+ unit and integration test coverage
- **End-to-End Tests**: 20% of testing effort focused on critical user workflows
- **PWA Testing**: Offline functionality, responsive design, and installation flows
- **WebSocket Testing**: Real-time functionality validation
- **Task Testing**: Background job and scheduled task validation

For detailed testing information, see the [Testing Guide](TESTING.md).

## Development Phases

This project follows a structured development roadmap. Current status: **Phase 6 Tests + CI/CD** ✅

For detailed project specifications, user flows, and development phases, see the [Roadmap](Roadmap.md).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the code quality standards
4. Run tests and ensure they pass
5. Submit a pull request

## License

GPL-3.0 License - see [LICENSE](../LICENSE) file for details.