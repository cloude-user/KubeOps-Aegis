# ============================================================
# Aegis Commerce: React Frontend Multi-Stage Dockerfile
# Builds Vite React App & serves via NGINX
# ============================================================

FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/frontend/package.json ./
RUN npm install

COPY apps/frontend/ ./
RUN npm run build

FROM nginx:alpine AS final

COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
