<!-- T-07 ② Students [D-1]: groups fill the list; the teacher unticks anyone to leave out
     and adds individuals. The ticked list is what's saved. -->
<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { computed, onMounted, ref } from 'vue'
import { type AudienceEntry, selectionSummary } from '~/features/assignments/utils/audience'
import DataTable from '~/shared/components/DataTable.vue'
import PickStudentsDialog from '~/shared/components/PickStudentsDialog.vue'
import { useActiveGroups } from '~/shared/composables/useActiveGroups'

interface Row { id: string, name: string, groups: string, note: string }

const props = defineProps<{ groupIds: string[] }>()
const audience = defineModel<AudienceEntry[]>('audience', { required: true })
const emit = defineEmits<{ pickGroups: [ids: string[]], add: [students: { id: string, name: string }[]] }>()

const groups = useActiveGroups()
const groupItems = computed(() => (groups.data.value ?? []).map(group => ({
  value: group.id,
  label: `${group.name} (${group.member_count})`,
})))
const pickedGroups = computed({
  get: () => props.groupIds,
  set: (ids: string[]) => emit('pickGroups', ids),
})
const filter = ref('')
const adding = ref(false)
const rows = computed<Row[]>(() => audience.value
  .filter(entry => entry.name.toLowerCase().includes(filter.value.trim().toLowerCase()))
  .map(entry => ({
    id: entry.studentId,
    name: entry.name,
    groups: entry.individual ? '– (added)' : entry.groupNames.join(', '),
    note: noteFor(entry),
  })))
const ticked = computed({
  get: () => audience.value.filter(entry => entry.ticked).map(entry => entry.studentId),
  set: (ids: string[]) => {
    audience.value = audience.value.map(entry => ({ ...entry, ticked: ids.includes(entry.studentId) }))
  },
})
const columns: TableColumn<Row>[] = [
  { accessorKey: 'name', header: 'Name' },
  { accessorKey: 'groups', header: 'Groups' },
  { accessorKey: 'note', header: '' },
]

function noteFor(entry: AudienceEntry): string {
  if (!entry.ticked) return 'left out'
  if (entry.individual) return 'individual'
  return entry.groupNames.length > 1 ? `in ${entry.groupNames.length} groups (once)` : ''
}

function setAll(on: boolean): void {
  audience.value = audience.value.map(entry => ({ ...entry, ticked: on }))
}

onMounted(() => groups.refresh())
</script>

<template>
  <div class="space-y-6">
    <UFormField label="1. Pick groups (any number)">
      <UCheckboxGroup v-model="pickedGroups" :items="groupItems" orientation="horizontal" class="flex-wrap" />
    </UFormField>
    <div class="space-y-3">
      <div class="flex flex-wrap items-center gap-3">
        <h3 class="font-medium">
          2. Confirm students
        </h3>
        <UInput v-model="filter" icon="i-lucide-search" placeholder="Filter…" aria-label="Filter students" class="w-56" />
        <UButton icon="i-lucide-plus" label="Add students" variant="outline" @click="adding = true" />
      </div>
      <DataTable
        v-model:selected="ticked"
        :rows="rows"
        :columns="columns"
        empty-title="Pick a group or add students."
        selectable
      />
      <div class="flex flex-wrap items-center gap-2 text-sm text-muted">
        <UButton label="Select all" size="xs" variant="ghost" @click="setAll(true)" />
        <UButton label="Select none" size="xs" variant="ghost" @click="setAll(false)" />
        <span class="ms-auto">{{ selectionSummary(audience) }}</span>
      </div>
    </div>
    <PickStudentsDialog
      v-model:open="adding"
      :member-ids="audience.map(entry => entry.studentId)"
      description="Add students from outside the picked groups."
      @add="students => { emit('add', students); adding = false }"
    />
  </div>
</template>
