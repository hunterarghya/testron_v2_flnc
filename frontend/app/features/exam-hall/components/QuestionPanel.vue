<!-- The current question (P-03/04/05): its number, marks, stem and answer, then Clear, Mark
     for review and the moves. Total timer: Prev/Next. Sections: also "Next section", or
     Submit in the last one. Rapid fire: only Next, which locks the answer; no going back.
     Moving never loses an answer: each change is already queued. -->
<script setup lang="ts">
import { computed } from 'vue'
import type { HallAnswer } from '~/api/types'
import AnswerChoices from '~/features/exam-hall/components/AnswerChoices.vue'
import NumericAnswer from '~/features/exam-hall/components/NumericAnswer.vue'
import { useHall } from '~/features/exam-hall/composables/useExamSession'
import RichContentView from '~/shared/components/rich-content/RichContentView.vue'
import { formatDecimal } from '~/shared/utils/decimals'

const props = defineProps<{ kind: string, lastStage: boolean, moving: boolean }>()
const emit = defineEmits<{ nextStage: [], submit: [] }>()

const hall = useHall()
const question = computed(() => hall.current.value)
const saved = computed(() => (question.value ? hall.responses.value[question.value.id] : undefined))
const answer = computed(() => saved.value?.answer ?? null)
const inStage = computed(() => hall.questions.value.length)
const rapid = computed(() => props.kind === 'PER_QUESTION')
const heading = computed(() => {
  const state = hall.state.value
  if (!question.value || !state) return ''
  if (props.kind === 'SECTIONED') return `S${state.current_stage_index + 1} · Q ${hall.position.value + 1} of ${inStage.value}`
  return `Q ${question.value.number} of ${rapid.value ? state.stage_meta.length : inStage.value}`
})
const lastInStage = computed(() => hall.position.value >= inStage.value - 1)

function change(value: HallAnswer | null): void {
  if (question.value) hall.answer(question.value.id, value, question.value.type === 'NUMERICAL')
}

function onward(): void {
  if (props.lastStage) emit('submit')
  else emit('nextStage')
}
</script>

<template>
  <section v-if="question" class="flex flex-col gap-4 p-4 sm:p-6" :aria-label="`Question ${question.number}`">
    <div class="flex items-center justify-between gap-2 text-sm">
      <span class="font-medium">{{ heading }}</span>
      <span class="text-muted">+{{ formatDecimal(question.marks) }} / −{{ formatDecimal(question.negative_marks) }}</span>
    </div>
    <RichContentView :doc="question.stem" eager-images />
    <NumericAnswer v-if="question.type === 'NUMERICAL'" :key="question.id" :answer="answer" @change="change" />
    <AnswerChoices v-else :question="question" :answer="answer" @change="change" />
    <div class="mt-auto flex flex-wrap items-center gap-2 pt-4">
      <UButton label="Clear" color="neutral" variant="outline" :disabled="!answer" @click="change(null)" />
      <UButton
        v-if="!rapid"
        icon="i-lucide-flag"
        :label="saved?.marked_for_review ? 'Unmark' : 'Mark for review'"
        color="neutral"
        :variant="saved?.marked_for_review ? 'soft' : 'outline'"
        @click="hall.toggleMark(question.id)"
      />
      <div class="ms-auto flex flex-wrap gap-2">
        <template v-if="!rapid">
          <UButton icon="i-lucide-chevron-left" label="Prev" color="neutral" variant="outline" :disabled="hall.position.value === 0" @click="hall.goTo(hall.position.value - 1)" />
          <UButton trailing-icon="i-lucide-chevron-right" label="Next" :disabled="lastInStage" @click="hall.goTo(hall.position.value + 1)" />
        </template>
        <UButton
          v-if="kind !== 'TOTAL'"
          :label="lastStage ? 'Submit' : (rapid ? 'Next' : 'Next section')"
          :trailing-icon="lastStage ? undefined : 'i-lucide-chevrons-right'"
          :loading="moving"
          @click="onward"
        />
      </div>
    </div>
  </section>
</template>
