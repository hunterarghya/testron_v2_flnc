<!-- T-13 Results inbox: closed tests by whether their results wait for the teacher. "Review"
     opens the gradebook (T-11). The "To publish" tab is what the menu badge counts. -->
<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { computed, h, onMounted, ref } from 'vue'
import { UButton } from '#components'
import type { ResultsInboxRow } from '~/api/types'
import { type InboxTab, listResultsInbox } from '~/features/results/composables/resultsInboxApi'
import DataTable from '~/shared/components/DataTable.vue'
import { useApiData } from '~/shared/composables/useApiData'
import { formatDateTime } from '~/shared/utils/time'

const tab = ref<InboxTab>('to_publish')
const inbox = useApiData(() => listResultsInbox(tab.value))
const TABS = [
  { label: 'To publish', value: 'to_publish' },
  { label: 'Published', value: 'published' },
  { label: 'All', value: 'all' },
]
type Row = ResultsInboxRow & { id: string }
const rows = computed<Row[]>(() => (inbox.data.value?.items ?? []).map(r => ({ ...r, id: r.assignment_id })))

const columns: TableColumn<Row>[] = [
  { accessorKey: 'title', header: 'Assignment' },
  { id: 'closed', header: 'Closed', cell: ({ row }) => (row.original.ends_at ? formatDateTime(row.original.ends_at) : '–') },
  { id: 'avg', header: 'Avg', cell: ({ row }) => (row.original.average_pct == null ? '–' : `${row.original.average_pct}%`) },
  { id: 'flags', header: 'Flags', cell: ({ row }) => row.original.flagged || '' },
  {
    id: 'review',
    header: '',
    cell: ({ row }) => h(UButton, { label: 'Review', trailingIcon: 'i-lucide-chevron-right', size: 'sm', variant: 'soft', to: `/admin/assignments/${row.original.assignment_id}/results` }),
  },
]

function choose(value: string | number): void {
  tab.value = value as InboxTab
  void inbox.refresh()
}

onMounted(() => inbox.refresh())
</script>

<template>
  <div class="space-y-4">
    <UTabs :model-value="tab" :items="TABS" :content="false" @update:model-value="choose" />
    <DataTable :rows="rows" :columns="columns" :loading="inbox.pending.value" :error="inbox.error.value" empty-title="Nothing here" @retry="inbox.refresh" />
  </div>
</template>
