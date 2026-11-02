// @ts-check
// Lint rules that CI enforces for the frontend (project_structure.md §1.4, §4.2).
import boundaries from 'eslint-plugin-boundaries'
import withNuxt from './.nuxt/eslint.config.mjs'

const NO_FETCH = 'Network calls go through app/api/client.ts (project_structure.md §4.2)'
const NO_INLINE_CSS = 'No inline CSS: use Nuxt UI props, the theme and Tailwind classes (Y-10)'

// Which folder may import which (project_structure.md §4.2). Anything not listed is refused.
const layerPolicies = [
  { from: 'pages', allow: ['feature', 'shared'] },
  { from: 'layouts', allow: ['shared'] },
  { from: 'app', allow: ['shared', 'api'] },
  // The keyboards and keypad components draw keys; engine/keyboards.ts decides what they do
  { from: 'shared', allow: ['shared', 'api', 'engine'] },
  { from: 'engine', allow: ['engine'] },
  { from: 'stores', allow: ['engine', 'api'] },
  { from: 'api', allow: ['api'] },
  { from: 'feature', allow: ['shared', 'engine', 'api', 'stores'] },
].map(({ from, allow }) => ({
  from: { element: { type: from } },
  allow: { to: { element: { types: { anyOf: allow } } } },
}))

// A feature may import its own files, never another feature's
const sameFeaturePolicy = {
  from: { element: { type: 'feature' } },
  allow: {
    to: { element: { type: 'feature', captured: { feature: '{{ from.element.captured.feature }}' } } },
  },
}

const NO_RAW_HTML = 'No raw HTML from data (CLAUDE.md rule 5); the one exception is renderMath.ts'

export default withNuxt(
  {
    rules: {
      'vue/no-v-html': 'error',
      'vue/no-static-inline-styles': ['error', { allowBinding: false }],
      'vue/no-restricted-v-bind': ['error', { argument: 'style', message: NO_INLINE_CSS }],
      '@typescript-eslint/no-explicit-any': 'error',
      'no-restricted-globals': [
        'error',
        { name: 'fetch', message: NO_FETCH },
        { name: '$fetch', message: NO_FETCH },
      ],
      'no-restricted-properties': [
        'error',
        { property: 'innerHTML', message: NO_RAW_HTML },
        { property: 'outerHTML', message: NO_RAW_HTML },
      ],
    },
  },
  {
    // KaTeX output (editor_content_spec.md §6) and reading back pasted HTML already cleaned
    files: ['app/shared/components/rich-content/renderMath.ts', 'app/shared/components/rich-content/paste.ts'],
    rules: { 'no-restricted-properties': 'off' },
  },
  {
    // The API client, and the browser export builders that load fonts and images (ADR-019)
    files: ['app/api/**', 'app/features/exports/**'],
    rules: { 'no-restricted-globals': 'off' },
  },
  {
    files: ['app/**/*.{ts,vue}'],
    plugins: { boundaries },
    settings: {
      // Resolves Nuxt's `~/` alias to real files, so imports can be classified
      'import/resolver': { typescript: { project: './.nuxt/tsconfig.app.json' } },
      'boundaries/elements': [
        { type: 'pages', pattern: 'app/pages' },
        { type: 'layouts', pattern: 'app/layouts' },
        { type: 'feature', pattern: 'app/features/*', capture: ['feature'] },
        { type: 'shared', pattern: 'app/shared' },
        { type: 'engine', pattern: 'app/engine' },
        { type: 'stores', pattern: 'app/stores' },
        { type: 'api', pattern: 'app/api' },
        { type: 'app', pattern: 'app/{middleware,plugins}' },
      ],
    },
    rules: {
      'boundaries/dependencies': ['error', {
        default: 'disallow',
        policies: [...layerPolicies, sameFeaturePolicy],
      }],
    },
  },
  {
    // The exam engine is plain TypeScript, portable and testable without Vue or Nuxt
    files: ['app/engine/**'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [{
          group: ['vue', 'vue/*', 'nuxt', 'nuxt/*', '#app', '#imports', 'pinia', '@nuxt/*'],
          message: 'app/engine is framework-free (frontend_spec.md §5)',
        }],
      }],
    },
  },
)
