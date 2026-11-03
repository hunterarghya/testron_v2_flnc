import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { Monitor, MonitorRow } from '~/api/types'
import AssignmentMonitor from '~/features/assignments/components/monitor/AssignmentMonitor.vue'
import { detail } from '../assignment-fixtures'
import { type FakeApi, ok } from '../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
const NOW = '2026-11-12T05:30:00Z'

function row(changes: Partial<MonitorRow>): MonitorRow {
  return {
    student_id: 's1', name: 'Aditi Roy', take_number: 1, attempt_id: 'att1', status: 'IN_PROGRESS',
    current_stage_index: 0, answered: 18, total_questions: 30, warning_count: 0,
    last_seen_at: '2026-11-12T05:29:56Z', deadline_at: '2026-11-12T06:20:00Z', ...changes,
  }
}

const MONITOR: Monitor = {
  title: 'Cell Biology – Take 1',
  rows: [
    row({}),
    row({ student_id: 's2', name: 'Arjun Das', attempt_id: 'att2', warning_count: 2, last_seen_at: '2026-11-12T05:28:00Z' }),
    row({ student_id: 's3', name: 'Rahul Saha', take_number: null, attempt_id: null, status: 'NOT_STARTED', current_stage_index: null, answered: 0, last_seen_at: null, deadline_at: null }),
  ],
  summary: { IN_PROGRESS: 2, NOT_STARTED: 1 },
  ends_at: '2026-11-12T06:20:00Z',
  server_now: NOW,
}

function button(wrapper: { element: Element }, label: string): HTMLButtonElement {
  const all = [...wrapper.element.querySelectorAll('button'), ...document.querySelectorAll('button')]
  const found = all.find(b => b.textContent?.trim() === label || b.getAttribute('aria-label') === label)
  if (!found) throw new Error(`no button ${label}`)
  return found
}

beforeEach(() => {
  fake.GET.mockReset().mockImplementation((path: string) => {
    if (path.endsWith('/monitor')) return ok(MONITOR)
    if (path.endsWith('/integrity-events')) return ok([{ kind: 'TAB_HIDDEN', left_at: '2026-11-12T05:21:00Z', returned_at: '2026-11-12T05:21:12Z', counted: true }])
    return ok(detail({ state: 'LIVE' }))
  })
  fake.POST.mockReset()
})

describe('AssignmentMonitor (T-10)', () => {
  it('shows each student, their progress, warnings and last contact', async () => {
    const wrapper = await mountSuspended(AssignmentMonitor, { props: { assignmentId: 'a1' } })
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('Cell Biology – Take 1 › Monitor')
    expect(text).toContain('ends 11:50 (00:50:00 left)')
    expect(text).toContain('18/30')
    expect(text).toContain('4s')
    expect(text).toContain('2 min')
    expect(text).toContain('Not started')
    expect(text).toContain('Summary: 2 in progress · 1 not started')
    button(wrapper, 'Warnings for Arjun Das').click()
    await flushPromises()
    expect(document.body.textContent).toContain('Tab hidden · 10:51 · away 12 s · counted')
    wrapper.unmount()
  })

  it('ends the test for everyone once END is typed', async () => {
    fake.POST.mockImplementation(() => ok({ ended_at: NOW, ended_attempts: 2 }))
    const wrapper = await mountSuspended(AssignmentMonitor, { props: { assignmentId: 'a1' } })
    await flushPromises()

    button(wrapper, 'End for everyone').click()
    await flushPromises()
    const input = [...document.querySelectorAll('input')].at(-1)!
    input.value = 'END'
    input.dispatchEvent(new Event('input'))
    await flushPromises()
    const confirms = [...document.querySelectorAll('button')].filter(b => b.textContent?.trim() === 'End for everyone')
    confirms.at(-1)!.click()
    await flushPromises()

    expect(fake.POST).toHaveBeenCalledWith('/api/v1/admin/assignments/{assignment_id}/end', expect.objectContaining({ body: { confirm: 'END' } }))
    wrapper.unmount()
  })
})
