// The open test's editor, shared with the blocks inside it without passing it down by hand.
import { inject, type InjectionKey, provide } from 'vue'
import type { useEditorActions } from '~/features/editor/composables/useEditorActions'
import type { TestEditor } from '~/features/editor/composables/useTestEditor'

export interface EditorContext {
  testId: string
  editor: TestEditor
  actions: ReturnType<typeof useEditorActions>
}

const KEY: InjectionKey<EditorContext> = Symbol('test-editor')

export function provideEditor(context: EditorContext): void {
  provide(KEY, context)
}

export function useEditorContext(): EditorContext {
  const context = inject(KEY)
  if (!context) throw new Error('useEditorContext() outside the test editor')
  return context
}
