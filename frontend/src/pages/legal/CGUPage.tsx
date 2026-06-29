/** Conditions Générales d'Utilisation (modèle vierge à compléter). */
import LegalScaffold, { type LegalSection } from './LegalScaffold';

const SECTIONS: LegalSection[] = [
  { title: 'Objet', hint: 'ce que régissent ces CGU et le service concerné (EduTutor IA).' },
  {
    title: 'Acceptation des conditions',
    hint: "comment l'utilisateur accepte les CGU (inscription, usage…).",
  },
  { title: 'Accès au service', hint: "conditions d'accès, disponibilité, prérequis techniques." },
  {
    title: 'Compte utilisateur',
    hint: 'création, responsabilité du mot de passe, exactitude des informations.',
  },
  {
    title: 'Comportements interdits',
    hint: 'usages abusifs, contenus illicites, atteinte à la sécurité.',
  },
  {
    title: 'Contenu généré par IA',
    hint: "limites des quiz générés (peuvent contenir des erreurs), responsabilité de l'utilisateur.",
  },
  { title: 'Responsabilité', hint: "limites de responsabilité de l'éditeur." },
  {
    title: 'Propriété intellectuelle',
    hint: "droits sur le service et sur les contenus déposés par l'utilisateur.",
  },
  { title: 'Modification des CGU', hint: 'comment et quand les CGU peuvent évoluer.' },
  { title: 'Droit applicable et litiges', hint: 'droit applicable et juridiction compétente.' },
];

export default function CGUPage() {
  return (
    <LegalScaffold
      title="Conditions Générales d'Utilisation"
      intro="Les règles d'utilisation du service EduTutor IA, acceptées par chaque utilisateur."
      sections={SECTIONS}
    />
  );
}
