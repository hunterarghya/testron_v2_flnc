// Drag a question by its ⠿ handle (T-03): over another question it goes before or after it (by
// which half the pointer is in); over a section header it goes first in that section.
import { type InjectionKey, inject, provide, ref } from 'vue'
import type { EditorSection } from '~/api/types'

export interface DropTarget {
  sectionId: string
  beforeId: string | null
}

export function createQuestionDrag(drop: (questionId: string, target: DropTarget) => Promise<void>) {
  const dragging = ref<string | null>(null)
  const target = ref<DropTarget | null>(null)

  function start(event: DragEvent, questionId: string): void {
    dragging.value = questionId
    event.dataTransfer?.setData('text/plain', questionId)
    if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
    const block = (event.target as HTMLElement).closest('section')
    if (block && event.dataTransfer) event.dataTransfer.setDragImage(block, 16, 16)
  }

  function overQuestion(event: DragEvent, section: EditorSection, questionId: string): void {
    if (!dragging.value) return
    event.preventDefault()
    const box = (event.currentTarget as HTMLElement).getBoundingClientRect()
    const lowerHalf = event.clientY > box.top + box.height / 2
    const index = section.questions.findIndex(q => q.id === questionId)
    const beforeId = lowerHalf ? section.questions[index + 1]?.id ?? null : questionId
    target.value = { sectionId: section.id, beforeId }
  }

  function overSection(event: DragEvent, section: EditorSection): void {
    if (!dragging.value) return
    event.preventDefault()
    target.value = { sectionId: section.id, beforeId: section.questions[0]?.id ?? null }
  }

  async function finish(): Promise<void> {
    const questionId = dragging.value
    const where = target.value
    dragging.value = null
    target.value = null
    if (questionId && where) await drop(questionId, where)
  }

  function cancel(): void {
    dragging.value = null
    target.value = null
  }

  return { dragging, target, start, overQuestion, overSection, finish, cancel }
}

export type QuestionDrag = ReturnType<typeof createQuestionDrag>
const KEY: InjectionKey<QuestionDrag> = Symbol('question-drag')

export function provideQuestionDrag(drag: QuestionDrag): void {
  provide(KEY, drag)
}

export function useQuestionDrag(): QuestionDrag {
  const drag = inject(KEY)
  if (!drag) throw new Error('useQuestionDrag() outside the test editor')
  return drag
}
