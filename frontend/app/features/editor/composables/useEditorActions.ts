// T-03's structural changes: add, duplicate, delete and move questions; add and delete
// sections. Each waits its turn in the save queue. Adding and removing update the page in
// place; changes that reshuffle sections reload the test.
import type { QuestionType } from '~/api/types'
import * as editorApi from '~/features/editor/composables/editorApi'
import type { TestEditor } from '~/features/editor/composables/useTestEditor'

export function useEditorActions(editor: TestEditor, testId: string) {
  const { doc, change } = editor

  function sectionOf(questionId: string) {
    return doc.value!.sections.find(section => section.questions.some(question => question.id === questionId))!
  }

  async function addQuestion(type: QuestionType, sectionId: string, afterId: string | null): Promise<string | undefined> {
    const result = await change(revision => editorApi.addQuestion(testId, revision, sectionId, afterId, type))
    if (!result) return undefined
    const section = doc.value!.sections.find(s => s.id === sectionId)!
    const at = afterId ? section.questions.findIndex(q => q.id === afterId) + 1 : 0
    section.questions.splice(at, 0, result.question)
    return result.question.id
  }

  async function duplicateQuestion(questionId: string): Promise<void> {
    const result = await change(revision => editorApi.duplicateQuestion(questionId, revision))
    if (!result) return
    const section = sectionOf(questionId)
    section.questions.splice(section.questions.findIndex(q => q.id === questionId) + 1, 0, result.question)
  }

  async function deleteQuestion(questionId: string): Promise<void> {
    const section = sectionOf(questionId)
    if (await change(revision => editorApi.deleteQuestion(questionId, revision))) {
      section.questions.splice(section.questions.findIndex(q => q.id === questionId), 1)
    }
  }

  /** One place up or down; past a section's edge it joins the neighbouring section. */
  async function moveQuestion(questionId: string, step: -1 | 1): Promise<void> {
    const layout = doc.value!.sections.map(s => ({ id: s.id, question_ids: s.questions.map(q => q.id) }))
    if (!moveInLayout(layout, questionId, step)) return
    if (await change(revision => editorApi.restructure(testId, revision, layout))) await editor.reload()
  }

  async function addSection(afterId: string | null): Promise<void> {
    if (await change(revision => editorApi.addSection(testId, revision, afterId))) await editor.reload()
  }

  async function deleteSection(sectionId: string, questions: 'move_to_previous' | 'delete' | null): Promise<void> {
    if (await change(revision => editorApi.deleteSection(sectionId, revision, questions))) await editor.reload()
  }

  return { addQuestion, duplicateQuestion, deleteQuestion, moveQuestion, addSection, deleteSection }
}

/** Moves the question in `layout`; false when it is already at that end of the test. */
export function moveInLayout(layout: { id: string, question_ids: string[] }[], questionId: string, step: -1 | 1): boolean {
  const from = layout.findIndex(section => section.question_ids.includes(questionId))
  const ids = layout[from]!.question_ids
  const index = ids.indexOf(questionId)
  const target = index + step
  if (target >= 0 && target < ids.length) {
    ids.splice(index, 1)
    ids.splice(target, 0, questionId)
    return true
  }
  const neighbour = layout[from + step]
  if (!neighbour) return false
  ids.splice(index, 1)
  if (step < 0) neighbour.question_ids.push(questionId)
  else neighbour.question_ids.unshift(questionId)
  return true
}
