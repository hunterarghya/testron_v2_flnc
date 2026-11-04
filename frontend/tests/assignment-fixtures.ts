// An assignment as the teacher's screens receive it, for component tests.
import type { AssignmentDetail, Gradebook, KeyedPaper, QuestionStat } from '~/api/types'
import { DOC } from './hall-fixtures'

export function detail(changes: Partial<AssignmentDetail> = {}): AssignmentDetail {
  return {
    id: 'a1',
    title: 'Cell Biology – Take 1',
    test_id: 't1',
    window_kind: 'MANUAL',
    window_summary: { planned_at: null, starts_at: null, opens_at: null, closes_at: null, late_entry_s: 600 },
    state: 'WAITING',
    audience: { count: 2, summary: '11A' },
    progress: { ended: 0, in_progress: 0, audience: 2 },
    publication_state: 'UNPUBLISHED',
    locked: true,
    gate: { requires_activation: true, has_password: true },
    timing: { kind: 'TOTAL', total_duration_s: 3000, allow_return: false },
    integrity: { grace_s: 5, max_warnings: 3, action: 'AUTO_SUBMIT' },
    publication: { mode: 'MANUAL', delay_s: null, content: 'SCORE_ONLY', show_paper: false, show_solutions: false, show_rank_and_stats: false, published_at: null, publish_at: null },
    activated_at: null,
    ended_at: null,
    ends_at: null,
    audience_students: [
      { id: 's1', name: 'Aditi Roy', group_names: ['11A'], has_attempt: false },
      { id: 's2', name: 'Arjun Das', group_names: ['11A'], has_attempt: false },
    ],
    source_group_ids: ['g1'],
    editable_fields: ['title', 'window', 'gate', 'integrity', 'publication', 'audience', 'password'],
    ...changes,
  }
}

// T-11: a closed test with a ranked, a disqualified and an absent student
export const BOOK: Gradebook = {
  title: 'Cell Biology', state: 'CLOSED', publication_state: 'UNPUBLISHED',
  rows: [
    { student_id: 's1', name: 'Mou', attempt_id: 'att1', take_number: 1, status: 'SUBMITTED', rank: 1, score: '7.00', max_score: '12.00', sections: [], time_taken_s: 3000, warning_count: 0, overridden: false },
    { student_id: 's2', name: 'Sneha', attempt_id: 'att2', take_number: 1, status: 'DISQUALIFIED', rank: null, score: '5.00', max_score: '12.00', sections: [], time_taken_s: 1800, warning_count: 3, overridden: false },
    { student_id: 's3', name: 'Rahul', attempt_id: null, take_number: null, status: 'ABSENT', rank: null, score: null, max_score: null, sections: [], time_taken_s: null, warning_count: 0, overridden: false },
  ],
  stats: { count: 1, mean: '7.00', highest: '7.00', lowest: '7.00', attempted: 2, absent: 1, disqualified: 1 },
}
export const STATS: QuestionStat[] = [{ question_id: 'q1', number: 1, type: 'MCQ', answered: 2, correct: 1, partial: 0, top_wrong_option_id: 'o2', top_wrong_count: 1, tags: [] }]
export const KEYED: KeyedPaper = {
  version: 1,
  paper: { sections: [{ questions: [{ id: 'q1', type: 'MCQ', stem: DOC, options: [{ id: 'o1' }, { id: 'o2' }] }] }] },
  entries: { q1: { type: 'MCQ', correct_option_ids: ['o1'] } },
  solutions: {},
}
