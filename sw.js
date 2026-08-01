// Three Bears Hockey Hub — Service Worker v3.2
const CACHE_NAME = 'three-bears-shell-v3';

const SHELL_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './3_Bears_logo_Pixel.png',
  './hockey_rink.png',
  './parking_lot.png',
  './game_card_bg.png',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return Promise.allSettled(
        SHELL_ASSETS.map(url => cache.add(url).catch(() => {}))
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  const alwaysLive = [
    'firebaseio.com','googleapis.com','google.com','gstatic.com',
    'anthropic.com','cdnjs.cloudflare.com','fonts.googleapis.com',
    'fonts.gstatic.com','sportninja.net',
  ];
  if (alwaysLive.some(host => url.hostname.includes(host))) return;
  if (url.origin === self.location.origin) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
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
