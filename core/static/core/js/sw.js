// Service Worker for FamilyChef PWA
// Implements offline caching strategy for menu and core functionality

const CACHE_NAME = 'familychef-v1';
const API_CACHE_NAME = 'familychef-api-v1';

// Static resources to cache
const STATIC_RESOURCES = [
    '/',
    '/static/core/css/main.css',
    '/static/core/js/main.js',
    '/static/core/js/pwa.js',
    '/static/core/manifest/manifest.json',
    '/api/health/',
];

// API endpoints to cache for offline access
const API_ENDPOINTS = [
    '/api/menu/',
    '/api/families/',
    '/api/ingredients/',
    '/api/cuisines/',
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching static resources');
                return cache.addAll(STATIC_RESOURCES);
            })
            .then(() => {
                console.log('Service Worker: Installed');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Service Worker: Install failed', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker: Activated');
            return self.clients.claim();
        })
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const requestUrl = new URL(event.request.url);
    
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Handle API requests with Network First strategy
    if (requestUrl.pathname.startsWith('/api/')) {
        event.respondWith(
            networkFirstStrategy(event.request)
        );
        return;
    }
    
    // Handle static resources with Cache First strategy
    event.respondWith(
        cacheFirstStrategy(event.request)
    );
});

// Network First strategy - try network first, fallback to cache
async function networkFirstStrategy(request) {
    const cache = await caches.open(API_CACHE_NAME);
    
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            // Clone the response because response streams can only be consumed once
            const responseClone = networkResponse.clone();
            cache.put(request, responseClone);
        }
        
        return networkResponse;
    } catch (error) {
        // Network failed, try cache
        console.log('Service Worker: Network failed, trying cache for', request.url);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline fallback for menu requests
        if (request.url.includes('/api/menu/')) {
            return new Response(
                JSON.stringify({
                    results: [],
                    message: 'Menu not available offline'
                }),
                {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' }
                }
            );
        }
        
        // Return generic offline response
        return new Response(
            JSON.stringify({ message: 'Offline - content not available' }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Cache First strategy - try cache first, fallback to network
async function cacheFirstStrategy(request) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Not in cache, try network
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            const responseClone = networkResponse.clone();
            cache.put(request, responseClone);
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Service Worker: Both cache and network failed for', request.url);
        
        // Return basic offline HTML for page requests
        if (request.headers.get('accept').includes('text/html')) {
            return new Response(
                `<!DOCTYPE html>
                <html>
                <head>
                    <title>FamilyChef - Offline</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                </head>
                <body>
                    <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
                        <h1>You're Offline</h1>
                        <p>FamilyChef is not available right now. Please check your internet connection.</p>
                        <button onclick="window.location.reload()">Try Again</button>
                    </div>
                </body>
                </html>`,
                {
                    status: 503,
                    headers: { 'Content-Type': 'text/html' }
                }
            );
        }
        
        return new Response('Offline', { status: 503 });
    }
}

// Handle background sync for when connection is restored
self.addEventListener('sync', (event) => {
    console.log('Service Worker: Background sync triggered', event.tag);
    
    if (event.tag === 'menu-sync') {
        event.waitUntil(
            syncMenuData()
        );
    }
});

// Sync menu data when connection is restored
async function syncMenuData() {
    try {
        console.log('Service Worker: Syncing menu data...');
        
        // Fetch fresh menu data
        const response = await fetch('/api/menu/');
        if (response.ok) {
            const cache = await caches.open(API_CACHE_NAME);
            await cache.put('/api/menu/', response.clone());
            console.log('Service Worker: Menu data synced');
        }
    } catch (error) {
        console.error('Service Worker: Menu sync failed', error);
    }
}

// Handle push notifications (for future use)
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: '/static/core/icons/icon-192x192.png',
            badge: '/static/core/icons/icon-72x72.png',
            vibrate: [100, 50, 100],
            data: data.data,
            actions: data.actions
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow(event.notification.data.url || '/')
    );
});