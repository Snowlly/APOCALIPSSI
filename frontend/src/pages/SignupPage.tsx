import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { signup } from '@/api/auth';
import { useAuth } from '@/contexts/AuthContext';
import { useSiteConfig } from '@/contexts/SiteConfigContext';
import { getApiErrorMessage } from '@/api/errors';

export default function SignupPage() {
  const { refresh } = useAuth();
  const { config } = useSiteConfig();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signup({
        email,
        password,
        first_name: firstName || undefined,
        last_name: lastName || undefined,
      });
      await refresh();
      // Un bandeau (dans le Layout) invitera ensuite à confirmer l'email.
      navigate('/upload', { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err, 'Inscription impossible.'));
    } finally {
      setLoading(false);
    }
  };

  // L'admin peut fermer les inscriptions (Lot 8).
  if (!config.allow_signups) {
    return (
      <div className="max-w-md mx-auto">
        <div className="card text-center">
          <div className="text-4xl mb-3">🔒</div>
          <h1 className="text-2xl font-bold text-slate-900 mb-2">Inscriptions fermées</h1>
          <p className="text-sm text-slate-500 mb-4">
            Les inscriptions sont actuellement désactivées. Revenez plus tard.
          </p>
          <Link to="/login" className="text-indigo-600 hover:underline">
            Déjà un compte ? Se connecter
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="card">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Créer un compte</h1>
        <p className="text-sm text-slate-500 mb-6">
          Déjà inscrit ?{' '}
          <Link to="/login" className="text-indigo-600 hover:underline">
            Se connecter
          </Link>
        </p>

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border-l-4 border-rose-500 text-sm text-rose-900 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
            <input
              type="email"
              required
              autoFocus
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Prénom <span className="text-slate-400 font-normal">(facultatif)</span>
              </label>
              <input
                type="text"
                autoComplete="given-name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Nom <span className="text-slate-400 font-normal">(facultatif)</span>
              </label>
              <input
                type="text"
                autoComplete="family-name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="input"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Mot de passe
              <span className="text-slate-400 font-normal"> (≥ 8 caractères)</span>
            </label>
            <input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
            />
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Création du compte…' : 'Créer mon compte'}
          </button>
        </form>
      </div>
    </div>
  );
}
