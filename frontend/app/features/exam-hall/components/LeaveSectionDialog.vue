<!-- P-04's transition dialog when a student moves on early: what's answered in this
     section, and whether they can come back (only while its timer runs, if allowed). -->
<script setup lang="ts">
import { computed } from 'vue'
import { formatCountdown } from '~/engine/clock'
import { useHall } from '~/features/exam-hall/composables/useExamSession'
import { hasAnswer } from '~/features/exam-hall/utils/palette'

const props = defineProps<{ remainingMs: number, moving: boolean }>()
defineEmits<{ go: [] }>()
const open = defineModel<boolean>('open', { required: true })

const hall = useHall()
const names = computed(() => {
  const state = hall.state.value
  const name = (index: number) => state?.stage_meta[index]?.title ?? `Section ${index + 1}`
  const current = state?.current_stage_index ?? 0
  return { here: `Section ${current + 1}: ${name(current)}`, next: `Section ${current + 2}` }
})
const answered = computed(() => hall.questions.value.filter(q => hasAnswer(hall.responses.value[q.id]?.answer)).length)
const total = computed(() => hall.questions.value.length)
const comeBack = computed(() => (hall.state.value?.timing.allow_return
  ? `You can come back until its timer ends (${formatCountdown(props.remainingMs)}).`
  : 'You can\'t come back to this section.'))
</script>

<template>
  <UModal v-model:open="open" :title="`Leave ${names.here}?`">
    <template #body>
      <p class="text-sm">
        Answered {{ answered }} of {{ total }} · {{ total - answered }} unanswered
      </p>
      <UAlert class="mt-3" color="warning" variant="subtle" icon="i-lucide-triangle-alert" :title="comeBack" />
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Stay" color="neutral" variant="outline" @click="open = false" />
        <UButton :label="`Go to ${names.next}`" trailing-icon="i-lucide-chevron-right" :loading="moving" @click="$emit('go')" />
      </div>
    </template>
  </UModal>
</template>
