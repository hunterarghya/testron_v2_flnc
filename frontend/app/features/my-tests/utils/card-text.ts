// What a My Tests card says (P-01).
import type { MyTestCard } from '~/api/types'
import { formatDateTime, formatDuration, relativeTime } from '~/shared/utils/time'

export const BUTTON: Partial<Record<MyTestCard['state'], string>> = {
  START: 'Start',
  JOIN: 'Join',
  RESUME: 'Resume',
  RETAKE_AVAILABLE: 'Retake',
}

/** "30 questions · 50 min · 3 sections" */
export function cardFacts(card: MyTestCard): string {
  const parts = [`${card.question_count} questions`, formatDuration(card.total_duration_s)]
  if (card.timing_kind === 'SECTIONED') parts.push(`${card.stage_count} sections`)
  return parts.join(' · ')
}

export function cardStatus(card: MyTestCard, serverNowMs: number): string {
  switch (card.state) {
    case 'JOIN':
      return 'Waiting for teacher to start'
    case 'RESUME':
      return 'In progress'
    case 'RETAKE_AVAILABLE':
      return 'Retake available'
    case 'STARTS_IN':
      return card.starts_at ? `${formatDateTime(card.starts_at)} · starts ${relativeTime(card.starts_at, serverNowMs)}` : 'Coming up'
    case 'START':
      return card.closes_at ? `Open until ${formatDateTime(card.closes_at)}` : 'Open now'
  }
}
