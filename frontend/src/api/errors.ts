/**
 * Extraction d'un message d'erreur lisible depuis une erreur d'appel API.
 *
 * Objectif pédagogique : ne plus masquer la cause réelle derrière un message
 * générique. Particulièrement utile pendant la semaine APOCAL'IPSSI quand les
 * équipes débuguent leur propre intégration front <-> back.
 *
 * Ordre de priorité :
 *   1. Erreur réseau / CORS (aucune réponse reçue du serveur)
 *   2. Erreurs de validation DRF par champ (username, email, password)
 *   3. non_field_errors (erreurs globales DRF)
 *   4. detail (message DRF générique, ex. 401 / 403)
 *   5. fallback fourni par l'appelant (+ code HTTP si disponible)
 */
import { AxiosError } from 'axios';

/** Normalise une valeur d'erreur DRF (string ou string[]) en string. */
function asString(value: unknown): string | undefined {
  if (typeof value === 'string') return value;
  if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'string') {
    return value[0];
  }
  return undefined;
}

export function getApiErrorMessage(err: unknown, fallback = 'Une erreur est survenue.'): string {
  if (err instanceof AxiosError) {
    // Aucune réponse = serveur injoignable ou requête bloquée (CORS, backend éteint).
    if (!err.response) {
      return (
        'Impossible de joindre le serveur. Vérifiez que le backend est démarré ' +
        "et que la configuration CORS autorise l'adresse du frontend."
      );
    }

    const data = err.response.data as Record<string, unknown> | undefined;
    if (data && typeof data === 'object') {
      const fieldError =
        asString(data.username) ??
        asString(data.email) ??
        asString(data.password) ??
        asString(data.non_field_errors) ??
        asString(data.detail);
      if (fieldError) return fieldError;
    }

    // Réponse sans corps exploitable : on expose au moins le code HTTP.
    return `${fallback} (HTTP ${err.response.status})`;
  }

  return fallback;
}
