// T-14's data: one tab of students (searchable, paged, by group), the count on each tab,
// and the admission actions, which refresh both (and the menu badge) afterwards.
import { onScopeDispose, ref, watch } from 'vue'
import { api, unwrap } from '~/api/client'
import type { BulkResult, ListedStatus, StudentPage } from '~/api/types'
import type { StudentAction } from '~/features/students/utils/bulk-summary'
import { type ShareChange, shareSummary } from '~/features/students/utils/share-plan'
import { useActiveGroups } from '~/shared/composables/useActiveGroups'
import { useApiData } from '~/shared/composables/useApiData'
import { useBadges } from '~/shared/composables/useBadges'

export const TABS: ListedStatus[] = ['ACTIVE', 'PENDING', 'DECLINED', 'DEACTIVATED']
export const PAGE_SIZE = 50
const SEARCH_DELAY_MS = 300

export function useStudents() {
  const tab = ref<ListedStatus>('ACTIVE')
  const search = ref('')
  const page = ref(1)
  // Narrows every tab to one group; undefined means all students
  const groupId = ref<string>()
  const badges = useBadges()

  const list = useApiData<StudentPage>(() =>
    unwrap(api.GET('/api/v1/admin/students', {
      params: { query: { status: tab.value, q: search.value.trim() || undefined, group_id: groupId.value, page: page.value, page_size: PAGE_SIZE } },
    })),
  )
  const counts = useApiData<Record<ListedStatus, number>>(loadCounts)
  const groups = useActiveGroups()

  async function refresh(): Promise<void> {
    // The badge is a nicety: if it fails to load, the table still refreshes
    await Promise.all([list.refresh(), counts.refresh(), badges.refresh().catch(() => undefined)])
  }

  async function act(action: StudentAction, studentIds: string[]): Promise<BulkResult> {
    const result = await unwrap(api.POST(`/api/v1/admin/students/${action}`, { body: { student_ids: studentIds } }))
    await refresh()
    return result
  }

  /** D-06: share and unshare in one save; returns the toast text. */
  async function sharePerformance(change: ShareChange): Promise<string> {
    const send = (path: '/api/v1/admin/performance-shares' | '/api/v1/admin/performance-shares/remove', ids: string[]) =>
      ids.length ? unwrap(api.POST(path, { body: { student_ids: ids } })).then(result => result.succeeded.length) : Promise.resolve(0)
    const counts = change.kind === 'group'
      ? [(await unwrap(api.POST('/api/v1/admin/performance-shares', { body: { group_id: change.groupId } }))).succeeded.length, 0]
      : [await send('/api/v1/admin/performance-shares', change.on), await send('/api/v1/admin/performance-shares/remove', change.off)]
    await refresh()
    return shareSummary(counts[0]!, counts[1]!)
  }

  async function anonymize(studentId: string, confirmName: string): Promise<void> {
    await api.POST('/api/v1/admin/students/{student_id}/anonymize', {
      params: { path: { student_id: studentId } },
      body: { confirm_name: confirmName },
    })
    await refresh()
  }

  watch([tab, page], () => list.refresh())
  watch(groupId, () => {
    page.value = 1
    void list.refresh()
  })
  let searchTimer: ReturnType<typeof setTimeout> | undefined
  watch(search, () => {
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      page.value = 1
      void list.refresh()
    }, SEARCH_DELAY_MS)
  })
  onScopeDispose(() => clearTimeout(searchTimer))

  return { tab, search, page, groupId, list, counts, groups, refresh, act, anonymize, sharePerformance }
}

async function loadCounts(): Promise<Record<ListedStatus, number>> {
  // One cheap call per tab (page size 1): only the totals are needed
  const totals = await Promise.all(TABS.map(status =>
    unwrap(api.GET('/api/v1/admin/students', { params: { query: { status, page_size: 1 } } }))
      .then(page => [status, page.total] as const),
  ))
  return Object.fromEntries(totals) as Record<ListedStatus, number>
}
