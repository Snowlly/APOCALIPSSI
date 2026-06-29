/** Onglet « Config app » de l'admin : réglages globaux de l'application. */
import { useEffect, useState, type FormEvent } from 'react';
import { getSiteConfig, updateSiteConfig, type SiteConfig } from '@/api/admin';
import { useSiteConfig } from '@/contexts/SiteConfigContext';
import { getApiErrorMessage } from '@/api/errors';

export default function SiteConfigTab() {
  const { refresh } = useSiteConfig();
  const [form, setForm] = useState<SiteConfig | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getSiteConfig()
      .then(setForm)
      .catch((err) => setError(getApiErrorMessage(err, 'Chargement impossible.')));
  }, []);

  if (error && !form) return <p className="text-rose-600">{error}</p>;
  if (!form) return <p className="text-slate-500">Chargement…</p>;

  const set = <K extends keyof SiteConfig>(key: K, value: SiteConfig[K]) =>
    setForm({ ...form, [key]: value });

  const save = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setLoading(true);
    try {
      const saved = await updateSiteConfig({
        app_name: form.app_name,
        allow_signups: form.allow_signups,
        require_email_verification: form.require_email_verification,
        banner_enabled: form.banner_enabled,
        banner_message: form.banner_message,
      });
      setForm(saved);
      await refresh(); // met à jour l'en-tête + la bannière dans toute l'app
      setMessage('Configuration enregistrée.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Enregistrement impossible.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={save} className="card space-y-5 max-w-2xl">
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

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Nom de l'application
        </label>
        <input
          type="text"
          value={form.app_name}
          onChange={(e) => set('app_name', e.target.value)}
          className="input"
        />
      </div>

      <label className="flex items-start gap-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.allow_signups}
          onChange={(e) => set('allow_signups', e.target.checked)}
          className="mt-1"
        />
        <span>
          <strong>Autoriser les inscriptions</strong>
          <span className="block text-slate-500">
            Décoché = plus aucune création de compte (le login reste ouvert).
          </span>
        </span>
      </label>

      <label className="flex items-start gap-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.require_email_verification}
          onChange={(e) => set('require_email_verification', e.target.checked)}
          className="mt-1"
        />
        <span>
          <strong>Exiger la validation d'email</strong>
          <span className="block text-slate-500">
            Coché = un email confirmé est requis pour générer des quiz.
          </span>
        </span>
      </label>

      <label className="flex items-start gap-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.banner_enabled}
          onChange={(e) => set('banner_enabled', e.target.checked)}
          className="mt-1"
        />
        <span>
          <strong>Afficher une bannière globale</strong>
          <span className="block text-slate-500">Annonce visible par tous les utilisateurs.</span>
        </span>
      </label>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          Message de la bannière
        </label>
        <textarea
          value={form.banner_message}
          onChange={(e) => set('banner_message', e.target.value)}
          rows={2}
          className="input"
          placeholder="Ex. Maintenance prévue ce soir à 20h."
        />
      </div>

      <button type="submit" disabled={loading} className="btn-primary">
        {loading ? 'Enregistrement…' : 'Enregistrer'}
      </button>
    </form>
  );
}
