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

- `GET /api/health/` - Health check
- `GET /admin/` - Django admin interface
- `GET /api/` - DRF browsable API root
- `POST /auth/` - Authentication endpoints

## Development

This project follows the roadmap outlined in `Roadmap.md`. Current status: **Phase 0 Setup** ✅

For detailed project specifications, user flows, and development phases, see [Roadmap.md](./Roadmap.md).

## License

GPL-3.0 License - see [LICENSE](./LICENSE) file for details.
