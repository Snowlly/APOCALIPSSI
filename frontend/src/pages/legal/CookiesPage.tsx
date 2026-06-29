/** Politique de gestion des cookies (modèle vierge à compléter). */
import LegalScaffold, { type LegalSection } from './LegalScaffold';

const SECTIONS: LegalSection[] = [
  { title: "Qu'est-ce qu'un cookie ?", hint: 'définition simple à destination des utilisateurs.' },
  {
    title: 'Cookies et stockage utilisés',
    hint: "lister ce que le site dépose (ex. token d'authentification en localStorage).",
  },
  {
    title: 'Finalité de chaque cookie',
    hint: "à quoi sert chaque cookie/stockage (technique, mesure d'audience…).",
  },
  {
    title: 'Consentement',
    hint: 'cookies nécessitant un consentement préalable et comment il est recueilli.',
  },
  { title: 'Durée de conservation', hint: 'combien de temps chaque cookie est conservé.' },
  {
    title: 'Gérer ou refuser les cookies',
    hint: 'comment paramétrer ou supprimer les cookies (navigateur, bannière).',
  },
];

export default function CookiesPage() {
  return (
    <LegalScaffold
      title="Politique de gestion des cookies"
      intro="Les cookies et technologies de stockage utilisés par le site, et comment les gérer."
      sections={SECTIONS}
    >
      <div className="mt-6 p-3 bg-slate-50 border border-slate-200 rounded text-sm text-slate-600">
        💡 Indice pour votre équipe : ce kit stocke actuellement le{' '}
        <code className="bg-slate-200 px-1 rounded">token</code> d'authentification dans le{' '}
        <code className="bg-slate-200 px-1 rounded">localStorage</code> du navigateur. C'est un bon
        point de départ à documenter ici.
      </div>
    </LegalScaffold>
  );
}
