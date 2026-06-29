/**
 * Onglet « Données » de l'admin : insérer des données de démo (seed) et
 * réinitialiser la base (DESTRUCTIF, double confirmation).
 */
import { useState, type FormEvent } from 'react';
import { seedData, resetData } from '@/api/admin';
import { getApiErrorMessage } from '@/api/errors';

export default function DataTab() {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Seed
  const [seeding, setSeeding] = useState(false);

  // Reset destructif
  const [confirmText, setConfirmText] = useState('');
  const [password, setPassword] = useState('');
  const [includeUsers, setIncludeUsers] = useState(false);
  const [resetting, setResetting] = useState(false);

  const doSeed = async () => {
    setMessage(null);
    setError(null);
    setSeeding(true);
    try {
      setMessage(await seedData());
    } catch (err) {
      setError(getApiErrorMessage(err, 'Seed impossible.'));
    } finally {
      setSeeding(false);
    }
  };

  const doReset = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setResetting(true);
    try {
      const r = await resetData(password, includeUsers);
      setMessage(
        `${r.detail} (${r.deleted_quizzes} quiz, ${r.deleted_users} utilisateurs supprimés)`,
      );
      setConfirmText('');
      setPassword('');
      setIncludeUsers(false);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Réinitialisation impossible.'));
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {message && (
        <div className="p-3 bg-emerald-50 border-l-4 border-emerald-500 text-sm text-emerald-900 rounded">
          {message}
        </div>
      )}
      {error && (
        <div className="p-3 bg-rose-50 border-l-4 border-rose-500 text-sm text-rose-900 rounded">
          {error}
        </div>
      )}

      {/* Seed */}
      <section className="card">
        <h2 className="text-lg font-semibold text-slate-900 mb-2">Données de démonstration</h2>
        <p className="text-sm text-slate-600 mb-4">
          Insère un utilisateur de test et des quiz d'exemple (commande <code>seed</code>).
        </p>
        <button onClick={doSeed} disabled={seeding} className="btn-secondary">
          {seeding ? 'Insertion…' : 'Insérer des données de démo'}
        </button>
      </section>

      {/* Reset destructif */}
      <section className="card border-2 border-rose-200">
        <h2 className="text-lg font-semibold text-rose-700 mb-2">Réinitialiser la base ⚠️</h2>
        <p className="text-sm text-slate-600 mb-4">
          Supprime <strong>tous les quiz</strong> (et leurs questions). Optionnellement, supprime
          aussi tous les comptes non-administrateurs. <strong>Action irréversible.</strong>
        </p>
        <form onSubmit={doReset} className="space-y-4">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={includeUsers}
              onChange={(e) => setIncludeUsers(e.target.checked)}
            />
            Supprimer aussi les comptes non-administrateurs
          </label>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Tapez <code className="bg-slate-100 px-1 rounded">RESET</code> pour confirmer
            </label>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              className="input font-mono"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Votre mot de passe administrateur
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              className="input"
            />
          </div>
          <button
            type="submit"
            disabled={resetting || confirmText !== 'RESET' || !password}
            className="px-4 py-2 rounded bg-rose-600 text-white font-medium hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {resetting ? 'Réinitialisation…' : 'Réinitialiser la base'}
          </button>
        </form>
      </section>
    </div>
  );
}
