<!-- P-06: the student left the test (fullscreen, the tab or the window) for longer than the
     grace period. It covers the question; the timer keeps running. The count is the
     server's. "Return to test" goes back to fullscreen. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useHall } from '~/features/exam-hall/composables/useExamSession'
import { warningText } from '~/features/exam-hall/utils/hall-text'

defineEmits<{ return: [] }>()

const hall = useHall()
const text = computed(() => {
  const state = hall.state.value
  const count = hall.clock.value?.warning_count ?? 0
  return state && count > 0 ? warningText(count, state.integrity.max_warnings, state.integrity.action) : null
})
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-default/95 p-6" role="alertdialog" aria-labelledby="integrity-title">
    <UCard class="w-full max-w-lg">
      <div class="space-y-3 text-center">
        <UIcon name="i-lucide-triangle-alert" class="size-10 text-warning" />
        <h2 id="integrity-title" class="text-lg font-semibold">
          You left the test
        </h2>
        <p>Leaving fullscreen or switching apps is not allowed.</p>
        <p v-if="text" class="font-medium">
          {{ text }}
        </p>
        <UButton size="xl" icon="i-lucide-maximize" label="Return to test (fullscreen)" @click="$emit('return')" />
      </div>
    </UCard>
  </div>
</template>
