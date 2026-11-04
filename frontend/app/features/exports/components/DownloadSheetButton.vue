<!-- T-12 Download: this answer sheet as one self-contained HTML file [H-5, H-6]. -->
<script setup lang="ts">
import { ref } from 'vue'
import type { AnswerSheet } from '~/api/types'
import { useExports } from '~/features/exports/composables/useExports'

const props = defineProps<{ sheet: AnswerSheet }>()

const exports = useExports()
const busy = ref(false)

async function download(): Promise<void> {
  busy.value = true
  try {
    await exports.downloadSheet(props.sheet)
  }
  finally {
    busy.value = false
  }
}
</script>

<template>
  <UButton label="Download" icon="i-lucide-download" color="neutral" variant="outline" :loading="busy" @click="download" />
</template>
