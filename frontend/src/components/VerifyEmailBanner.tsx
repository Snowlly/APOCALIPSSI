/**
 * Bandeau d'invitation à confirmer son adresse email.
 *
 * [Note pédagogique] Validation "soft" : on NE bloque PAS l'accès à
 * l'application tant que l'email n'est pas confirmé. On affiche simplement ce
 * bandeau non intrusif, avec un bouton pour renvoyer l'email de confirmation.
 * Il disparaît dès que l'email est vérifié (user.email_verified === true).
 */
import { useState } from 'react';
import { resendVerification } from '@/api/auth';
import { useAuth } from '@/contexts/AuthContext';
import { getApiErrorMessage } from '@/api/errors';

export default function VerifyEmailBanner() {
  const { user } = useAuth();
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Rien à afficher si non connecté, ou si l'email est déjà confirmé.
  if (!user || user.email_verified) return null;

  const handleResend = async () => {
    setLoading(true);
    setMessage(null);
    try {
      setMessage(await resendVerification());
    } catch (err) {
      setMessage(getApiErrorMessage(err, 'Impossible de renvoyer l’email pour le moment.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-amber-50 border-b border-amber-200">
      <div className="max-w-6xl mx-auto px-4 py-2 text-sm text-amber-900 flex flex-wrap items-center justify-between gap-2">
        <span>
          ✉️ Votre adresse email n'est pas encore confirmée. Vérifiez votre boîte de réception
          {message ? ` — ${message}` : '.'}
        </span>
        <button
          onClick={handleResend}
          disabled={loading}
          className="underline hover:no-underline font-medium disabled:opacity-50"
        >
          {loading ? 'Envoi…' : 'Renvoyer l’email'}
        </button>
      </div>
    </div>
  );
}
