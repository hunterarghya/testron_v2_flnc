// T-02's data: one page of tests (search by name or tag, tag filter, status, sort) and the
// library's actions, which refresh the page afterwards.
import { onScopeDispose, ref, watch } from 'vue'
import { api, unwrap } from '~/api/client'
import type { TestDocument, TestPage, TestRow } from '~/api/types'
import { useApiData } from '~/shared/composables/useApiData'

export type LibraryStatus = 'active' | 'archived'
export type LibrarySort = '-updated_at' | 'title' | '-last_assigned_at'
export const PAGE_SIZE = 50
const SEARCH_DELAY_MS = 300

export function useTestLibrary() {
  const search = ref('')
  const tagId = ref<string>()
  const status = ref<LibraryStatus>('active')
  const sort = ref<LibrarySort>('-updated_at')
  const page = ref(1)

  const list = useApiData<TestPage>(() => unwrap(api.GET('/api/v1/admin/tests', {
    params: {
      query: { q: search.value.trim() || undefined, tag_id: tagId.value, status: status.value, sort: sort.value, page: page.value, page_size: PAGE_SIZE },
    },
  })))
  const tags = useApiData(() => unwrap(api.GET('/api/v1/admin/tags')))

  function createTest(): Promise<TestDocument> {
    return unwrap(api.POST('/api/v1/admin/tests'))
  }

  async function duplicate(testId: string): Promise<TestDocument> {
    const copy = await unwrap(api.POST('/api/v1/admin/tests/{test_id}/duplicate', { params: { path: { test_id: testId } } }))
    await list.refresh()
    return copy
  }

  async function setArchived(testIds: string[], archived: boolean): Promise<TestRow[]> {
    const path = archived ? '/api/v1/admin/tests/{test_id}/archive' : '/api/v1/admin/tests/{test_id}/restore'
    const rows = await Promise.all(testIds.map(id => unwrap(api.POST(path, { params: { path: { test_id: id } } }))))
    await list.refresh()
    return rows
  }

  watch([tagId, status, sort], () => {
    page.value = 1
    void list.refresh()
  })
  watch(page, () => list.refresh())
  let searchTimer: ReturnType<typeof setTimeout> | undefined
  watch(search, () => {
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      page.value = 1
      void list.refresh()
    }, SEARCH_DELAY_MS)
  })
  onScopeDispose(() => clearTimeout(searchTimer))

  return { search, tagId, status, sort, page, list, tags, createTest, duplicate, setArchived }
}
