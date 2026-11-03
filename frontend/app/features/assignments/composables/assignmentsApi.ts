// Every assignments call the teacher screens make (api_contract.md §2.6), in one place.
import { api, unwrap } from '~/api/client'
import type {
  Activation,
  AssignmentChanges,
  AssignmentDetail,
  AssignmentPage,
  AudienceCandidate,
  BulkResult,
  Lobby,
  NewAssignment,
  TestDocument,
} from '~/api/types'

export type AssignmentTab = 'upcoming' | 'live' | 'closed' | 'cancelled'

export interface AssignmentQuery {
  tab: AssignmentTab
  search: string
  groupId?: string
  page: number
  pageSize: number
}

const byId = (assignmentId: string) => ({ params: { path: { assignment_id: assignmentId } } })

export function listAssignments(query: AssignmentQuery): Promise<AssignmentPage> {
  return unwrap(api.GET('/api/v1/admin/assignments', {
    params: {
      query: {
        state: query.tab,
        q: query.search.trim() || undefined,
        group_id: query.groupId,
        page: query.page,
        page_size: query.pageSize,
      },
    },
  }))
}

export function getAssignment(assignmentId: string): Promise<AssignmentDetail> {
  return unwrap(api.GET('/api/v1/admin/assignments/{assignment_id}', byId(assignmentId)))
}

export function createAssignment(body: NewAssignment): Promise<AssignmentDetail> {
  return unwrap(api.POST('/api/v1/admin/assignments', { body }))
}

export function updateAssignment(assignmentId: string, body: AssignmentChanges): Promise<AssignmentDetail> {
  return unwrap(api.PATCH('/api/v1/admin/assignments/{assignment_id}', { ...byId(assignmentId), body }))
}

export function changeAudience(assignmentId: string, studentIds: string[], add: boolean): Promise<BulkResult> {
  const init = { ...byId(assignmentId), body: { student_ids: studentIds } }
  return add
    ? unwrap(api.POST('/api/v1/admin/assignments/{assignment_id}/audience/add', init))
    : unwrap(api.POST('/api/v1/admin/assignments/{assignment_id}/audience/remove', init))
}

export async function setPassword(assignmentId: string, password: string | null, confirm?: string): Promise<void> {
  await api.PUT('/api/v1/admin/assignments/{assignment_id}/password', {
    ...byId(assignmentId),
    body: { password, password_confirm: confirm ?? null },
  })
}

export async function revealPassword(assignmentId: string): Promise<string | null> {
  const body = await unwrap(api.GET('/api/v1/admin/assignments/{assignment_id}/password', byId(assignmentId)))
  return body.password
}

export async function cancelAssignment(assignmentId: string): Promise<void> {
  await api.POST('/api/v1/admin/assignments/{assignment_id}/cancel', byId(assignmentId))
}

export function startAssignment(assignmentId: string): Promise<Activation> {
  return unwrap(api.POST('/api/v1/admin/assignments/{assignment_id}/activate', byId(assignmentId)))
}

export function getLobby(assignmentId: string): Promise<Lobby> {
  return unwrap(api.GET('/api/v1/admin/assignments/{assignment_id}/lobby', byId(assignmentId)))
}

export function previewAudience(groupIds: string[]): Promise<AudienceCandidate[]> {
  return unwrap(api.GET('/api/v1/admin/audience-preview', { params: { query: { group_ids: groupIds } } }))
}

export function getTestDocument(testId: string): Promise<TestDocument> {
  return unwrap(api.GET('/api/v1/admin/tests/{test_id}', { params: { path: { test_id: testId } } }))
}
