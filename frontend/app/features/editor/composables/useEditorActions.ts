// T-03's structural changes: add, duplicate, delete and move questions; add and delete
// sections. Each waits its turn in the save queue. Adding and removing update the page in
// place; changes that reshuffle sections reload the test.
import type { QuestionType, TestPatch } from '~/api/types'
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
    const layout = currentLayout()
    if (!moveInLayout(layout, questionId, step)) return
    if (await change(revision => editorApi.restructure(testId, revision, layout))) await editor.reload()
  }

  async function addSection(afterId: string | null): Promise<void> {
    if (await change(revision => editorApi.addSection(testId, revision, afterId))) await editor.reload()
  }

  async function deleteSection(sectionId: string, questions: 'move_to_previous' | 'delete' | null): Promise<void> {
    if (await change(revision => editorApi.deleteSection(sectionId, revision, questions))) await editor.reload()
  }

  /** Settings change the timing too, which may merge or create sections: the test reloads. */
  async function saveSettings(settings: NonNullable<TestPatch['settings']>): Promise<boolean> {
    const saved = await change(revision => editorApi.saveSettings(testId, revision, settings))
    if (saved) await editor.reload()
    return Boolean(saved)
  }

  async function importQuestions(sourceIds: string[], sectionId: string, afterId: string | null): Promise<number> {
    const result = await change(revision => editorApi.importQuestions(testId, revision, sourceIds, sectionId, afterId))
    if (!result) return 0
    await editor.reload()
    return result.questions.length
  }

  /** Drag and drop: the question goes into `sectionId`, before `beforeId` (or last). */
  async function dropQuestion(questionId: string, sectionId: string, beforeId: string | null): Promise<void> {
    const layout = currentLayout()
    if (!placeInLayout(layout, questionId, sectionId, beforeId)) return
    if (await change(revision => editorApi.restructure(testId, revision, layout))) await editor.reload()
  }

  async function moveSection(sectionId: string, step: -1 | 1): Promise<void> {
    const layout = currentLayout()
    const from = layout.findIndex(section => section.id === sectionId)
    const to = from + step
    if (to < 0 || to >= layout.length) return
    layout.splice(to, 0, ...layout.splice(from, 1))
    if (await change(revision => editorApi.restructure(testId, revision, layout))) await editor.reload()
  }

  function currentLayout() {
    return doc.value!.sections.map(s => ({ id: s.id, question_ids: s.questions.map(q => q.id) }))
  }

  return {
    addQuestion,
    duplicateQuestion,
    deleteQuestion,
    moveQuestion,
    addSection,
    deleteSection,
    saveSettings,
    importQuestions,
    dropQuestion,
    moveSection,
  }
}

/** Puts the question into `sectionId` before `beforeId` (or last); false when nothing moves. */
export function placeInLayout(
  layout: { id: string, question_ids: string[] }[],
  questionId: string,
  sectionId: string,
  beforeId: string | null,
): boolean {
  if (questionId === beforeId) return false
  const before = JSON.stringify(layout)
  for (const section of layout) section.question_ids = section.question_ids.filter(id => id !== questionId)
  const target = layout.find(section => section.id === sectionId)
  if (!target) return false
  const at = beforeId ? target.question_ids.indexOf(beforeId) : -1
  target.question_ids.splice(at < 0 ? target.question_ids.length : at, 0, questionId)
  return JSON.stringify(layout) !== before
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
