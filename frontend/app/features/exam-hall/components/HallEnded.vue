<!-- P-07 Submitted, and its variants (time's up, ended by the teacher, …). Never a score:
     results come when the teacher publishes them [F-6, H-1]. Also the "taken over" screen:
     the test was opened on another device, which now owns it (frontend_spec.md §5.7). -->
<script setup lang="ts">
import { computed } from 'vue'
import type { Ending } from '~/features/exam-hall/composables/useExamSession'
import { ENDING_TITLE } from '~/features/exam-hall/utils/hall-text'
import { formatDateTime } from '~/shared/utils/time'

const props = defineProps<{ title: string, ending: Ending | null }>()

const heading = computed(() => (props.ending ? ENDING_TITLE[props.ending.reason] : 'This test was opened on another device'))
const disqualified = computed(() => props.ending?.reason === 'DISQUALIFIED')
</script>

<template>
  <UContainer class="flex min-h-screen items-center justify-center py-10">
    <UCard class="w-full max-w-md text-center">
      <div class="space-y-3">
        <UIcon
          :name="ending ? (disqualified ? 'i-lucide-ban' : 'i-lucide-circle-check') : 'i-lucide-monitor-smartphone'"
          class="size-10"
          :class="ending && !disqualified ? 'text-success' : 'text-muted'"
        />
        <h1 class="text-xl font-semibold">
          {{ heading }}
        </h1>
        <p class="font-medium">
          {{ title }}
        </p>
        <p v-if="ending" class="text-sm text-muted">
          {{ formatDateTime(ending.endedAt) }}
        </p>
        <p class="text-sm">
          {{ ending ? 'Results will be published by your teacher.' : 'Continue there. Your saved answers are safe.' }}
        </p>
        <UButton label="Back to My Tests" to="/" />
      </div>
    </UCard>
  </UContainer>
</template>
