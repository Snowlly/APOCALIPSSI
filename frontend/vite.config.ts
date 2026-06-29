import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// Config Vite (build + dev). La config des tests vit dans vitest.config.ts.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // accessible depuis l'hôte (utile en Docker)
    port: 3000,
    strictPort: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
