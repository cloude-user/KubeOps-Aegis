# ============================================================
# Aegis Commerce: React Frontend Multi-Stage Dockerfile
# Builds Vite React App & serves via production NGINX
# ============================================================

FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/frontend/package.json ./
RUN npm install

COPY apps/frontend/ ./
RUN npm run build

FROM nginx:alpine AS final

# Install custom NGINX configuration with SPA routing and API reverse proxy
COPY apps/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
