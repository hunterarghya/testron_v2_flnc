import { defineVitestProject } from '@nuxt/test-utils/config'
import { defineConfig } from 'vitest/config'

// Two kinds of test (testing_strategy.md §4):
// - unit: plain TypeScript (engine, utils, api client), fast, no Nuxt
// - component: Vue components mounted inside a Nuxt app
export default defineConfig({
  test: {
    passWithNoTests: true,
    projects: [
      {
        test: {
          name: 'unit',
          include: ['tests/unit/**/*.test.ts'],
          environment: 'node',
        },
      },
      await defineVitestProject({
        test: {
          name: 'component',
          include: ['tests/component/**/*.test.ts'],
          environment: 'nuxt',
        },
      }),
    ],
    coverage: {
      provider: 'v8',
      include: ['app/**/*.{ts,vue}'],
      exclude: ['app/api/schema.d.ts'],
      thresholds: {
        lines: 70,
        // Every branch of the exam engine is tested (testing_strategy.md §6)
        'app/engine/**': { branches: 100 },
      },
    },
  },
})
