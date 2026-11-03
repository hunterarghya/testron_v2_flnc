// The exam hall's one session (frontend_spec.md §5.5): loading → active ⇄ review → submitting
// → ended, or taken over by another device. Components read its state and call its intents;
// the server's answers are always the truth, the device only adds changes not yet sent.
// ADR-075: a feature composable rather than a Pinia store (no new dependency for one store).
import { computed, inject, type InjectionKey, ref, shallowRef } from 'vue'
import { type ApiProblem, toProblem } from '~/api/problems'
import type { AttemptClock, AttemptState, EndReason, HallAnswer } from '~/api/types'
import type { SaveQueue } from '~/engine/save-queue'
import { stageQuestionIds } from '~/engine/stage-navigator'
import { loadAttempt, recordVisit } from '~/features/exam-hall/composables/hallApi'
import { createHallQueue, waitingChanges } from '~/features/exam-hall/composables/hallQueue'
import { type LocalResponse, responsesFrom, serverSeq } from '~/features/exam-hall/utils/palette'
import { forgetAttempt } from '~/shared/utils/exam-device'
import { exitFullscreen } from '~/shared/utils/fullscreen'

// The hall's picture of the stages is out of date: the server's state is loaded again
const STALE = new Set(['stage_closed', 'stage_navigation_invalid', 'question_not_in_stage'])

export type HallPhase = 'loading' | 'active' | 'review' | 'submitting' | 'ended' | 'taken_over' | 'error'

export interface Ending {
  reason: EndReason
  endedAt: string
}

export function useExamSession(attemptId: string) {
  const phase = ref<HallPhase>('loading')
  const state = shallowRef<AttemptState | null>(null)
  const clock = shallowRef<AttemptClock | null>(null)
  const responses = ref<Record<string, LocalResponse>>({})
  const position = ref(0)
  const problem = shallowRef<ApiProblem | null>(null)
  const ending = shallowRef<Ending | null>(null)
  const queueStatus = ref({ waiting: 0, offline: false })
  const lastContactAt = ref(Date.now())
  let queue: SaveQueue<HallAnswer> | null = null

  // Only the current stage's questions: the palette shows one section at a time (P-04)
  const questions = computed(() => {
    const loaded = state.value
    if (!loaded) return []
    const ids = new Set(stageQuestionIds(loaded.stage_meta, loaded))
    return loaded.questions.filter(question => ids.has(question.id))
  })
  const current = computed(() => questions.value[position.value])

  function finish(reason: EndReason, endedAt: string): void {
    queue?.stop()
    ending.value = { reason, endedAt }
    phase.value = 'ended'
    forgetAttempt(attemptId)
    void exitFullscreen()
  }

  function takenOver(): void {
    queue?.stop()
    phase.value = 'taken_over'
    forgetAttempt(attemptId)
    void exitFullscreen()
  }

  function applyClock(next: AttemptClock): void {
    const before = clock.value
    clock.value = next
    lastContactAt.value = Date.now()
    if (next.status === 'ENDED' && next.end_reason && next.ended_at) finish(next.end_reason, next.ended_at)
    // The server moved to the next stage: follow it (frontend_spec.md §5.3)
    else if (before && next.current_stage_index !== before.current_stage_index) void load()
  }

  function startQueue(loaded: AttemptState): void {
    queue = createHallQueue(attemptId, serverSeq(loaded.responses), {
      onAck: applyClock,
      onStop: reason => (reason === 'taken_over' ? takenOver() : void load()),
      onChange: () => {
        queueStatus.value = { waiting: queue?.waiting() ?? 0, offline: queue?.offline() ?? false }
      },
      onDropped: () => void load(),
    })
  }

  function apply(loaded: AttemptState): void {
    const movedStage = state.value !== null && state.value.current_stage_index !== loaded.current_stage_index
    state.value = loaded
    if (loaded.status === 'ENDED' && loaded.end_reason && loaded.ended_at) {
      finish(loaded.end_reason, loaded.ended_at)
      return
    }
    const unsent = Object.entries(waitingChanges(attemptId))
      .map(([id, change]) => [id, { answer: change.answer, marked_for_review: change.marked_for_review, visited: true }])
    responses.value = { ...responsesFrom(loaded.responses), ...Object.fromEntries(unsent) }
    if (!queue) startQueue(loaded)
    // A whole state is already the newest: no need to load it again for a new stage
    clock.value = loaded
    lastContactAt.value = Date.now()
    position.value = movedStage ? 0 : Math.min(position.value, Math.max(0, questions.value.length - 1))
    if (phase.value === 'loading' || phase.value === 'error') phase.value = 'active'
  }

  async function load(): Promise<void> {
    try {
      apply(await loadAttempt(attemptId))
    }
    catch (error) {
      handleProblem(toProblem(error))
    }
  }

  function handleProblem(found: ApiProblem): void {
    if (found.code === 'attempt_taken_over') takenOver()
    else if (found.code === 'attempt_ended' || STALE.has(found.code)) void load()
    else if (phase.value === 'loading') {
      problem.value = found
      phase.value = 'error'
    }
  }

  function change(questionId: string, update: Partial<LocalResponse>, debounce = false): void {
    const next = { answer: null, marked_for_review: false, ...responses.value[questionId], ...update, visited: true }
    responses.value = { ...responses.value, [questionId]: next }
    queue?.change(questionId, next.answer, next.marked_for_review, { debounce })
  }

  function goTo(index: number): void {
    position.value = index
    const question = current.value
    if (!question || responses.value[question.id]?.visited) return
    responses.value = { ...responses.value, [question.id]: { answer: null, marked_for_review: false, visited: true } }
    recordVisit(attemptId, question.id).catch(error => handleProblem(toProblem(error)))
  }

  return {
    attemptId,
    phase,
    state,
    clock,
    responses,
    position,
    questions,
    current,
    problem,
    ending,
    queueStatus,
    lastContactAt,
    load,
    apply,
    applyClock,
    finish,
    handleProblem,
    goTo,
    answer: (questionId: string, value: HallAnswer | null, debounce = false) => change(questionId, { answer: value }, debounce),
    toggleMark: (questionId: string) => change(questionId, { marked_for_review: !responses.value[questionId]?.marked_for_review }),
    drain: (timeoutMs: number) => queue?.drain(timeoutMs) ?? Promise.resolve(true),
  }
}

export type ExamSession = ReturnType<typeof useExamSession>
export const EXAM_SESSION: InjectionKey<ExamSession> = Symbol('exam-session')

/** The session of the hall this component is inside (ExamHall provides it). */
export function useHall(): ExamSession {
  const session = inject(EXAM_SESSION)
  if (!session) throw new Error('useHall() must be used inside ExamHall')
  return session
}
