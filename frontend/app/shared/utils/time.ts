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
