// An assignment's results for the teacher (api_contract.md §2.7; T-11, T-12, D-01, D-05,
// D-09). The CSV is a plain download from the server; the other exports are built in the
// browser from the answer sheets and key (ADR-019).
import { api, unwrap } from '~/api/client'
import type {
  Gradebook,
  KeyCorrected,
  KeyEntry,
  PublicationOptions,
  PublicationView,
  QuestionStat,
} from '~/api/types'

const assignment = (assignmentId: string) => ({ params: { path: { assignment_id: assignmentId } } })
const attempt = (attemptId: string) => ({ params: { path: { attempt_id: attemptId } } })

export function getGradebook(assignmentId: string): Promise<Gradebook> {
  return unwrap(api.GET('/api/v1/admin/assignments/{assignment_id}/gradebook', assignment(assignmentId)))
}

export function getQuestionStats(assignmentId: string): Promise<QuestionStat[]> {
  return unwrap(api.GET('/api/v1/admin/assignments/{assignment_id}/question-stats', assignment(assignmentId)))
}

export function publishResults(assignmentId: string, options: PublicationOptions): Promise<PublicationView> {
  return unwrap(api.POST('/api/v1/admin/assignments/{assignment_id}/publish', { ...assignment(assignmentId), body: { options } }))
}

export function unpublishResults(assignmentId: string): Promise<PublicationView> {
  return unwrap(api.POST('/api/v1/admin/assignments/{assignment_id}/unpublish', assignment(assignmentId)))
}

export function correctAnswerKey(assignmentId: string, questionId: string, entry: KeyEntry, reason: string): Promise<KeyCorrected> {
  return unwrap(api.POST('/api/v1/admin/assignments/{assignment_id}/answer-key-corrections', {
    ...assignment(assignmentId),
    body: { question_id: questionId, entry, reason },
  }))
}

export async function overrideDisqualification(attemptId: string, reason: string): Promise<void> {
  await unwrap(api.POST('/api/v1/admin/attempts/{attempt_id}/override-disqualification', { ...attempt(attemptId), body: { reason } }))
}

/** A same-origin link: the browser downloads it with the session cookie. */
export function gradebookCsvUrl(assignmentId: string): string {
  return `/api/v1/admin/assignments/${assignmentId}/exports/gradebook.csv`
}
