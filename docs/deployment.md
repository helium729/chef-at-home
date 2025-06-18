# FamilyChef Deployment Guide

This guide covers deploying FamilyChef to production environments.

## Production Requirements

- **Python**: 3.11+
- **Database**: PostgreSQL 12+
- **Cache/Queue**: Redis 6+
- **Web Server**: Nginx (recommended)
- **WSGI Server**: Gunicorn or uWSGI
- **Process Manager**: systemd or Docker
- **SSL Certificate**: Required for PWA features

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/familychef

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Static Files
STATIC_ROOT=/var/www/familychef/static/
MEDIA_ROOT=/var/www/familychef/media/
```

## Docker Deployment (Recommended)

### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn familychef.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    env_file:
      - .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: familychef
      POSTGRES_USER: familychef_user
      POSTGRES_PASSWORD: secure_password

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

  nginx:
    build: ./nginx
    volumes:
      - static_volume:/var/www/html/static
      - media_volume:/var/www/html/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

  celery:
    build: .
    command: celery -A familychef worker --loglevel=info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### 2. Nginx Configuration

Create `nginx/default.conf`:

```nginx
upstream familychef {
    server web:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    location / {
        proxy_pass http://familychef;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_redirect off;
    }

    location /static/ {
        alias /var/www/html/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/html/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://familychef;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Deploy Commands

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up --build -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Manual Deployment

### 1. Server Setup

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv postgresql redis-server nginx

# Create application user
sudo useradd --system --shell /bin/bash --home /opt/familychef familychef

# Create directories
sudo mkdir -p /opt/familychef
sudo chown familychef:familychef /opt/familychef
```

### 2. Application Setup

```bash
# Switch to application user
sudo -u familychef -i

# Clone repository
git clone <repository-url> /opt/familychef/app
cd /opt/familychef/app

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Set up environment
cp .env.example .env
# Edit .env with production values
```

### 3. Database Setup

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE familychef;
CREATE USER familychef_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE familychef TO familychef_user;
\q

# Run migrations
cd /opt/familychef/app
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Systemd Services

Create `/etc/systemd/system/familychef.service`:

```ini
[Unit]
Description=FamilyChef Django App
After=network.target

[Service]
Type=notify
User=familychef
Group=familychef
RuntimeDirectory=familychef
WorkingDirectory=/opt/familychef/app
Environment=PATH=/opt/familychef/app/venv/bin
EnvironmentFile=/opt/familychef/app/.env
ExecStart=/opt/familychef/app/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/familychef/familychef.sock \
    --access-logfile - \
    --error-logfile - \
    familychef.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/familychef-celery.service`:

```ini
[Unit]
Description=FamilyChef Celery Worker
After=network.target

[Service]
Type=forking
User=familychef
Group=familychef
WorkingDirectory=/opt/familychef/app
Environment=PATH=/opt/familychef/app/venv/bin
EnvironmentFile=/opt/familychef/app/.env
ExecStart=/opt/familychef/app/venv/bin/celery -A familychef worker --detach --loglevel=info
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 5. Start Services

```bash
# Enable and start services
sudo systemctl enable familychef familychef-celery
sudo systemctl start familychef familychef-celery

# Check status
sudo systemctl status familychef
sudo systemctl status familychef-celery
```

## CI/CD Deployment

### GitHub Actions

The repository includes automated deployment workflows:

- **CI Pipeline**: `.github/workflows/ci.yml` - Testing and validation
- **Staging Deploy**: `.github/workflows/staging-deploy.yml` - Staging deployment

### Manual Deployment Trigger

```bash
# Tag a release
git tag v1.0.0
git push origin v1.0.0

# Deployment will trigger automatically
```

## Monitoring and Maintenance

### Health Checks

- **Application**: `GET /api/health/`
- **Database**: Check PostgreSQL connection
- **Cache**: Check Redis connection
- **Celery**: Check worker status

### Log Locations

- **Application**: `/var/log/familychef/`
- **Nginx**: `/var/log/nginx/`
- **PostgreSQL**: `/var/log/postgresql/`
- **Systemd**: `journalctl -u familychef`

### Backup Strategy

```bash
# Database backup
pg_dump familychef > backup_$(date +%Y%m%d_%H%M%S).sql

# Media files backup
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz /var/www/familychef/media/

# Automated backups (crontab)
0 2 * * * /opt/familychef/scripts/backup.sh
```

### Updates and Upgrades

```bash
# Update application
cd /opt/familychef/app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart familychef familychef-celery
```

## Security Considerations

### SSL/TLS

- Use Let's Encrypt for free SSL certificates
- Implement HSTS headers
- Use secure cookie settings

### Database Security

- Use strong passwords
- Limit database access to application servers
- Regular security updates

### Application Security

- Keep Django and dependencies updated
- Use environment variables for secrets
- Implement proper CSRF protection
- Regular security scanning

### Monitoring

- Set up log monitoring
- Implement application performance monitoring
- Configure alerts for critical errors

## Troubleshooting

### Common Issues

**Static files not loading**:
```bash
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

**Database connection errors**:
- Check PostgreSQL status
- Verify connection credentials
- Check firewall settings

**Celery tasks not running**:
```bash
sudo systemctl status familychef-celery
sudo systemctl restart familychef-celery
```

**WebSocket connections failing**:
- Check Nginx WebSocket configuration
- Verify Django Channels setup
- Check Redis connection

For more deployment help, see the [Development Guide](development.md) or contact your system administrator.