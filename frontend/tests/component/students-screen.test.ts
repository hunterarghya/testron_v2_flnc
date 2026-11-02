import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { StudentRow } from '~/api/types'
import StudentsBulkActions from '~/features/students/components/StudentsBulkActions.vue'
import StudentsTable from '~/features/students/components/StudentsTable.vue'
import { type FakeApi, fails, ok } from '../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi

function student(id: string, name: string, status: StudentRow['status'] = 'PENDING'): StudentRow {
  return {
    id, name, email: `${id}@x.in`, status, joined_at: '2026-11-01T10:00:00Z',
    requested_at: '2026-11-12T08:00:00Z', decided_at: null, deactivated_at: null, performance_shared: false,
    group_names: ['Class 11 A'],
  }
}

function pageOf(items: StudentRow[]) {
  return { items, page: 1, page_size: 50, total: items.length }
}

function queryOf(call: unknown[] | undefined): Record<string, unknown> {
  return ((call?.[1] as { params: { query: Record<string, unknown> } }).params.query)
}

describe('StudentsTable (T-14)', () => {
  beforeEach(() => {
    fake.GET.mockReset().mockImplementation((path, init) => {
      if (path === '/api/v1/admin/groups') {
        return ok([{ id: 'g1', name: 'Class 11 A' }])
      }
      if (path === '/api/v1/admin/badges') {
        return ok({ pending_students: 2, results_to_publish: 0 })
      }
      const query = (init as { params: { query: { status: string, page_size?: number } } }).params.query
      const rows = query.status === 'PENDING' ? [student('a', 'Aditi'), student('t', 'Tapas')] : []
      return ok(pageOf(query.page_size === 1 ? rows.slice(0, 1) : rows))
    })
    fake.POST.mockReset().mockImplementation(() => ok({ succeeded: ['a'], skipped: [] }))
  })

  it('loads the active tab and the count on every tab', async () => {
    const wrapper = await mountSuspended(StudentsTable)
    await flushPromises()

    const statuses = fake.GET.mock.calls.filter(call => call[0] === '/api/v1/admin/students').map(call => queryOf(call).status)
    expect(new Set(statuses)).toEqual(new Set(['ACTIVE', 'PENDING', 'DECLINED', 'DEACTIVATED']))
    expect(wrapper.text()).toContain('No active students yet')
  })

  it('shows the pending requests on the Pending tab', async () => {
    const wrapper = await mountSuspended(StudentsTable)
    await flushPromises()

    await wrapper.findAll('button[role="tab"]').find(tab => tab.text().startsWith('Pending'))!.trigger('mousedown')
    await flushPromises()

    expect(wrapper.text()).toContain('Aditi')
    expect(wrapper.text()).toContain('Tapas')
  })

  it('links each name to the profile and lists the groups', async () => {
    const wrapper = await mountSuspended(StudentsTable)
    await flushPromises()
    await wrapper.findAll('button[role="tab"]').find(tab => tab.text().startsWith('Pending'))!.trigger('mousedown')
    await flushPromises()

    expect(wrapper.find('a[href="/admin/students/a"]').text()).toBe('Aditi')
    expect(wrapper.text()).toContain('Class 11 A')
  })
})

describe('StudentsBulkActions', () => {
  const act = vi.fn()
  const anonymize = vi.fn()

  beforeEach(() => {
    act.mockReset().mockResolvedValue({ succeeded: ['a'], skipped: [{ id: 't', reason: 'status_active' }] })
    anonymize.mockReset().mockResolvedValue(undefined)
  })

  it.each([
    ['PENDING', ['Approve', 'Decline']],
    ['ACTIVE', ['Deactivate']],
    ['DEACTIVATED', ['Reactivate', 'Delete permanently']],
    ['DECLINED', []],
  ] as const)('the %s tab offers %o', async (tab, labels) => {
    const wrapper = await mountSuspended(StudentsBulkActions, {
      props: { tab, selected: [student('a', 'Aditi', tab)], act, anonymize },
    })

    expect(wrapper.findAll('button').map(button => button.text())).toEqual(labels)
  })

  it('approves the ticked students straight away', async () => {
    const wrapper = await mountSuspended(StudentsBulkActions, {
      props: { tab: 'PENDING', selected: [student('a', 'Aditi'), student('t', 'Tapas')], act, anonymize },
    })

    await wrapper.findAll('button').find(button => button.text() === 'Approve')!.trigger('click')
    await flushPromises()

    expect(act).toHaveBeenCalledWith('approve', ['a', 't'])
    expect(wrapper.emitted('done')).toHaveLength(1)
  })

  it('offers delete only for one student at a time', async () => {
    const wrapper = await mountSuspended(StudentsBulkActions, {
      props: { tab: 'DEACTIVATED', selected: [student('a', 'A', 'DEACTIVATED'), student('b', 'B', 'DEACTIVATED')], act, anonymize },
    })

    expect(wrapper.text()).not.toContain('Delete permanently')
  })

  it('reports a failed action instead of finishing', async () => {
    act.mockImplementation(() => fails(403, 'forbidden'))
    const wrapper = await mountSuspended(StudentsBulkActions, {
      props: { tab: 'PENDING', selected: [student('a', 'Aditi')], act, anonymize },
    })

    await wrapper.findAll('button').find(button => button.text() === 'Approve')!.trigger('click')
    await flushPromises()

    expect(wrapper.emitted('done')).toBeUndefined()
  })
})
