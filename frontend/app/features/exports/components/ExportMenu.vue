<!-- T-11 Export ▾ [H-5, H-6]: the answer key and the answer sheets as self-contained HTML,
     built in this browser (ADR-019). With students selected, only their sheets go in the ZIP.
     Building many sheets shows "12 / 42". -->
<script setup lang="ts">
import { computed } from 'vue'
import { toProblem } from '~/api/problems'
import { problemMessage } from '~/api/problem-messages'
import { useExports } from '~/features/exports/composables/useExports'

const props = defineProps<{ assignmentId: string, title: string, attemptIds?: string[] }>()

const exports = useExports()
const toast = useToast()
const chosen = computed(() => props.attemptIds?.length ?? 0)

async function run(work: () => Promise<void>): Promise<void> {
  try {
    await work()
  }
  catch (error) {
    toast.add({ title: problemMessage(toProblem(error)), color: 'error' })
  }
}

const items = computed(() => [
  { label: 'Answer key (HTML)', icon: 'i-lucide-key-round', onSelect: () => run(() => exports.downloadKey(props.assignmentId, props.title)) },
  {
    label: chosen.value ? `Answer sheets of ${chosen.value} selected (ZIP)` : 'All answer sheets (ZIP)',
    icon: 'i-lucide-file-archive',
    onSelect: () => run(() => exports.downloadSheets(props.assignmentId, props.title, props.attemptIds)),
  },
])
</script>

<template>
  <UDropdownMenu :items="items">
    <UButton label="Export" icon="i-lucide-download" trailing-icon="i-lucide-chevron-down" color="neutral" variant="outline" :loading="exports.progress.value !== null" />
  </UDropdownMenu>
  <UModal :open="exports.progress.value !== null" title="Building answer sheets" :dismissible="false">
    <template #body>
      <UProgress :model-value="exports.progress.value?.done ?? 0" :max="exports.progress.value?.total || 1" />
      <p class="mt-2 text-center text-sm">
        {{ exports.progress.value?.done }} / {{ exports.progress.value?.total }}
      </p>
    </template>
  </UModal>
</template>
