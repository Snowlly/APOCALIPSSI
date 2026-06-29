/**
 * Dashboard de progression (MVP2 — Lot 6, fonctionnalité démo).
 *
 * Affiche quelques indicateurs clés (KPI) et un petit graphique de progression
 * des scores au fil du temps. Le graphique est dessiné « à la main » avec de
 * simples <div> (barres) : pas de librairie de charting, pour garder le kit
 * léger. Vous pourrez le remplacer par recharts/chart.js dans votre MVP2.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getStats, type Stats } from '@/api/quizzes';
import { getApiErrorMessage } from '@/api/errors';

/** Couleur d'une barre selon le score (vert / ambre / rouge). */
function barColor(score: number): string {
  if (score >= 7) return 'bg-emerald-500';
  if (score >= 4) return 'bg-amber-500';
  return 'bg-rose-500';
}

function KpiCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="card">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="text-3xl font-bold text-slate-900 mt-1">{value}</div>
      {hint && <div className="text-xs text-slate-400 mt-1">{hint}</div>}
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch((err) => setError(getApiErrorMessage(err, 'Impossible de charger les statistiques.')))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-slate-500">Chargement…</p>;
  if (error) return <p className="text-rose-600">{error}</p>;
  if (!stats) return null;

  const hasData = stats.quizzes_taken > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Tableau de bord</h1>
          <p className="text-slate-500 text-sm">Votre progression sur EduTutor IA.</p>
        </div>
        <Link to="/upload" className="btn-primary">
          + Nouveau quiz
        </Link>
      </div>

      {!hasData ? (
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">📊</div>
          <p className="text-slate-600 mb-4">
            Passez votre premier quiz pour voir vos statistiques apparaître ici.
          </p>
          <Link to="/upload" className="btn-primary">
            Créer un quiz
          </Link>
        </div>
      ) : (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              label="Quiz passés"
              value={String(stats.quizzes_taken)}
              hint={`${stats.total_quizzes} créés au total`}
            />
            <KpiCard
              label="Score moyen"
              value={stats.average_score !== null ? `${stats.average_score}/10` : '—'}
            />
            <KpiCard
              label="Meilleur score"
              value={stats.best_score !== null ? `${stats.best_score}/10` : '—'}
            />
            <KpiCard
              label="Précision"
              value={stats.accuracy !== null ? `${stats.accuracy}%` : '—'}
              hint={`${stats.questions_correct}/${stats.questions_answered} bonnes réponses`}
            />
          </div>

          {/* Graphique de progression (barres maison) */}
          <div className="card">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Progression des scores</h2>
            <div className="flex items-end gap-2 h-48 border-b border-l border-slate-200 pl-2 pb-px">
              {stats.history.map((p) => (
                <div
                  key={p.id}
                  className="flex-1 flex flex-col items-center justify-end h-full group"
                >
                  <span className="text-xs text-slate-500 mb-1">{p.score}</span>
                  <div
                    className={`w-full rounded-t ${barColor(p.score)} transition-all`}
                    style={{ height: `${(p.score / 10) * 100}%` }}
                    title={`${p.title} — ${p.score}/10 (${new Date(p.created_at).toLocaleDateString('fr-FR')})`}
                  />
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Chaque barre = un quiz passé, dans l'ordre chronologique. Survolez pour voir le
              détail.
            </p>
          </div>

          <div className="flex gap-3">
            <Link to="/review" className="btn-secondary">
              📕 Réviser mes erreurs
            </Link>
            <Link to="/history" className="btn-secondary">
              📚 Voir l'historique
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
