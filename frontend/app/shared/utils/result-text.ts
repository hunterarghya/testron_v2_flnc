// What a result says (P-09, T-12): marks, outcomes, percentages and time. Marks stay decimal
// strings (CLAUDE.md rule 7); a number is made only for a bar's width or a whole percentage.
import type { Result, ResultQuestion } from '~/api/types'
import { formatDecimal } from '~/shared/utils/decimals'
import { formatDuration } from '~/shared/utils/time'

export type QuestionFilter = 'all' | 'wrong' | 'unanswered'

export const OUTCOME: Record<string, { icon: string, color: 'success' | 'warning' | 'error' | 'neutral', label: string }> = {
  CORRECT: { icon: 'i-lucide-check', color: 'success', label: 'Correct' },
  PARTIAL: { icon: 'i-lucide-circle-half', color: 'warning', label: 'Partly correct' },
  INCORRECT: { icon: 'i-lucide-x', color: 'error', label: 'Wrong' },
  UNANSWERED: { icon: 'i-lucide-minus', color: 'neutral', label: 'Not answered' },
}

/** "+4", "−1", "0" */
export function signedMarks(value: string): string {
  const shown = formatDecimal(value.replace('-', ''))
  if (value.startsWith('-')) return `−${shown}`
  return Number(value) > 0 ? `+${shown}` : shown
}

/** "88 / 120" */
export function scoreText(score: string | null | undefined, max: string): string {
  return `${score == null ? '–' : formatDecimal(score)} / ${formatDecimal(max)}`
}

/** A whole percentage for display: "73%". Never stored or sent. */
export function percent(part: string, whole: string): number {
  const total = Number(whole)
  return total > 0 ? Math.round((Number(part) / total) * 100) : 0
}

export function headerFacts(result: Result): string[] {
  const facts = [`Time ${formatDuration(result.time_taken_s)}`]
  const rank = result.rank_and_stats
  if (rank) facts.unshift(`Rank ${rank.rank} of ${rank.pool}`, `Class avg ${formatDecimal(rank.mean)}`)
  return facts
}

export function matches(question: ResultQuestion, filter: QuestionFilter): boolean {
  if (filter === 'wrong') return question.outcome === 'INCORRECT' || question.outcome === 'PARTIAL'
  if (filter === 'unanswered') return question.outcome === 'UNANSWERED'
  return true
}

/** A numerical answer as the student gave it, or "–". */
export function givenValue(question: ResultQuestion): string {
  const answer = question.your_answer as { kind?: string, value?: string } | null | undefined
  return answer?.kind === 'NUMERIC' && answer.value ? answer.value : '–'
}

/** The options the student picked. */
export function pickedIds(question: ResultQuestion): string[] {
  const answer = question.your_answer as { option_ids?: string[] } | null | undefined
  return answer?.option_ids ?? []
}
