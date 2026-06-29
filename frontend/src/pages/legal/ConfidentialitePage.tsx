/** Politique de confidentialité (modèle vierge à compléter). */
import LegalScaffold, { type LegalSection } from './LegalScaffold';

const SECTIONS: LegalSection[] = [
  {
    title: 'Responsable du traitement',
    hint: 'qui décide pourquoi et comment les données sont traitées.',
  },
  {
    title: 'Données personnelles collectées',
    hint: 'email, nom, prénom, documents envoyés, historique de quiz…',
  },
  {
    title: 'Finalités du traitement',
    hint: 'pourquoi vous collectez ces données (créer un compte, générer des quiz…).',
  },
  { title: 'Base légale', hint: 'consentement, contrat, intérêt légitime… (RGPD art. 6).' },
  {
    title: 'Durée de conservation',
    hint: 'combien de temps les données sont gardées, puis supprimées/anonymisées.',
  },
  {
    title: 'Destinataires des données',
    hint: 'qui y a accès (équipe, sous-traitants, fournisseurs LLM…).',
  },
  {
    title: 'Transferts hors UE',
    hint: 'si un fournisseur cloud héberge les données hors Union européenne.',
  },
  {
    title: 'Vos droits',
    hint: 'accès, rectification, suppression, portabilité, opposition, et comment les exercer.',
  },
  { title: 'Cookies', hint: 'renvoi vers la politique de cookies du site.' },
  {
    title: 'Contact & réclamation',
    hint: 'email du référent données + droit de réclamation auprès de la CNIL.',
  },
];

export default function ConfidentialitePage() {
  return (
    <LegalScaffold
      title="Politique de confidentialité"
      intro="Comment les données personnelles des utilisateurs sont collectées, utilisées et protégées (RGPD)."
      sections={SECTIONS}
    />
  );
}
