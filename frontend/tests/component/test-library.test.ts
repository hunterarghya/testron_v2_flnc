import { mockNuxtImport, mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { TestRow } from '~/api/types'
import TestLibrary from '~/features/library/components/TestLibrary.vue'
import { type FakeApi, ok } from '../fake-api'

const { navigateTo } = vi.hoisted(() => ({ navigateTo: vi.fn() }))
mockNuxtImport('navigateTo', () => navigateTo)

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi

function row(id: string, title: string, problems = 0): TestRow {
  return {
    id, title, question_count: 30, total_marks: '120.00', timing_kind: 'SECTIONED', problem_count: problems,
    last_assigned_at: null, updated_at: '2026-11-12T04:30:00Z', archived_at: null,
  }
}

function queryOf(call: unknown[] | undefined): Record<string, unknown> {
  return (call?.[1] as { params: { query: Record<string, unknown> } }).params.query
}

describe('TestLibrary (T-02)', () => {
  beforeEach(() => {
    navigateTo.mockReset()
    fake.GET.mockReset().mockImplementation(path => (path === '/api/v1/admin/tags'
      ? ok([{ id: 'tag1', kind: 'CHAPTER', name: 'Cell', question_count: 3, test_count: 1 }])
      : ok({ items: [row('t1', 'Cell Biology'), row('t2', 'Genetics MCQ', 2)], page: 1, page_size: 50, total: 2 })))
    fake.POST.mockReset().mockImplementation(() => ok({ id: 'new1', title: 'Untitled test' }))
  })

  it('lists tests with counts, timing, problems and links to the editor', async () => {
    const wrapper = await mountSuspended(TestLibrary)
    await flushPromises()

    expect(wrapper.find('a[href="/admin/tests/t1"]').text()).toBe('Cell Biology')
    expect(wrapper.text()).toContain('⚠ 2')
    expect(wrapper.text()).toContain('Sections')
    expect(wrapper.text()).toContain('never')
    expect(queryOf(fake.GET.mock.calls.find(call => call[0] === '/api/v1/admin/tests'))).toMatchObject({ status: 'active', sort: '-updated_at' })
  })

  it('New test creates a draft and opens it', async () => {
    const wrapper = await mountSuspended(TestLibrary)
    await flushPromises()

    await wrapper.findAll('button').find(b => b.text() === 'New test')!.trigger('click')
    await flushPromises()

    expect(fake.POST).toHaveBeenCalledWith('/api/v1/admin/tests')
    expect(navigateTo).toHaveBeenCalledWith('/admin/tests/new1')
  })

  it('ticked tests can be archived together', async () => {
    const wrapper = await mountSuspended(TestLibrary)
    await flushPromises()

    await wrapper.find('[aria-label="Select all on this page"]').trigger('click')
    await wrapper.findAll('button').find(b => b.text() === 'Archive')!.trigger('click')
    await flushPromises()

    const paths = fake.POST.mock.calls.map(call => [call[0], (call[1] as { params: { path: { test_id: string } } }).params.path.test_id])
    expect(paths).toEqual([['/api/v1/admin/tests/{test_id}/archive', 't1'], ['/api/v1/admin/tests/{test_id}/archive', 't2']])
  })
})
