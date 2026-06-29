import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      <section className="text-center py-12">
        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
          Révise mieux,{' '}
          <span className="bg-gradient-to-r from-indigo-600 to-amber-500 bg-clip-text text-transparent">
            grâce à l'IA.
          </span>
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
          Upload ton cours, EduTutor te génère 10 questions QCM, te corrige et identifie tes
          lacunes. Le tout sur ta machine, en open source.
        </p>

        <div className="mt-8 flex flex-wrap gap-3 justify-center">
          {user ? (
            <>
              <Link to="/upload" className="btn-primary px-6 py-3 text-base">
                Créer un quiz
              </Link>
              <Link to="/history" className="btn-secondary px-6 py-3 text-base">
                Voir mon historique
              </Link>
            </>
          ) : (
            <>
              <Link to="/signup" className="btn-primary px-6 py-3 text-base">
                Commencer gratuitement
              </Link>
              <Link to="/login" className="btn-secondary px-6 py-3 text-base">
                Se connecter
              </Link>
            </>
          )}
        </div>
      </section>

      <section className="grid md:grid-cols-3 gap-4">
        <div className="card">
          <div className="text-2xl mb-2">📄</div>
          <h3 className="font-semibold text-slate-900 mb-2">Uploade ton cours</h3>
          <p className="text-sm">PDF ≤ 5 Mo ou texte collé. Tout reste local sur ta machine.</p>
        </div>
        <div className="card">
          <div className="text-2xl mb-2">🤖</div>
          <h3 className="font-semibold text-slate-900 mb-2">10 QCM générés</h3>
          <p className="text-sm">
            Llama 3.1 8B via Ollama. Aucune API payante, aucune fuite de données.
          </p>
        </div>
        <div className="card">
          <div className="text-2xl mb-2">📈</div>
          <h3 className="font-semibold text-slate-900 mb-2">Mesure ta progression</h3>
          <p className="text-sm">
            Historique des scores, lacunes identifiées (extension Release 2).
          </p>
        </div>
      </section>

      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded text-sm">
        <strong className="text-slate-900">Kit de démarrage APOCAL'IPSSI 2026.</strong> Ce frontend
        est volontairement minimaliste — c'est à vous de l'enrichir pendant la semaine. Consultez le{' '}
        <a
          href="https://github.com/melafrit/IPSSI_APOCAL_KIT"
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-600 underline"
        >
          README
        </a>
        .
      </div>
    </div>
  );
}
