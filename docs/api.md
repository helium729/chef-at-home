# FamilyChef API Reference

This document provides comprehensive API documentation for the FamilyChef application.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Core Endpoints

### Health and Admin

- `GET /api/health/` - Health check endpoint
- `GET /admin/` - Django admin interface
- `GET /api/` - DRF browsable API root
- `POST /auth/` - Authentication endpoints

## Phase 1 - Core Models & APIs

### Family Management

- `GET|POST /api/families/` - List and create families
- `GET|PUT|PATCH|DELETE /api/families/{id}/` - Family detail operations

### Family Members

- `GET|POST /api/family-members/` - List and add family members
- `GET|PUT|PATCH|DELETE /api/family-members/{id}/` - Family member operations

### Ingredients

- `GET|POST /api/ingredients/` - List and create ingredients
- `GET|PUT|PATCH|DELETE /api/ingredients/{id}/` - Ingredient operations

### Recipes/Cuisines

- `GET|POST /api/cuisines/` - List and create recipes
- `GET|PUT|PATCH|DELETE /api/cuisines/{id}/` - Recipe operations

### Recipe Ingredients

- `GET|POST /api/recipe-ingredients/` - List and create recipe ingredients
- `GET|PUT|PATCH|DELETE /api/recipe-ingredients/{id}/` - Recipe ingredient operations

### Pantry Stock

- `GET|POST /api/pantry-stock/` - List and manage pantry stock
- `GET|PUT|PATCH|DELETE /api/pantry-stock/{id}/` - Stock operations

### Users

- `GET /api/users/` - User information (read-only, family-scoped)

## Phase 2 - Ordering Flow

### Menu Display

- `GET /api/menu/` - Menu display with availability information
  - Shows which recipes can be made with current stock
  - Includes ingredient availability status

### Order Management

- `GET|POST /api/orders/` - List and create orders
- `GET|PUT|PATCH|DELETE /api/orders/{id}/` - Order operations
- `PATCH /api/orders/{id}/update_status/` - Update order status

### Real-time Updates

- **WebSocket**: `/ws/orders/{family_id}/` - Real-time order updates
  - Subscribe to order status changes
  - Real-time notifications for chefs

## Phase 3 - Chef & Pantry

### Alerts Management

- `GET|POST /api/alerts/` - List and create alerts (low-stock, expiry)
- `GET|PUT|PATCH|DELETE /api/alerts/{id}/` - Alert operations
- `PATCH /api/alerts/{id}/resolve/` - Mark alerts as resolved

### Stock Thresholds

- `GET|POST /api/low-stock-thresholds/` - Manage alert thresholds
- `GET|PUT|PATCH|DELETE /api/low-stock-thresholds/{id}/` - Threshold operations

### Automated Features

- **Ingredient Deduction**: Automatic stock deduction when orders are completed
- **Background Tasks**: Celery tasks for daily low-stock and expiry checking

## Phase 4 - Shopping List

### Shopping List Management

- `GET|POST /api/shopping-list/` - List and create shopping items
- `GET|PUT|PATCH|DELETE /api/shopping-list/{id}/` - Shopping item operations
- `PATCH /api/shopping-list/{id}/resolve/` - Mark shopping items as resolved

### Automated Features

- **Auto-generation**: Automatic shopping list generation from alerts
- **Real-time Updates**: WebSocket `/ws/shopping/{family_id}/` for live updates
- **Background Tasks**: Daily shopping list generation via Celery

## Phase 5 - PWA Features

### Progressive Web App

- `GET /manifest.json` - PWA manifest for add-to-home-screen functionality
- **Service Worker**: Offline caching for menu and core functionality
- **Offline Strategy**: Offline-first caching for menu data
- **Install Prompt**: Native app-like installation experience

### Frontend Templates

- `GET /` - Main menu page with PWA functionality
- `GET /chef/` - Chef dashboard template
- `GET /pantry/` - Pantry management template
- `GET /shopping/` - Shopping list template

### Performance Features

- **Offline Caching**: Menu data cached via service worker
- **Progressive Enhancement**: Network connectivity awareness
- **Background Sync**: Data updates when connection restored
- **Responsive Design**: Mobile-first with touch-friendly interface

## WebSocket Endpoints

### Order Updates

**Endpoint**: `/ws/orders/{family_id}/`

**Purpose**: Real-time order status updates

**Messages**:
```json
{
    "type": "order_update",
    "order_id": 123,
    "status": "cooking",
    "estimated_time": "25 minutes"
}
```

### Shopping Updates

**Endpoint**: `/ws/shopping/{family_id}/`

**Purpose**: Real-time shopping list updates

**Messages**:
```json
{
    "type": "shopping_update",
    "item_id": 456,
    "action": "added",
    "ingredient": "carrots"
}
```

## Error Handling

The API follows standard HTTP status codes:

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **General endpoints**: 100 requests per minute
- **Authentication endpoints**: 10 requests per minute
- **WebSocket connections**: 5 concurrent per family

## Data Formats

### Request/Response Format

All API endpoints accept and return JSON data with `Content-Type: application/json`.

### Date/Time Format

All timestamps use ISO 8601 format: `2024-01-15T10:30:00Z`

### Pagination

List endpoints support pagination:

```json
{
    "count": 150,
    "next": "http://api.example.com/api/items/?page=3",
    "previous": "http://api.example.com/api/items/?page=1",
    "results": []
}
```

## Family Isolation

All API endpoints respect family isolation - users can only access data belonging to their family. The system automatically filters data based on the authenticated user's family membership.

## Testing the API

Use the browsable API interface at `/api/` for interactive testing, or use tools like curl or Postman:

```bash
# Health check
curl http://localhost:8000/api/health/

# Get menu (requires authentication)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/menu/
```

For detailed testing information, see the [Testing Guide](TESTING.md).