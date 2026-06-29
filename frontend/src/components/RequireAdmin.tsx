import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import type { ReactNode } from 'react';

/**
 * Wrap une route réservée aux ADMINS (is_staff).
 * - Pas connecté -> /login
 * - Connecté mais non-staff -> accueil (pas d'accès admin)
 */
export default function RequireAdmin({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <div className="text-center text-slate-500 py-12">Chargement…</div>;
  }
  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  if (!user.is_staff) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
