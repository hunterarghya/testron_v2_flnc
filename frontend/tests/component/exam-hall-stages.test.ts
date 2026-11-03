import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { AttemptState } from '~/api/types'
import ExamHall from '~/features/exam-hall/components/ExamHall.vue'
import { type FakeApi, ok } from '../fake-api'
import { attempt, DOC, LATER } from '../hall-fixtures'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
const SOON = new Date(Date.now() + 600_000).toISOString()

function question(id: string, number: number) {
  return { id, number, type: 'MCQ' as const, stem: DOC, marks: '4.00', negative_marks: '1.00', time_s: null,
    options: [{ id: `${id}-a`, label: 'A', content: DOC }] }
}

function staged(kind: 'SECTIONED' | 'PER_QUESTION', current: number): AttemptState {
  const stage = (index: number) => ({
    index, kind: kind === 'SECTIONED' ? 'SECTION' as const : 'QUESTION' as const,
    title: kind === 'SECTIONED' ? `Part ${index + 1}` : null, instructions: null, duration_s: 600, question_ids: [`q${index + 1}`],
  })
  const state = (index: number) => (index < current ? 'CLOSED' as const : index === current ? 'OPEN' as const : 'NOT_ENTERED' as const)
  return attempt({
    timing: { kind, allow_return: false },
    current_stage_index: current,
    stages: [0, 1].map(index => ({ index, state: state(index), deadline_at: index === 1 ? LATER : SOON })),
    stage_meta: [stage(0), stage(1)],
    questions: [question(`q${current + 1}`, current + 1)],
  })
}

type Mounted = Awaited<ReturnType<typeof mountSuspended>>
// The hall's own buttons, and those of its dialogs (shown outside it)
function byText(wrapper: Mounted, text: string): HTMLButtonElement | undefined {
  const all = [...wrapper.findAll('button').map(b => b.element as HTMLButtonElement), ...document.querySelectorAll('button')]
  return all.find(b => b.textContent?.trim() === text)
}

beforeEach(() => {
  localStorage.clear()
  for (const method of [fake.GET, fake.PUT, fake.POST]) method.mockReset()
})

describe('sections (P-04)', () => {
  it('shows the section bar and moves on after confirming', async () => {
    fake.GET.mockImplementation(() => ok(staged('SECTIONED', 0)))
    fake.POST.mockImplementation((path: string) => ok(path.endsWith('/stages/next') ? staged('SECTIONED', 1) : undefined))
    const wrapper = await mountSuspended(ExamHall, { props: { attemptId: 'att1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('S1 · Q 1 of 1')
    expect(wrapper.find('nav[aria-label="Sections"]').text()).toContain('S2 Part 2 · 10 min')
    byText(wrapper, 'Next section')!.click()
    await flushPromises()
    expect(document.body.textContent).toContain('Leave Section 1: Part 1?')
    expect(document.body.textContent).toContain('You can\'t come back to this section.')
    byText(wrapper, 'Go to Section 2')!.click()
    await flushPromises()

    const next = fake.POST.mock.calls.find(([path]) => path.endsWith('/stages/next'))!
    expect(next[1]).toMatchObject({ body: { from_stage_index: 0 }, headers: { 'X-Exam-Client': 'dev1' } })
    expect(wrapper.text()).toContain('S2 · Q 1 of 1')
    expect(wrapper.text()).toContain('Submit')
    wrapper.unmount()
  })
})

describe('rapid fire (P-05)', () => {
  it('has no palette and Next goes straight on', async () => {
    fake.GET.mockImplementation(() => ok(staged('PER_QUESTION', 0)))
    fake.POST.mockImplementation((path: string) => ok(path.endsWith('/stages/next') ? staged('PER_QUESTION', 1) : undefined))
    const wrapper = await mountSuspended(ExamHall, { props: { attemptId: 'att1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('Q 1 of 2')
    expect(wrapper.find('nav[aria-label="Questions"]').exists()).toBe(false)
    expect(byText(wrapper, 'Prev')).toBeUndefined()
    byText(wrapper, 'Next')!.click()
    await flushPromises()

    expect(wrapper.text()).toContain('Q 2 of 2')
    wrapper.unmount()
  })
})
