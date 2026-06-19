// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: ['@vite-pwa/nuxt'],
  pwa: {
    registerType: 'autoUpdate',
    manifest: {
      name: 'Kopiko',
      short_name: 'Kopiko',
      theme_color: '#ffffff',
      // icons: [
      //   {
      //     src: 'pwa-192x192.png',
      //     sizes: '192x192',
      //     type: 'image/png'
      //   },
      //   {
      //     src: 'pwa-512x512.png',
      //     sizes: '512x512',
      //     type: 'image/png'
      //   }
      // ]
    },
    workbox: {
      navigateFallback: '/',
      globPatterns: ['**/*.{js,css,html,png,svg,ico}']
    }
  },
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      apiBase: 'http://127.0.0.1:4001',
    },
  },
  devServer: {
    port: 4000,
  },
  app: {
    head: {
      title: 'Kopiko - Voice Advisory',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover' },
        { name: 'theme-color', content: '#FAF7F2' },
        { name: 'description', content: 'Voice-first guided conversation farm advisory powered by Web Speech APIs' }
      ]
    }
  }
})
