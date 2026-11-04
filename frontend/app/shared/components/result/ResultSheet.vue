<!-- A result, P-09 for the student and T-12 for the teacher (screens.md: "the same component"):
     the score, rank and class average when shown, the time, section scores, the chapter and
     topic breakdown, then the questions with a filter. What it gets is already filtered by
     the publish options; it shows whatever is there. -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Result } from '~/api/types'
import ResultQuestionCard from '~/shared/components/result/ResultQuestionCard.vue'
import { formatDecimal } from '~/shared/utils/decimals'
import { headerFacts, matches, percent, type QuestionFilter, scoreText } from '~/shared/utils/result-text'

// printable: for an exported file, every question, no filter buttons, solutions shown
const props = defineProps<{ result: Result, disqualified?: boolean, printable?: boolean }>()

const filter = ref<QuestionFilter>('all')
const FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'wrong', label: 'Wrong' },
  { value: 'unanswered', label: 'Unanswered' },
]
const questions = computed(() => (props.result.questions ?? []).filter(q => matches(q, filter.value)))
const chapters = computed(() => props.result.tags.filter(t => t.kind === 'CHAPTER'))
const topics = computed(() => props.result.tags.filter(t => t.kind === 'TOPIC'))
</script>

<template>
  <div class="space-y-4">
    <UCard>
      <div class="space-y-3">
        <div class="flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <p v-if="disqualified" class="text-2xl font-semibold text-error">
            Disqualified
          </p>
          <p v-else class="text-2xl font-semibold">
            {{ scoreText(result.score, result.max_score) }}
          </p>
          <span v-for="fact in headerFacts(result)" :key="fact" class="text-sm text-muted">{{ fact }}</span>
        </div>
        <p v-if="result.sections.length > 1 && !disqualified" class="text-sm">
          Sections:
          <span v-for="(part, i) in result.sections" :key="part.title">{{ i ? ' · ' : '' }}{{ part.title }} {{ formatDecimal(part.score) }}/{{ formatDecimal(part.max) }}</span>
        </p>
        <div v-for="group in [{ name: 'Chapters', tags: chapters }, { name: 'Topics', tags: topics }]" :key="group.name">
          <div v-if="group.tags.length && !disqualified" class="space-y-1">
            <p class="text-sm font-medium">
              {{ group.name }}
            </p>
            <div v-for="tag in group.tags" :key="tag.id" class="flex items-center gap-2 text-sm">
              <span class="w-40 truncate">{{ tag.name }}</span>
              <UProgress :model-value="Math.max(0, percent(tag.score, tag.max))" class="flex-1" size="sm" />
              <span class="w-12 text-end font-mono">{{ percent(tag.score, tag.max) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </UCard>
    <template v-if="result.questions">
      <div v-if="!printable" class="flex flex-wrap items-center gap-2">
        <span class="text-sm text-muted">Filter</span>
        <UButton
          v-for="option in FILTERS"
          :key="option.value"
          :label="option.label"
          size="sm"
          :variant="filter === option.value ? 'solid' : 'outline'"
          color="neutral"
          @click="filter = option.value as QuestionFilter"
        />
      </div>
      <ResultQuestionCard v-for="question in questions" :key="question.id" :question="question" :printable="printable">
        <template #actions>
          <slot name="question-actions" :question="question" />
        </template>
      </ResultQuestionCard>
    </template>
  </div>
</template>
