// P-07 Submit (frontend_spec.md §5.2 step 8): every waiting answer goes first (up to 10 s),
// then the submit. Offline, nothing is lost: the answers stay on this device and the student
// is told to reconnect. Submitting twice is safe; the server returns the same ending.
import { ref, shallowRef } from 'vue'
import { type ApiProblem, NETWORK_ERROR, toProblem } from '~/api/problems'
import { submitAttempt } from '~/features/exam-hall/composables/hallApi'
import type { ExamSession } from '~/features/exam-hall/composables/useExamSession'

export const SUBMIT_FLUSH_MS = 10_000
// The session itself handles these: the attempt ended or moved to another device
const SESSION_CODES = new Set(['attempt_ended', 'attempt_taken_over'])

export function useHallSubmit(session: ExamSession) {
  const offline = ref(false)
  const problem = shallowRef<ApiProblem | null>(null)

  function backToReview(found: ApiProblem | null): void {
    offline.value = found === null || found.code === NETWORK_ERROR
    problem.value = offline.value ? null : found
    session.phase.value = 'review'
  }

  async function submit(): Promise<void> {
    session.phase.value = 'submitting'
    offline.value = false
    problem.value = null
    const sent = await session.drain(SUBMIT_FLUSH_MS)
    // Meanwhile the attempt may have ended or moved to another device
    if (session.phase.value !== 'submitting') return
    if (!sent) {
      backToReview(null)
      return
    }
    try {
      const result = await submitAttempt(session.attemptId)
      session.finish(result.end_reason, result.ended_at)
    }
    catch (error) {
      const found = toProblem(error)
      if (SESSION_CODES.has(found.code)) session.handleProblem(found)
      else backToReview(found)
    }
  }

  return {
    offline,
    problem,
    submit,
    open: () => {
      offline.value = false
      problem.value = null
      session.phase.value = 'review'
    },
    close: () => {
      session.phase.value = 'active'
    },
  }
}
