// "2 approved, 1 skipped (already active)": the toast after a bulk action (frontend_spec.md §4).
import type { BulkResult } from '~/api/types'

export type StudentAction = 'approve' | 'decline' | 'deactivate' | 'reactivate'

const DONE: Record<StudentAction, string> = {
  approve: 'approved',
  decline: 'declined',
  deactivate: 'deactivated',
  reactivate: 'reactivated',
}
// The server's skip reasons, in words
const REASONS: Record<string, string> = {
  not_found: 'not found',
  status_active: 'already active',
  status_pending: 'still pending',
  status_declined: 'declined',
  status_deactivated: 'deactivated',
  status_unverified: 'email not verified',
  status_anonymized: 'deleted',
}

export function bulkSummary(result: BulkResult, action: StudentAction): string {
  const done = `${result.succeeded.length} ${DONE[action]}`
  if (result.skipped.length === 0) {
    return done
  }
  const reasons = [...new Set(result.skipped.map(skip => REASONS[skip.reason] ?? skip.reason))]
  return `${done}, ${result.skipped.length} skipped (${reasons.join(', ')})`
}
