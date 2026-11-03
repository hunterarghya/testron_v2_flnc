// The server sends UTC; people read Indian time (domain_model.md §0).
export const DISPLAY_TIME_ZONE = 'Asia/Kolkata'

const dateTimeFormat = new Intl.DateTimeFormat('en-IN', {
  timeZone: DISPLAY_TIME_ZONE,
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

/** "12 Nov 2026, 10:00" from "2026-11-12T04:30:00Z". */
export function formatDateTime(isoUtc: string): string {
  return dateTimeFormat.format(new Date(isoUtc))
}

const relativeFormat = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['day', 86_400_000],
  ['hour', 3_600_000],
  ['minute', 60_000],
]

/** "2 hours ago", "yesterday", "in 5 minutes": a hint next to an exact time. */
export function relativeTime(isoUtc: string, nowMs: number): string {
  const difference = new Date(isoUtc).getTime() - nowMs
  for (const [unit, size] of UNITS) {
    if (Math.abs(difference) >= size) {
      return relativeFormat.format(Math.round(difference / size), unit)
    }
  }
  return 'just now'
}

/** "1 h 20 min", "50 min", "45 s": a length of time for people. */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds} s`
  const minutes = Math.round(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (!hours) return `${minutes} min`
  return rest ? `${hours} h ${rest} min` : `${hours} h`
}

// India has one offset all year (no daylight saving), so a fixed offset is exact
const INDIA_OFFSET = '+05:30'
const INDIA_OFFSET_MS = 330 * 60_000

/** A datetime-local input's "2026-11-12T10:00", read as Indian time, as UTC ISO. */
export function fromIndianLocal(local: string): string {
  return new Date(`${local}:00${INDIA_OFFSET}`).toISOString()
}

/** UTC ISO as a datetime-local input's value in Indian time ("2026-11-12T10:00"). */
export function toIndianLocal(isoUtc: string): string {
  return new Date(new Date(isoUtc).getTime() + INDIA_OFFSET_MS).toISOString().slice(0, 16)
}

const timeFormat = new Intl.DateTimeFormat('en-IN', {
  timeZone: DISPLAY_TIME_ZONE,
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

/** "10:58" (Indian time) from "2026-11-12T05:28:00Z" or a Date. */
export function formatTime(at: string | Date): string {
  return timeFormat.format(new Date(at))
}
