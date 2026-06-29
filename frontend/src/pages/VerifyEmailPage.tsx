/**
 * Page de confirmation d'email.
 *
 * L'utilisateur arrive ici via le lien reçu par email : /verify-email?token=...
 * On lit le token, on appelle le backend automatiquement au chargement, puis on
 * affiche le résultat. Si l'utilisateur est connecté, on rafraîchit son profil
 * pour faire disparaître le bandeau « email non confirmé ».
 */
import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { verifyEmail } from '@/api/auth';
import { useAuth } from '@/contexts/AuthContext';
import { getApiErrorMessage } from '@/api/errors';

type Status = 'loading' | 'success' | 'error';

export default function VerifyEmailPage() {
  const [params] = useSearchParams();
  const { refresh } = useAuth();
  const token = params.get('token') ?? '';

  const [status, setStatus] = useState<Status>('loading');
  const [message, setMessage] = useState('Validation en cours…');
  // Évite un double appel en mode StrictMode (React 18 monte deux fois en dev).
  const done = useRef(false);

  useEffect(() => {
    if (done.current) return;
    done.current = true;

    if (!token) {
      setStatus('error');
      setMessage('Lien de validation incomplet (token manquant).');
      return;
    }

    verifyEmail(token)
      .then(async (detail) => {
        setStatus('success');
        setMessage(detail);
        // Rafraîchit le profil si l'utilisateur est connecté (bandeau à jour).
        await refresh().catch(() => undefined);
      })
      .catch((err) => {
        setStatus('error');
        setMessage(getApiErrorMessage(err, 'Lien de validation invalide ou expiré.'));
      });
  }, [token, refresh]);

  const tone =
    status === 'success'
      ? 'bg-emerald-50 border-emerald-500 text-emerald-900'
      : status === 'error'
        ? 'bg-rose-50 border-rose-500 text-rose-900'
        : 'bg-slate-50 border-slate-400 text-slate-700';

  return (
    <div className="max-w-md mx-auto">
      <div className="card">
        <h1 className="text-2xl font-bold text-slate-900 mb-4">Confirmation d'email</h1>

        <div className={`p-3 border-l-4 text-sm rounded ${tone}`}>{message}</div>

        <div className="mt-6 flex gap-4 text-sm">
          <Link to="/upload" className="text-indigo-600 hover:underline">
            Aller à l'application
          </Link>
          <Link to="/login" className="text-indigo-600 hover:underline">
            Se connecter
          </Link>
        </div>
      </div>
    </div>
  );
}
