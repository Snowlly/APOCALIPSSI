/**
 * Contexte d'authentification.
 *
 * Au démarrage, tente de restaurer l'utilisateur via /api/accounts/me/ si un
 * token est présent en localStorage.
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { getToken } from '@/api/client';
import { me, login as apiLogin, logout as apiLogout, type User } from '@/api/auth';

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setLoading] = useState(true);

  useEffect(() => {
    // Restaure la session si un token est présent
    if (getToken()) {
      me()
        .then(setUser)
        .catch(() => setUser(null))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const u = await apiLogin(email, password);
    setUser(u);
  };

  const logout = async () => {
    await apiLogout();
    setUser(null);
  };

  const refresh = async () => {
    if (!getToken()) {
      setUser(null);
      return;
    }
    const u = await me();
    setUser(u);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé à l'intérieur d'un AuthProvider");
  return ctx;
}
