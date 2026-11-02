import { describe, expect, it } from 'vitest'
import type { EditorQuestion } from '~/api/types'
import { moveInLayout } from '~/features/editor/composables/useEditorActions'
import { adoptIds, isNewOption, newOption, optionLabel, questionBody, retyped } from '~/features/editor/utils/question-body'
import { formatDecimal } from '~/shared/utils/decimals'
import { formatDuration } from '~/shared/utils/time'
import { EMPTY_DOC, textToDoc } from '../../docs'

function question(changes: Partial<EditorQuestion> = {}): EditorQuestion {
  return {
    id: 'q1', section_id: 's1', position: 0, type: 'MCQ', stem: textToDoc('Which organelle?'), solution: null,
    marks_override: null, negative_marks_override: null, time_override_s: null,
    options: [{ id: 'o1', content: textToDoc('Mitochondria'), is_correct: true }],
    numeric_answer: null, numeric_tolerance: '0',
    chapter_tags: [{ id: 't1', kind: 'CHAPTER', name: 'Cell' }], topic_tags: [],
    ...changes,
  }
}

describe('question payloads', () => {
  it('sends the whole question with tags by name and new options without ids', () => {
    const local = question()
    local.options.push(newOption(textToDoc('Golgi')))

    const body = questionBody(local)

    expect(body.chapter_tags).toEqual(['Cell'])
    expect(body.options?.map(o => o.id)).toEqual(['o1', null])
    expect(body).not.toHaveProperty('numeric_answer')
  })

  it('numerical questions send the answer and no options', () => {
    const body = questionBody(question({ type: 'NUMERICAL', numeric_answer: '6.02', options: [] }))

    expect([body.options, body.numeric_answer, body.numeric_tolerance]).toEqual([[], '6.02', '0'])
  })

  it('adopts the ids the server gave new options and tags', () => {
    const local = question({ chapter_tags: [{ id: '', kind: 'CHAPTER', name: 'cell ' }] })
    local.options.push(newOption())
    const saved = question({ options: [local.options[0]!, { id: 'o2', content: EMPTY_DOC, is_correct: false }] })

    adoptIds(local, saved)

    expect(local.options.map(o => o.id)).toEqual(['o1', 'o2'])
    expect(local.chapter_tags[0]!.id).toBe('t1')
  })

  it('a type switch keeps, drops or starts options as the rules say', () => {
    const local = question()
    retyped(local, 'MSQ')
    expect(local.options).toHaveLength(1)
    retyped(local, 'NUMERICAL')
    expect(local.options).toHaveLength(0)
    retyped(local, 'MCQ')
    expect(local.options.every(isNewOption)).toBe(true)
    expect(local.options).toHaveLength(4)
  })

  it('labels options A, B, C…', () => {
    expect([0, 1, 9].map(optionLabel)).toEqual(['A', 'B', 'J'])
  })
})

describe('moving a question', () => {
  const layout = () => [{ id: 's1', question_ids: ['a', 'b'] }, { id: 's2', question_ids: ['c'] }]

  it('moves within a section, across sections, and not past the ends', () => {
    const within = layout()
    expect(moveInLayout(within, 'a', 1)).toBe(true)
    expect(within[0]!.question_ids).toEqual(['b', 'a'])

    const across = layout()
    expect(moveInLayout(across, 'b', 1)).toBe(true)
    expect(across.map(s => s.question_ids)).toEqual([['a'], ['b', 'c']])

    const back = layout()
    expect(moveInLayout(back, 'c', -1)).toBe(true)
    expect(back.map(s => s.question_ids)).toEqual([['a', 'b', 'c'], []])

    expect(moveInLayout(layout(), 'a', -1)).toBe(false)
    expect(moveInLayout(layout(), 'c', 1)).toBe(false)
  })
})

describe('formatting', () => {
  it.each([['4.00', '4'], ['2.50', '2.5'], ['120', '120'], ['0.25', '0.25']])('%s reads %s', (raw, shown) => {
    expect(formatDecimal(raw)).toBe(shown)
  })

  it.each([[45, '45 s'], [3000, '50 min'], [3600, '1 h'], [4800, '1 h 20 min']])('%i s is %s', (seconds, shown) => {
    expect(formatDuration(seconds)).toBe(shown)
  })
})
