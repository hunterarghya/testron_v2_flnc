<!-- T-17 "Add students": search the active students and tick the ones to add. Students
     already in the group are left out of the list. -->
<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { computed, ref, watch } from 'vue'
import { api, unwrap } from '~/api/client'
import type { StudentRow } from '~/api/types'
import DataTable from '~/shared/components/DataTable.vue'
import { useApiData } from '~/shared/composables/useApiData'

const SEARCH_DELAY_MS = 300
// Enough to find anyone by typing; the teacher searches rather than scrolls
const SHOWN = 50

const props = defineProps<{ memberIds: string[], pending?: boolean }>()
const open = defineModel<boolean>('open', { required: true })
const emit = defineEmits<{ add: [studentIds: string[]] }>()

const search = ref('')
const selected = ref<string[]>([])
const found = useApiData(() => unwrap(api.GET('/api/v1/admin/students', {
  params: { query: { status: 'ACTIVE', q: search.value.trim() || undefined, page_size: SHOWN } },
})))
const rows = computed(() => (found.data.value?.items ?? []).filter(row => !props.memberIds.includes(row.id)))
const columns: TableColumn<StudentRow>[] = [
  { accessorKey: 'name', header: 'Name' },
  { accessorKey: 'email', header: 'Email' },
]

watch(open, (isOpen) => {
  if (isOpen) {
    search.value = ''
    selected.value = []
    void found.refresh()
  }
})
let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => void found.refresh(), SEARCH_DELAY_MS)
})
</script>

<template>
  <UModal v-model:open="open" title="Add students" description="Only active students can join a group." :ui="{ content: 'max-w-2xl' }">
    <template #body>
      <div class="space-y-3">
        <UInput v-model="search" icon="i-lucide-search" placeholder="Search name or email" class="w-full" aria-label="Search students" />
        <DataTable
          v-model:selected="selected"
          :rows="rows"
          :columns="columns"
          :loading="found.pending.value"
          :error="found.error.value"
          empty-title="No students to add."
          selectable
          @retry="found.refresh"
        />
      </div>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="ghost" @click="open = false" />
        <UButton
          :label="selected.length ? `Add ${selected.length}` : 'Add'"
          :disabled="!selected.length"
          :loading="pending"
          @click="emit('add', selected)"
        />
      </div>
    </template>
  </UModal>
</template>
