/**
 * Service Worker pour Alimante PWA
 * Gère la mise en cache et le fonctionnement hors ligne
 */

const CACHE_NAME = "alimante-v1.0.0";
const STATIC_CACHE = "alimante-static-v1.0.0";
const DYNAMIC_CACHE = "alimante-dynamic-v1.0.0";

// Fichiers à mettre en cache statiquement
const STATIC_FILES = [
  "/",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/images/icon-192.png",
  "/static/images/icon-512.png",
  "/manifest.json",
];

// Fichiers à ignorer pour le cache dynamique
const IGNORE_FILES = [
  "/api/status",
  "/api/sensors
  "/api/controls",
  "/api/alerts",
];

// Installation du service worker
self.addEventListener("install", (event) => {
  console.log("Service Worker: Installation...");

  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => {
        console.log("Service Worker: Mise en cache des fichiers statiques");
        return cache.addAll(STATIC_FILES);
      })
      .then(() => {
        console.log("Service Worker: Installation terminée");
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error("Service Worker: Erreur installation", error);
      })
  );
});

// Activation du service worker
self.addEventListener("activate", (event) => {
  console.log("Service Worker: Activation...");

  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log(
                "Service Worker: Suppression ancien cache",
                cacheName
              );
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log("Service Worker: Activation terminée");
        return self.clients.claim();
      })
  );
});

// Interception des requêtes
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorer les requêtes API en temps réel
  if (IGNORE_FILES.some((path) => url.pathname.includes(path))) {
    return;
  }

  // Stratégie de cache
  if (request.method === "GET") {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          console.log(
            "Service Worker: Ressource trouvée en cache",
            request.url
          );
          return cachedResponse;
        }

        return fetch(request)
          .then((response) => {
            // Vérifier si la réponse est valide
            if (
              !response ||
              response.status !== 200 ||
              response.type !== "basic"
            ) {
              return response;
            }

            // Mettre en cache la réponse
            const responseToCache = response.clone();
            caches.open(DYNAMIC_CACHE).then((cache) => {
              cache.put(request, responseToCache);
            });

            return response;
          })
          .catch((error) => {
            console.error("Service Worker: Erreur fetch", error);

            // Retourner une page d'erreur hors ligne si c'est une page HTML
            if (request.headers.get("accept").includes("text/html")) {
              return caches.match("/offline.html");
            }

            throw error;
          });
      })
    );
  }
});

// Gestion des messages du client
self.addEventListener("message", (event) => {
  const { type, payload } = event.data;

  switch (type) {
    case "SKIP_WAITING":
      self.skipWaiting();
      break;

    case "CACHE_UPDATE":
      updateCache();
      break;

    case "CLEAR_CACHE":
      clearCache();
      break;

    default:
      console.log("Service Worker: Message inconnu", type);
  }
});

// Mise à jour du cache
async function updateCache() {
  try {
    const cache = await caches.open(STATIC_CACHE);
    await cache.addAll(STATIC_FILES);
    console.log("Service Worker: Cache mis à jour");
  } catch (error) {
    console.error("Service Worker: Erreur mise à jour cache", error);
  }
}

// Nettoyage du cache
async function clearCache() {
  try {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map((cacheName) => caches.delete(cacheName)));
    console.log("Service Worker: Cache nettoyé");
  } catch (error) {
    console.error("Service Worker: Erreur nettoyage cache", error);
  }
}

// Gestion des notifications push (pour futures fonctionnalités)
self.addEventListener("push", (event) => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: "/static/images/icon-192.png",
      badge: "/static/images/icon-72.png",
      vibrate: [200, 100, 200],
      data: data.data || {},
    };

    event.waitUntil(self.registration.showNotification(data.title, options));
  }
});

// Gestion des clics sur les notifications
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const urlToOpen = event.notification.data?.url || "/";

  event.waitUntil(
    clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clientList) => {
        // Si une fenêtre est déjà ouverte, la focus
        for (const client of clientList) {
          if (client.url === urlToOpen && "focus" in client) {
            return client.focus();
          }
        }

        // Sinon, ouvrir une nouvelle fenêtre
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Gestion de la synchronisation en arrière-plan (pour futures fonctionnalités)
self.addEventListener("sync", (event) => {
  if (event.tag === "background-sync") {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  try {
    console.log("Service Worker: Synchronisation en arrière-plan");
    // Implémenter la logique de synchronisation
  } catch (error) {
    console.error("Service Worker: Erreur synchronisation", error);
  }
}

// Gestion des erreurs
self.addEventListener("error", (event) => {
  console.error("Service Worker: Erreur", event.error);
});

self.addEventListener("unhandledrejection", (event) => {
  console.error("Service Worker: Promesse rejetée", event.reason);
});

console.log("Service Worker: Chargé");
