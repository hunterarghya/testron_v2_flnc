// Plain-language lines for an assignment's settings: the wizard's Review (T-07 ④), the
// overview's Summary (T-08) and the list's Window column (T-06).
import type { AssignmentDetail, AssignmentRow, AssignmentState } from '~/api/types'
import type { WhenForm } from '~/features/assignments/utils/when-form'
import { formatDateTime, formatDuration } from '~/shared/utils/time'

type BadgeColor = 'neutral' | 'info' | 'success' | 'warning' | 'error'

export const STATE_LABELS: Record<AssignmentState, { label: string, color: BadgeColor }> = {
  SCHEDULED: { label: 'Scheduled', color: 'info' },
  WAITING: { label: 'Waiting', color: 'warning' },
  LIVE: { label: 'Live', color: 'success' },
  CLOSED: { label: 'Closed', color: 'neutral' },
  CANCELLED: { label: 'Cancelled', color: 'error' },
}

export function windowLabel(row: AssignmentRow): string {
  const window = row.window_summary
  switch (row.window_kind) {
    case 'MANUAL':
      return window.planned_at ? `Manual · planned ${formatDateTime(window.planned_at)}` : 'Manual'
    case 'SCHEDULED':
      return `Scheduled ${formatDateTime(window.starts_at ?? '')}`
    case 'DEADLINE':
      return `Deadline ${formatDateTime(window.opens_at ?? '')} – ${formatDateTime(window.closes_at ?? '')}`
    case 'OPEN':
      return 'Open: any time'
  }
}

export function gateLabel(requiresActivation: boolean, hasPassword: boolean): string {
  const parts = [requiresActivation && 'activation', hasPassword && 'password'].filter(Boolean)
  return parts.length ? `Locked: ${parts.join(' + ')}` : 'No gate'
}

export function integrityLabel(integrity: { max_warnings: number, action: string }): string {
  const action = integrity.action === 'DISQUALIFY' ? 'disqualify' : 'auto-submit'
  return `${integrity.max_warnings} warnings → ${action}`
}

export function publicationLabel(mode: string, delayS: number | null): string {
  if (mode === 'AUTO_IMMEDIATE') return 'Auto-publish when each student finishes'
  if (mode === 'AUTO_DELAYED') return `Auto-publish ${formatDuration(delayS ?? 0)} after the test ends`
  return 'I publish manually'
}

/** Review (T-07 ④): one line per part, from the wizard's answers. */
export function reviewLines(form: WhenForm, delayS: number | null): string[] {
  return [
    form.windowKind === 'MANUAL' ? 'Manual start' : `Window: ${form.windowKind.toLowerCase()}`,
    gateLabel(form.requiresActivation, form.usePassword),
    integrityLabel(form.integrity),
    publicationLabel(form.publication.mode, delayS),
  ]
}

/** Summary (T-08): label → value. */
export function summaryRows(detail: AssignmentDetail): [string, string][] {
  return [
    ['Window', windowLabel(detail)],
    ['Gate', gateLabel(detail.gate.requires_activation, detail.gate.has_password)],
    ['Timing', `${detail.timing.kind.toLowerCase().replace('_', ' ')} · ${formatDuration(detail.timing.total_duration_s)}`],
    ['Integrity', integrityLabel(detail.integrity)],
    ['Results', publicationLabel(detail.publication.mode, detail.publication.delay_s)],
  ]
}
