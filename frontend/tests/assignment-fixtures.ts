// An assignment as the teacher's screens receive it, for component tests.
import type { AssignmentDetail } from '~/api/types'

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
