import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import ExamHall from '~/features/exam-hall/components/ExamHall.vue'
import { type FakeApi, fails, ok } from '../fake-api'
import { attempt, clockOf, NOW } from '../hall-fixtures'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
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
  // A save still due (typing waits 500 ms) may land after a test: answer it like the server
  fake.PUT.mockImplementation(() => ok({ ...clockOf(attempt()), saved_at: NOW, applied: true }))
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

describe('leaving the test (P-06)', () => {
  it('reports a departure past the grace period and shows the server\'s warning', async () => {
    fake.GET.mockImplementation(() => ok(attempt({ integrity: { grace_s: 0, max_warnings: 3, action: 'AUTO_SUBMIT' } })))
    fake.PUT.mockImplementation(() => ok({ ...clockOf(attempt()), warning_count: 1, counted: true, max_warnings: 3, action: 'WARN' }))
    const wrapper = await mountHall()
    const hidden = Object.getOwnPropertyDescriptor(Document.prototype, 'hidden')
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => true })

    document.dispatchEvent(new Event('visibilitychange'))
    await flushPromises()
    await new Promise(resolve => setTimeout(resolve, 10))
    await flushPromises()

    const reports = fake.PUT.mock.calls.filter(([path]) => path.includes('integrity-events'))
    expect(reports.map(([, init]) => (init as { body: { kind: string, beyond_grace: boolean } }).body))
      .toEqual([expect.objectContaining({ kind: 'TAB_HIDDEN', beyond_grace: false }), expect.objectContaining({ kind: 'TAB_HIDDEN', beyond_grace: true })])
    expect(wrapper.text()).toContain('You left the test')
    expect(wrapper.text()).toContain('Warning 1 of 3. 2 more and your test will be submitted automatically.')
    if (hidden) Object.defineProperty(document, 'hidden', hidden)
    else delete (document as { hidden?: boolean }).hidden
    wrapper.unmount()
  })
})
