/**
 * Onglet « Config LLM » de l'admin.
 *
 * Permet de choisir le fournisseur LLM, son modèle et sa clé API — avec une AIDE
 * spécifique à chaque fournisseur (comment obtenir une clé, modèle conseillé,
 * gratuit/payant). La config est enregistrée EN BASE et prioritaire sur le .env.
 *
 * Sécurité : les clés ne sont jamais réaffichées en clair ; on indique seulement
 * si une clé est « déjà définie ». Laisser le champ vide = ne pas changer.
 */
import { useEffect, useState, type FormEvent } from 'react';
import { getLLMConfig, updateLLMConfig, type LLMConfig, type ProviderInfo } from '@/api/admin';
import { getApiErrorMessage } from '@/api/errors';

export default function LLMConfigTab() {
  const [cfg, setCfg] = useState<LLMConfig | null>(null);
  const [backend, setBackend] = useState('');
  const [model, setModel] = useState('');
  const [ollamaHost, setOllamaHost] = useState('');
  const [timeout, setTimeoutVal] = useState<string>('');
  const [keyInput, setKeyInput] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const apply = (c: LLMConfig) => {
    setCfg(c);
    setBackend(c.backend || c.effective.backend || 'ollama');
    setModel(c.model);
    setOllamaHost(c.ollama_host);
    setTimeoutVal(c.timeout !== null ? String(c.timeout) : '');
    setKeyInput('');
  };

  useEffect(() => {
    getLLMConfig()
      .then(apply)
      .catch((err) => setError(getApiErrorMessage(err, 'Chargement impossible.')));
  }, []);

  if (error && !cfg) return <p className="text-rose-600">{error}</p>;
  if (!cfg) return <p className="text-slate-500">Chargement…</p>;

  const provider: ProviderInfo | undefined = cfg.providers.find((p) => p.key === backend);
  const keyAlreadySet = cfg.api_keys_set[backend];

  const save = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setLoading(true);
    try {
      const patch: Parameters<typeof updateLLMConfig>[0] = {
        backend,
        model,
        timeout: timeout ? Number(timeout) : null,
      };
      if (backend === 'ollama') patch.ollama_host = ollamaHost;
      if (keyInput) patch.api_keys = { [backend]: keyInput };
      apply(await updateLLMConfig(patch));
      setMessage('Configuration LLM enregistrée. Elle est active immédiatement.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Enregistrement impossible.'));
    } finally {
      setLoading(false);
    }
  };

  const clearKey = async () => {
    setLoading(true);
    setMessage(null);
    setError(null);
    try {
      apply(await updateLLMConfig({ api_keys: { [backend]: '' } }));
      setMessage('Clé supprimée.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Suppression impossible.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Config effective (ce qui est réellement utilisé) */}
      <div className="card bg-slate-50">
        <div className="text-sm text-slate-500">Configuration active (effective)</div>
        <div className="mt-1 font-mono text-sm text-slate-900">
          {cfg.effective.backend} · {cfg.effective.model || '(modèle par défaut)'}
        </div>
        <p className="text-xs text-slate-400 mt-1">
          « La base l'emporte si renseignée, sinon repli sur le .env. »
        </p>
      </div>

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

      <form onSubmit={save} className="card space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Fournisseur</label>
          <select value={backend} onChange={(e) => setBackend(e.target.value)} className="input">
            {cfg.providers.map((p) => (
              <option key={p.key} value={p.key}>
                {p.label}
                {p.paid ? ' — payant' : p.cloud ? ' — cloud' : ' — local/gratuit'}
              </option>
            ))}
          </select>
        </div>

        {/* Aide spécifique au fournisseur sélectionné */}
        {provider && (
          <div className="p-3 bg-indigo-50 border-l-4 border-indigo-400 rounded text-sm text-indigo-900 space-y-1">
            <div className="flex flex-wrap gap-2">
              {provider.cloud && (
                <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 text-xs">
                  ☁️ Cloud — données hors serveur (RGPD)
                </span>
              )}
              {provider.paid && (
                <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 text-xs">
                  💳 Payant (crédit requis)
                </span>
              )}
              {!provider.cloud && (
                <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-xs">
                  🔒 Local / gratuit
                </span>
              )}
            </div>
            <p>{provider.help}</p>
            {provider.keys_url && (
              <a
                href={provider.keys_url}
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:no-underline font-medium"
              >
                Obtenir une clé API →
              </a>
            )}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Modèle <span className="text-slate-400 font-normal">(vide = défaut du .env)</span>
          </label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={provider?.default_model}
            className="input font-mono"
          />
        </div>

        {backend === 'ollama' && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              URL Ollama <span className="text-slate-400 font-normal">(vide = OLLAMA_HOST)</span>
            </label>
            <input
              type="text"
              value={ollamaHost}
              onChange={(e) => setOllamaHost(e.target.value)}
              placeholder="http://ollama:11434"
              className="input font-mono"
            />
          </div>
        )}

        {provider?.needs_key && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Clé API
              {keyAlreadySet && (
                <span className="text-emerald-600 font-normal"> — déjà définie (•••)</span>
              )}
            </label>
            <input
              type="password"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              placeholder={keyAlreadySet ? 'Laisser vide pour ne pas changer' : 'Saisir la clé API'}
              className="input font-mono"
              autoComplete="off"
            />
            {keyAlreadySet && (
              <button
                type="button"
                onClick={clearKey}
                disabled={loading}
                className="text-xs text-rose-600 hover:underline mt-1"
              >
                Supprimer la clé enregistrée
              </button>
            )}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Timeout (s) <span className="text-slate-400 font-normal">(vide = défaut)</span>
          </label>
          <input
            type="number"
            min={0}
            value={timeout}
            onChange={(e) => setTimeoutVal(e.target.value)}
            className="input w-32"
          />
        </div>

        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? 'Enregistrement…' : 'Enregistrer la config LLM'}
        </button>
      </form>

      {/* Avertissement sécurité (parti pris pédagogique du kit) */}
      <div className="p-3 bg-amber-50 border-l-4 border-amber-400 rounded text-xs text-amber-900">
        ⚠️ <strong>Sécurité</strong> : les clés API sont stockées <em>en base</em>
        (jamais réaffichées en clair). C'est acceptable pour ce kit pédagogique, mais en{' '}
        <strong>production</strong> il faudrait les chiffrer (ex. Fernet) ou utiliser un
        gestionnaire de secrets.
      </div>
    </div>
  );
}
