import { describe, expect, it } from 'vitest'
import { ApiProblem } from '~/api/problems'
import { outcomeOf } from '~/features/exam-hall/composables/hallQueue'
import { ENDING_TITLE, hallTitle, saveStatus } from '~/features/exam-hall/utils/hall-text'
import { hasAnswer, paletteCounts, paletteMark, responsesFrom, serverSeq } from '~/features/exam-hall/utils/palette'

const problem = (code: string, status = 409) => new ApiProblem({ status, code, detail: code })

describe('palette (P-03)', () => {
  it('marks each question', () => {
    expect(paletteMark(undefined)).toBe('not_visited')
    expect(paletteMark({ answer: null, marked_for_review: false, visited: true })).toBe('not_answered')
    expect(paletteMark({ answer: { v: 1, kind: 'NUMERIC', value: '4' }, marked_for_review: false, visited: true })).toBe('answered')
    expect(paletteMark({ answer: null, marked_for_review: true, visited: true })).toBe('marked')
  })

  it('an empty choice or value is no answer', () => {
    expect(hasAnswer({ v: 1, kind: 'CHOICE', option_ids: [] })).toBe(false)
    expect(hasAnswer({ v: 1, kind: 'CHOICE', option_ids: ['o'] })).toBe(true)
    expect(hasAnswer({ v: 1, kind: 'NUMERIC', value: '' })).toBe(false)
    expect(hasAnswer(null)).toBe(false)
  })

  it('counts the legend and reads the server\'s answers', () => {
    const server = {
      a: { answer: { v: 1 as const, kind: 'CHOICE' as const, option_ids: ['o'] }, marked_for_review: false, visited: true, client_seq: 4 },
      b: { answer: null, marked_for_review: false, visited: true, client_seq: 0 },
    }
    const local = responsesFrom(server)
    expect(paletteCounts(['a', 'b', 'c'], local)).toEqual({ answered: 1, not_answered: 1, not_visited: 1, marked: 0 })
    expect(serverSeq(server)).toBe(4)
    expect(serverSeq({})).toBe(0)
  })
})

describe('hall text', () => {
  it('says how the save is going', () => {
    expect(saveStatus(0, false).label).toBe('Saved')
    expect(saveStatus(2, false).label).toBe('Saving…')
    expect(saveStatus(1, true).label).toBe('Offline, 1 answer waiting')
    expect(saveStatus(3, true).label).toBe('Offline, 3 answers waiting')
  })

  it('names each ending and the take', () => {
    expect(ENDING_TITLE.TIMED_OUT).toBe('Time\'s up — submitted')
    expect(hallTitle('Cell Biology', 2)).toBe('Cell Biology – Take 2')
  })
})

describe('what the queue does with a refusal', () => {
  it.each([
    ['attempt_ended', 'ended'],
    ['attempt_taken_over', 'taken_over'],
    ['stage_closed', 'drop'],
    ['answer_invalid', 'drop'],
    ['network_error', 'retry'],
    ['internal_error', 'retry'],
    ['rate_limited', 'retry'],
  ])('%s → %s', (code, outcome) => {
    expect(outcomeOf(problem(code))).toBe(outcome)
  })
})
