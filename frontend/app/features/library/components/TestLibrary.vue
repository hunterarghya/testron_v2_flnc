<!-- T-02 Test Library: search (name or tag), tag and status filters, sort; "New test" opens the
     editor straight away; ⋯ Open · Duplicate · Archive/Restore; tick to archive many. -->
<script setup lang="ts">
import type { DropdownMenuItem, TableColumn } from '@nuxt/ui'
import { computed, h, onMounted, ref, watch } from 'vue'
import { navigateTo, useToast } from '#imports'
import { UBadge, UButton, UDropdownMenu, ULink } from '#components'
import { problemMessage } from '~/api/problem-messages'
import { toProblem } from '~/api/problems'
import type { TestRow } from '~/api/types'
import { PAGE_SIZE, useTestLibrary } from '~/features/library/composables/useTestLibrary'
import { testColumns } from '~/features/library/utils/columns'
import DataTable from '~/shared/components/DataTable.vue'

const SORTS = [
  { label: 'Recently edited', value: '-updated_at' },
  { label: 'Name', value: 'title' },
  { label: 'Recently used', value: '-last_assigned_at' },
]
const STATUSES = [{ label: 'Active', value: 'active' }, { label: 'Archived', value: 'archived' }]

const toast = useToast()
const library = useTestLibrary()
const { search, tagId, status, sort, page, list, tags } = library
const selected = ref<string[]>([])
const creating = ref(false)
const archived = computed(() => status.value === 'archived')
const tagItems = computed(() => [{ label: 'Any tag', value: undefined }, ...(tags.data.value ?? []).map(tag => ({ label: tag.name, value: tag.id }))])

const nameColumn: TableColumn<TestRow> = {
  accessorKey: 'title',
  header: 'Name',
  cell: ({ row }) => h('span', { class: 'flex items-center gap-2' }, [
    h(ULink, { to: `/admin/tests/${row.original.id}`, class: 'font-medium' }, () => row.original.title),
    row.original.problem_count ? h(UBadge, { label: `⚠ ${row.original.problem_count}`, color: 'warning', variant: 'subtle', size: 'sm', title: 'Problems to fix before assigning' }) : null,
  ]),
}
const menuColumn: TableColumn<TestRow> = {
  id: 'menu',
  header: '',
  cell: ({ row }) => h(UDropdownMenu, { items: rowMenu(row.original) }, () =>
    h(UButton, { 'icon': 'i-lucide-ellipsis', 'color': 'neutral', 'variant': 'ghost', 'size': 'xs', 'aria-label': `More for ${row.original.title}` })),
}
const columns = [nameColumn, ...testColumns(), menuColumn]

function rowMenu(row: TestRow): DropdownMenuItem[] {
  return [
    { label: 'Open', icon: 'i-lucide-pencil', onSelect: () => navigateTo(`/admin/tests/${row.id}`) },
    { label: 'Duplicate', icon: 'i-lucide-copy', onSelect: () => run(async () => `${(await library.duplicate(row.id)).title} created`) },
    row.archived_at
      ? { label: 'Restore', icon: 'i-lucide-archive-restore', onSelect: () => archive([row.id], false) }
      : { label: 'Archive', icon: 'i-lucide-archive', onSelect: () => archive([row.id], true) },
  ]
}

async function run(action: () => Promise<string>): Promise<void> {
  try {
    toast.add({ title: await action(), color: 'success' })
  }
  catch (caught) {
    toast.add({ title: problemMessage(toProblem(caught)), color: 'error' })
  }
}

async function archive(ids: string[], on: boolean): Promise<void> {
  await run(async () => {
    await library.setArchived(ids, on)
    selected.value = []
    return `${ids.length} test${ids.length === 1 ? '' : 's'} ${on ? 'archived' : 'restored'}`
  })
}

async function newTest(): Promise<void> {
  creating.value = true
  try {
    const created = await library.createTest()
    await navigateTo(`/admin/tests/${created.id}`)
  }
  catch (caught) {
    toast.add({ title: problemMessage(toProblem(caught)), color: 'error' })
  }
  finally {
    creating.value = false
  }
}

watch(status, () => (selected.value = []))
onMounted(() => Promise.all([list.refresh(), tags.refresh()]))
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <UInput v-model="search" icon="i-lucide-search" placeholder="Search name or tag…" class="w-full max-w-xs" aria-label="Search tests" />
      <USelect v-model="tagId" :items="tagItems" class="w-44" aria-label="Filter by tag" />
      <USelect v-model="status" :items="STATUSES" class="w-32" aria-label="Status" />
      <USelect v-model="sort" :items="SORTS" class="w-44" aria-label="Sort" />
      <UButton label="New test" icon="i-lucide-plus" class="ms-auto" :loading="creating" @click="newTest" />
    </div>
    <DataTable
      v-model:selected="selected"
      :rows="list.data.value?.items ?? []"
      :columns="columns"
      :loading="list.pending.value"
      :error="list.error.value"
      :empty-title="archived ? 'No archived tests.' : 'No tests yet.'"
      :empty-description="archived ? undefined : 'Create your first test.'"
      selectable
      @retry="list.refresh"
    >
      <template #bulk>
        <UButton :label="archived ? 'Restore' : 'Archive'" color="neutral" variant="outline" @click="archive(selected, !archived)" />
      </template>
    </DataTable>
    <UPagination
      v-if="(list.data.value?.total ?? 0) > PAGE_SIZE"
      v-model:page="page"
      :total="list.data.value?.total ?? 0"
      :items-per-page="PAGE_SIZE"
    />
  </div>
</template>
