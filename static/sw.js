// 简化版 Service Worker - 不做缓存，避免卡住
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', event => {
  // 网络优先，不缓存
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
