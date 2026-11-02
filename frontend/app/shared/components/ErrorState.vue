<!-- What went wrong, a reference code to quote, and a way to try again (screens.md §6) -->
<script setup lang="ts">
import { computed } from 'vue'
import { problemMessage } from '~/api/problem-messages'
import type { ApiProblem } from '~/api/problems'

const props = defineProps<{ problem: ApiProblem }>()
const emit = defineEmits<{ retry: [] }>()

const description = computed(() =>
  props.problem.traceId ? `Reference code: ${props.problem.traceId}` : undefined,
)
const actions = [{ label: 'Try again', icon: 'i-lucide-rotate-cw', onClick: () => emit('retry') }]
</script>

<template>
  <UEmpty
    icon="i-lucide-triangle-alert"
    :title="problemMessage(problem)"
    :description="description"
    :actions="actions"
  />
</template>
