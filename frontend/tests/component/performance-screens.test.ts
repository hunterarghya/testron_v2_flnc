import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { Performance, SessionUser, StudentRow } from '~/api/types'
import MyPerformance from '~/features/performance/components/MyPerformance.vue'
import ShareDialog from '~/features/students/components/ShareDialog.vue'
import StudentLayout from '~/layouts/student.vue'
import { useSession } from '~/shared/composables/useSession'
import { type FakeApi, fails, ok } from '../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi

const tag = (id: string, name: string, kind: string) => ({ id, name, kind })
const REPORT: Performance = {
  based_on_attempts: 2,
  chapters: [
    { tag: tag('t1', 'Genetics', 'CHAPTER'), score_pct: '-25.0', accuracy_pct: '0.0', attempted_pct: '100.0', questions: 2 },
    { tag: tag('t2', 'Cell', 'CHAPTER'), score_pct: '81.0', accuracy_pct: '90.0', attempted_pct: '95.0', questions: 20 },
  ],
  topics: [{ tag: tag('t3', 'Mitochondria', 'TOPIC'), score_pct: '50.0', accuracy_pct: '50.0', attempted_pct: '100.0', questions: 4 }],
  trend: [
    { attempt_id: 'a1', label: 'Cell Biology — 12 Nov 2026, 10:00 — Take 1', ended_at: '2026-11-12T05:00:00Z', score_pct: '40.0' },
    { attempt_id: 'a2', label: 'Genetics — 19 Nov 2026, 10:00 — Take 1', ended_at: '2026-11-19T05:00:00Z', score_pct: '62.5' },
  ],
}

describe('P-10 My Performance', () => {
  beforeEach(() => fake.GET.mockReset())

  it('lists chapters weakest first, with the trend for screen readers too', async () => {
    fake.GET.mockImplementation(() => ok(REPORT))
    const wrapper = await mountSuspended(MyPerformance)
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('Based on 2 published tests')
    expect(text.indexOf('Genetics')).toBeLessThan(text.indexOf('Cell'))
    expect(text).toContain('-25.0%')
    expect(text).toContain('Accuracy 90.0% · Answered 95.0% · 20 questions')
    expect(wrapper.find('ul.sr-only').text()).toContain('Genetics — 19 Nov 2026, 10:00 — Take 1: 62.5%')
  })

  it('says nothing is published yet, and shows Not found when not shared', async () => {
    fake.GET.mockImplementationOnce(() => ok({ ...REPORT, based_on_attempts: 0, chapters: [], topics: [], trend: [] }))
    const empty = await mountSuspended(MyPerformance)
    await flushPromises()
    expect(empty.text()).toContain('Nothing to show yet.')

    fake.GET.mockImplementationOnce(() => fails(404, 'performance_not_shared'))
    const hidden = await mountSuspended(MyPerformance)
    await flushPromises()
    expect(hidden.text()).toContain('couldn\'t find this')
  })
})

describe('the student menu', () => {
  it('shows Performance only while it is shared [I-3]', async () => {
    const session = useSession()
    const me = { role: 'STUDENT', status: 'ACTIVE', performance_shared: false } as SessionUser
    session.set(me)
    const hidden = await mountSuspended(StudentLayout)
    expect(hidden.find('a[href="/performance"]').exists()).toBe(false)

    session.set({ ...me, performance_shared: true })
    const shown = await mountSuspended(StudentLayout)
    expect(shown.find('a[href="/performance"]').exists()).toBe(true)
    session.set(null)
  })
})

function student(id: string, name: string, shared: boolean): StudentRow {
  return {
    id, name, email: `${id}@x.in`, status: 'ACTIVE', joined_at: '2026-11-01T10:00:00Z', requested_at: null,
    decided_at: null, deactivated_at: null, performance_shared: shared, group_names: [],
  }
}

describe('D-06 Share performance', () => {
  it('saves only the switches that moved', async () => {
    const wrapper = await mountSuspended(ShareDialog, {
      props: { open: false, students: [student('a', 'Aditi', false), student('t', 'Tapas', true)], groups: [], pending: false },
    })
    await wrapper.setProps({ open: true })
    await flushPromises()

    const switches = [...document.querySelectorAll('[role="switch"]')] as HTMLElement[]
    expect(switches.map(s => s.getAttribute('aria-checked'))).toEqual(['false', 'true'])
    switches[0]!.click()
    switches[1]!.click()
    await flushPromises()
    const save = [...document.querySelectorAll('button')].find(b => b.textContent?.trim() === 'Save')!
    save.click()

    expect(wrapper.emitted('save')).toEqual([[{ kind: 'students', on: ['a'], off: ['t'] }]])
    wrapper.unmount()
  })
})
