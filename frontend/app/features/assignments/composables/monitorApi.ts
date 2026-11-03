// The teacher's live monitor and its actions (api_contract.md §2.6; T-10, D-02-D-04).
import { api, unwrap } from '~/api/client'
import type {
  AttemptSummary,
  BulkResult,
  EndedForEveryone,
  Extended,
  IntegrityEventView,
  Monitor,
  MonitorFilter,
} from '~/api/types'

const assignment = (assignmentId: string) => ({ params: { path: { assignment_id: assignmentId } } })
const attempt = (attemptId: string) => ({ params: { path: { attempt_id: attemptId } } })

export function getMonitor(assignmentId: string, filter: MonitorFilter): Promise<Monitor> {
  return unwrap(api.GET('/api/v1/admin/assignments/{assignment_id}/monitor', {
    params: { path: { assignment_id: assignmentId }, query: { filter } },
  }))
}

export interface ExtensionRequest {
  seconds: number
  // Absent: everyone
  student_ids?: string[]
  // Absent: the final section
  stage_index?: number
}

export function extendTime(assignmentId: string, body: ExtensionRequest): Promise<Extended> {
  return unwrap(api.POST('/api/v1/admin/assignments/{assignment_id}/extensions', { ...assignment(assignmentId), body }))
}

export function endForEveryone(assignmentId: string, confirm: string): Promise<EndedForEveryone> {
  return unwrap(api.POST('/api/v1/admin/assignments/{assignment_id}/end', { ...assignment(assignmentId), body: { confirm } }))
}

export function grantRetakes(assignmentId: string, studentIds: string[]): Promise<BulkResult> {
  return unwrap(api.POST('/api/v1/admin/assignments/{assignment_id}/retake-grants', {
    ...assignment(assignmentId),
    body: { student_ids: studentIds },
  }))
}

export function forceSubmit(attemptId: string): Promise<AttemptSummary> {
  return unwrap(api.POST('/api/v1/admin/attempts/{attempt_id}/force-submit', attempt(attemptId)))
}

export function listIntegrityEvents(attemptId: string): Promise<IntegrityEventView[]> {
  return unwrap(api.GET('/api/v1/admin/attempts/{attempt_id}/integrity-events', attempt(attemptId)))
}
