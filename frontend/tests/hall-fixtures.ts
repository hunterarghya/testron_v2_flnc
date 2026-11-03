// A student's attempt as the hall receives it, for component tests (api_contract.md §3.4).
import type { AttemptState } from '~/api/types'

export const NOW = new Date().toISOString()
export const LATER = new Date(Date.now() + 3_600_000).toISOString()
export const DOC = { v: 1, type: 'doc', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Which organelle?' }] }] }

export function attempt(changes: Partial<AttemptState> = {}): AttemptState {
  return {
    status: 'IN_PROGRESS', end_reason: null, ended_at: null, server_now: NOW, attempt_deadline: LATER,
    current_stage_index: 0, stages: [{ index: 0, state: 'OPEN', deadline_at: LATER }], warning_count: 0, notice: null,
    attempt_id: 'att1', assignment_id: 'a1', title: 'Cell Biology', take_number: 1, exam_client_id: 'dev1',
    timing: { kind: 'TOTAL', allow_return: false }, integrity: { grace_s: 5, max_warnings: 3, action: 'AUTO_SUBMIT' },
    stage_meta: [{ index: 0, kind: 'WHOLE', title: null, instructions: null, duration_s: 3600, question_ids: ['q1', 'q2'] }],
    questions: [
      { id: 'q1', number: 1, type: 'MCQ', stem: DOC, marks: '4.00', negative_marks: '1.00', time_s: null,
        options: [{ id: 'o1', label: 'A', content: DOC }, { id: 'o2', label: 'B', content: DOC }] },
      { id: 'q2', number: 2, type: 'NUMERICAL', stem: DOC, marks: '4.00', negative_marks: '0.00', time_s: null, options: [] },
    ],
    responses: {},
    ...changes,
  } as AttemptState
}

export function clockOf(state: AttemptState) {
  const { status, end_reason, ended_at, server_now, attempt_deadline, current_stage_index, stages, warning_count, notice } = state
  return { status, end_reason, ended_at, server_now, attempt_deadline, current_stage_index, stages, warning_count, notice }
}
