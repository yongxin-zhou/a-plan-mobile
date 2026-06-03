// 禁用 Service Worker - 不做任何缓存
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.skipWaiting());
