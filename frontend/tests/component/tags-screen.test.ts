import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import { ApiProblem } from '~/api/problems'
import type { TagUsage } from '~/api/types'
import RenameTagDialog from '~/features/tags/components/RenameTagDialog.vue'
import TagsTable from '~/features/tags/components/TagsTable.vue'
import { mergeTarget } from '~/features/tags/composables/useTags'
import { type FakeApi, ok } from '../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
const GENETCS: TagUsage = { id: 't1', kind: 'CHAPTER', name: 'Genetcs', question_count: 2, test_count: 1 }
const MITOSIS: TagUsage = { id: 't2', kind: 'TOPIC', name: 'Mitosis', question_count: 5, test_count: 2 }
const tagExists = new ApiProblem({
  status: 409, code: 'tag_exists', detail: 'x',
  context: { target: { id: 't9', name: 'Genetics', question_count: 25 } },
})

describe('TagsTable (T-18)', () => {
  beforeEach(() => {
    fake.GET.mockReset().mockImplementation(() => ok([GENETCS, MITOSIS]))
    fake.DELETE.mockReset().mockImplementation(() => ok({ removed_from_questions: 2 }))
  })

  it('shows one kind per tab and filters by text', async () => {
    const wrapper = await mountSuspended(TagsTable)
    await flushPromises()

    expect(wrapper.text()).toContain('Genetcs')
    expect(wrapper.text()).not.toContain('Mitosis')
    await wrapper.find('input[aria-label="Filter tags"]').setValue('zzz')

    expect(wrapper.text()).toContain('No tags here.')
  })

  it('deletes after confirming', async () => {
    const wrapper = await mountSuspended(TagsTable)
    await flushPromises()

    await wrapper.find('button[aria-label="Delete Genetcs"]').trigger('click')
    await flushPromises()
    const confirm = [...document.querySelectorAll('button')].find(b => b.textContent?.trim() === 'Delete tag')!
    confirm.click()
    await flushPromises()

    expect(fake.DELETE).toHaveBeenCalledWith('/api/v1/admin/tags/{tag_id}', { params: { path: { tag_id: 't1' } } })
    wrapper.unmount()
  })
})

describe('RenameTagDialog', () => {
  it('asks before merging, then merges', async () => {
    const rename = vi.fn().mockRejectedValueOnce(tagExists).mockResolvedValueOnce(undefined)
    const wrapper = await mountSuspended(RenameTagDialog, { props: { open: false, tag: GENETCS, rename } })
    await wrapper.setProps({ open: true })
    await flushPromises()

    document.querySelector<HTMLFormElement>('#rename-tag')!.requestSubmit()
    await flushPromises()
    expect(document.body.textContent).toContain('into Genetics (25)')
    ;[...document.querySelectorAll('button')].find(b => b.textContent?.trim() === 'Merge')!.click()
    await flushPromises()

    expect(rename.mock.calls).toEqual([['t1', 'Genetcs', false], ['t1', 'Genetcs', true]])
    wrapper.unmount()
  })

  it('reads the merge target only from tag_exists', () => {
    expect(mergeTarget(tagExists)?.name).toBe('Genetics')
    expect(mergeTarget(new ApiProblem({ status: 404, code: 'not_found', detail: 'x' }))).toBeNull()
    expect(mergeTarget(new Error('bug'))).toBeNull()
  })
})
