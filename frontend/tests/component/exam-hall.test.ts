import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { AttemptState } from '~/api/types'
import ExamHall from '~/features/exam-hall/components/ExamHall.vue'
import { type FakeApi, fails, ok } from '../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
const NOW = new Date().toISOString()
const LATER = new Date(Date.now() + 3_600_000).toISOString()
const DOC = { v: 1, type: 'doc', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Which organelle?' }] }] }

function attempt(changes: Partial<AttemptState> = {}): AttemptState {
  return {
    status: 'IN_PROGRESS', end_reason: null, ended_at: null, server_now: NOW, attempt_deadline: LATER,
    current_stage_index: 0, stages: [{ index: 0, state: 'OPEN', deadline_at: LATER }], warning_count: 0, notice: null,
    attempt_id: 'att1', assignment_id: 'a1', title: 'Cell Biology', take_number: 1, exam_client_id: 'dev1',
    timing: { kind: 'TOTAL', allow_return: false }, integrity: { grace_s: 5, max_warnings: 3, action: 'AUTO_SUBMIT' },
    stage_meta: [{ index: 0, kind: 'WHOLE', title: null, instructions: null, duration_s: 3600, question_ids: ['q1', 'q2'] }],
    questions: [
      { id: 'q1', number: 1, type: 'MCQ', stem: DOC, marks: '4.00', negative_marks: '1.00', time_s: null,
        options: [{ id: 'o1', label: 'A', content: DOC }, { id: 'o2', label: 'B', content: DOC }] },
      { id: 'q2', number: 2, type: 'NUMERICAL', stem: DOC, marks: '4.00', negative_marks: '0.00', time_s: null, options: [] },
    ],
    responses: {},
    ...changes,
  } as AttemptState
}

function clockOf(state: AttemptState) {
  const { status, end_reason, ended_at, server_now, attempt_deadline, current_stage_index, stages, warning_count, notice } = state
  return { status, end_reason, ended_at, server_now, attempt_deadline, current_stage_index, stages, warning_count, notice }
}

async function mountHall() {
  const wrapper = await mountSuspended(ExamHall, { props: { attemptId: 'att1' } })
  await flushPromises()
  return wrapper
}

function button(wrapper: Awaited<ReturnType<typeof mountHall>>, label: string) {
  return wrapper.findAll('button').find(b => b.text() === label)!
}

beforeEach(() => {
  localStorage.clear()
  for (const method of [fake.GET, fake.PUT, fake.POST]) method.mockReset()
  fake.GET.mockImplementation(() => ok(attempt()))
  fake.POST.mockImplementation(() => ok(undefined))
})

describe('ExamHall (P-03)', () => {
  it('shows the first question, the timer and the palette, and marks it seen', async () => {
    const wrapper = await mountHall()

    expect(wrapper.text()).toContain('Cell Biology – Take 1')
    expect(wrapper.text()).toContain('Q 1 of 2')
    expect(wrapper.text()).toContain('+4 / −1')
    expect(wrapper.find('[role="timer"]').text()).toMatch(/^(01:00:00|00:59:\d\d)$/)
    expect(fake.POST).toHaveBeenCalledWith('/api/v1/attempts/{attempt_id}/questions/{question_id}/visit', expect.anything())
    expect(localStorage.getItem('exam:att1:client')).toBe('dev1')
    wrapper.unmount()
  })

  it('saves a choice at once with this device\'s id', async () => {
    fake.PUT.mockImplementation(() => ok({ ...clockOf(attempt()), saved_at: NOW, applied: true }))
    const wrapper = await mountHall()

    await wrapper.find('input[type="radio"][value="o2"], [role="radio"][value="o2"], button[value="o2"]').trigger('click')
    await flushPromises()

    const [path, init] = fake.PUT.mock.calls[0]!
    expect(path).toBe('/api/v1/attempts/{attempt_id}/responses/{question_id}')
    expect(init).toMatchObject({
      headers: { 'X-Exam-Client': 'dev1' },
      body: { answer: { v: 1, kind: 'CHOICE', option_ids: ['o2'] }, marked_for_review: false, client_seq: 1 },
    })
    expect(wrapper.text()).toContain('Saved')
    wrapper.unmount()
  })

  it('keeps the answer on the device while offline', async () => {
    fake.PUT.mockImplementation(() => fails(0, 'network_error'))
    const wrapper = await mountHall()

    await button(wrapper, 'Mark for review').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Offline, 1 answer waiting')
    expect(JSON.parse(localStorage.getItem('exam:att1:queue')!).pending.q1.marked_for_review).toBe(true)
    wrapper.unmount()
  })

  it('submits after review and shows the ending without a score', async () => {
    fake.POST.mockImplementation((path: string) => (path.endsWith('/submit')
      ? ok({ status: 'ENDED', end_reason: 'SUBMITTED', ended_at: NOW, result_available: false })
      : ok(undefined)))
    const wrapper = await mountHall()

    await button(wrapper, 'Submit').trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('Submit test?')
    expect(document.body.textContent).toContain('Not answered')
    const confirm = [...document.querySelectorAll('button')].filter(b => b.textContent?.trim() === 'Submit').at(-1)!
    confirm.click()
    await flushPromises()

    expect(wrapper.text()).toContain('Submitted')
    expect(wrapper.text()).toContain('Results will be published by your teacher.')
    expect(localStorage.getItem('exam:att1:client')).toBeNull()
    wrapper.unmount()
  })

  it('shows how an attempt already over ended', async () => {
    fake.GET.mockImplementation(() => ok(attempt({ status: 'ENDED', end_reason: 'TIMED_OUT', ended_at: NOW, questions: [] })))
    const wrapper = await mountHall()

    expect(wrapper.text()).toContain('Time\'s up — submitted')
    wrapper.unmount()
  })

  it('stops when another device takes the test over', async () => {
    fake.PUT.mockImplementation(() => fails(409, 'attempt_taken_over'))
    const wrapper = await mountHall()

    await button(wrapper, 'Mark for review').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('This test was opened on another device')
    expect(localStorage.getItem('exam:att1:queue')).toBeNull()
    wrapper.unmount()
  })

  it('types a number with the keypad, keeping to the rules', async () => {
    const wrapper = await mountHall()
    await button(wrapper, 'Next').trigger('click')
    await flushPromises()

    for (const key of ['Minus', '1', 'Point', '5']) {
      await wrapper.find(`button[aria-label="${key}"]`).trigger('click')
    }
    await flushPromises()

    expect((wrapper.find('input[inputmode="none"]').element as HTMLInputElement).value).toBe('-1.5')
    wrapper.unmount()
  })
})
