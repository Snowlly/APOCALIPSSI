/**
 * Client axios partagé.
 *
 * - Lit l'URL de base depuis VITE_API_BASE_URL (configuré dans .env).
 * - Injecte automatiquement le token DRF si présent en localStorage.
 * - Gère la 401 globale en supprimant le token + en redirigeant vers /login.
 */
import axios, { AxiosError, type AxiosInstance } from 'axios';

// Vite remplace import.meta.env.VITE_API_BASE_URL au BUILD (ou au démarrage du
// dev-server), pas au runtime. En dev (npm run dev), la valeur vient du .env via
// docker compose. Pour un build de prod, passez VITE_API_BASE_URL en ARG/ENV au
// moment du docker build, sinon c'est le fallback ci-dessous qui est figé.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';
const TOKEN_KEY = 'apocal_token';

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // 2 min — utile pour generate-quiz qui peut être long
});

// --- Token utilities ---

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// --- Interceptors ---

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // En cas de 401, on nettoie le token. La redirection se fait côté UI
    // via le RequireAuth qui détecte l'absence de session.
    if (error.response?.status === 401) {
      clearToken();
    }
    return Promise.reject(error);
  },
);
