// T-06's data: one tab of assignments (searchable, by group, paged) and each tab's count.
import { onScopeDispose, ref, watch } from 'vue'
import type { AssignmentPage } from '~/api/types'
import { type AssignmentTab, listAssignments } from '~/features/assignments/composables/assignmentsApi'
import { useActiveGroups } from '~/shared/composables/useActiveGroups'
import { useApiData } from '~/shared/composables/useApiData'

export const TABS: AssignmentTab[] = ['upcoming', 'live', 'closed', 'cancelled']
export const PAGE_SIZE = 50
const SEARCH_DELAY_MS = 300

export function useAssignments() {
  const tab = ref<AssignmentTab>('upcoming')
  const search = ref('')
  const groupId = ref<string>()
  const page = ref(1)

  const list = useApiData<AssignmentPage>(() => listAssignments({
    tab: tab.value,
    search: search.value,
    groupId: groupId.value,
    page: page.value,
    pageSize: PAGE_SIZE,
  }))
  const counts = useApiData<Record<AssignmentTab, number>>(loadCounts)
  const groups = useActiveGroups()

  async function refresh(): Promise<void> {
    await Promise.all([list.refresh(), counts.refresh()])
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

  return { tab, search, groupId, page, list, counts, groups, refresh }
}

async function loadCounts(): Promise<Record<AssignmentTab, number>> {
  // One cheap call per tab (page size 1): only the totals are needed
  const totals = await Promise.all(TABS.map(tab =>
    listAssignments({ tab, search: '', page: 1, pageSize: 1 }).then(page => [tab, page.total] as const),
  ))
  return Object.fromEntries(totals) as Record<AssignmentTab, number>
}
