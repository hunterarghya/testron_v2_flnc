// What the hall says: the P-07 headline for each way a test ends, and the save status.
import type { EndReason } from '~/api/types'

export const ENDING_TITLE: Record<EndReason, string> = {
  SUBMITTED: 'Submitted',
  TIMED_OUT: 'Time\'s up — submitted',
  AUTO_SUBMITTED: 'Submitted automatically (warnings)',
  DISQUALIFIED: 'Disqualified',
  FORCE_SUBMITTED: 'Submitted by your teacher',
  ENDED_BY_TEACHER: 'Ended by your teacher',
}

export interface SaveStatus {
  label: string
  icon: string
  tone: 'success' | 'neutral' | 'warning'
}

/** "● Saved", "◌ Saving…" or "⚠ Offline, 3 answers waiting" (P-03). */
export function saveStatus(waiting: number, offline: boolean): SaveStatus {
  if (offline) {
    const answers = waiting === 1 ? '1 answer' : `${waiting} answers`
    return { label: `Offline, ${answers} waiting`, icon: 'i-lucide-wifi-off', tone: 'warning' }
  }
  if (waiting > 0) return { label: 'Saving…', icon: 'i-lucide-loader', tone: 'neutral' }
  return { label: 'Saved', icon: 'i-lucide-check', tone: 'success' }
}

// The timer turns amber for the last 5 minutes (P-03)
export const LAST_MINUTES_MS = 5 * 60_000

/** "Cell Biology – Take 2"; a first take shows "Take 1" too, as on the gate. */
export function hallTitle(title: string, take: number): string {
  return `${title} – Take ${take}`
}
