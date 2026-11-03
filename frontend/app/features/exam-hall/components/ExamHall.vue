<!-- P-03 the exam hall (total timer), with P-07: loads the attempt, then the question, the
     palette (a bottom sheet on phones) and the header; the review before submitting; and
     the ending or "opened on another device" screen. Copy, right-click and text selection
     are blocked here as a deterrent [F-5]. -->
<script setup lang="ts">
import { computed, onMounted, provide, ref, watch } from 'vue'
import HallHeader from '~/features/exam-hall/components/HallHeader.vue'
import HallEnded from '~/features/exam-hall/components/HallEnded.vue'
import QuestionPalette from '~/features/exam-hall/components/QuestionPalette.vue'
import QuestionPanel from '~/features/exam-hall/components/QuestionPanel.vue'
import SubmitReview from '~/features/exam-hall/components/SubmitReview.vue'
import { EXAM_SESSION, useExamSession } from '~/features/exam-hall/composables/useExamSession'
import { useHallClock } from '~/features/exam-hall/composables/useHallClock'
import { useHallSubmit } from '~/features/exam-hall/composables/useHallSubmit'
import { hallTitle, LAST_MINUTES_MS } from '~/features/exam-hall/utils/hall-text'
import ErrorState from '~/shared/components/ErrorState.vue'

const props = defineProps<{ attemptId: string }>()

const hall = useExamSession(props.attemptId)
provide(EXAM_SESSION, hall)
const timer = useHallClock(hall)
const submitting = useHallSubmit(hall)
const toast = useToast()
const paletteOpen = ref(false)
const phase = hall.phase
const title = computed(() => (hall.state.value ? hallTitle(hall.state.value.title, hall.state.value.take_number) : ''))
const reviewOpen = computed({
  get: () => phase.value === 'review' || phase.value === 'submitting',
  set: (open: boolean) => {
    if (!open) submitting.close()
  },
})

onMounted(async () => {
  await hall.load()
  hall.goTo(0)
})

watch(() => timer.remainingMs.value <= LAST_MINUTES_MS, (last, before) => {
  if (last && before === false && phase.value === 'active') toast.add({ title: '5 minutes left', color: 'warning' })
})
</script>

<template>
  <div v-if="phase === 'loading'" class="flex min-h-screen items-center justify-center text-muted">
    Loading your test…
  </div>
  <UContainer v-else-if="phase === 'error' && hall.problem.value" class="py-10">
    <ErrorState :problem="hall.problem.value" @retry="hall.load" />
  </UContainer>
  <HallEnded v-else-if="phase === 'ended' || phase === 'taken_over'" :title="title" :ending="phase === 'ended' ? hall.ending.value : null" />
  <div v-else class="flex min-h-screen select-none flex-col print:hidden" @contextmenu.prevent @copy.prevent @cut.prevent @dragstart.prevent>
    <HallHeader :remaining-ms="timer.remainingMs.value" @submit="submitting.open" @palette="paletteOpen = true" />
    <div class="flex flex-1">
      <QuestionPanel class="flex-1" />
      <QuestionPalette class="hidden w-72 border-s border-default lg:block" />
    </div>
    <USlideover v-model:open="paletteOpen" side="bottom" title="Questions">
      <template #body>
        <QuestionPalette @picked="paletteOpen = false" />
      </template>
    </USlideover>
    <SubmitReview
      v-model:open="reviewOpen"
      :remaining-ms="timer.remainingMs.value"
      :offline="submitting.offline.value"
      :problem="submitting.problem.value"
      @submit="submitting.submit"
      @back="submitting.close"
    />
  </div>
</template>
