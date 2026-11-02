// T-03's state: the test as loaded, edited in place, with every change saved through one queue
// (editor_content_spec.md §4.4). Typing never waits for a save. The outline's problems and
// totals come from each save's answer; the whole test is never re-fetched after a save.
import { computed, onBeforeUnmount, ref, shallowRef } from 'vue'
import { useToast } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { type ApiProblem, toProblem } from '~/api/problems'
import type { EditorQuestion, EditorSection, TestDocument, TestMutation } from '~/api/types'
import { getTest, type SavePayload, sendSave } from '~/features/editor/composables/editorApi'
import { pendingStore, setAsideForRecovery } from '~/features/editor/utils/pending-store'
import { adoptIds, questionBody } from '~/features/editor/utils/question-body'
import { type Mutation, SaveQueue, type SaveStatus } from '~/features/editor/utils/save-queue'

export const SAVE_DELAY_MS = 800

export function useTestEditor(testId: string) {
  const toast = useToast()
  const doc = ref<TestDocument | null>(null)
  const loadProblem = shallowRef<ApiProblem | null>(null)
  const status = ref<SaveStatus>('saved')
  const readOnly = computed(() => status.value === 'conflict')
  let queue: SaveQueue<SavePayload> | null = null
  const timers = new Map<string, { timer: ReturnType<typeof setTimeout>, build: () => SavePayload }>()

  async function load(): Promise<void> {
    try {
      doc.value = await getTest(testId)
      loadProblem.value = null
    }
    catch (caught) {
      loadProblem.value = toProblem(caught)
      return
    }
    queue = new SaveQueue<SavePayload>({
      revision: doc.value.revision,
      send: (payload, revision) => sendSave(testId, payload, revision),
      store: pendingStore<SavePayload>(testId),
      onSaved,
      onFailed: (_key, problem) => toast.add({ title: 'Couldn\'t save a change', description: problemMessage(problem), color: 'error' }),
      onStatus: (next) => {
        status.value = next
        if (next === 'conflict') setAsideForRecovery(testId)
      },
    })
  }

  function onSaved(key: string, result: Mutation): void {
    apply(result as TestMutation)
    const saved = (result as { question?: EditorQuestion }).question
    if (key.startsWith('question:') && saved) {
      const local = findQuestion(saved.id)
      if (local) adoptIds(local, saved)
    }
  }

  /** The outline's numbers after any change. */
  function apply(result: TestMutation): void {
    if (!doc.value) return
    doc.value.revision = result.revision
    doc.value.problems = result.problems
    doc.value.totals = result.totals
  }

  function findQuestion(id: string): EditorQuestion | undefined {
    return doc.value?.sections.flatMap(section => section.questions).find(question => question.id === id)
  }

  function schedule(key: string, build: () => SavePayload): void {
    clearTimeout(timers.get(key)?.timer)
    timers.set(key, { build, timer: setTimeout(() => flush(key), SAVE_DELAY_MS) })
  }

  function flush(key: string): void {
    const waiting = timers.get(key)
    if (!waiting) return
    clearTimeout(waiting.timer)
    timers.delete(key)
    queue?.save(key, waiting.build())
  }

  function flushAll(): void {
    for (const key of [...timers.keys()]) flush(key)
  }

  const edits = {
    question: (question: EditorQuestion) =>
      schedule(`question:${question.id}`, () => ({ kind: 'question', id: question.id, body: questionBody(question) })),
    test: () => schedule('test', () => ({ kind: 'test', body: { title: doc.value!.title, instructions: doc.value!.instructions } })),
    section: (section: EditorSection) =>
      schedule(`section:${section.id}`, () => ({ kind: 'section', id: section.id, body: { title: section.title, duration_s: section.duration_s } })),
  }

  /** A structural change (add, delete, reorder): typed edits go first, then it takes its turn. */
  async function change<T extends TestMutation>(task: (revision: number) => Promise<T>): Promise<T | undefined> {
    flushAll()
    try {
      const result = await queue!.run(task)
      apply(result)
      return result
    }
    catch (caught) {
      toast.add({ title: problemMessage(toProblem(caught)), color: 'error' })
      return undefined
    }
  }

  async function reload(): Promise<void> {
    flushAll()
    doc.value = await getTest(testId)
    queue!.revision = doc.value.revision
  }

  const onPageHide = () => flushAll()
  window.addEventListener('pagehide', onPageHide)
  onBeforeUnmount(() => {
    flushAll()
    window.removeEventListener('pagehide', onPageHide)
  })

  return { doc, loadProblem, status, readOnly, load, edits, flush, flushAll, change, reload, findQuestion }
}

export type TestEditor = ReturnType<typeof useTestEditor>
