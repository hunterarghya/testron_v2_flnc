import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { Group, GroupMember } from '~/api/types'
import GroupDetail from '~/features/groups/components/GroupDetail.vue'
import GroupFormDialog from '~/features/groups/components/GroupFormDialog.vue'
import GroupsTable from '~/features/groups/components/GroupsTable.vue'
import { outcome } from '~/features/groups/composables/useGroup'
import { type FakeApi, fails, ok } from '../fake-api'
import { ApiProblem } from '~/api/problems'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi

function group(id: string, name: string, archived = false): Group {
  return { id, name, description: '', archived_at: archived ? '2026-11-10T00:00:00Z' : null, member_count: 2, created_at: '2026-11-01T00:00:00Z' }
}

function member(id: string, name: string): GroupMember {
  return { id, name, email: `${id}@x.in`, status: 'ACTIVE', added_at: '2026-11-02T00:00:00Z', performance_shared: false }
}

function button(wrapper: { findAll: (s: string) => { text: () => string, trigger: (e: string) => Promise<void> }[] }, label: string) {
  const found = wrapper.findAll('button').find(b => b.text() === label)
  if (!found) {
    throw new Error(`no button ${label}`)
  }
  return found
}

describe('GroupsTable (T-16)', () => {
  beforeEach(() => {
    fake.GET.mockReset().mockImplementation(() => ok([group('g1', 'Class 11 A')]))
    fake.POST.mockReset().mockImplementation(() => ok(group('g1', 'Class 11 A', true)))
  })

  it('lists groups with links and archives one', async () => {
    const wrapper = await mountSuspended(GroupsTable)
    await flushPromises()

    expect(wrapper.find('a[href="/admin/groups/g1"]').text()).toBe('Class 11 A')
    await button(wrapper, 'Archive').trigger('click')
    await flushPromises()

    expect(fake.POST.mock.calls[0]![0]).toBe('/api/v1/admin/groups/{group_id}/archive')
  })
})

describe('GroupFormDialog', () => {
  it('shows a taken name under the name field', async () => {
    fake.POST.mockReset().mockImplementation(() => Promise.reject(new ApiProblem({
      status: 422, code: 'validation_error', detail: 'x',
      errors: [{ field: 'name', code: 'taken', message: 'Another active group has this name' }],
    })))
    const wrapper = await mountSuspended(GroupFormDialog, { props: { open: false } })
    await wrapper.setProps({ open: true })
    await flushPromises()
    const name = document.querySelector<HTMLInputElement>('#group-form input')!
    name.value = 'Class 11 A'
    name.dispatchEvent(new Event('input'))

    document.querySelector<HTMLFormElement>('#group-form')!.requestSubmit()
    await flushPromises()

    expect(document.body.textContent).toContain('Another active group has this name')
    wrapper.unmount()
  })
})

describe('GroupDetail (T-17)', () => {
  beforeEach(() => {
    fake.GET.mockReset().mockImplementation(() => ok({ group: group('g1', 'Class 11 A'), members: [member('a', 'Aditi'), member('r', 'Rina')] }))
    fake.POST.mockReset().mockImplementation(() => ok({ succeeded: ['a'], skipped: [] }))
  })

  it('shows the members and removes the ticked ones', async () => {
    const wrapper = await mountSuspended(GroupDetail, { props: { groupId: 'g1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('Aditi')
    await wrapper.findAll('[aria-label="Select row"]')[0]!.trigger('click')
    await button(wrapper, 'Remove from group').trigger('click')
    await flushPromises()

    expect(fake.POST.mock.calls[0]![0]).toBe('/api/v1/admin/groups/{group_id}/members/remove')
    expect(fake.POST.mock.calls[0]![1]).toMatchObject({ body: { student_ids: ['a'] } })
  })

  it('shows an error state when the group is gone', async () => {
    fake.GET.mockReset().mockImplementation(() => fails(404, 'not_found'))
    const wrapper = await mountSuspended(GroupDetail, { props: { groupId: 'gone' } })
    await flushPromises()

    expect(wrapper.text()).toContain('couldn\'t find')
  })
})

describe('bulk outcome', () => {
  it('mentions skipped students only when there are some', () => {
    expect(outcome({ succeeded: ['a', 'b'], skipped: [] }, 'added')).toBe('2 added')
    expect(outcome({ succeeded: ['a'], skipped: [{ id: 'b', reason: 'already_member' }] }, 'added')).toBe('1 added, 1 skipped')
  })
})
