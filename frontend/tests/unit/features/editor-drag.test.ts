import { describe, expect, it, vi } from 'vitest'
import type { EditorSection } from '~/api/types'
import { placeInLayout } from '~/features/editor/composables/useEditorActions'
import { createQuestionDrag } from '~/features/editor/composables/useQuestionDrag'

const layout = () => [{ id: 's1', question_ids: ['a', 'b', 'c'] }, { id: 's2', question_ids: ['d'] }]

describe('placing a dropped question', () => {
  it('goes before the target, into another section, or last', () => {
    const before = layout()
    expect(placeInLayout(before, 'c', 's1', 'a')).toBe(true)
    expect(before[0]!.question_ids).toEqual(['c', 'a', 'b'])

    const across = layout()
    expect(placeInLayout(across, 'a', 's2', 'd')).toBe(true)
    expect(across.map(s => s.question_ids)).toEqual([['b', 'c'], ['a', 'd']])

    const last = layout()
    expect(placeInLayout(last, 'a', 's2', null)).toBe(true)
    expect(last[1]!.question_ids).toEqual(['d', 'a'])
  })

  it('a drop that changes nothing sends nothing', () => {
    expect(placeInLayout(layout(), 'a', 's1', 'a')).toBe(false)
    expect(placeInLayout(layout(), 'a', 's1', 'b')).toBe(false)
    expect(placeInLayout(layout(), 'a', 'gone', null)).toBe(false)
  })
})

describe('dragging', () => {
  const section = { id: 's1', questions: [{ id: 'a' }, { id: 'b' }] } as EditorSection

  function overEvent(clientY: number): DragEvent {
    const target = { getBoundingClientRect: () => ({ top: 0, height: 100 }) }
    return { clientY, currentTarget: target, preventDefault: vi.fn() } as unknown as DragEvent
  }

  it('the upper half drops before a question, the lower half after it', async () => {
    const drop = vi.fn(() => Promise.resolve())
    const drag = createQuestionDrag(drop)
    drag.start({ target: { closest: () => null }, dataTransfer: null } as unknown as DragEvent, 'b')

    drag.overQuestion(overEvent(20), section, 'a')
    expect(drag.target.value).toEqual({ sectionId: 's1', beforeId: 'a' })
    drag.overQuestion(overEvent(80), section, 'a')
    expect(drag.target.value).toEqual({ sectionId: 's1', beforeId: 'b' })
    drag.overQuestion(overEvent(80), section, 'b')
    expect(drag.target.value).toEqual({ sectionId: 's1', beforeId: null })

    await drag.finish()
    expect(drop).toHaveBeenCalledWith('b', { sectionId: 's1', beforeId: null })
    expect(drag.dragging.value).toBeNull()
  })

  it('over a section header it goes first; without a drag nothing happens', async () => {
    const drop = vi.fn(() => Promise.resolve())
    const drag = createQuestionDrag(drop)

    drag.overSection(overEvent(0), section)
    await drag.finish()
    expect(drop).not.toHaveBeenCalled()

    drag.start({ target: { closest: () => null }, dataTransfer: null } as unknown as DragEvent, 'b')
    drag.overSection(overEvent(0), section)
    expect(drag.target.value).toEqual({ sectionId: 's1', beforeId: 'a' })
    drag.cancel()
    expect(drag.target.value).toBeNull()
  })
})
