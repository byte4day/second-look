import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'manifest.webmanifest'],
      manifest: {
        name: 'Scam Shield',
        short_name: 'Scam Shield',
        description: 'Plain help to spot scams and practise what to say.',
        display: 'standalone',
        start_url: '/',
        background_color: '#FAF7F0',
        theme_color: '#0B4F9C',
        icons: [
          {
            src: '/favicon.svg',
            sizes: 'any',
            type: 'image/svg+xml',
            purpose: 'any',
          },
        ],
      },
      workbox: {
        navigateFallback: '/index.html',
        runtimeCaching: [
          {
            urlPattern: /\/api\/content\/help-now/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'help-now',
              networkTimeoutSeconds: 3,
              expiration: { maxEntries: 4, maxAgeSeconds: 60 * 60 * 24 * 7 },
            },
          },
        ],
      },
    }),
  ],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    typecheck: {
      tsconfig: './tsconfig.vitest.json',
    },
  },
})