# syntax=docker/dockerfile:1
# ============================================================================
# IPSSI_APOCAL_KIT — Dockerfile frontend PRODUCTION (multi-stage -> nginx)
# ----------------------------------------------------------------------------
# Stage 1 : build du bundle statique (Vite). VITE_API_BASE_URL est figée AU
#           BUILD (passée en --build-arg par docker-compose.prod.yml).
# Stage 2 : service du bundle par nginx (léger), avec fallback SPA.
# ============================================================================

# ---- Stage 1 : build ----
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci || npm install --no-audit --no-fund

# URL de l'API injectée AU BUILD (figée dans le bundle). Par défaut "/api"
# (same-origin derrière Caddy) -> aucun CORS, bundle indépendant du domaine.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY . .
RUN npm run build

# ---- Stage 2 : service statique ----
FROM nginx:alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html

# Config nginx : fallback SPA (React Router) + cache long des assets hashés.
RUN cat > /etc/nginx/conf.d/default.conf <<'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Assets versionnés par Vite (hash dans le nom) : cache long et immuable.
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    # SPA : toute route inconnue retombe sur index.html (React Router).
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

EXPOSE 80
