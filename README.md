# FamilyChef – H5 Cooking-Assistant

A Django-powered mobile web ("H5") application that helps families plan, cook, and restock ingredients with minimal friction.

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (optional)
- PostgreSQL and Redis (for production)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chef-at-home
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Test the setup**
   ```bash
   curl http://localhost:8000/api/health/
   ```

### Docker Setup

1. **Build and start services**
   ```bash
   docker-compose up --build
   ```

2. **Run migrations (in another terminal)**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser**
   ```bash
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
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Docker configuration
├── Dockerfile         # Docker image definition
└── Roadmap.md         # Project roadmap and specifications
```

## API Endpoints

### Core Endpoints
- `GET /api/health/` - Health check
- `GET /admin/` - Django admin interface
- `GET /api/` - DRF browsable API root
- `POST /auth/` - Authentication endpoints

### Phase 1 - Core Models & APIs
- `GET|POST /api/families/` - Family management
- `GET|POST|PUT|PATCH|DELETE /api/family-members/` - Family membership management
- `GET|POST|PUT|PATCH|DELETE /api/ingredients/` - Ingredient management
- `GET|POST|PUT|PATCH|DELETE /api/cuisines/` - Recipe/cuisine management
- `GET|POST|PUT|PATCH|DELETE /api/recipe-ingredients/` - Recipe ingredient management
- `GET|POST|PUT|PATCH|DELETE /api/pantry-stock/` - Pantry stock management
- `GET /api/users/` - User information (read-only, family-scoped)

### Phase 2 - Ordering Flow
- `GET /api/menu/` - Menu display with availability information
- `GET|POST|PUT|PATCH|DELETE /api/orders/` - Order management
- `PATCH /api/orders/{id}/update_status/` - Order status updates
- WebSocket: `/ws/orders/{family_id}/` - Real-time order updates

### Phase 3 - Chef & Pantry
- `GET|POST|PUT|PATCH|DELETE /api/alerts/` - Low-stock and expiry alerts
- `PATCH /api/alerts/{id}/resolve/` - Mark alerts as resolved
- `GET|POST|PUT|PATCH|DELETE /api/low-stock-thresholds/` - Configurable alert thresholds
- Automated ingredient deduction when orders are completed
- Celery tasks for daily low-stock and expiry checking

### Phase 4 - Shopping List
- `GET|POST|PUT|PATCH|DELETE /api/shopping-list/` - Shopping list management
- `PATCH /api/shopping-list/{id}/resolve/` - Mark shopping list items as resolved
- Automatic shopping list generation from low-stock and expired ingredient alerts
- WebSocket: `/ws/shopping/{family_id}/` - Real-time shopping list updates
- Celery task for daily shopping list generation

### Phase 5 - Polish & PWA
- **Progressive Web App (PWA) Features:**
  - `GET /manifest.json` - PWA manifest for add-to-home-screen functionality
  - Service worker for offline caching of menu and core functionality
  - Offline-first caching strategy for menu data
  - Install prompt for native app-like experience
- **Responsive UI:**
  - Mobile-first responsive design (1-column ≤480px, 2-column tablets, multi-column desktop)
  - Touch-friendly interface with appropriate touch targets (44px+ minimum)
  - Dark mode support with system preference detection
  - High contrast and reduced motion accessibility support
- **Frontend Templates:**
  - `GET /` - Main menu page with PWA functionality
  - `GET /chef/` - Chef dashboard (template)
  - `GET /pantry/` - Pantry management (template)
  - `GET /shopping/` - Shopping list (template)
- **Performance Optimizations:**
  - Offline menu caching via service worker
  - Progressive enhancement for network connectivity
  - Background sync for data updates when connection restored

## Development

This project follows the roadmap outlined in `Roadmap.md`. Current status: **Phase 6 Tests + CI/CD** ✅

### Code Quality and CI/CD

The project includes comprehensive CI/CD workflows with automated testing, code quality checks, and staging deployment:

#### Continuous Integration
- **Automated Testing**: Django tests run on Python 3.11 and 3.12 with 84%+ code coverage
- **End-to-End Testing**: Playwright-based e2e tests for critical user workflows
- **Code Formatting**: Black formatter ensures consistent code style
- **Import Sorting**: isort organizes imports automatically  
- **Linting**: flake8 catches syntax errors and style issues
- **Security Scanning**: bandit and safety scan for security vulnerabilities
- **Docker Testing**: Full Docker Compose stack validation

#### Staging Deployment
- **Automated Deployment**: Successful CI builds trigger staging deployment
- **Health Checks**: Post-deployment verification of all endpoints
- **Staging E2E Tests**: End-to-end testing against staging environment
- **Docker Registry**: Automated image building and publishing

#### Development Tools
- **Code Formatting**: Run `black .` to format code
- **Import Sorting**: Run `isort .` to organize imports
- **Linting**: Run `flake8 .` to check for issues
- **Security**: Run `bandit -r .` and `safety scan -r requirements.txt`

#### Running Tests Locally

##### Unit and Integration Tests
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

##### End-to-End Tests
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

##### Code Quality Checks
```bash
# Run all code quality checks
black --check .
isort --check-only .
flake8 .
bandit -r .
safety scan -r requirements.txt
```

### Testing Strategy

The project follows Phase 6 testing requirements:

- **Backend Coverage**: 84%+ unit and integration test coverage
- **End-to-End Tests**: 20% of testing effort focused on critical user workflows
- **PWA Testing**: Offline functionality, responsive design, and installation flows
- **WebSocket Testing**: Real-time functionality validation
- **Task Testing**: Background job and scheduled task validation

For detailed project specifications, user flows, and development phases, see [Roadmap.md](./Roadmap.md).

## License

GPL-3.0 License - see [LICENSE](./LICENSE) file for details.
