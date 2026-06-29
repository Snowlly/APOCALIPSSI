/**
 * Contexte de configuration PUBLIQUE du site (Lot 8).
 *
 * Récupère au démarrage le nom de l'application, la bannière globale et l'état
 * des inscriptions, pour que toute l'UI s'y adapte (en-tête, bannière, page
 * d'inscription). Rafraîchissable après une modification dans l'admin.
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { getPublicSiteConfig, type PublicSiteConfig } from '@/api/siteConfig';

const DEFAULTS: PublicSiteConfig = {
  app_name: 'EduTutor IA',
  allow_signups: true,
  banner_enabled: false,
  banner_message: '',
};

type SiteConfigContextValue = {
  config: PublicSiteConfig;
  refresh: () => Promise<void>;
};

const SiteConfigContext = createContext<SiteConfigContextValue | null>(null);

export function SiteConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<PublicSiteConfig>(DEFAULTS);

  const refresh = async () => {
    try {
      setConfig(await getPublicSiteConfig());
    } catch {
      setConfig(DEFAULTS); // en cas d'erreur, on garde des valeurs par défaut sûres
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <SiteConfigContext.Provider value={{ config, refresh }}>{children}</SiteConfigContext.Provider>
  );
}

export function useSiteConfig(): SiteConfigContextValue {
  const ctx = useContext(SiteConfigContext);
  if (!ctx) throw new Error('useSiteConfig doit être utilisé dans un SiteConfigProvider');
  return ctx;
}
