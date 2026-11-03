// The student's calls before the exam hall (api_contract.md §2.8). Each answer carries
// `server_now`, so each one also keeps the server clock in sync.
import { api, unwrap } from '~/api/client'
import type { AttemptState, GateState, MyTests } from '~/api/types'
import { useServerClock } from '~/shared/composables/useServerClock'
import { rememberExamClient } from '~/shared/utils/exam-device'

export function listMyTests(): Promise<MyTests> {
  return useServerClock().measure(() => unwrap(api.GET('/api/v1/my/tests')))
}

export function getGate(assignmentId: string): Promise<GateState> {
  return useServerClock().measure(() => unwrap(api.GET('/api/v1/my/tests/{assignment_id}/gate', {
    params: { path: { assignment_id: assignmentId } },
  })))
}

/** P-02 Start: a new sitting, or the one in progress. Keeps this device's exam client id. */
export async function startAttempt(assignmentId: string, password: string | null): Promise<AttemptState> {
  const state = await useServerClock().measure(() => unwrap(api.POST('/api/v1/my/tests/{assignment_id}/attempts', {
    params: { path: { assignment_id: assignmentId } },
    body: { password },
  })))
  rememberExamClient(state.attempt_id, state.exam_client_id)
  return state
}
