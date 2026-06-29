import { describe, it, expect } from 'vitest';
import { AxiosError } from 'axios';
import { getApiErrorMessage } from './errors';

describe('getApiErrorMessage', () => {
  it('renvoie le message de repli pour une erreur non-Axios', () => {
    expect(getApiErrorMessage(new Error('boom'), 'Oups')).toBe('Oups');
    expect(getApiErrorMessage('pas une erreur', 'Oups')).toBe('Oups');
  });

  it('signale un serveur injoignable quand aucune réponse n’est reçue', () => {
    const err = new AxiosError('Network Error');
    expect(getApiErrorMessage(err, 'fallback')).toContain('joindre le serveur');
  });
});
