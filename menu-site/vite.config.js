import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5174 },
  build: {
    rollupOptions: {
      // La carta (/), la página de links que reemplaza al Linktree (/links) y Mis cafecitos (/cafecitos)
      input: {
        main: resolve(__dirname, 'index.html'),
        links: resolve(__dirname, 'links.html'),
        cafecitos: resolve(__dirname, 'cafecitos.html'),
      },
    },
  },
  test: { environment: 'node' },
})
