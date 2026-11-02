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
