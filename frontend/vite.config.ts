/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Proxies API calls to the local FastAPI backend during development
    // so the browser only ever talks to one origin (this dev server).
    // That avoids needing CORS middleware on the backend, which this
    // frontend does not modify. VITE_API_BASE_URL stays empty in dev
    // (see .env.example) so the API client issues relative requests
    // that land here and get forwarded below.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
  },
})
