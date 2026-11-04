<!-- D-01 Publish results [H-2]: score only or score + answer review; the paper (on by
     default with review), solutions (with review only), rank and class stats. A summary says
     what a student will see. Results show within seconds; the options can change later. -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { problemMessage } from '~/api/problem-messages'
import type { PublicationView } from '~/api/types'
import { publishResults } from '~/features/assignments/composables/resultsApi'
import { useSubmit } from '~/shared/composables/useSubmit'

const props = defineProps<{ assignmentId: string, current: PublicationView | null }>()
const emit = defineEmits<{ done: [] }>()
const open = defineModel<boolean>('open', { required: true })

const review = ref(false)
const paper = ref(false)
const solutions = ref(false)
const rank = ref(false)
const publishing = useSubmit(publishResults)
const CONTENT = [
  { value: false, label: 'Score only' },
  { value: true, label: 'Score + answer review' },
]

watch(open, (now) => {
  if (!now || !props.current) return
  review.value = props.current.content === 'ANSWER_REVIEW'
  paper.value = props.current.show_paper || review.value
  solutions.value = props.current.show_solutions
  rank.value = props.current.show_rank_and_stats
})
watch(review, (on) => {
  if (on) paper.value = true
  else solutions.value = false
})

const preview = computed(() => [
  'Their score, time, section scores and chapter breakdown',
  ...(paper.value ? ['The question paper'] : []),
  ...(review.value ? ['Their answers, the correct answers and the marks for each'] : []),
  ...(solutions.value ? ['Solutions'] : []),
  ...(rank.value ? ['Their rank and the class average'] : []),
])

async function publish(): Promise<void> {
  const done = await publishing.submit(props.assignmentId, {
    content: review.value ? 'ANSWER_REVIEW' : 'SCORE_ONLY',
    show_paper: paper.value,
    show_solutions: solutions.value,
    show_rank_and_stats: rank.value,
  })
  if (!done) return
  open.value = false
  emit('done')
}
</script>

<template>
  <UModal v-model:open="open" title="Publish results">
    <template #body>
      <div class="space-y-4">
        <URadioGroup v-model="review" :items="CONTENT" legend="Content" />
        <UCheckbox v-model="paper" label="Show the question paper" />
        <UCheckbox v-model="solutions" label="Include solutions" :disabled="!review" />
        <UCheckbox v-model="rank" label="Show rank and class stats" />
        <div class="rounded-md bg-elevated p-3 text-sm">
          <p class="font-medium">
            Students will see:
          </p>
          <ul class="list-disc ps-5">
            <li v-for="line in preview" :key="line">
              {{ line }}
            </li>
          </ul>
        </div>
        <UAlert v-if="publishing.problem.value" color="error" variant="subtle" :title="problemMessage(publishing.problem.value)" />
      </div>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="outline" @click="open = false" />
        <UButton label="Publish" :loading="publishing.pending.value" @click="publish" />
      </div>
    </template>
  </UModal>
</template>
