import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config';

// Config des tests : on réutilise la config Vite (alias @, plugins) et on ajoute
// le bloc `test`. Séparée de vite.config.ts pour garder le build TypeScript propre.
export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
    },
  }),
);
