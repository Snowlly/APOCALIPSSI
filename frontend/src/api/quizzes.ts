import { api } from './client';

export type Question = {
  index: number;
  prompt: string;
  options: string[];
  correct_index: number;
};

export type Quiz = {
  id: number;
  title: string;
  source_text: string;
  score: number | null;
  created_at: string;
  questions: Question[];
};

export type QuizSummary = {
  id: number;
  title: string;
  score: number | null;
  nb_questions: number;
  created_at: string;
};

type PaginatedQuizzes = {
  count: number;
  next: string | null;
  previous: string | null;
  results: QuizSummary[];
};

export type AnswerDetail = {
  index: number;
  selected_index: number;
  correct_index: number;
  correct: boolean;
};

export type AnswerResult = {
  score: number;
  total: number;
  details: AnswerDetail[];
};

export async function listQuizzes(): Promise<PaginatedQuizzes> {
  const { data } = await api.get<PaginatedQuizzes>('/quizzes/');
  return data;
}

export async function getQuiz(id: number): Promise<Quiz> {
  const { data } = await api.get<Quiz>(`/quizzes/${id}/`);
  return data;
}

export async function submitAnswers(
  quizId: number,
  answers: { index: number; selected_index: number }[],
): Promise<AnswerResult> {
  const { data } = await api.post<AnswerResult>(`/quizzes/${quizId}/answer/`, { answers });
  return data;
}

// ---------------------------------------------------------------------------
// MVP2 (Lot 6) — Dashboard de progression & Révision des erreurs
// ---------------------------------------------------------------------------

export type ScorePoint = {
  id: number;
  title: string;
  score: number;
  created_at: string;
};

export type Stats = {
  total_quizzes: number;
  quizzes_taken: number;
  average_score: number | null;
  best_score: number | null;
  last_score: number | null;
  questions_answered: number;
  questions_correct: number;
  accuracy: number | null;
  history: ScorePoint[];
};

export type Mistake = {
  quiz_id: number;
  quiz_title: string;
  index: number;
  prompt: string;
  options: string[];
  correct_index: number;
  selected_index: number;
};

/** Statistiques de progression de l'utilisateur connecté. */
export async function getStats(): Promise<Stats> {
  const { data } = await api.get<Stats>('/quizzes/stats/');
  return data;
}

/** Liste des questions ratées (pour la révision des erreurs). */
export async function getMistakes(): Promise<{ count: number; mistakes: Mistake[] }> {
  const { data } = await api.get<{ count: number; mistakes: Mistake[] }>('/quizzes/mistakes/');
  return data;
}
