<!-- One question of a result (P-09, T-12): its number and marks, the stem, the options with
     the student's pick and the correct one marked (only when the result includes them), a
     numerical answer against the key, and the solution behind a toggle. -->
<script setup lang="ts">
import { computed } from 'vue'
import type { ResultQuestion } from '~/api/types'
import RichContentView from '~/shared/components/rich-content/RichContentView.vue'
import { formatDecimal } from '~/shared/utils/decimals'
import { givenValue, OUTCOME, pickedIds, signedMarks } from '~/shared/utils/result-text'

const props = defineProps<{ question: ResultQuestion }>()

const outcome = computed(() => (props.question.outcome ? OUTCOME[props.question.outcome] : null))
const picked = computed(() => new Set(pickedIds(props.question)))
const correct = computed(() => new Set(props.question.correct_answer?.option_ids ?? []))
const reviewed = computed(() => props.question.correct_answer != null)
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex flex-wrap items-center gap-2 text-sm">
        <span class="font-medium">Q{{ question.number }}</span>
        <UBadge
          v-if="outcome && question.marks_awarded != null"
          :icon="outcome.icon"
          :color="outcome.color"
          variant="subtle"
          :label="`${signedMarks(question.marks_awarded)} · ${outcome.label}`"
        />
        <span class="ms-auto text-muted">+{{ formatDecimal(question.marks) }} / −{{ formatDecimal(question.negative_marks) }}</span>
        <slot name="actions" />
      </div>
    </template>
    <div class="space-y-3">
      <RichContentView :doc="question.stem" />
      <ul v-if="question.options.length" class="space-y-1">
        <li
          v-for="option in question.options"
          :key="option.id"
          class="flex items-start gap-2 rounded-md border border-default p-2"
          :class="reviewed && correct.has(option.id) ? 'border-success' : ''"
        >
          <span class="font-medium">{{ option.label }}</span>
          <RichContentView :doc="option.content" class="flex-1" />
          <UBadge v-if="picked.has(option.id)" label="your answer" color="neutral" variant="outline" size="sm" />
          <UIcon v-if="reviewed && correct.has(option.id)" name="i-lucide-check" class="size-4 text-success" aria-label="Correct" />
        </li>
      </ul>
      <p v-else-if="reviewed" class="text-sm">
        Your answer <span class="font-mono">{{ givenValue(question) }}</span> · correct
        <span class="font-mono">{{ question.correct_answer?.value }}</span>
        <span v-if="question.correct_answer?.tolerance && Number(question.correct_answer.tolerance) > 0"> ± {{ question.correct_answer.tolerance }}</span>
      </p>
      <UCollapsible v-if="question.solution">
        <UButton label="Solution" icon="i-lucide-lightbulb" color="neutral" variant="link" size="sm" />
        <template #content>
          <RichContentView :doc="question.solution" class="mt-2 rounded-md bg-elevated p-3" />
        </template>
      </UCollapsible>
    </div>
  </UCard>
</template>
