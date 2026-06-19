// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
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
