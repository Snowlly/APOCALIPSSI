/**
 * Contexte de thème clair / sombre (MVP2 — Lot 6).
 *
 * [Note pédagogique] On pilote le mode sombre via une classe `dark` ajoutée sur
 * <html> (configuré dans tailwind.config.js avec darkMode: 'class'). Le choix de
 * l'utilisateur est mémorisé dans localStorage ; à défaut, on suit la préférence
 * système (prefers-color-scheme).
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

type Theme = 'light' | 'dark';

type ThemeContextValue = {
  theme: Theme;
  toggleTheme: () => void;
};

const STORAGE_KEY = 'edututor-theme';
const ThemeContext = createContext<ThemeContextValue | null>(null);

/** Détermine le thème initial : préférence stockée, sinon préférence système. */
function getInitialTheme(): Theme {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches;
  return prefersDark ? 'dark' : 'light';
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  // Applique la classe `dark` sur <html> et persiste le choix à chaque changement.
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme doit être utilisé à l'intérieur d'un ThemeProvider");
  return ctx;
}
