<!-- Every list screen's table, with its loading, empty and error states (frontend_spec.md §2).
     With `selectable`, a checkbox column picks rows by id and the `bulk` slot shows a bar of
     actions for the selection (screens.md §0.1). -->
<script setup lang="ts" generic="Row extends { id: string }">
import type { TableColumn } from '@nuxt/ui'
import { computed, h } from 'vue'
import { UCheckbox } from '#components'
import type { ApiProblem } from '~/api/problems'
import ErrorState from '~/shared/components/ErrorState.vue'

const props = defineProps<{
  rows: Row[]
  columns: TableColumn<Row>[]
  loading?: boolean
  error?: ApiProblem | null
  emptyTitle: string
  emptyDescription?: string
  selectable?: boolean
}>()
const selected = defineModel<string[]>('selected', { default: () => [] })
const emit = defineEmits<{ retry: [] }>()

const allSelected = computed(
  () => props.rows.length > 0 && props.rows.every(row => selected.value.includes(row.id)),
)

function toggle(id: string, on: boolean): void {
  selected.value = on ? [...new Set([...selected.value, id])] : selected.value.filter(other => other !== id)
}

function toggleAll(on: boolean): void {
  const ids = props.rows.map(row => row.id)
  selected.value = on
    ? [...new Set([...selected.value, ...ids])]
    : selected.value.filter(id => !ids.includes(id))
}

const selectColumn: TableColumn<Row> = {
  id: 'select',
  header: () => h(UCheckbox, {
    'modelValue': allSelected.value,
    'aria-label': 'Select all on this page',
    'onUpdate:modelValue': (on: unknown) => toggleAll(on === true),
  }),
  cell: ({ row }) => h(UCheckbox, {
    'modelValue': selected.value.includes(row.original.id),
    'aria-label': 'Select row',
    'onUpdate:modelValue': (on: unknown) => toggle(row.original.id, on === true),
  }),
}
const shownColumns = computed(() => (props.selectable ? [selectColumn, ...props.columns] : props.columns))
</script>

<template>
  <ErrorState v-if="error" :problem="error" @retry="emit('retry')" />
  <div v-else class="space-y-2">
    <div
      v-if="selectable && selected.length > 0"
      class="flex flex-wrap items-center gap-2 rounded-md bg-elevated px-3 py-2"
    >
      <span class="text-sm font-medium">Selected {{ selected.length }}:</span>
      <slot name="bulk" :selected="selected" />
    </div>
    <UTable :data="rows" :columns="shownColumns" :loading="loading">
      <template #empty>
        <UEmpty icon="i-lucide-inbox" :title="emptyTitle" :description="emptyDescription" />
      </template>
    </UTable>
  </div>
</template>
