<!-- The question palette (P-03): jump to any question, see which are answered, seen, or
     marked, and the legend's counts. A side panel on laptops, a bottom sheet on phones. -->
<script setup lang="ts">
import { computed } from 'vue'
import { useHall } from '~/features/exam-hall/composables/useExamSession'
import { PALETTE_LEGEND, type PaletteMark, paletteCounts, paletteMark } from '~/features/exam-hall/utils/palette'

const emit = defineEmits<{ picked: [] }>()
const hall = useHall()

const COLOR: Record<PaletteMark, 'success' | 'neutral' | 'warning' | 'info'> = {
  answered: 'success',
  not_visited: 'neutral',
  not_answered: 'warning',
  marked: 'info',
}
const ids = computed(() => hall.questions.value.map(q => q.id))
const counts = computed(() => paletteCounts(ids.value, hall.responses.value))

function pick(index: number): void {
  hall.goTo(index)
  emit('picked')
}
</script>

<template>
  <nav class="space-y-4 p-4" aria-label="Questions">
    <h2 class="text-sm font-medium">
      Questions
    </h2>
    <div class="grid grid-cols-6 gap-2">
      <UButton
        v-for="(question, index) in hall.questions.value"
        :key="question.id"
        :label="String(question.number)"
        :aria-label="`Question ${question.number}, ${paletteMark(hall.responses.value[question.id]).replace('_', ' ')}`"
        :aria-current="index === hall.position.value ? 'step' : undefined"
        :color="COLOR[paletteMark(hall.responses.value[question.id])]"
        :variant="index === hall.position.value ? 'solid' : 'soft'"
        size="sm"
        class="justify-center"
        @click="pick(index)"
      />
    </div>
    <ul class="space-y-1 text-sm">
      <li v-for="entry in PALETTE_LEGEND" :key="entry.mark" class="flex items-center gap-2">
        <UIcon :name="entry.icon" class="size-4" />
        <span class="flex-1">{{ entry.label }}</span>
        <span class="font-mono">{{ counts[entry.mark] }}</span>
      </li>
    </ul>
  </nav>
</template>
