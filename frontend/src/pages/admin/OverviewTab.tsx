/** Onglet « Vue d'ensemble » de l'admin : statistiques globales. */
import { useEffect, useState } from 'react';
import { getAdminStats, type AdminStats } from '@/api/admin';
import { getApiErrorMessage } from '@/api/errors';

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="text-3xl font-bold text-slate-900 mt-1">{value}</div>
    </div>
  );
}

export default function OverviewTab() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdminStats()
      .then(setStats)
      .catch((err) => setError(getApiErrorMessage(err, 'Chargement impossible.')));
  }, []);

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!stats) return <p className="text-slate-500">Chargement…</p>;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Stat label="Utilisateurs" value={stats.users_total} />
      <Stat label="Comptes actifs" value={stats.users_active} />
      <Stat label="Administrateurs" value={stats.users_staff} />
      <Stat label="Quiz créés" value={stats.quizzes_total} />
      <Stat label="Quiz passés" value={stats.quizzes_taken} />
      <Stat
        label="Score moyen"
        value={stats.average_score !== null ? `${stats.average_score}/10` : '—'}
      />
      <Stat label="Questions totales" value={stats.questions_total} />
    </div>
  );
}
