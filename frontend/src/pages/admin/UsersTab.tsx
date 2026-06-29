/** Onglet « Utilisateurs » de l'admin : liste, recherche et actions. */
import { useEffect, useState } from 'react';
import {
  listAdminUsers,
  updateAdminUser,
  deleteAdminUser,
  resendUserVerification,
  type AdminUser,
} from '@/api/admin';
import { getApiErrorMessage } from '@/api/errors';

export default function UsersTab() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [q, setQ] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = (query = '') => {
    setLoading(true);
    listAdminUsers(query)
      .then(setUsers)
      .catch((err) => setError(getApiErrorMessage(err, 'Chargement impossible.')))
      .finally(() => setLoading(false));
  };

  // Recherche : recharge 300 ms après la dernière frappe (debounce simple).
  useEffect(() => {
    const t = setTimeout(() => load(q), 300);
    return () => clearTimeout(t);
  }, [q]);

  const patch = async (u: AdminUser, change: Parameters<typeof updateAdminUser>[1]) => {
    setMessage(null);
    setError(null);
    try {
      const updated = await updateAdminUser(u.id, change);
      setUsers((list) => list.map((x) => (x.id === u.id ? updated : x)));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Action impossible.'));
    }
  };

  const remove = async (u: AdminUser) => {
    if (!window.confirm(`Supprimer définitivement le compte ${u.email} ?`)) return;
    setMessage(null);
    setError(null);
    try {
      await deleteAdminUser(u.id);
      setUsers((list) => list.filter((x) => x.id !== u.id));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Suppression impossible.'));
    }
  };

  const resend = async (u: AdminUser) => {
    setMessage(null);
    setError(null);
    try {
      setMessage(await resendUserVerification(u.id));
    } catch (err) {
      setError(getApiErrorMessage(err, 'Envoi impossible.'));
    }
  };

  return (
    <div className="space-y-4">
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Rechercher par email ou nom…"
        className="input max-w-sm"
      />

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

      {loading ? (
        <p className="text-slate-500">Chargement…</p>
      ) : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-left">
              <tr>
                <th className="px-3 py-2">Email</th>
                <th className="px-3 py-2">Nom</th>
                <th className="px-3 py-2">Quiz</th>
                <th className="px-3 py-2">Email vérifié</th>
                <th className="px-3 py-2">Statut</th>
                <th className="px-3 py-2">Rôle</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-slate-200">
                  <td className="px-3 py-2 font-mono text-xs">
                    {u.email}
                    {u.is_superuser && (
                      <span className="ml-1 px-1 rounded bg-indigo-100 text-indigo-700 text-[10px]">
                        super
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {[u.first_name, u.last_name].filter(Boolean).join(' ') || '—'}
                  </td>
                  <td className="px-3 py-2">{u.quiz_count}</td>
                  <td className="px-3 py-2">
                    {u.email_verified ? (
                      <span className="text-emerald-600">✓ oui</span>
                    ) : (
                      <span className="text-slate-400">non</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {u.is_active ? (
                      <span className="text-emerald-600">actif</span>
                    ) : (
                      <span className="text-rose-600">désactivé</span>
                    )}
                  </td>
                  <td className="px-3 py-2">{u.is_staff ? 'admin' : 'membre'}</td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-2 text-xs">
                      <button
                        onClick={() => patch(u, { is_active: !u.is_active })}
                        className="text-indigo-600 hover:underline"
                      >
                        {u.is_active ? 'Désactiver' : 'Activer'}
                      </button>
                      <button
                        onClick={() => patch(u, { is_staff: !u.is_staff })}
                        className="text-indigo-600 hover:underline"
                      >
                        {u.is_staff ? 'Retirer admin' : 'Rendre admin'}
                      </button>
                      {!u.email_verified && (
                        <>
                          <button
                            onClick={() => patch(u, { email_verified: true })}
                            className="text-indigo-600 hover:underline"
                          >
                            Forcer vérif.
                          </button>
                          <button
                            onClick={() => resend(u)}
                            className="text-indigo-600 hover:underline"
                          >
                            Renvoyer mail
                          </button>
                        </>
                      )}
                      <button onClick={() => remove(u)} className="text-rose-600 hover:underline">
                        Supprimer
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-center text-slate-400">
                    Aucun utilisateur trouvé.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
