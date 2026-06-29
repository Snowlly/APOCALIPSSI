# ============================================================================
# IPSSI_APOCAL_KIT — Dockerfile frontend (React + Vite)
# ============================================================================

FROM node:20-alpine

WORKDIR /app

# Installer les dépendances en premier (cache layer)
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

# Copier le reste
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
