/**
 * Appels API de l'interface d'administration (Lot 8).
 *
 * Toutes ces routes sont réservées aux comptes staff côté backend
 * (permission IsAdminUser). Le frontend protège aussi l'accès via RequireAdmin.
 */
import { api } from './client';

// ----- Vue d'ensemble -----

export type AdminStats = {
  users_total: number;
  users_active: number;
  users_staff: number;
  quizzes_total: number;
  quizzes_taken: number;
  average_score: number | null;
  questions_total: number;
};

export async function getAdminStats(): Promise<AdminStats> {
  const { data } = await api.get<AdminStats>('/admin/stats/');
  return data;
}

// ----- Config du site -----

export type SiteConfig = {
  app_name: string;
  allow_signups: boolean;
  require_email_verification: boolean;
  banner_enabled: boolean;
  banner_message: string;
  updated_at?: string;
};

export async function getSiteConfig(): Promise<SiteConfig> {
  const { data } = await api.get<SiteConfig>('/admin/site-config/');
  return data;
}

export async function updateSiteConfig(patch: Partial<SiteConfig>): Promise<SiteConfig> {
  const { data } = await api.patch<SiteConfig>('/admin/site-config/', patch);
  return data;
}

// ----- Config LLM -----

export type ProviderInfo = {
  key: string;
  label: string;
  cloud: boolean;
  paid: boolean;
  needs_key: boolean;
  default_model: string;
  help: string;
  keys_url: string;
};

export type LLMConfig = {
  backend: string;
  model: string;
  ollama_host: string;
  timeout: number | null;
  api_keys_set: Record<string, boolean>;
  providers: ProviderInfo[];
  effective: { backend: string; model: string; ollama_host: string; timeout: number | null };
};

export async function getLLMConfig(): Promise<LLMConfig> {
  const { data } = await api.get<LLMConfig>('/admin/llm-config/');
  return data;
}

export async function updateLLMConfig(patch: {
  backend?: string;
  model?: string;
  ollama_host?: string;
  timeout?: number | null;
  api_keys?: Record<string, string>;
}): Promise<LLMConfig> {
  const { data } = await api.patch<LLMConfig>('/admin/llm-config/', patch);
  return data;
}

// ----- Utilisateurs -----

export type AdminUser = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  email_verified: boolean;
  quiz_count: number;
};

export async function listAdminUsers(q = ''): Promise<AdminUser[]> {
  const { data } = await api.get<AdminUser[]>('/admin/users/', { params: q ? { q } : {} });
  return data;
}

export async function updateAdminUser(
  id: number,
  patch: { is_active?: boolean; is_staff?: boolean; email_verified?: boolean },
): Promise<AdminUser> {
  const { data } = await api.patch<AdminUser>(`/admin/users/${id}/`, patch);
  return data;
}

export async function deleteAdminUser(id: number): Promise<void> {
  await api.delete(`/admin/users/${id}/`);
}

export async function resendUserVerification(id: number): Promise<string> {
  const { data } = await api.post<{ detail: string }>(`/admin/users/${id}/resend-verification/`);
  return data.detail;
}

// ----- Opérations base -----

export async function seedData(): Promise<string> {
  const { data } = await api.post<{ detail: string }>('/admin/seed/');
  return data.detail;
}

export async function resetData(
  password: string,
  includeUsers: boolean,
): Promise<{ detail: string; deleted_quizzes: number; deleted_users: number }> {
  const { data } = await api.post('/admin/reset-data/', {
    confirm: 'RESET',
    password,
    include_users: includeUsers,
  });
  return data;
}
