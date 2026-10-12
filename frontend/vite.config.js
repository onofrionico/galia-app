import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    // Service worker solo para el Camarero (scope /camarero): el resto de Galia no queda cacheado.
    // El manifest es public/site.webmanifest (lo enlaza index.html); la API nunca se cachea.
    VitePWA({
      registerType: 'prompt',
      injectRegister: false,
      manifest: false,
      scope: '/camarero',
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],
        globIgnores: ['uploads/**'],
        navigateFallback: '/index.html',
        navigateFallbackAllowlist: [/^\/camarero/],
        navigateFallbackDenylist: [/^\/api/],
        runtimeCaching: [],
      },
      devOptions: { enabled: false },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.js'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
})
