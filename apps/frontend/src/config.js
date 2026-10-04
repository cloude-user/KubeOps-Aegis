// Centralized Frontend Configuration
// When running in AKS behind NGINX proxy or local Vite proxy, relative path '' is used.
// If accessing an external backend LoadBalancer, VITE_API_URL can be set (e.g. http://20.x.x.x:8000).
export const API_BASE_URL = import.meta.env.VITE_API_URL || '';
