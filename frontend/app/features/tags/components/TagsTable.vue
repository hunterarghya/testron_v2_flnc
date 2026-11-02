<!-- T-18 Tags (housekeeping only): tags are created in the editor; here they are renamed
     (or merged) and deleted everywhere at once. -->
<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { computed, h, onMounted, ref } from 'vue'
import { useToast } from '#imports'
import { UButton } from '#components'
import { problemMessage } from '~/api/problem-messages'
import { toProblem } from '~/api/problems'
import type { TagUsage } from '~/api/types'
import RenameTagDialog from '~/features/tags/components/RenameTagDialog.vue'
import { useTags } from '~/features/tags/composables/useTags'
import ConfirmDialog from '~/shared/components/ConfirmDialog.vue'
import DataTable from '~/shared/components/DataTable.vue'

const toast = useToast()
const { kind, filter, all, counts, shown, rename, remove } = useTags()
const renaming = ref<TagUsage | null>(null)
const deleting = ref<TagUsage | null>(null)
const pending = ref(false)
const renameOpen = computed({ get: () => renaming.value !== null, set: (open) => { if (!open) renaming.value = null } })
const deleteOpen = computed({ get: () => deleting.value !== null, set: (open) => { if (!open) deleting.value = null } })
const tabs = computed(() => [
  { value: 'CHAPTER', label: 'Chapters', badge: counts.value.CHAPTER },
  { value: 'TOPIC', label: 'Topics', badge: counts.value.TOPIC },
])
const columns = computed<TableColumn<TagUsage>[]>(() => [
  { accessorKey: 'name', header: kind.value === 'CHAPTER' ? 'Chapter' : 'Topic' },
  { accessorKey: 'question_count', header: 'Questions' },
  { accessorKey: 'test_count', header: 'Tests' },
  {
    id: 'actions',
    header: '',
    cell: ({ row }) => h('div', { class: 'flex justify-end gap-1' }, [
      h(UButton, { label: 'Rename', icon: 'i-lucide-pencil', size: 'sm', color: 'neutral', variant: 'ghost', onClick: () => (renaming.value = row.original) }),
      h(UButton, { 'icon': 'i-lucide-trash-2', 'size': 'sm', 'color': 'error', 'variant': 'ghost', 'aria-label': `Delete ${row.original.name}`, 'onClick': () => (deleting.value = row.original) }),
    ]),
  },
])

async function onDelete(): Promise<void> {
  const tag = deleting.value
  if (!tag) {
    return
  }
  pending.value = true
  try {
    const removed = await remove(tag.id)
    toast.add({ title: `${tag.name} deleted from ${removed} question${removed === 1 ? '' : 's'}`, color: 'success' })
  }
  catch (caught) {
    toast.add({ title: problemMessage(toProblem(caught)), color: 'error' })
  }
  finally {
    pending.value = false
    deleting.value = null
  }
}

onMounted(all.refresh)
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <UTabs v-model="kind" :items="tabs" :content="false" />
      <UInput v-model="filter" icon="i-lucide-search" placeholder="Filter…" class="w-full max-w-xs" aria-label="Filter tags" />
    </div>
    <DataTable
      :rows="shown"
      :columns="columns"
      :loading="all.pending.value"
      :error="all.error.value"
      empty-title="No tags here."
      empty-description="Tags are created in the question editor, by typing a new one."
      @retry="all.refresh"
    />
    <RenameTagDialog v-model:open="renameOpen" :tag="renaming" :rename="rename" />
    <ConfirmDialog
      v-model:open="deleteOpen"
      :title="`Delete ${deleting?.name ?? ''}?`"
      :description="`It is removed from ${deleting?.question_count ?? 0} questions. Questions and results stay; this tag disappears from performance reports.`"
      confirm-label="Delete tag"
      danger
      :pending="pending"
      @confirm="onDelete"
    />
  </div>
</template>
