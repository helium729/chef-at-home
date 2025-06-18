# FamilyChef PWA Features

This document describes the Progressive Web App (PWA) features implemented in Phase 5 of the FamilyChef project.

## Overview

FamilyChef is now a fully functional Progressive Web App that provides:
- **Offline functionality** - Menu and core features work without internet
- **Install to home screen** - Users can install the app like a native mobile app
- **Responsive design** - Optimized for mobile, tablet, and desktop devices
- **Touch-friendly interface** - Designed for mobile-first usage

## PWA Features

### 1. Web App Manifest

**File:** `/manifest.json`

The manifest provides metadata about the application:
- App name, description, and icons
- Display mode (standalone for app-like experience)
- Theme and background colors
- Start URL and scope
- Icon definitions for various sizes

### 2. Service Worker

**File:** `/static/core/js/sw.js`

Implements offline functionality with two caching strategies:

**Cache First Strategy** (for static resources):
- CSS, JavaScript, images
- Falls back to network if not in cache

**Network First Strategy** (for API data):
- Menu data (`/api/menu/`)
- Other API endpoints
- Falls back to cache when offline
- Provides offline placeholder data when needed

### 3. PWA JavaScript Controller

**File:** `/static/core/js/pwa.js`

Handles PWA lifecycle events:
- Service worker registration
- Install prompt management
- Online/offline status detection
- Update notifications
- Theme management
- Responsive design handling

### 4. Responsive Design

**File:** `/static/core/css/main.css`

Mobile-first responsive design with:
- CSS Grid and Flexbox layouts
- Responsive breakpoints:
  - Mobile: ≤480px (1-column layout)
  - Tablet: 481px-768px (2-column layout)
  - Desktop: >768px (multi-column layout)
- Touch-friendly components (44px+ touch targets)
- Dark mode support with CSS custom properties

## Installation

### For Users

1. **Mobile (Chrome/Edge):**
   - Visit the website
   - Tap the "Install App" button when prompted
   - Or use browser's "Add to Home Screen" option

2. **Desktop (Chrome/Edge):**
   - Visit the website
   - Click the install icon in the address bar
   - Or use "Install FamilyChef" option in browser menu

### For Developers

The PWA features are automatically available when:
1. The app is served over HTTPS (or localhost for development)
2. Static files are properly collected
3. Service worker is accessible at the root domain

## Offline Functionality

### What Works Offline:
- Viewing previously loaded menu items
- Basic navigation between pages
- App shell and core UI components
- Previously cached static resources

### What Requires Internet:
- Loading new menu data
- Placing orders
- Real-time updates via WebSockets
- User authentication

### Caching Strategy:
- **Static resources** (CSS, JS, images): Cached first, updated in background
- **Menu data**: Network first, cache fallback with 5-minute freshness
- **API endpoints**: Network first with intelligent fallbacks

## Responsive Design

### Breakpoints:
```css
/* Mobile: Default styles */
@media (min-width: 481px) { /* Tablet */ }
@media (min-width: 769px) { /* Desktop */ }
```

### Touch Optimization:
- Minimum 44px touch targets
- Touch-specific hover effects disabled
- Optimized spacing for thumb navigation
- Swipe-friendly horizontal scrolling

### Accessibility:
- High contrast mode support
- Reduced motion preference support
- Keyboard navigation
- Screen reader compatibility
- Focus indicators

## Dark Mode

Supports both automatic and manual theme switching:
- **Automatic**: Follows system `prefers-color-scheme`
- **Manual**: Theme toggle button in header
- **Persistent**: User preference stored in localStorage

### CSS Variables:
```css
:root {
  --primary-color: #4CAF50;
  --bg-primary: #ffffff;
  --text-primary: #212121;
}

[data-theme="dark"] {
  --bg-primary: #121212;
  --text-primary: #ffffff;
}
```

## Performance Features

### Service Worker Caching:
- **Static resources**: Long-term caching with version control
- **API responses**: Fresh data with stale fallback
- **Background sync**: Updates when connection restored

### Optimizations:
- CSS and JavaScript minification ready
- Image optimization placeholders
- Lazy loading preparation
- Critical CSS inlining ready

## Development

### Adding New Cacheable Resources:

1. **Static files** - Add to `STATIC_RESOURCES` array in `sw.js`
2. **API endpoints** - Add to `API_ENDPOINTS` array in `sw.js`
3. **Update service worker version** when making changes

### Testing PWA Features:

```bash
# Run tests
python manage.py test core.tests.PWATests

# Check PWA compliance
# Use Chrome DevTools > Lighthouse > PWA audit
```

### PWA Debugging:

1. **Chrome DevTools:**
   - Application tab > Service Workers
   - Application tab > Storage (view caches)
   - Network tab > check offline functionality

2. **Console logging:**
   - Service worker events logged to console
   - PWA state changes logged

## Browser Support

### Full PWA Support:
- Chrome 67+ (Android/Desktop)
- Edge 79+ (Windows/Android)
- Samsung Internet 7.2+
- Firefox 58+ (limited install support)

### Progressive Enhancement:
- Safari: Core features work, limited PWA features
- Older browsers: Falls back to standard web app

## Security

### Requirements:
- HTTPS in production (PWA requirement)
- Service worker served from same origin
- Manifest file accessible via HTTPS

### Best Practices:
- Content Security Policy (CSP) configured
- Service worker scope limited appropriately
- Sensitive data not cached offline

## Future Enhancements

Potential Phase 6+ improvements:
- **Push notifications** for order updates
- **Background sync** for offline order queuing
- **Web Share API** for recipe sharing
- **Payment Request API** for shopping integration
- **File System Access API** for recipe import/export
- **Contact Picker API** for family member invites