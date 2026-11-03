<!-- The current question (P-03): its number, marks, stem and answer, then Clear, Mark for
     review, Prev and Next. Moving never loses an answer: each change is already queued. -->
<script setup lang="ts">
import { computed } from 'vue'
import type { HallAnswer } from '~/api/types'
import AnswerChoices from '~/features/exam-hall/components/AnswerChoices.vue'
import NumericAnswer from '~/features/exam-hall/components/NumericAnswer.vue'
import { useHall } from '~/features/exam-hall/composables/useExamSession'
import RichContentView from '~/shared/components/rich-content/RichContentView.vue'
import { formatDecimal } from '~/shared/utils/decimals'

const hall = useHall()
const question = computed(() => hall.current.value)
const saved = computed(() => (question.value ? hall.responses.value[question.value.id] : undefined))
const answer = computed(() => saved.value?.answer ?? null)
const total = computed(() => hall.questions.value.length)

function change(value: HallAnswer | null): void {
  if (question.value) hall.answer(question.value.id, value, question.value.type === 'NUMERICAL')
}
</script>

<template>
  <section v-if="question" class="flex flex-col gap-4 p-4 sm:p-6" :aria-label="`Question ${question.number}`">
    <div class="flex items-center justify-between gap-2 text-sm">
      <span class="font-medium">Q {{ question.number }} of {{ total }}</span>
      <span class="text-muted">+{{ formatDecimal(question.marks) }} / −{{ formatDecimal(question.negative_marks) }}</span>
    </div>
    <RichContentView :doc="question.stem" eager-images />
    <NumericAnswer v-if="question.type === 'NUMERICAL'" :key="question.id" :answer="answer" @change="change" />
    <AnswerChoices v-else :question="question" :answer="answer" @change="change" />
    <div class="mt-auto flex flex-wrap items-center gap-2 pt-4">
      <UButton label="Clear" color="neutral" variant="outline" :disabled="!answer" @click="change(null)" />
      <UButton
        icon="i-lucide-flag"
        :label="saved?.marked_for_review ? 'Unmark' : 'Mark for review'"
        color="neutral"
        :variant="saved?.marked_for_review ? 'soft' : 'outline'"
        @click="hall.toggleMark(question.id)"
      />
      <div class="ms-auto flex gap-2">
        <UButton icon="i-lucide-chevron-left" label="Prev" color="neutral" variant="outline" :disabled="hall.position.value === 0" @click="hall.goTo(hall.position.value - 1)" />
        <UButton trailing-icon="i-lucide-chevron-right" label="Next" :disabled="hall.position.value >= total - 1" @click="hall.goTo(hall.position.value + 1)" />
      </div>
    </div>
  </section>
</template>
