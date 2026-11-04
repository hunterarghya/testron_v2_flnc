// The student's past tests and results (api_contract.md §2.9; P-08, P-09).
import { api, unwrap } from '~/api/client'
import type { PastTestsPage, Result } from '~/api/types'

// Past Tests shows every card at once: a student sits tens of tests, not thousands
const ALL = 200

export function listPastTests(): Promise<PastTestsPage> {
  return unwrap(api.GET('/api/v1/my/past-tests', { params: { query: { page: 1, page_size: ALL } } }))
}

export function getMyResult(attemptId: string): Promise<Result> {
  return unwrap(api.GET('/api/v1/my/results/{attempt_id}', { params: { path: { attempt_id: attemptId } } }))
}
