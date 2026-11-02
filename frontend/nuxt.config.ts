// The SPA is built to static files and served by Django from the same origin as the API
// (frontend_spec.md §1, ADR-004).
export default defineNuxtConfig({
  compatibilityDate: '2026-11-01',
  ssr: false,
  devtools: { enabled: false },
  modules: ['@nuxt/ui', '@nuxt/eslint', '@nuxt/test-utils/module'],
  css: ['~/assets/css/main.css'],

  app: {
    head: {
      htmlAttrs: { lang: 'en' },
      title: 'Test Platform',
    },
  },

  ui: {
    // Fonts are self-hosted (ADR-034): no request to a font CDN, which the CSP forbids
    fonts: false,
    // Light only: dark mode is out of scope (frontend_spec.md §2)
    colorMode: false,
  },

  icon: {
    // Icons are bundled into the build; nothing is fetched from an icon API at runtime
    provider: 'none',
    clientBundle: { scan: true },
  },

  typescript: {
    strict: true,
  },

  eslint: {
    config: { stylistic: false },
  },

  nitro: {
    // `just dev`: the browser talks only to :3000 and /api goes to Django on :8000,
    // so cookies and CSRF behave as in production (dev_environment_and_deployment.md §1.3)
    devProxy: {
      '/api': { target: 'http://127.0.0.1:8000/api', changeOrigin: false },
    },
  },
})
