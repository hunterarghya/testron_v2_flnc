// The exam hall's calls (api_contract.md §2.8). Every one carries this device's exam client
// id, even the read: that is what keeps a refresh from counting as a takeover (§5.7). Every
// answer with `server_now` also keeps the server clock in sync.
import { api, unwrap } from '~/api/client'
import type { AttemptClock, AttemptState, HallAnswer, SaveAck, SubmitResult } from '~/api/types'
import { useServerClock } from '~/shared/composables/useServerClock'
import { examClientHeaders, rememberExamClient } from '~/shared/utils/exam-device'

export interface SaveBody {
  answer: HallAnswer | null
  marked_for_review: boolean
  client_seq: number
}

function attemptPath(attemptId: string) {
  return { params: { path: { attempt_id: attemptId } }, headers: examClientHeaders(attemptId) }
}

export async function loadAttempt(attemptId: string): Promise<AttemptState> {
  const state = await useServerClock().measure(() => unwrap(api.GET('/api/v1/attempts/{attempt_id}', attemptPath(attemptId))))
  rememberExamClient(attemptId, state.exam_client_id)
  return state
}

export function saveResponse(attemptId: string, questionId: string, body: SaveBody): Promise<SaveAck> {
  return useServerClock().measure(() => unwrap(api.PUT('/api/v1/attempts/{attempt_id}/responses/{question_id}', {
    params: { path: { attempt_id: attemptId, question_id: questionId } },
    headers: examClientHeaders(attemptId),
    body,
  })))
}

export async function recordVisit(attemptId: string, questionId: string): Promise<void> {
  await unwrap(api.POST('/api/v1/attempts/{attempt_id}/questions/{question_id}/visit', {
    params: { path: { attempt_id: attemptId, question_id: questionId } },
    headers: examClientHeaders(attemptId),
  }))
}

export function heartbeat(attemptId: string): Promise<AttemptClock> {
  return useServerClock().measure(() => unwrap(api.POST('/api/v1/attempts/{attempt_id}/heartbeat', attemptPath(attemptId))))
}

export function submitAttempt(attemptId: string): Promise<SubmitResult> {
  return unwrap(api.POST('/api/v1/attempts/{attempt_id}/submit', attemptPath(attemptId)))
}
