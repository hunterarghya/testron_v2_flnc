import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { api } from '~/api/client'
import type { EditorQuestion, TestDocument, TestMutation } from '~/api/types'
import { useEditorActions } from '~/features/editor/composables/useEditorActions'
import type { TestEditor } from '~/features/editor/composables/useTestEditor'
import { type FakeApi, ok } from '../../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
const MUTATION: TestMutation = { revision: 4, problems: [], totals: { questions: 0, marks: '0', duration_s: 3600 } }

function question(id: string): EditorQuestion {
  return {
    id, section_id: 's1', position: 0, type: 'MCQ', stem: { v: 1, type: 'doc', content: [] }, solution: null,
    marks_override: null, negative_marks_override: null, time_override_s: null, options: [],
    numeric_answer: null, numeric_tolerance: '0', chapter_tags: [], topic_tags: [],
  }
}

function setup() {
  const doc = ref({
    sections: [
      { id: 's1', questions: [question('a'), question('b')] },
      { id: 's2', questions: [question('c')] },
    ],
  } as unknown as TestDocument)
  const editor = {
    doc,
    change: vi.fn(<T extends TestMutation>(task: (revision: number) => Promise<T>) => task(3)),
    reload: vi.fn(() => Promise.resolve()),
  } as unknown as TestEditor
  return { doc, editor, actions: useEditorActions(editor, 't1') }
}

const ids = (doc: TestDocument) => doc.sections.map(s => s.questions.map(q => q.id))

describe('editor actions', () => {
  beforeEach(() => {
    fake.POST.mockReset().mockImplementation(() => ok({ ...MUTATION, question: question('new') }))
    fake.DELETE.mockReset().mockImplementation(() => ok(MUTATION))
    fake.PUT.mockReset().mockImplementation(() => ok(MUTATION))
  })

  it('adds a question where asked and returns its id', async () => {
    const { doc, actions } = setup()

    expect(await actions.addQuestion('MSQ', 's1', 'a')).toBe('new')

    expect(ids(doc.value)).toEqual([['a', 'new', 'b'], ['c']])
    expect(fake.POST.mock.calls[0]![1]).toMatchObject({ body: { revision: 3, section_id: 's1', after_question_id: 'a', type: 'MSQ' } })
  })

  it('duplicates right after and deletes in place', async () => {
    const { doc, actions } = setup()

    await actions.duplicateQuestion('b')
    await actions.deleteQuestion('a')

    expect(ids(doc.value)).toEqual([['b', 'new'], ['c']])
  })

  it('a refused change leaves the page as it was', async () => {
    const { doc, editor, actions } = setup()
    vi.mocked(editor.change).mockResolvedValueOnce(undefined)

    await actions.deleteQuestion('a')

    expect(ids(doc.value)).toEqual([['a', 'b'], ['c']])
  })

  it('moving sends the new layout, then reloads', async () => {
    const { editor, actions } = setup()

    await actions.moveQuestion('b', 1)

    expect(fake.PUT.mock.calls[0]![1]).toMatchObject({ body: { sections: [{ id: 's1', question_ids: ['a'] }, { id: 's2', question_ids: ['b', 'c'] }] } })
    expect(editor.reload).toHaveBeenCalled()
  })

  it('moving past the end does nothing', async () => {
    const { editor, actions } = setup()

    await actions.moveQuestion('c', 1)

    expect(editor.change).not.toHaveBeenCalled()
  })

  it('sections are added and deleted, then the test reloads', async () => {
    const { editor, actions } = setup()

    await actions.addSection('s1')
    await actions.deleteSection('s2', 'move_to_previous')

    expect(fake.DELETE.mock.calls[0]![1]).toMatchObject({ params: { path: { section_id: 's2' }, query: { revision: 3, questions: 'move_to_previous' } } })
    expect(editor.reload).toHaveBeenCalledTimes(2)
  })
})
