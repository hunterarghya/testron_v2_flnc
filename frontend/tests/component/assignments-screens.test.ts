import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { Lobby } from '~/api/types'
import AssignmentsList from '~/features/assignments/components/AssignmentsList.vue'
import AssignmentLobby from '~/features/assignments/components/lobby/AssignmentLobby.vue'
import AssignmentOverview from '~/features/assignments/components/overview/AssignmentOverview.vue'
import { detail } from '../assignment-fixtures'
import { type FakeApi, ok } from '../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi


// Buttons in the component itself, or in a dialog (dialogs render into the page body)
function button(wrapper: { element: Element }, label: string): HTMLButtonElement {
  const all = [...wrapper.element.querySelectorAll('button'), ...document.querySelectorAll('button')]
  const found = all.find(b => b.textContent?.trim() === label || b.getAttribute('aria-label') === label)
  if (!found) throw new Error(`no button ${label}`)
  return found
}

describe('AssignmentsList (T-06)', () => {
  beforeEach(() => {
    fake.GET.mockReset().mockImplementation((path: string) => (path === '/api/v1/admin/groups'
      ? ok([])
      : ok({ items: [detail()], page: 1, page_size: 50, total: 1 })))
  })

  it('shows each assignment with its audience, window and state', async () => {
    const wrapper = await mountSuspended(AssignmentsList)
    await flushPromises()

    expect(wrapper.find('a[href="/admin/assignments/a1"]').text()).toBe('Cell Biology – Take 1')
    expect(wrapper.text()).toContain('11A (2)')
    expect(wrapper.text()).toContain('Manual')
    expect(wrapper.text()).toContain('Waiting')
    expect(wrapper.find('[aria-label="Locked"]').exists()).toBe(true)
  })
})

describe('AssignmentOverview (T-08)', () => {
  beforeEach(() => {
    fake.GET.mockReset().mockImplementation((path: string) => (path.endsWith('/password') ? ok({ password: '4321' }) : ok(detail())))
    fake.POST.mockReset().mockImplementation(() => ok({ succeeded: ['s2'], skipped: [] }))
  })

  it('shows the summary and reveals the password only when asked', async () => {
    const wrapper = await mountSuspended(AssignmentOverview, { props: { assignmentId: 'a1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('Locked: activation + password')
    expect(wrapper.text()).not.toContain('4321')
    button(wrapper, 'Reveal password').click()
    await flushPromises()
    expect(wrapper.text()).toContain('4321')
  })

  it('removes a student who has not begun', async () => {
    const wrapper = await mountSuspended(AssignmentOverview, { props: { assignmentId: 'a1' } })
    await flushPromises()

    button(wrapper, 'Edit').click()
    await flushPromises()
    button(wrapper, 'Remove Arjun Das').click()
    await flushPromises()

    expect(fake.POST.mock.calls[0]![0]).toBe('/api/v1/admin/assignments/{assignment_id}/audience/remove')
    wrapper.unmount()
  })
})

describe('AssignmentLobby (T-09)', () => {
  const lobby: Lobby = {
    joined: [{ student_id: 's1', name: 'Aditi Roy', last_seen_at: '2026-11-12T05:28:12Z' }],
    not_joined: [{ student_id: 's2', name: 'Arjun Das' }],
    counts: { joined: 1, audience: 2 },
    state: 'WAITING',
    server_now: '2026-11-12T05:28:20Z',
  }

  beforeEach(() => {
    fake.GET.mockReset().mockImplementation((path: string) => (path.endsWith('/lobby') ? ok(lobby) : ok(detail())))
    fake.POST.mockReset().mockImplementation(() => ok({ activated_at: '2026-11-12T05:30:00Z', anchor_at: '2026-11-12T05:30:00Z', ends_at: null }))
  })

  it('lists who joined and starts after confirming', async () => {
    const wrapper = await mountSuspended(AssignmentLobby, { props: { assignmentId: 'a1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('Joined 1 / 2')
    expect(wrapper.text()).toContain('Arjun Das')
    button(wrapper, 'Start test for everyone').click()
    await flushPromises()
    button(wrapper, 'Start').click()
    await flushPromises()

    expect(fake.POST.mock.calls[0]![0]).toBe('/api/v1/admin/assignments/{assignment_id}/activate')
    wrapper.unmount()
  })
})
