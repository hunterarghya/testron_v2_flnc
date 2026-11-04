// The key screens have no serious or critical accessibility problems (build_phases.md Phase 7
// exit criteria; testing_strategy.md "a11y.spec", run here on mounted screens, ADR-085).
import { mockNuxtImport, mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { type Component, defineComponent, h } from 'vue'
import { api } from '~/api/client'
import AssignmentResults from '~/features/assignments/components/results/AssignmentResults.vue'
import LoginForm from '~/features/auth/components/LoginForm.vue'
import ExamHall from '~/features/exam-hall/components/ExamHall.vue'
import MyTests from '~/features/my-tests/components/MyTests.vue'
import PastTests from '~/features/past-tests/components/PastTests.vue'
import MyPerformance from '~/features/performance/components/MyPerformance.vue'
import { seriousViolations } from '../a11y'
import { BOOK, detail, KEYED, STATS } from '../assignment-fixtures'
import { type FakeApi, ok } from '../fake-api'
import { attempt, clockOf, NOW } from '../hall-fixtures'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})
mockNuxtImport('navigateTo', () => vi.fn())

const fake = api as unknown as FakeApi

const CARD = {
  assignment_id: 'a1', title: 'Cell Biology', question_count: 30, total_duration_s: 3000, stage_count: 1,
  timing_kind: 'TOTAL', locked: false, state: 'START', starts_at: null, closes_at: null, attempt_id: null,
}
const PERFORMANCE = {
  based_on_attempts: 1,
  chapters: [{ tag: { id: 't1', name: 'Genetics', kind: 'CHAPTER' }, score_pct: '42.0', accuracy_pct: '50.0', attempted_pct: '90.0', questions: 10 }],
  topics: [],
  trend: [{ attempt_id: 'att1', label: 'Cell Biology — 12 Nov 2026, 10:00 — Take 1', ended_at: NOW, score_pct: '42.0' }],
}
const PAST = {
  items: [{ attempt_id: 'att1', assignment_id: 'a1', label: 'Cell Biology — 12 Nov 2026, 10:00 — Take 1', state: 'PUBLISHED', at: NOW, score: '7.00', max_score: '12.00', rank: 1, rank_pool: 2 }],
  page: 1, page_size: 200, total: 1,
}

// What each screen's reads answer, by the end of the path
const ANSWERS: [string, unknown][] = [
  ['/gradebook', BOOK],
  ['/question-stats', STATS],
  ['/answer-key', KEYED],
  ['/answer-key-corrections', []],
  ['/my/tests', { available: [CARD], upcoming: [], server_now: NOW }],
  ['/my/performance', PERFORMANCE],
  ['/my/past-tests', PAST],
  ['/attempts/{attempt_id}', attempt()],
]

beforeEach(() => {
  localStorage.clear()
  fake.GET.mockReset().mockImplementation((path: string) => {
    const found = ANSWERS.find(([end]) => path.endsWith(end))
    return ok(found ? found[1] : detail({ state: 'CLOSED' }))
  })
  fake.POST.mockReset().mockImplementation(() => ok(undefined))
  fake.PUT.mockReset().mockImplementation(() => ok({ ...clockOf(attempt()), saved_at: NOW, applied: true }))
})

afterEach(() => {
  document.body.replaceChildren()
})

describe('accessibility of the key screens', () => {
  it.each<[string, Component, Record<string, unknown>, string]>([
    ['login', LoginForm, {}, 'Log in'],
    ['My Tests (P-01)', MyTests, {}, 'Cell Biology'],
    ['exam hall (P-03)', ExamHall, { attemptId: 'att1' }, 'Q 1 of 2'],
    ['gradebook (T-11)', AssignmentResults, { assignmentId: 'a1' }, 'Sneha'],
    ['Past Tests (P-08)', PastTests, {}, 'Rank 1 of 2'],
    ['My Performance (P-10)', MyPerformance, {}, 'Genetics'],
  ])('%s has no serious or critical problems', async (_name, screen, props, shown) => {
    const wrapper = await mountSuspended(screen, { props, attachTo: document.body })
    await flushPromises()

    expect(document.body.textContent).toContain(shown)
    expect(await seriousViolations(document.body)).toEqual([])
    wrapper.unmount()
  })
})

describe('the accessibility check itself', () => {
  it('catches a button with no name', async () => {
    const nameless = defineComponent({ render: () => h('button', { type: 'button' }) })
    const wrapper = await mountSuspended(nameless, { attachTo: document.body })

    expect(await seriousViolations(document.body)).toEqual([expect.stringMatching(/^button-name: /)])
    wrapper.unmount()
  })
})
