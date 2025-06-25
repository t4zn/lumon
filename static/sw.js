// Flora PWA Service Worker
const CACHE_NAME = 'flora-v1.0.0';
const STATIC_CACHE_URLS = [
  '/',
  '/app',
  '/static/landing.css',
  '/static/landing.js',
  '/static/style.css',
  '/static/script.js',
  '/static/icon-192.png',
  '/static/icon-512.png',
  '/manifest.json',
  // External CDN resources
  'https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js'
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Flora: Caching app shell');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .then(() => {
        console.log('Flora: Service worker installed');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Flora: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Flora: Service worker activated');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip Chrome extension requests
  if (event.request.url.startsWith('chrome-extension://')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }

        return fetch(event.request).then((response) => {
          // Don't cache non-successful responses
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response for caching
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });

          return response;
        });
      })
      .catch(() => {
        // Return offline page for navigation requests
        if (event.request.mode === 'navigate') {
          return caches.match('/');
        }
      })
  );
});

// Handle background sync for offline plant identification
self.addEventListener('sync', (event) => {
  if (event.tag === 'plant-identification') {
    event.waitUntil(
      // Process queued plant identification requests when back online
      processOfflineRequests()
    );
  }
});

// Background sync function
async function processOfflineRequests() {
  // Implementation for offline plant identification processing
  console.log('Flora: Processing offline plant identification requests');
}