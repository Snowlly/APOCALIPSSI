/**
 * Page "Mon profil".
 *
 * Trois zones :
 *   1. Mes informations  : modifier prénom / nom / email
 *   2. Mot de passe       : changer son mot de passe (ancien requis)
 *   3. Zone de danger     : supprimer définitivement son compte
 *
 * [Note pédagogique] Changer son email = re-valider (le bandeau « email non
 * confirmé » réapparaîtra). La suppression est une action DESTRUCTIVE : on la
 * protège par une confirmation au mot de passe.
 *
 * [TODO J3-bis RGPD] Ajouter ici un bouton « Exporter mes données » (droit à la
 *   portabilité) — placeholder présent plus bas, à implémenter pendant la semaine.
 * [TODO J4] Ajouter un bouton « Signaler un contenu / un quiz » — placeholder.
 */
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { changePassword, deleteAccount, updateProfile } from '@/api/auth';
import { getApiErrorMessage } from '@/api/errors';

export default function ProfilePage() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();

  // --- Zone 1 : informations ---
  const [firstName, setFirstName] = useState(user?.first_name ?? '');
  const [lastName, setLastName] = useState(user?.last_name ?? '');
  const [email, setEmail] = useState(user?.email ?? '');
  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [infoErr, setInfoErr] = useState<string | null>(null);
  const [infoLoading, setInfoLoading] = useState(false);

  // --- Zone 2 : mot de passe ---
  const [oldPwd, setOldPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [pwdMsg, setPwdMsg] = useState<string | null>(null);
  const [pwdErr, setPwdErr] = useState<string | null>(null);
  const [pwdLoading, setPwdLoading] = useState(false);

  // --- Zone 3 : suppression ---
  const [delPwd, setDelPwd] = useState('');
  const [delConfirm, setDelConfirm] = useState(false);
  const [delErr, setDelErr] = useState<string | null>(null);
  const [delLoading, setDelLoading] = useState(false);

  const handleInfo = async (e: FormEvent) => {
    e.preventDefault();
    setInfoMsg(null);
    setInfoErr(null);
    setInfoLoading(true);
    try {
      await updateProfile({ first_name: firstName, last_name: lastName, email });
      await refresh();
      setInfoMsg('Profil mis à jour.');
    } catch (err) {
      setInfoErr(getApiErrorMessage(err, 'Mise à jour impossible.'));
    } finally {
      setInfoLoading(false);
    }
  };

  const handlePassword = async (e: FormEvent) => {
    e.preventDefault();
    setPwdMsg(null);
    setPwdErr(null);
    if (newPwd !== confirmPwd) {
      setPwdErr('Les deux nouveaux mots de passe ne correspondent pas.');
      return;
    }
    setPwdLoading(true);
    try {
      const detail = await changePassword(oldPwd, newPwd);
      setPwdMsg(detail);
      setOldPwd('');
      setNewPwd('');
      setConfirmPwd('');
    } catch (err) {
      setPwdErr(getApiErrorMessage(err, 'Changement de mot de passe impossible.'));
    } finally {
      setPwdLoading(false);
    }
  };

  const handleDelete = async (e: FormEvent) => {
    e.preventDefault();
    setDelErr(null);
    setDelLoading(true);
    try {
      await deleteAccount(delPwd);
      await refresh(); // token effacé -> l'utilisateur passe à null
      navigate('/', { replace: true });
    } catch (err) {
      setDelErr(getApiErrorMessage(err, 'Suppression impossible.'));
      setDelLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Mon profil</h1>

      {/* Zone 1 : informations */}
      <section className="card">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Mes informations</h2>
        {infoMsg && (
          <div className="mb-4 p-3 bg-emerald-50 border-l-4 border-emerald-500 text-sm text-emerald-900 rounded">
            {infoMsg}
          </div>
        )}
        {infoErr && (
          <div className="mb-4 p-3 bg-rose-50 border-l-4 border-rose-500 text-sm text-rose-900 rounded">
            {infoErr}
          </div>
        )}
        <form onSubmit={handleInfo} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Prénom</label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nom</label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="input"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Email{' '}
              {user && !user.email_verified && (
                <span className="text-amber-600 font-normal">(non confirmé)</span>
              )}
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
            />
            <p className="text-xs text-slate-500 mt-1">
              Changer d'email nécessitera une nouvelle confirmation par mail.
            </p>
          </div>
          <button type="submit" disabled={infoLoading} className="btn-primary">
            {infoLoading ? 'Enregistrement…' : 'Enregistrer'}
          </button>
        </form>
      </section>

      {/* Zone 2 : mot de passe */}
      <section className="card">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Changer mon mot de passe</h2>
        {pwdMsg && (
          <div className="mb-4 p-3 bg-emerald-50 border-l-4 border-emerald-500 text-sm text-emerald-900 rounded">
            {pwdMsg}
          </div>
        )}
        {pwdErr && (
          <div className="mb-4 p-3 bg-rose-50 border-l-4 border-rose-500 text-sm text-rose-900 rounded">
            {pwdErr}
          </div>
        )}
        <form onSubmit={handlePassword} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Mot de passe actuel
            </label>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={oldPwd}
              onChange={(e) => setOldPwd(e.target.value)}
              className="input"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Nouveau mot de passe
              </label>
              <input
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={newPwd}
                onChange={(e) => setNewPwd(e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Confirmer</label>
              <input
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                value={confirmPwd}
                onChange={(e) => setConfirmPwd(e.target.value)}
                className="input"
              />
            </div>
          </div>
          <button type="submit" disabled={pwdLoading} className="btn-primary">
            {pwdLoading ? 'Modification…' : 'Modifier le mot de passe'}
          </button>
        </form>
      </section>

      {/* Placeholders RGPD / signalement (à compléter pendant la semaine) */}
      <section className="card bg-slate-50">
        <h2 className="text-lg font-semibold text-slate-900 mb-2">Mes données</h2>
        <p className="text-sm text-slate-500 mb-4">
          Fonctionnalités à construire pendant la semaine APOCAL'IPSSI.
        </p>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            disabled
            title="À implémenter (J3-bis) — droit à la portabilité RGPD"
            className="btn-secondary opacity-60 cursor-not-allowed"
          >
            Exporter mes données (bientôt)
          </button>
          <button
            type="button"
            disabled
            title="À implémenter (J4) — signalement de contenu"
            className="btn-secondary opacity-60 cursor-not-allowed"
          >
            Signaler un contenu (bientôt)
          </button>
        </div>
      </section>

      {/* Zone 3 : danger */}
      <section className="card border-2 border-rose-200">
        <h2 className="text-lg font-semibold text-rose-700 mb-2">Zone de danger</h2>
        <p className="text-sm text-slate-600 mb-4">
          La suppression de votre compte est <strong>définitive</strong> et efface toutes vos
          données (quiz, historique). Cette action est irréversible.
        </p>
        {delErr && (
          <div className="mb-4 p-3 bg-rose-50 border-l-4 border-rose-500 text-sm text-rose-900 rounded">
            {delErr}
          </div>
        )}
        <form onSubmit={handleDelete} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Confirmez avec votre mot de passe
            </label>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={delPwd}
              onChange={(e) => setDelPwd(e.target.value)}
              className="input"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={delConfirm}
              onChange={(e) => setDelConfirm(e.target.checked)}
            />
            Je comprends que cette action est irréversible.
          </label>
          <button
            type="submit"
            disabled={delLoading || !delConfirm}
            className="px-4 py-2 rounded bg-rose-600 text-white font-medium hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {delLoading ? 'Suppression…' : 'Supprimer définitivement mon compte'}
          </button>
        </form>
      </section>
    </div>
  );
}
