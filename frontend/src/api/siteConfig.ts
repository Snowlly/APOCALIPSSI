/** Config PUBLIQUE du site (nom de l'app, bannière, inscriptions ouvertes). */
import { api } from './client';

export type PublicSiteConfig = {
  app_name: string;
  allow_signups: boolean;
  banner_enabled: boolean;
  banner_message: string;
};

export async function getPublicSiteConfig(): Promise<PublicSiteConfig> {
  const { data } = await api.get<PublicSiteConfig>('/site-config/');
  return data;
}
