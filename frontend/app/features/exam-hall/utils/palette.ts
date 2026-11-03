// The question palette (P-03): each question's mark and the legend's counts. The hall's own
// copy of the answers is the server's, with every change made since laid on top.
import type { HallAnswer, HallResponse } from '~/api/types'

export type PaletteMark = 'answered' | 'not_answered' | 'not_visited' | 'marked'

export interface LocalResponse {
  answer: HallAnswer | null
  marked_for_review: boolean
  visited: boolean
}

export const PALETTE_LEGEND: { mark: PaletteMark, label: string, icon: string }[] = [
  { mark: 'answered', label: 'Answered', icon: 'i-lucide-circle-check' },
  { mark: 'not_visited', label: 'Not visited', icon: 'i-lucide-circle' },
  { mark: 'not_answered', label: 'Not answered', icon: 'i-lucide-circle-dashed' },
  { mark: 'marked', label: 'Marked', icon: 'i-lucide-flag' },
]

/** A choice with no option picked, or no value, is no answer. */
export function hasAnswer(answer: HallAnswer | null | undefined): boolean {
  if (!answer) return false
  return answer.kind === 'CHOICE' ? answer.option_ids.length > 0 : answer.value !== ''
}

export function paletteMark(response: LocalResponse | undefined): PaletteMark {
  if (response?.marked_for_review) return 'marked'
  if (hasAnswer(response?.answer)) return 'answered'
  return response?.visited ? 'not_answered' : 'not_visited'
}

export function paletteCounts(questionIds: readonly string[], responses: Record<string, LocalResponse>): Record<PaletteMark, number> {
  const counts: Record<PaletteMark, number> = { answered: 0, not_answered: 0, not_visited: 0, marked: 0 }
  for (const id of questionIds) counts[paletteMark(responses[id])] += 1
  return counts
}

export function responsesFrom(server: Record<string, HallResponse>): Record<string, LocalResponse> {
  return Object.fromEntries(Object.entries(server).map(([id, saved]) => [id, {
    answer: saved.answer ?? null,
    marked_for_review: saved.marked_for_review,
    visited: saved.visited,
  }]))
}

/** The highest seq the server holds: a new change must go above it (frontend_spec.md §5.2). */
export function serverSeq(server: Record<string, HallResponse>): number {
  return Math.max(0, ...Object.values(server).map(saved => saved.client_seq))
}
