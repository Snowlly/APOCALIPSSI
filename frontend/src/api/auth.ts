/**
 * Appels API liés à l'authentification (Lot 3 : identifiant = EMAIL).
 *
 * [Note pédagogique] L'inscription et la connexion se font désormais par EMAIL
 * (et non plus par un "nom d'utilisateur"). Le backend stocke username = email
 * en interne, mais le front n'a plus à connaître cette astuce : il manipule
 * uniquement l'email.
 */
import { api, setToken, clearToken } from './client';

export type User = {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  /** L'utilisateur a-t-il confirmé son adresse email (lien reçu par mail) ? */
  email_verified?: boolean;
  /** Compte administrateur (accès à la page /admin) ? */
  is_staff?: boolean;
};

type LoginResponse = { token: string; user: User };

/** Connexion par email + mot de passe. Stocke le token et renvoie l'utilisateur. */
export async function login(email: string, password: string): Promise<User> {
  const { data } = await api.post<LoginResponse>('/accounts/login/', { email, password });
  setToken(data.token);
  return data.user;
}

/** Inscription par email. Connecte automatiquement l'utilisateur ensuite. */
export async function signup(input: {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}): Promise<User> {
  const { data } = await api.post<User>('/accounts/signup/', input);
  // Auto-login après signup (réutilise email + mot de passe).
  await login(input.email, input.password);
  return data;
}

export async function logout(): Promise<void> {
  try {
    await api.post('/accounts/logout/');
  } finally {
    clearToken();
  }
}

export async function me(): Promise<User> {
  const { data } = await api.get<User>('/accounts/me/');
  return data;
}

// ---------------------------------------------------------------------------
// Validation d'email
// ---------------------------------------------------------------------------

/** Confirme l'adresse email à partir du token reçu par email. */
export async function verifyEmail(token: string): Promise<string> {
  const { data } = await api.post<{ detail: string }>('/accounts/verify-email/', { token });
  return data.detail;
}

/** Renvoie l'email de validation à l'utilisateur connecté. */
export async function resendVerification(): Promise<string> {
  const { data } = await api.post<{ detail: string }>('/accounts/resend-verification/');
  return data.detail;
}

// ---------------------------------------------------------------------------
// Mot de passe oublié
// ---------------------------------------------------------------------------

/** Demande un lien de réinitialisation (réponse identique que le compte existe ou non). */
export async function requestPasswordReset(email: string): Promise<string> {
  const { data } = await api.post<{ detail: string }>('/accounts/password-reset/', { email });
  return data.detail;
}

/** Définit le nouveau mot de passe à partir du lien (uid + token). */
export async function confirmPasswordReset(
  uid: string,
  token: string,
  new_password: string,
): Promise<string> {
  const { data } = await api.post<{ detail: string }>('/accounts/password-reset/confirm/', {
    uid,
    token,
    new_password,
  });
  return data.detail;
}

// ---------------------------------------------------------------------------
// Profil (Lot 4) : modifier ses infos, son mot de passe, supprimer son compte
// ---------------------------------------------------------------------------

/** Modifie le profil (prénom / nom / email). Renvoie l'utilisateur à jour. */
export async function updateProfile(input: {
  first_name?: string;
  last_name?: string;
  email?: string;
}): Promise<User> {
  const { data } = await api.patch<User>('/accounts/profile/', input);
  return data;
}

/** Change le mot de passe (ancien requis). Le backend renvoie un nouveau token. */
export async function changePassword(old_password: string, new_password: string): Promise<string> {
  const { data } = await api.post<{ detail: string; token: string }>('/accounts/change-password/', {
    old_password,
    new_password,
  });
  // Le mot de passe a changé -> on remplace le token stocké par le nouveau.
  setToken(data.token);
  return data.detail;
}

/** Supprime définitivement le compte (confirmé par le mot de passe). */
export async function deleteAccount(password: string): Promise<void> {
  // axios : le corps d'une requête DELETE se passe via la clé `data`.
  await api.delete('/accounts/profile/', { data: { password } });
  clearToken();
}
