/** Mentions légales (modèle vierge à compléter). */
import LegalScaffold, { type LegalSection } from './LegalScaffold';

const SECTIONS: LegalSection[] = [
  {
    title: 'Éditeur du site',
    hint: "nom de l'organisation/équipe, statut, adresse, email de contact.",
  },
  {
    title: 'Directeur de la publication',
    hint: 'nom de la personne responsable du contenu publié.',
  },
  { title: 'Hébergeur', hint: "nom, adresse et téléphone de l'hébergeur du site." },
  {
    title: 'Propriété intellectuelle',
    hint: 'à qui appartiennent les textes, logos, code, contenus.',
  },
  { title: 'Contact', hint: 'comment vous joindre pour toute question juridique.' },
];

export default function MentionsLegalesPage() {
  return (
    <LegalScaffold
      title="Mentions légales"
      intro="Informations légales obligatoires identifiant l'éditeur et l'hébergeur du site."
      sections={SECTIONS}
    />
  );
}
