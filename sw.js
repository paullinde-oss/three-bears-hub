// Three Bears Hockey Hub — Service Worker v1.0
// App-shell / offline resilience only. No receipt or account data cached.

const CACHE_NAME = 'three-bears-shell-v1';

// Only cache the app shell (static assets). Firebase data is never cached.
const SHELL_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './3_Bears_logo_Pixel.png',
  './hockey_rink.png',
  './parking_lot.png',
  './game_card_bg.png',
];

// Install: pre-cache the app shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      // Use individual fetch + catch so one missing asset doesn't break install
      return Promise.allSettled(
        SHELL_ASSETS.map(url =>
          cache.add(url).catch(() => { /* ignore missing assets */ })
        )
      );
    }).then(() => self.skipWaiting())
  );
});

// Activate: remove old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch: network-first for Firebase/API calls, cache-first for shell assets
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Always fetch live for Firebase, Google APIs, and external resources
  const alwaysLive = [
    'firebaseio.com',
    'googleapis.com',
    'google.com',
    'gstatic.com',
    'anthropic.com',
    'cdnjs.cloudflare.com',
    'fonts.googleapis.com',
    'fonts.gstatic.com',
  ];
  if (alwaysLive.some(host => url.hostname.includes(host))) {
    return; // let browser handle it normally
  }

  // For same-origin requests: network-first with cache fallback
  if (url.origin === self.location.origin) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Cache successful GET responses for shell assets
          if (event.request.method === 'GET' && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
  }
});
