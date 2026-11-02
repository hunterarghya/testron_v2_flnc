<!-- Every list screen's table, with its loading, empty and error states (frontend_spec.md §2).
     Sorting, selection and the bulk bar are added with the first screen that needs them. -->
<script setup lang="ts" generic="Row">
import type { TableColumn } from '@nuxt/ui'
import type { ApiProblem } from '~/api/problems'
import ErrorState from '~/shared/components/ErrorState.vue'

defineProps<{
  rows: Row[]
  columns: TableColumn<Row>[]
  loading?: boolean
  error?: ApiProblem | null
  emptyTitle: string
  emptyDescription?: string
}>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <ErrorState v-if="error" :problem="error" @retry="emit('retry')" />
  <UTable v-else :data="rows" :columns="columns" :loading="loading">
    <template #empty>
      <UEmpty icon="i-lucide-inbox" :title="emptyTitle" :description="emptyDescription" />
    </template>
  </UTable>
</template>
