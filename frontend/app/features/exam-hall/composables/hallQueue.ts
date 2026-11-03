// The hall's save queue: the engine's queue (engine/save-queue.ts) kept in this browser's
// localStorage and sending through the API. Each refusal maps to what the queue should do.
import { type ApiProblem, toProblem } from '~/api/problems'
import type { HallAnswer, SaveAck } from '~/api/types'
import {
  createSaveQueue,
  type QueueSnapshot,
  type QueueStorage,
  type SaveQueue,
  type SendOutcome,
  type StopReason,
} from '~/engine/save-queue'
import { saveResponse } from '~/features/exam-hall/composables/hallApi'
import { queueKey, readItem, removeItem, writeItem } from '~/shared/utils/exam-device'

export interface HallQueueHandlers {
  onAck: (ack: SaveAck) => void
  onStop: (reason: StopReason) => void
  onChange: () => void
  onDropped: (questionId: string) => void
}

// The answer can never be stored: its stage closed, or it doesn't fit the question
const DROP = new Set(['stage_closed', 'question_not_in_stage', 'answer_invalid', 'validation_error'])

export function outcomeOf(problem: ApiProblem): SendOutcome {
  if (problem.code === 'attempt_ended') return 'ended'
  if (problem.code === 'attempt_taken_over') return 'taken_over'
  if (DROP.has(problem.code)) return 'drop'
  // Offline, the server busy or briefly failing: keep it and try again
  return 'retry'
}

export function queueStorage(attemptId: string): QueueStorage<HallAnswer> {
  const key = queueKey(attemptId)
  return {
    read: () => {
      const raw = readItem(key)
      return raw ? (JSON.parse(raw) as QueueSnapshot<HallAnswer>) : null
    },
    write: snapshot => writeItem(key, JSON.stringify(snapshot)),
    clear: () => removeItem(key),
  }
}

/** The changes this browser still has to send, e.g. after a reload while offline. */
export function waitingChanges(attemptId: string): QueueSnapshot<HallAnswer>['pending'] {
  return queueStorage(attemptId).read()?.pending ?? {}
}

export function createHallQueue(attemptId: string, serverSeq: number, handlers: HallQueueHandlers): SaveQueue<HallAnswer> {
  async function send(questionId: string, save: Parameters<typeof saveResponse>[2]): Promise<SendOutcome> {
    try {
      handlers.onAck(await saveResponse(attemptId, questionId, save))
      return 'saved'
    }
    catch (error) {
      return outcomeOf(toProblem(error))
    }
  }

  return createSaveQueue<HallAnswer>({
    send,
    storage: queueStorage(attemptId),
    onStop: handlers.onStop,
    onChange: handlers.onChange,
    onDropped: handlers.onDropped,
  }, serverSeq)
}
