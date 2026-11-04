// One question of the keyed paper (database_schema.md §4.2-4.3), as D-05 edits it: the stem,
// the options labelled A, B, … in the teacher's order, and the current answer.
import type { KeyedPaper, RichDoc } from '~/api/types'

export interface KeyedQuestion {
  type: 'MCQ' | 'MSQ' | 'NUMERICAL'
  stem: RichDoc
  options: { id: string, label: string }[]
  correct: string[]
  answer: string | null
  tolerance: string | null
}

interface PaperQuestion { id: string, type: KeyedQuestion['type'], stem: RichDoc, options?: { id: string }[] }
interface KeyEntryJson { correct_option_ids?: string[], answer?: string, tolerance?: string }

export function keyedQuestion(keyed: KeyedPaper, questionId: string): KeyedQuestion | null {
  const sections = (keyed.paper.sections ?? []) as { questions: PaperQuestion[] }[]
  const question = sections.flatMap(s => s.questions).find(q => q.id === questionId)
  if (!question) return null
  const entry = (keyed.entries[questionId] ?? {}) as KeyEntryJson
  return {
    type: question.type,
    stem: question.stem,
    options: (question.options ?? []).map((o, i) => ({ id: o.id, label: String.fromCharCode(65 + i) })),
    correct: entry.correct_option_ids ?? [],
    answer: entry.answer ?? null,
    tolerance: entry.tolerance ?? null,
  }
}
