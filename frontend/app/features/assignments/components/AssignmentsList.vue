<!-- T-06 Assignments: a tab per state, search and group filter; rows open the overview. -->
<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { computed, h, onMounted } from 'vue'
import { UBadge, UIcon, ULink } from '#components'
import type { AssignmentRow } from '~/api/types'
import type { AssignmentTab } from '~/features/assignments/composables/assignmentsApi'
import { PAGE_SIZE, TABS, useAssignments } from '~/features/assignments/composables/useAssignments'
import { STATE_LABELS, windowLabel } from '~/features/assignments/utils/describe'
import DataTable from '~/shared/components/DataTable.vue'

const LABELS: Record<AssignmentTab, string> = { upcoming: 'Upcoming', live: 'Live', closed: 'Closed', cancelled: 'Cancelled' }
const EMPTY: Record<AssignmentTab, string> = {
  upcoming: 'Nothing coming up. Assign a test to get started.',
  live: 'No test is running right now.',
  closed: 'No closed tests yet.',
  cancelled: 'No cancelled tests.',
}
const PUBLICATION: Record<AssignmentRow['publication_state'], string> = {
  UNPUBLISHED: 'Unpublished',
  SCHEDULED: 'Auto-publish',
  PUBLISHED: 'Published',
}

const assignments = useAssignments()
const { tab, search, groupId, page, list, counts, groups } = assignments
const ALL_GROUPS = 'all'
const groupItems = computed(() => [
  { label: 'All groups', value: ALL_GROUPS },
  ...(groups.data.value ?? []).map(group => ({ label: group.name, value: group.id })),
])
const groupFilter = computed({
  get: () => groupId.value ?? ALL_GROUPS,
  set: (value: string) => { groupId.value = value === ALL_GROUPS ? undefined : value },
})
const tabs = computed(() => TABS.map(value => ({ value, label: LABELS[value], badge: counts.data.value?.[value] || undefined })))
const columns: TableColumn<AssignmentRow>[] = [
  {
    accessorKey: 'title',
    header: 'Assignment',
    cell: ({ row }) => h('span', { class: 'inline-flex items-center gap-1' }, [
      h(ULink, { to: `/admin/assignments/${row.original.id}` }, () => row.original.title),
      row.original.locked ? h(UIcon, { name: 'i-lucide-lock', class: 'size-4 text-muted', 'aria-label': 'Locked' }) : null,
    ]),
  },
  { id: 'audience', header: 'Audience', cell: ({ row }) => `${row.original.audience.summary} (${row.original.audience.count})` },
  { id: 'window', header: 'Window', cell: ({ row }) => windowLabel(row.original) },
  {
    id: 'state',
    header: 'Status',
    cell: ({ row }) => h(UBadge, { ...STATE_LABELS[row.original.state], variant: 'subtle' }),
  },
  { id: 'done', header: 'Done', cell: ({ row }) => `${row.original.progress.ended}/${row.original.progress.audience}` },
  { id: 'publication', header: 'Results', cell: ({ row }) => PUBLICATION[row.original.publication_state] },
]

onMounted(() => Promise.all([assignments.refresh(), groups.refresh()]))
</script>

<template>
  <div class="space-y-4">
    <UTabs v-model="tab" :items="tabs" :content="false" />
    <div class="flex flex-wrap items-center gap-3">
      <UInput v-model="search" icon="i-lucide-search" placeholder="Search…" class="w-full max-w-sm" aria-label="Search assignments" />
      <USelect v-model="groupFilter" :items="groupItems" class="w-48" aria-label="Filter by group" />
    </div>
    <DataTable
      :rows="list.data.value?.items ?? []"
      :columns="columns"
      :loading="list.pending.value"
      :error="list.error.value"
      :empty-title="EMPTY[tab]"
      @retry="assignments.refresh"
    />
    <UPagination
      v-if="(list.data.value?.total ?? 0) > PAGE_SIZE"
      v-model:page="page"
      :total="list.data.value?.total ?? 0"
      :items-per-page="PAGE_SIZE"
    />
  </div>
</template>
