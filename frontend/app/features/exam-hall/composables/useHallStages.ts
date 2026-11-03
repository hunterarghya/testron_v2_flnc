// Moving between stages by choice (P-04 "Next section" and chips, P-05 "Next"). The answers
// still waiting are sent first: leaving a stage usually closes it, and a closed stage takes
// no more answers. The server's reply is the new state; the hall never moves on its own.
import { computed, ref } from 'vue'
import { toProblem } from '~/api/problems'
import type { AttemptState } from '~/api/types'
import { isLastStage, returnableStages } from '~/engine/stage-navigator'
import { nextStage, returnToStage } from '~/features/exam-hall/composables/hallApi'
import type { ExamSession } from '~/features/exam-hall/composables/useExamSession'

// How long the waiting answers get before the hall moves on anyway
const FLUSH_BEFORE_MOVE_MS = 5000

export function useHallStages(session: ExamSession) {
  const moving = ref(false)
  const state = session.state
  const kind = computed(() => state.value?.timing.kind ?? 'TOTAL')
  const meta = computed(() => state.value?.stage_meta.find(stage => stage.index === state.value?.current_stage_index))
  const lastStage = computed(() => (state.value ? isLastStage(state.value) : true))
  const returnable = computed(() => (state.value ? returnableStages(state.value, state.value.timing.allow_return) : []))

  async function move(call: () => Promise<AttemptState>): Promise<void> {
    moving.value = true
    try {
      await session.drain(FLUSH_BEFORE_MOVE_MS)
      session.apply(await call())
    }
    catch (error) {
      session.handleProblem(toProblem(error))
    }
    finally {
      moving.value = false
    }
  }

  return {
    kind,
    meta,
    lastStage,
    returnable,
    moving,
    next: () => move(() => nextStage(session.attemptId, state.value?.current_stage_index ?? 0)),
    returnTo: (index: number) => move(() => returnToStage(session.attemptId, index)),
  }
}

export type HallStages = ReturnType<typeof useHallStages>
