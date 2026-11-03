// The student's calls before the exam hall (api_contract.md §2.8). Each answer carries
// `server_now`, so each one also keeps the server clock in sync.
import { api, unwrap } from '~/api/client'
import type { GateState, MyTests } from '~/api/types'
import { useServerClock } from '~/shared/composables/useServerClock'

export function listMyTests(): Promise<MyTests> {
  return useServerClock().measure(() => unwrap(api.GET('/api/v1/my/tests')))
}

export function getGate(assignmentId: string): Promise<GateState> {
  return useServerClock().measure(() => unwrap(api.GET('/api/v1/my/tests/{assignment_id}/gate', {
    params: { path: { assignment_id: assignmentId } },
  })))
}
