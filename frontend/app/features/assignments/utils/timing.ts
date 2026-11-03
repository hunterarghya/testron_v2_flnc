// "Timing ✎" in the wizard (T-07 ③): this assignment's paper only, never the test. Its kind
// is always the test's own (api_contract.md §2.6).
import type { TestDocument, TimingOverride } from '~/api/types'

export interface TimingEdit {
  // TOTAL: the whole test, in minutes
  totalMin: number
  // PER_QUESTION: the default time per question, in seconds
  questionS: number
  // SECTIONED: minutes per section id
  sectionMin: Record<string, number>
}

const minutes = (seconds: number | null | undefined) => Math.round((seconds ?? 0) / 60)

/** The test's own timing, as the starting point for an edit. */
export function timingEditFrom(test: TestDocument): TimingEdit {
  const timing = test.settings.timing
  return {
    totalMin: timing.kind === 'TOTAL' ? minutes(timing.duration_s) : 0,
    questionS: timing.kind === 'PER_QUESTION' ? timing.default_question_s : 0,
    sectionMin: Object.fromEntries(test.sections.map(section => [section.id, minutes(section.duration_s)])),
  }
}

export function toTimingOverride(test: TestDocument, edit: TimingEdit): TimingOverride {
  switch (test.settings.timing.kind) {
    case 'TOTAL':
      return { kind: 'TOTAL', duration_s: edit.totalMin * 60 }
    case 'PER_QUESTION':
      return { kind: 'PER_QUESTION', default_question_s: edit.questionS }
    case 'SECTIONED':
      return {
        kind: 'SECTIONED',
        section_durations_s: Object.fromEntries(Object.entries(edit.sectionMin).map(([id, min]) => [id, min * 60])),
      }
  }
}
