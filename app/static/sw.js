/* Service Worker mínimo para tornar o SIGUS instalável como PWA.
   Todas as requisições passam direto para a rede. */
self.addEventListener('install', function () {
  self.skipWaiting();
});
self.addEventListener('activate', function (e) {
  e.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', function () {
  /* Pass-through: sempre busca na rede */
});
