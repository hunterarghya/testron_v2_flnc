<!-- One question as a student sees it, for the preview; with answers on, the correct options,
     the numerical answer and the solution show too. -->
<script setup lang="ts">
import { computed } from 'vue'
import type { components } from '~/api/schema'
import RichContentView from '~/shared/components/rich-content/RichContentView.vue'
import { formatDecimal } from '~/shared/utils/decimals'

type Schemas = components['schemas']

const props = defineProps<{ question: Schemas['PreviewQuestionOut'], answer?: Schemas['PreviewAnswerOut'] }>()

const correct = computed(() => new Set(props.answer?.correct_option_ids ?? []))
const marks = computed(() => `+${formatDecimal(props.question.marks)} / −${formatDecimal(props.question.negative_marks)}`)
</script>

<template>
  <article class="space-y-3 rounded-lg border border-default p-4">
    <header class="flex items-center gap-2 text-sm text-muted">
      <span class="font-semibold text-default">Question {{ question.number }}</span>
      <span>{{ question.type === 'MSQ' ? 'One or more correct (partial marks; a wrong pick costs the penalty)' : question.type === 'MCQ' ? 'One correct' : 'Type a number' }}</span>
      <span class="ms-auto">{{ marks }}</span>
      <span v-if="question.time_s">· {{ question.time_s }} s</span>
    </header>
    <RichContentView :doc="question.stem" eager-images />
    <ul v-if="question.options.length" class="space-y-2">
      <li
        v-for="option in question.options"
        :key="option.id"
        class="flex gap-3 rounded-md border p-2"
        :class="correct.has(option.id) ? 'border-success bg-success/10' : 'border-default'"
      >
        <span class="font-semibold">{{ option.label }}</span>
        <RichContentView :doc="option.content" class="flex-1" />
        <UIcon v-if="correct.has(option.id)" name="i-lucide-check" class="size-5 text-success" aria-label="Correct" />
      </li>
    </ul>
    <UInput v-else disabled placeholder="Answer" class="w-48" aria-label="Answer box" />
    <div v-if="answer" class="space-y-1 rounded-md bg-elevated p-3 text-sm">
      <p v-if="answer.numeric_answer !== null">
        Answer: <strong>{{ formatDecimal(answer.numeric_answer) }}</strong>
        <span v-if="Number(answer.numeric_tolerance) > 0"> (± {{ formatDecimal(answer.numeric_tolerance) }})</span>
      </p>
      <template v-if="answer.solution">
        <p class="font-medium">Solution</p>
        <RichContentView :doc="answer.solution" />
      </template>
      <p v-if="answer.numeric_answer === null && !answer.solution && !correct.size" class="text-muted">No answer set yet.</p>
    </div>
  </article>
</template>
