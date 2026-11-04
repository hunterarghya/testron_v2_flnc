// The answer key export shows each paper question the way a result does (the same card), with
// its correct answer and solution, in the teacher's order (domain_model.md §6.6).
import type { KeyedPaper, ResultQuestion, RichDoc } from '~/api/types'

interface PaperQuestion {
  id: string
  type: ResultQuestion['type']
  stem: RichDoc
  marks: string
  negative_marks: string
  options?: { id: string, content: RichDoc }[]
}
interface KeyEntryJson { correct_option_ids?: string[], answer?: string, tolerance?: string }

export function keyAsQuestions(keyed: KeyedPaper): ResultQuestion[] {
  const sections = (keyed.paper.sections ?? []) as { questions: PaperQuestion[] }[]
  return sections.flatMap(s => s.questions).map((q, i) => {
    const entry = (keyed.entries[q.id] ?? {}) as KeyEntryJson
    return {
      id: q.id,
      number: i + 1,
      type: q.type,
      stem: q.stem,
      marks: q.marks,
      negative_marks: q.negative_marks,
      options: (q.options ?? []).map((o, n) => ({ id: o.id, label: String.fromCharCode(65 + n), content: o.content })),
      correct_answer: q.type === 'NUMERICAL'
        ? { value: entry.answer ?? null, tolerance: entry.tolerance ?? null }
        : { option_ids: entry.correct_option_ids ?? [] },
      solution: (keyed.solutions[q.id] as RichDoc | undefined) ?? null,
    }
  })
}
