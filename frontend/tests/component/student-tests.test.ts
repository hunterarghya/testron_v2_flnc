import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { GateState, MyTestCard } from '~/api/types'
import MyTests from '~/features/my-tests/components/MyTests.vue'
import TestGate from '~/features/my-tests/components/TestGate.vue'
import { lateJoinMessage, markingLine, ruleBullets, stagesLine } from '~/features/my-tests/utils/gate-text'
import { type FakeApi, ok } from '../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
const NOW = '2026-11-12T05:00:00Z'

function card(changes: Partial<MyTestCard>): MyTestCard {
  return {
    assignment_id: 'a1', title: 'Cell Biology', question_count: 30, total_duration_s: 3000, stage_count: 3,
    timing_kind: 'SECTIONED', locked: true, state: 'JOIN', starts_at: null, closes_at: null, attempt_id: null, ...changes,
  }
}

function gate(changes: Partial<GateState> = {}): GateState {
  return {
    assignment_id: 'a1',
    title: 'Cell Biology – Take 1',
    rules: {
      question_count: 30, total_marks: '120.00', total_duration_s: 3000, timing_kind: 'SECTIONED',
      stages: [{ title: 'Botany', duration_s: 1200 }, { title: 'Zoology', duration_s: 1800 }],
      marking: { marks: '4.00', negative_marks: '1.00' }, allow_return: false, max_warnings: 3, action: 'AUTO_SUBMIT',
    },
    state: 'WAITING_FOR_TEACHER',
    requires_password: true,
    opens_at: null,
    late_entry_until: null,
    time_remaining_if_started_now_s: null,
    attempt_id: null,
    next_take_number: 1,
    server_now: NOW,
    ...changes,
  }
}

async function readRules(wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> }, findAll: (s: string) => { text: () => string, trigger: (e: string) => Promise<void> }[] }) {
  await wrapper.find('[role="checkbox"]').trigger('click')
  await wrapper.findAll('button').find(b => b.text() === 'Continue')!.trigger('click')
}

describe('MyTests (P-01)', () => {
  it('shows available cards with their button and the upcoming list', async () => {
    fake.GET.mockReset().mockImplementation(() => ok({
      available: [card({}), card({ assignment_id: 'a2', title: 'Respiration', state: 'START', locked: false, timing_kind: 'TOTAL', stage_count: 1 })],
      upcoming: [card({ assignment_id: 'a3', title: 'Plant Kingdom', state: 'STARTS_IN', starts_at: '2026-11-14T04:30:00Z' })],
      server_now: NOW,
    }))
    const wrapper = await mountSuspended(MyTests)
    await flushPromises()

    expect(wrapper.text()).toContain('30 questions · 50 min · 3 sections')
    expect(wrapper.text()).toContain('Waiting for teacher to start')
    expect(wrapper.find('a[href="/tests/a1"]').text()).toContain('Join')
    expect(wrapper.find('a[href="/tests/a2"]').text()).toContain('Start')
    expect(wrapper.text()).toContain('Plant Kingdom')
    expect(wrapper.text()).toContain('in 2 days')
    wrapper.unmount()
  })

  it('has a friendly empty state', async () => {
    fake.GET.mockReset().mockImplementation(() => ok({ available: [], upcoming: [], server_now: NOW }))
    const wrapper = await mountSuspended(MyTests)
    await flushPromises()

    expect(wrapper.text()).toContain('No tests right now.')
    wrapper.unmount()
  })
})

describe('TestGate (P-02)', () => {
  beforeEach(() => {
    fake.GET.mockReset()
  })

  it('shows the rules first, then waits for the teacher', async () => {
    fake.GET.mockImplementation(() => ok(gate()))
    const wrapper = await mountSuspended(TestGate, { props: { assignmentId: 'a1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('Sections: Botany 20 min · Zoology 30 min')
    await readRules(wrapper)
    expect(wrapper.text()).toContain('Waiting for your teacher to start the test')
    wrapper.unmount()
  })

  it('asks for the password once ready, and tells a late joiner their time', async () => {
    fake.GET.mockImplementation(() => ok(gate({ state: 'READY', time_remaining_if_started_now_s: 2640, late_entry_until: '2026-11-12T05:10:00Z' })))
    const wrapper = await mountSuspended(TestGate, { props: { assignmentId: 'a1' } })
    await flushPromises()
    await readRules(wrapper)

    expect(wrapper.text()).toContain('Enter the password from your teacher')
    expect(wrapper.text()).toContain('You have 44 min. Entry closes at 10:40.')
    wrapper.unmount()
  })

  it('counts down to a scheduled start in server time', async () => {
    fake.GET.mockImplementation(() => ok(gate({ state: 'NOT_OPEN', opens_at: '2026-11-12T05:02:41Z', server_now: new Date().toISOString() })))
    const wrapper = await mountSuspended(TestGate, { props: { assignmentId: 'a1' } })
    await flushPromises()
    await readRules(wrapper)

    expect(wrapper.text()).toContain('Starts in')
    wrapper.unmount()
  })
})

describe('gate text', () => {
  it('describes marking, stages and the rules', () => {
    const rules = gate().rules
    expect(markingLine(rules)).toBe('Marking: +4 / −1')
    expect(markingLine({ ...rules, marking: 'MIXED' })).toBe('Marking: shown with each question')
    expect(stagesLine({ ...rules, timing_kind: 'TOTAL' })).toBeNull()
    expect(ruleBullets({ ...rules, action: 'DISQUALIFY' })[1]).toContain('3 warnings → disqualification')
    expect(ruleBullets({ ...rules, timing_kind: 'PER_QUESTION' })[2]).toContain('own timer')
  })

  it('says nothing to an on-time student', () => {
    expect(lateJoinMessage(gate({ state: 'READY', time_remaining_if_started_now_s: 3000 }))).toBeNull()
    expect(lateJoinMessage(gate({ state: 'READY', time_remaining_if_started_now_s: 600 }))).toBe('The test has already started. You have 10 min.')
  })
})
