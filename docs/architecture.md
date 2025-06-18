# FamilyChef Architecture

This document describes the system architecture and design decisions for FamilyChef.

## System Overview

FamilyChef is a Django-powered Progressive Web Application (PWA) designed for family cooking coordination. The system follows a modern web architecture with real-time features and offline capabilities.

```
┌──────────────┐   HTTPS/WSS   ┌──────────────────┐
│   Frontend   │◄─────────────►│   Django API     │
│   (PWA)      │  JSON/WebSocket│   + Channels     │
└──────────────┘               └─────────┬────────┘
                                         │
                               ┌─────────▼─────────┐
                               │   PostgreSQL      │
                               │   (Primary DB)    │
                               └───────────────────┘
                                         │
┌──────────────┐               ┌─────────▼─────────┐
│  Service     │◄─────────────►│     Redis         │
│  Worker      │  Task Queue   │  (Cache/Queue)    │
│  (Celery)    │               └───────────────────┘
└──────────────┘
```

## Technology Stack

### Backend

- **Framework**: Django 5.x
- **API**: Django REST Framework (DRF)
- **Real-time**: Django Channels (WebSockets)
- **Background Tasks**: Celery + Redis
- **Authentication**: Django Allauth + JWT
- **Database**: PostgreSQL (production), SQLite (development)
- **Cache**: Redis

### Frontend

- **Type**: Progressive Web App (PWA)
- **Templates**: Django Templates with modern JavaScript
- **Offline**: Service Worker with caching strategies
- **Real-time**: WebSocket connections
- **Responsive**: Mobile-first design

### Infrastructure

- **Web Server**: Nginx (reverse proxy)
- **WSGI**: Gunicorn
- **Container**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: Automated staging and production

## Architecture Patterns

### 1. API-First Design

All functionality is exposed through REST API endpoints, enabling:
- Clean separation between frontend and backend
- Easy integration with mobile apps or third-party tools
- Consistent data access patterns

### 2. Family-Scoped Data

All data is scoped to families, ensuring privacy and isolation:
- Family-based authentication and authorization
- Data filtering at the database level
- Multi-tenant architecture without complexity

### 3. Real-time Communication

WebSocket connections provide live updates:
- Order status changes
- Shopping list updates
- Stock level changes
- Chef dashboard notifications

### 4. Progressive Web App

Modern web app features:
- Offline functionality with service workers
- Installation prompts for native app experience
- Responsive design for all device sizes
- Fast loading with caching strategies

## Data Architecture

### Core Models

```
Family
├── FamilyMember (User relationship)
├── Ingredient (family-specific catalog)
├── Cuisine (recipes)
├── RecipeIngredient (recipe components)
├── PantryStock (current inventory)
├── Order (meal requests)
├── Alert (low stock/expiry warnings)
└── ShoppingListItem (items to buy)
```

### Model Relationships

- **Family → Users**: Many-to-many through FamilyMember
- **Cuisine → Ingredients**: Many-to-many through RecipeIngredient
- **Family → Stock**: One-to-many PantryStock entries
- **Family → Orders**: One-to-many Order entries

### Data Flow

1. **Recipe Creation**: Chef adds cuisine with required ingredients
2. **Stock Management**: Family updates pantry quantities
3. **Menu Display**: API calculates availability based on stock
4. **Order Placement**: Family members request meals
5. **Cooking Process**: Chef processes orders, stock auto-deducts
6. **Alerts**: System monitors stock levels and expiry dates
7. **Shopping**: Auto-generated lists from alerts and planning

## Security Architecture

### Authentication Flow

1. User logs in via Django Allauth
2. JWT token issued for API access
3. Token included in all API requests
4. Family membership verified for data access

```
┌─────────────┐    Login     ┌─────────────┐    JWT      ┌─────────────┐
│   Browser   │─────────────►│   Django    │────────────►│   API       │
│             │              │   Auth      │             │   Endpoint  │
└─────────────┘              └─────────────┘             └─────────────┘
```

### Authorization Levels

- **Family Member**: Read menu, place orders, view own data
- **Chef**: Manage recipes, process orders, full pantry access
- **Shopper**: Manage shopping lists, update stock levels
- **Family Admin**: Manage family members and settings

### Data Protection

- **Family Isolation**: All queries filtered by family membership
- **Input Validation**: DRF serializers validate all input
- **SQL Injection**: Django ORM prevents SQL injection
- **CSRF Protection**: Django middleware handles CSRF
- **HTTPS**: All production traffic encrypted

## Performance Architecture

### Caching Strategy

- **Redis**: API response caching, session storage
- **Service Worker**: Frontend asset and API response caching
- **Database**: Query optimization with proper indexing
- **Static Files**: CDN delivery with long-term caching

### Database Optimization

- **Indexes**: Strategic indexing on frequently queried fields
- **Query Optimization**: Select/prefetch related objects
- **Connection Pooling**: Efficient database connections
- **Read Replicas**: Future scaling option

### Background Processing

- **Celery Tasks**: Asynchronous processing for:
  - Daily stock level checks
  - Expiry date monitoring
  - Shopping list generation
  - Email notifications

### Scaling Considerations

Current architecture supports:
- **Horizontal Scaling**: Multiple Django instances behind load balancer
- **Database Scaling**: Read replicas and connection pooling
- **Cache Scaling**: Redis clustering
- **Task Processing**: Multiple Celery workers

## Real-time Architecture

### WebSocket Implementation

```python
# Consumer example
class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.family_id = self.scope['url_route']['kwargs']['family_id']
        await self.channel_layer.group_add(
            f"orders_{self.family_id}",
            self.channel_name
        )
        await self.accept()
```

### Message Flow

1. **Order Update**: Chef changes order status
2. **Signal Dispatch**: Django signal triggers WebSocket message
3. **Channel Layer**: Redis channels distribute to connected clients
4. **Browser Update**: Real-time UI updates without page refresh

## PWA Architecture

### Service Worker Strategy

```javascript
// Cache-first for static assets
// Network-first for API calls
// Offline fallback for core functionality
```

### Offline Capabilities

- **Menu Browsing**: Cached menu data available offline
- **Order Queue**: Orders queued when offline, synced when online
- **Stock Viewing**: Last known stock levels cached
- **Progressive Enhancement**: Features degrade gracefully

## Development Architecture

### Code Organization

```
familychef/
├── familychef/          # Django project settings
│   ├── settings/        # Environment-specific settings
│   ├── wsgi.py         # WSGI configuration
│   └── asgi.py         # ASGI configuration
├── core/               # Core application
│   ├── models.py       # Data models
│   ├── serializers.py  # API serializers
│   ├── views.py        # API views
│   ├── consumers.py    # WebSocket consumers
│   ├── tasks.py        # Celery tasks
│   └── tests.py        # Test suite
├── templates/          # Django templates
├── static/             # Static assets
├── docs/              # Documentation
└── tests/             # End-to-end tests
```

### Testing Architecture

- **Unit Tests**: Django TestCase for models and API
- **Integration Tests**: Multi-component workflow testing
- **E2E Tests**: Playwright for browser automation
- **Load Tests**: Performance testing for scalability
- **Security Tests**: Automated vulnerability scanning

### CI/CD Pipeline

```
Code Push → GitHub Actions → Tests → Build → Deploy → Verify
```

## Deployment Architecture

### Production Environment

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Nginx     │    │   Django    │    │ PostgreSQL  │
│ (Reverse    │───►│   (Gunicorn)│───►│ (Primary    │
│  Proxy)     │    │             │    │  Database)  │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                   ┌─────────────┐    ┌─────────────┐
                   │   Celery    │    │   Redis     │
                   │  (Workers)  │───►│ (Cache/     │
                   │             │    │  Queue)     │
                   └─────────────┘    └─────────────┘
```

### Container Architecture

- **Web Container**: Django application with Gunicorn
- **Database Container**: PostgreSQL with persistent volumes
- **Cache Container**: Redis for caching and task queue
- **Worker Container**: Celery for background processing
- **Proxy Container**: Nginx for load balancing and SSL termination

## Future Architecture Considerations

### Scalability Enhancements

- **Microservices**: Split into recipe, order, and inventory services
- **Event Sourcing**: Audit trail for all family actions
- **CQRS**: Separate read/write models for performance
- **GraphQL**: More efficient data fetching

### Mobile Native Apps

- **React Native**: Cross-platform mobile app
- **API Reuse**: Same Django API for web and mobile
- **Push Notifications**: Native mobile notifications

### Advanced Features

- **Machine Learning**: Recipe recommendations based on family preferences
- **IoT Integration**: Smart kitchen appliance integration
- **Voice Interface**: Voice-controlled ordering and status
- **Analytics**: Family cooking patterns and optimization

This architecture supports the current feature set while providing a foundation for future growth and enhancement.