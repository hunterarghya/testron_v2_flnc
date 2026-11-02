<!-- T-16 Groups: search, archived ones on request, new group, archive and restore. Archiving
     hides a group from pickers; its members and history stay (domain_model.md [B-1]). -->
<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { h, onMounted, ref, watch } from 'vue'
import { useToast } from '#imports'
import { UButton, ULink } from '#components'
import { problemMessage } from '~/api/problem-messages'
import { toProblem } from '~/api/problems'
import type { Group } from '~/api/types'
import GroupFormDialog from '~/features/groups/components/GroupFormDialog.vue'
import { listGroups, setArchived } from '~/features/groups/composables/groupsApi'
import DataTable from '~/shared/components/DataTable.vue'
import { useApiData } from '~/shared/composables/useApiData'

const SEARCH_DELAY_MS = 300

const toast = useToast()
const archived = ref(false)
const search = ref('')
const creating = ref(false)
const list = useApiData(() => listGroups(archived.value, search.value))

const columns: TableColumn<Group>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => h(ULink, { to: `/admin/groups/${row.original.id}`, class: 'font-medium' }, () => row.original.name),
  },
  { accessorKey: 'member_count', header: 'Students' },
  { accessorKey: 'description', header: 'Description' },
  {
    id: 'actions',
    header: '',
    cell: ({ row }) => h(UButton, {
      label: row.original.archived_at ? 'Restore' : 'Archive',
      color: 'neutral',
      variant: 'ghost',
      size: 'sm',
      onClick: () => toggleArchived(row.original),
    }),
  },
]

async function toggleArchived(group: Group): Promise<void> {
  try {
    await setArchived(group.id, !group.archived_at)
    toast.add({ title: `${group.name} ${group.archived_at ? 'restored' : 'archived'}`, color: 'success' })
    await list.refresh()
  }
  catch (caught) {
    toast.add({ title: problemMessage(toProblem(caught)), color: 'error' })
  }
}

async function onCreated(group: Group): Promise<void> {
  toast.add({ title: `${group.name} created`, color: 'success' })
  await list.refresh()
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => void list.refresh(), SEARCH_DELAY_MS)
})
watch(archived, () => list.refresh())
onMounted(list.refresh)
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <UInput v-model="search" icon="i-lucide-search" placeholder="Search groups" class="w-full max-w-xs" aria-label="Search groups" />
      <USwitch v-model="archived" label="Show archived" />
      <UButton label="New group" icon="i-lucide-plus" class="ms-auto" @click="creating = true" />
    </div>
    <DataTable
      :rows="list.data.value ?? []"
      :columns="columns"
      :loading="list.pending.value"
      :error="list.error.value"
      :empty-title="archived ? 'No archived groups.' : 'No groups yet.'"
      :empty-description="archived ? undefined : 'Create one for each class or batch.'"
      @retry="list.refresh"
    />
    <GroupFormDialog v-model:open="creating" @saved="onCreated" />
  </div>
</template>
