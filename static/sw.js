const CACHE_NAME = 'a-plan-v1';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:opsz@14..32&display=swap'
];

// 安装事件 - 缓存资源
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
  self.skipWaiting();
});

// 激活事件 - 清理旧缓存
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// 请求事件 - 网络优先，缓存兜底
self.addEventListener('fetch', event => {
  // API 请求不缓存
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // 克隆响应并缓存
        const responseClone = response.clone();
        caches.open(CACHE_NAME)
          .then(cache => {
            cache.put(event.request, responseClone);
          });
        return response;
      })
      .catch(() => {
        // 网络失败时从缓存读取
        return caches.match(event.request);
      })
  );
});

// 推送通知
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const options = {
    body: data.body || '你有新的提醒',
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-192.png',
    vibrate: [200, 100, 200],
    tag: data.tag || 'reminder',
    data: data.url || '/'
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'A计划', options)
  );
});

// 通知点击
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data || '/')
  );
});
