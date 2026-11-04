import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { Gradebook, KeyedPaper, PastTest, QuestionStat, Result } from '~/api/types'
import AssignmentResults from '~/features/assignments/components/results/AssignmentResults.vue'
import MyResult from '~/features/past-tests/components/MyResult.vue'
import PastTests from '~/features/past-tests/components/PastTests.vue'
import ResultsInbox from '~/features/results/components/ResultsInbox.vue'
import TeacherDashboard from '~/features/results/components/TeacherDashboard.vue'
import { detail } from '../assignment-fixtures'
import { type FakeApi, fails, ok } from '../fake-api'
import { DOC } from '../hall-fixtures'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
const NOW = '2026-11-12T05:30:00Z'

const RESULT: Result = {
  attempt_id: 'att1', label: 'Cell Biology — 12 Nov 2026, 10:00 — Take 1', take_number: 1, ended_at: NOW,
  time_taken_s: 3000, end_reason: 'SUBMITTED', score: '7.00', max_score: '12.00',
  sections: [{ title: 'Botany', score: '4.00', max: '8.00' }, { title: 'Zoology', score: '3.00', max: '4.00' }],
  tags: [{ id: 't1', name: 'Cell', kind: 'CHAPTER', score: '4.00', max: '4.00' }],
  rank_and_stats: { rank: 1, pool: 2, mean: '4.50', highest: '7.00' },
  questions: [
    { id: 'q1', number: 1, type: 'MCQ', stem: DOC, marks: '4.00', negative_marks: '1.00',
      options: [{ id: 'o1', label: 'A', content: DOC }, { id: 'o2', label: 'B', content: DOC }],
      your_answer: { v: 1, kind: 'CHOICE', option_ids: ['o2'] }, correct_answer: { option_ids: ['o1'] },
      outcome: 'INCORRECT', marks_awarded: '-1.00', solution: DOC },
    { id: 'q2', number: 2, type: 'NUMERICAL', stem: DOC, marks: '4.00', negative_marks: '0.00', options: [],
      your_answer: { v: 1, kind: 'NUMERIC', value: '46' }, correct_answer: { value: '46.000000', tolerance: '0.000000' },
      outcome: 'CORRECT', marks_awarded: '4.00', solution: null },
  ],
}

function past(changes: Partial<PastTest>): PastTest {
  return { attempt_id: 'att1', assignment_id: 'a1', label: RESULT.label, state: 'PUBLISHED', at: NOW, score: '7.00', max_score: '12.00', rank: 1, rank_pool: 2, ...changes }
}

function button(wrapper: { element: Element }, label: string): HTMLButtonElement {
  const all = [...wrapper.element.querySelectorAll('button'), ...document.querySelectorAll('button')]
  const found = all.find(b => b.textContent?.trim() === label || b.getAttribute('aria-label') === label)
  if (!found) throw new Error(`no button ${label}`)
  return found
}

beforeEach(() => {
  for (const method of [fake.GET, fake.POST]) method.mockReset()
})

describe('student results (P-08, P-09)', () => {
  it('lists past tests with score and rank only once published', async () => {
    fake.GET.mockImplementation(() => ok({ items: [past({}), past({ attempt_id: 'att2', state: 'AWAITING_RESULTS', score: null, max_score: null, rank: null }), past({ attempt_id: null, state: 'MISSED', label: 'Plant Kingdom' })], page: 1, page_size: 200, total: 3 }))
    const wrapper = await mountSuspended(PastTests)
    await flushPromises()

    expect(wrapper.text()).toContain('7 / 12 · Rank 1 of 2')
    expect(wrapper.text()).toContain('Awaiting results')
    expect(wrapper.text()).toContain('Missed')
    expect(wrapper.findAll('a[href="/past/att1"]')).toHaveLength(1)
    wrapper.unmount()
  })

  it('shows the result with answers, and filters the wrong ones', async () => {
    fake.GET.mockImplementation(() => ok(RESULT))
    const wrapper = await mountSuspended(MyResult, { props: { attemptId: 'att1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('7 / 12')
    expect(wrapper.text()).toContain('Rank 1 of 2')
    expect(wrapper.text()).toContain('Botany 4/8')
    expect(wrapper.text()).toContain('−1 · Wrong')
    expect(wrapper.text()).toContain('Your answer 46 · correct 46.000000')
    button(wrapper, 'Wrong').click()
    await flushPromises()
    expect(wrapper.text()).not.toContain('Your answer 46')
    wrapper.unmount()
  })

  it('an unpublished result is not found', async () => {
    fake.GET.mockImplementation(() => fails(404, 'results_not_published'))
    const wrapper = await mountSuspended(MyResult, { props: { attemptId: 'att1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('couldn\'t find')
    wrapper.unmount()
  })
})

const BOOK: Gradebook = {
  title: 'Cell Biology', state: 'CLOSED', publication_state: 'UNPUBLISHED',
  rows: [
    { student_id: 's1', name: 'Mou', attempt_id: 'att1', take_number: 1, status: 'SUBMITTED', rank: 1, score: '7.00', max_score: '12.00', sections: [], time_taken_s: 3000, warning_count: 0, overridden: false },
    { student_id: 's2', name: 'Sneha', attempt_id: 'att2', take_number: 1, status: 'DISQUALIFIED', rank: null, score: '5.00', max_score: '12.00', sections: [], time_taken_s: 1800, warning_count: 3, overridden: false },
    { student_id: 's3', name: 'Rahul', attempt_id: null, take_number: null, status: 'ABSENT', rank: null, score: null, max_score: null, sections: [], time_taken_s: null, warning_count: 0, overridden: false },
  ],
  stats: { count: 1, mean: '7.00', highest: '7.00', lowest: '7.00', attempted: 2, absent: 1, disqualified: 1 },
}
const STATS: QuestionStat[] = [{ question_id: 'q1', number: 1, type: 'MCQ', answered: 2, correct: 1, partial: 0, top_wrong_option_id: 'o2', top_wrong_count: 1, tags: [] }]
const KEYED: KeyedPaper = {
  version: 1,
  paper: { sections: [{ questions: [{ id: 'q1', type: 'MCQ', stem: DOC, options: [{ id: 'o1' }, { id: 'o2' }] }] }] },
  entries: { q1: { type: 'MCQ', correct_option_ids: ['o1'] } },
  solutions: {},
}

describe('AssignmentResults (T-11)', () => {
  beforeEach(() => {
    fake.GET.mockImplementation((path: string) => {
      if (path.endsWith('/gradebook')) return ok(BOOK)
      if (path.endsWith('/question-stats')) return ok(STATS)
      if (path.endsWith('/answer-key')) return ok(KEYED)
      if (path.endsWith('/answer-key-corrections')) return ok([])
      return ok(detail({ state: 'CLOSED' }))
    })
  })

  it('lists everyone, brackets a disqualified score, and publishes with the options chosen', async () => {
    fake.POST.mockImplementation(() => ok(detail().publication))
    const wrapper = await mountSuspended(AssignmentResults, { props: { assignmentId: 'a1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('Avg 7 · High 7 · Low 7 · 2 attempted · 1 absent · 1 disq.')
    expect(wrapper.text()).toContain('(5)')
    expect(wrapper.text()).toContain('Absent')
    button(wrapper, 'Publish').click()
    await flushPromises()
    expect(document.body.textContent).toContain('Students will see:')
    const publish = [...document.querySelectorAll('button')].filter(b => b.textContent?.trim() === 'Publish').at(-1)!
    publish.click()
    await flushPromises()

    expect(fake.POST.mock.calls[0]![0]).toBe('/api/v1/admin/assignments/{assignment_id}/publish')
    wrapper.unmount()
  })
})

describe('teacher inbox and dashboard (T-13, T-01)', () => {
  it('lists closed tests to publish with their average', async () => {
    fake.GET.mockImplementation(() => ok({ items: [{ assignment_id: 'a1', title: 'Cell Biology', state: 'CLOSED', publication_state: 'UNPUBLISHED', ends_at: NOW, audience: 3, ended: 2, in_progress: 0, starts_at: null, average_pct: '58', flagged: 1 }], page: 1, page_size: 200, total: 1 }))
    const wrapper = await mountSuspended(ResultsInbox)
    await flushPromises()

    expect(wrapper.text()).toContain('Cell Biology')
    expect(wrapper.text()).toContain('58%')
    expect(wrapper.find('a[href="/admin/assignments/a1/results"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('shows what needs the teacher', async () => {
    fake.GET.mockImplementation(() => ok({ live: [], upcoming: [], recent: [], pending_students: 2, results_to_publish: 1 }))
    const wrapper = await mountSuspended(TeacherDashboard)
    await flushPromises()

    expect(wrapper.text()).toContain('No test running.')
    expect(wrapper.text()).toContain('2 student(s) waiting for approval')
    expect(wrapper.text()).toContain('1 result(s) ready to publish')
    wrapper.unmount()
  })
})
