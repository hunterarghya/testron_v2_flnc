<!-- P-03/04/05 the exam hall, with P-07: loads the attempt, then the question, the palette (a
     bottom sheet on phones; none in rapid fire), the section bar, and the header; "leave
     this section?", "time is over" between sections, the review before submitting, and the
     ending or "opened on another device" screen. Copy, right-click and text selection are
     blocked here as a deterrent [F-5]. -->
<script setup lang="ts">
import { computed, onMounted, provide, ref, watch } from 'vue'
import HallEnded from '~/features/exam-hall/components/HallEnded.vue'
import HallHeader from '~/features/exam-hall/components/HallHeader.vue'
import IntegrityOverlay from '~/features/exam-hall/components/IntegrityOverlay.vue'
import LeaveSectionDialog from '~/features/exam-hall/components/LeaveSectionDialog.vue'
import QuestionPalette from '~/features/exam-hall/components/QuestionPalette.vue'
import QuestionPanel from '~/features/exam-hall/components/QuestionPanel.vue'
import SectionBar from '~/features/exam-hall/components/SectionBar.vue'
import SubmitReview from '~/features/exam-hall/components/SubmitReview.vue'
import { EXAM_SESSION, useExamSession } from '~/features/exam-hall/composables/useExamSession'
import { useHallClock } from '~/features/exam-hall/composables/useHallClock'
import { useHallIntegrity } from '~/features/exam-hall/composables/useHallIntegrity'
import { useHallStages } from '~/features/exam-hall/composables/useHallStages'
import { useHallSubmit } from '~/features/exam-hall/composables/useHallSubmit'
import { hallTitle, LAST_MINUTES_MS } from '~/features/exam-hall/utils/hall-text'
import ErrorState from '~/shared/components/ErrorState.vue'

const props = defineProps<{ attemptId: string }>()

const hall = useExamSession(props.attemptId)
provide(EXAM_SESSION, hall)
const timer = useHallClock(hall)
const stages = useHallStages(hall)
const submitting = useHallSubmit(hall)
const integrity = useHallIntegrity(hall)
const toast = useToast()
const paletteOpen = ref(false)
const leaving = ref(false)
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
  if (last && before === false && phase.value === 'active' && stages.kind.value === 'TOTAL') {
    toast.add({ title: '5 minutes left', color: 'warning' })
  }
})
// A new stage starts on its first question, which counts as seen
watch(() => hall.state.value?.current_stage_index, (index, before) => {
  if (before !== undefined && index !== before) hall.goTo(0)
})

function nextStage(): void {
  if (stages.kind.value === 'SECTIONED') leaving.value = true
  else void stages.next()
}

async function leaveSection(): Promise<void> {
  await stages.next()
  leaving.value = false
}
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
    <HallHeader :remaining-ms="timer.remainingMs.value" :palette="stages.kind.value !== 'PER_QUESTION'" @submit="submitting.open" @palette="paletteOpen = true" />
    <SectionBar v-if="stages.kind.value === 'SECTIONED'" :now-ms="timer.nowMs.value" :returnable="stages.returnable.value" @return="stages.returnTo" />
    <div class="flex flex-1">
      <QuestionPanel class="flex-1" :kind="stages.kind.value" :last-stage="stages.lastStage.value" :moving="stages.moving.value" @next-stage="nextStage" @submit="submitting.open" />
      <QuestionPalette v-if="stages.kind.value !== 'PER_QUESTION'" class="hidden w-72 border-s border-default lg:block" />
    </div>
    <USlideover v-model:open="paletteOpen" side="bottom" title="Questions">
      <template #body>
        <QuestionPalette @picked="paletteOpen = false" />
      </template>
    </USlideover>
    <LeaveSectionDialog v-model:open="leaving" :remaining-ms="timer.remainingMs.value" :moving="stages.moving.value" @go="leaveSection" />
    <SubmitReview
      v-model:open="reviewOpen"
      :remaining-ms="timer.remainingMs.value"
      :offline="submitting.offline.value"
      :problem="submitting.problem.value"
      @submit="submitting.submit"
      @back="submitting.close"
    />
    <IntegrityOverlay v-if="integrity.warning.value" @return="integrity.returnToTest" />
    <div v-if="timer.interstitial.value" class="fixed inset-0 z-50 flex items-center justify-center bg-default/95 p-6 text-center text-lg font-medium" role="status">
      {{ timer.interstitial.value }}
    </div>
  </div>
</template>
