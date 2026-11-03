import { describe, expect, it } from 'vitest'
import {
  type ClockView,
  currentStage,
  isLastStage,
  returnableStages,
  stageQuestionIds,
  watchedDeadline,
} from '~/engine/stage-navigator'

const END = '2026-11-12T05:30:00Z'
const SECTIONED: ClockView = {
  current_stage_index: 1,
  attempt_deadline: END,
  stages: [
    { index: 0, state: 'LEFT', deadline_at: '2026-11-12T04:50:00Z' },
    { index: 1, state: 'OPEN', deadline_at: '2026-11-12T05:10:00Z' },
    { index: 2, state: 'NOT_ENTERED', deadline_at: END },
  ],
}

describe('stage navigator (frontend_spec.md §5.3)', () => {
  it('finds the current stage and the deadline to count down to', () => {
    expect(currentStage(SECTIONED)?.index).toBe(1)
    expect(watchedDeadline(SECTIONED)).toBe('2026-11-12T05:10:00Z')
  })

  it('falls back to the attempt deadline', () => {
    const odd: ClockView = { ...SECTIONED, current_stage_index: 7 }
    expect(watchedDeadline(odd)).toBe(END)
    const missed: ClockView = { ...SECTIONED, stages: [{ index: 1, state: 'MISSED', deadline_at: null }] }
    expect(watchedDeadline(missed)).toBe(END)
  })

  it('lists stages to go back to only when returning is allowed', () => {
    expect(returnableStages(SECTIONED, true)).toEqual([0])
    expect(returnableStages(SECTIONED, false)).toEqual([])
  })

  it('knows the last stage', () => {
    expect(isLastStage(SECTIONED)).toBe(false)
    expect(isLastStage({ ...SECTIONED, current_stage_index: 2 })).toBe(true)
  })

  it('shows the current stage\'s questions', () => {
    const meta = [{ index: 0, question_ids: ['a'] }, { index: 1, question_ids: ['b', 'c'] }]
    expect(stageQuestionIds(meta, SECTIONED)).toEqual(['b', 'c'])
    expect(stageQuestionIds(meta, { ...SECTIONED, current_stage_index: 2 })).toEqual([])
  })
})
