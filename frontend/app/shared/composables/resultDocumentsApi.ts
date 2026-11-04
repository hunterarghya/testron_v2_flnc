// The documents behind T-11's key, T-12's sheet and the browser exports (api_contract.md
// §2.7, ADR-019): shared by the results screens and the exports.
import { api, unwrap } from '~/api/client'
import type { AnswerSheet, KeyedPaper } from '~/api/types'

export function getAnswerKey(assignmentId: string): Promise<KeyedPaper> {
  return unwrap(api.GET('/api/v1/admin/assignments/{assignment_id}/answer-key', { params: { path: { assignment_id: assignmentId } } }))
}

export function getAnswerSheet(attemptId: string): Promise<AnswerSheet> {
  return unwrap(api.GET('/api/v1/admin/attempts/{attempt_id}/sheet', { params: { path: { attempt_id: attemptId } } }))
}

/** The chosen attempts' sheets, or every ended attempt's when none are given. */
export function listAnswerSheets(assignmentId: string, attemptIds: string[] = []): Promise<AnswerSheet[]> {
  return unwrap(api.GET('/api/v1/admin/assignments/{assignment_id}/answer-sheets', {
    params: { path: { assignment_id: assignmentId }, query: attemptIds.length ? { attempt_ids: attemptIds.join(',') } : {} },
  }))
}
