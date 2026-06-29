// ESLint 9 — configuration "flat" (remplace l'ancien .eslintrc.cjs).
// Utilise les paquets installés : @typescript-eslint, react-hooks, react-refresh.
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';

export default [
  // Fichiers/dossiers à ne pas analyser.
  { ignores: ['dist/**', 'coverage/**', 'node_modules/**', '*.config.js', '*.config.ts'] },

  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      ecmaVersion: 2022,
      sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      // Désactivé : règle de confort HMR (les contextes exportent hooks + providers).
      'react-refresh/only-export-components': 'off',
    },
  },
];
