// What the live monitor says (T-10): each status in words, "last seen" and the summary line.
import type { IntegrityEventView, Monitor, MonitorRow, MonitorStatus } from '~/api/types'
import { formatTime } from '~/shared/utils/time'

export const STATUS_LABEL: Record<MonitorStatus, string> = {
  NOT_STARTED: 'Not started',
  IN_PROGRESS: 'In progress',
  SUBMITTED: 'Submitted',
  TIMED_OUT: 'Timed out',
  AUTO_SUBMITTED: 'Auto-submit',
  DISQUALIFIED: 'Disqualified',
  FORCE_SUBMITTED: 'Force-submitted',
  ENDED_BY_TEACHER: 'Ended',
}

// After this long without a save or heartbeat the student may be offline (T-10)
export const QUIET_MS = 60_000

/** "4s" while sitting (amber past a minute), the time of the last contact once ended. */
export function lastSeen(row: MonitorRow, nowMs: number): { text: string, quiet: boolean } {
  if (!row.last_seen_at) return { text: '–', quiet: false }
  if (row.status !== 'IN_PROGRESS') return { text: formatTime(row.last_seen_at), quiet: false }
  const ago = Math.max(0, nowMs - Date.parse(row.last_seen_at))
  const text = ago < 60_000 ? `${Math.floor(ago / 1000)}s` : `${Math.floor(ago / 60_000)} min`
  return { text, quiet: ago > QUIET_MS }
}

export function answeredText(row: MonitorRow): string {
  return row.status === 'NOT_STARTED' ? '–' : `${row.answered}/${row.total_questions}`
}

/** "30 in progress · 6 submitted · 7 not started" */
export function summaryLine(monitor: Monitor): string {
  return Object.entries(monitor.summary)
    .map(([status, count]) => `${count} ${STATUS_LABEL[status as MonitorStatus].toLowerCase()}`)
    .join(' · ')
}

/** The ⚑ panel: "Tab hidden · 10:21 · away 12 s · counted" */
export function eventLine(event: IntegrityEventView): string {
  const kind = { FULLSCREEN_EXIT: 'Left fullscreen', TAB_HIDDEN: 'Tab hidden', WINDOW_BLUR: 'Switched window', DEVICE_CHANGED: 'Device changed' }[event.kind]
  const away = event.returned_at
    ? `away ${Math.round((Date.parse(event.returned_at) - Date.parse(event.left_at)) / 1000)} s`
    : 'not back yet'
  return [kind, formatTime(event.left_at), away, event.counted ? 'counted' : 'not counted'].join(' · ')
}
