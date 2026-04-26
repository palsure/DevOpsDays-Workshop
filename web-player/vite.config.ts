import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

const apiProxy = {
  '/api': {
    target: 'http://localhost:8080',
    changeOrigin: true,
  },
} as const;

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: apiProxy,
  },
  preview: {
    proxy: apiProxy,
  },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
    reporters: ['default', ['junit', { outputFile: 'test-results/vitest-junit.xml' }]],
  },
});
