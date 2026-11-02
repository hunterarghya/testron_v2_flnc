<!-- The outline (T-03, left): structure with a ⚠ on questions that have problems, live totals,
     and the problems list. Clicking a problem scrolls to it. -->
<script setup lang="ts">
import { computed } from 'vue'
import type { TestDocument, TestProblem } from '~/api/types'
import { formatDecimal } from '~/shared/utils/decimals'
import { formatDuration } from '~/shared/utils/time'

const props = defineProps<{ doc: TestDocument }>()

const sectioned = computed(() => props.doc.settings.timing.kind === 'SECTIONED')
const flagged = computed(() => new Set(props.doc.problems.map(p => p.question_id).filter(Boolean)))
const numbered = computed(() => {
  let number = 0
  return props.doc.sections.map(section => ({
    section,
    questions: section.questions.map(question => ({ id: question.id, number: ++number })),
  }))
})

function show(problem: TestProblem): void {
  const target = problem.question_id ? `question-${problem.question_id}` : problem.section_id ? `section-${problem.section_id}` : null
  if (target) document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function jump(questionId: string): void {
  document.getElementById(`question-${questionId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <nav class="space-y-4 text-sm" aria-label="Outline">
    <div v-for="({ section, questions }, s) in numbered" :key="section.id" class="space-y-1">
      <p v-if="sectioned" class="truncate font-medium">S{{ s + 1 }} {{ section.title }}</p>
      <div class="flex flex-wrap gap-1">
        <UButton
          v-for="question in questions"
          :key="question.id"
          :label="String(question.number)"
          :color="flagged.has(question.id) ? 'warning' : 'neutral'"
          :variant="flagged.has(question.id) ? 'soft' : 'ghost'"
          size="xs"
          @click="jump(question.id)"
        />
      </div>
    </div>
    <div>
      <p class="font-medium">Totals</p>
      <p class="text-muted">
        {{ doc.totals.questions }} Qs · {{ formatDecimal(doc.totals.marks) }} marks · {{ doc.totals.duration_s === null ? 'time not set' : formatDuration(doc.totals.duration_s) }}
      </p>
    </div>
    <div>
      <p class="font-medium">Problems ({{ doc.problems.length }})</p>
      <p v-if="!doc.problems.length" class="text-muted">None. This test can be assigned.</p>
      <ul v-else class="space-y-1">
        <li v-for="(problem, i) in doc.problems" :key="i">
          <UButton :label="problem.message" color="warning" variant="link" size="xs" class="text-start" @click="show(problem)" />
        </li>
      </ul>
    </div>
  </nav>
</template>
