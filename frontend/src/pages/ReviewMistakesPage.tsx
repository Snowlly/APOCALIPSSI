/**
 * Révision des erreurs (MVP2 — Lot 6, fonctionnalité démo).
 *
 * Liste toutes les questions que l'utilisateur a ratées (sa dernière réponse
 * était fausse), en montrant SA réponse (en rouge) et la BONNE réponse (en
 * vert). Objectif pédagogique pour l'apprenant : apprendre de ses erreurs.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMistakes, type Mistake } from '@/api/quizzes';
import { getApiErrorMessage } from '@/api/errors';

function OptionRow({
  text,
  isCorrect,
  isSelected,
}: {
  text: string;
  isCorrect: boolean;
  isSelected: boolean;
}) {
  let cls = 'border-slate-200 text-slate-600';
  let tag = '';
  if (isCorrect) {
    cls = 'border-emerald-400 bg-emerald-50 text-emerald-900';
    tag = '✓ Bonne réponse';
  } else if (isSelected) {
    cls = 'border-rose-400 bg-rose-50 text-rose-900';
    tag = '✗ Votre réponse';
  }
  return (
    <div className={`flex items-center justify-between gap-3 px-3 py-2 border rounded ${cls}`}>
      <span>{text}</span>
      {tag && <span className="text-xs font-semibold whitespace-nowrap">{tag}</span>}
    </div>
  );
}

export default function ReviewMistakesPage() {
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMistakes()
      .then((res) => setMistakes(res.mistakes))
      .catch((err) => setError(getApiErrorMessage(err, 'Impossible de charger vos erreurs.')))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-slate-500">Chargement…</p>;
  if (error) return <p className="text-rose-600">{error}</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Réviser mes erreurs</h1>
        <p className="text-slate-500 text-sm">
          {mistakes.length === 0
            ? 'Aucune erreur enregistrée — bravo !'
            : `${mistakes.length} question${mistakes.length > 1 ? 's' : ''} à revoir.`}
        </p>
      </div>

      {mistakes.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-5xl mb-4">🎯</div>
          <p className="text-slate-600 mb-4">
            Vous n'avez aucune erreur à réviser. Passez un quiz pour vous entraîner !
          </p>
          <Link to="/upload" className="btn-primary">
            Créer un quiz
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {mistakes.map((m) => (
            <div key={`${m.quiz_id}-${m.index}`} className="card">
              <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                <span className="font-mono text-xs text-slate-500">
                  Quiz #{m.quiz_id} · Question {m.index}
                </span>
                <Link to={`/quiz/${m.quiz_id}`} className="text-xs text-indigo-600 hover:underline">
                  Refaire ce quiz →
                </Link>
              </div>
              <h3 className="font-semibold text-slate-900 mb-3">{m.prompt}</h3>
              <div className="space-y-2">
                {m.options.map((opt, i) => (
                  <OptionRow
                    key={i}
                    text={opt}
                    isCorrect={i === m.correct_index}
                    isSelected={i === m.selected_index}
                  />
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-2">Issue du quiz « {m.quiz_title} ».</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
