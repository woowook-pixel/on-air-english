// 앱 화면은 캐시해서 오프라인에서도 열리게 하고, 목록 데이터는 항상 네트워크를 먼저 확인한다.
const CACHE = 'script-v23';
const SHELL = ['./', 'index.html', 'manifest.webmanifest'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('message', e => { if (e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting(); });

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return; // 오디오·영상 등 외부 파일은 그대로 통과

  if (url.pathname.endsWith('/version.json')) return; // 새 버전 확인은 항상 네트워크로 (오프라인이면 실패해야 한다)

  // 네트워크 우선, 실패하면 캐시
  e.respondWith(
    fetch(e.request, { cache: 'no-cache' })  // 브라우저 임시 보관(HTTP 캐시)에 남은 옛 파일을 쓰지 않고 매번 서버에 확인한다
      .then(res => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
        }
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
