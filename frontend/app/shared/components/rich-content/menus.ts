// The format bar on a selection and the "/" insert menu (screens.md T-03, editor_content_spec.md
// §4.1). Inserting a question or section belongs to the page around the field, so those are
// passed up as commands; images open the file picker; maths and tables go in here.
import type { EditorSuggestionMenuItem, EditorToolbarItem } from '@nuxt/ui'
import type { Editor } from '@tiptap/core'
import type { Profile } from '~/shared/components/rich-content/extensions'

export type EditorCommand
  = | { kind: 'question', questionType: 'MCQ' | 'MSQ' | 'NUMERICAL' }
    | { kind: 'section' }

/** Inserts that act on the page around the field, offered only where they make sense. */
export type PageInsert = EditorCommand['kind']

export interface InsertCallbacks {
  pickImage: () => void
  command: (command: EditorCommand) => void
}

type Handlers = ReturnType<typeof useInsertHandlers>
type ToolbarItem = EditorToolbarItem<Handlers>
type SlashItem = EditorSuggestionMenuItem<Handlers>

export function toolbarItems(profile: Profile): ToolbarItem[][] {
  const marks: ToolbarItem[] = [
    { 'kind': 'mark', 'mark': 'bold', 'icon': 'i-lucide-bold', 'aria-label': 'Bold' },
    { 'kind': 'mark', 'mark': 'italic', 'icon': 'i-lucide-italic', 'aria-label': 'Italic' },
    { 'kind': 'mark', 'mark': 'underline', 'icon': 'i-lucide-underline', 'aria-label': 'Underline' },
    { 'kind': 'subscript', 'icon': 'i-lucide-subscript', 'aria-label': 'Subscript (Ctrl+,)' },
    { 'kind': 'superscript', 'icon': 'i-lucide-superscript', 'aria-label': 'Superscript (Ctrl+.)' },
  ]
  if (profile === 'compact') return [marks]
  return [marks, [
    { 'kind': 'bulletList', 'icon': 'i-lucide-list', 'aria-label': 'Bulleted list' },
    { 'kind': 'orderedList', 'icon': 'i-lucide-list-ordered', 'aria-label': 'Numbered list' },
    { 'kind': 'textAlign', 'align': 'center', 'icon': 'i-lucide-align-center', 'aria-label': 'Centre' },
  ]]
}

export function slashItems(profile: Profile, page: PageInsert[] = []): SlashItem[][] {
  const inserts: SlashItem[] = [
    { kind: 'image', label: 'Image', icon: 'i-lucide-image' },
    { kind: 'math', display: profile === 'full', label: 'Equation', icon: 'i-lucide-sigma' },
  ]
  if (profile === 'compact') return [inserts]
  const questions: SlashItem[] = page.includes('question')
    ? [
        { kind: 'question', questionType: 'MCQ', label: 'MCQ (single correct)', icon: 'i-lucide-circle-dot' },
        { kind: 'question', questionType: 'MSQ', label: 'MSQ (multiple correct)', icon: 'i-lucide-square-check' },
        { kind: 'question', questionType: 'NUMERICAL', label: 'Numerical', icon: 'i-lucide-hash' },
      ]
    : []
  const sections: SlashItem[] = page.includes('section') ? [{ kind: 'section', label: 'Section', icon: 'i-lucide-separator-horizontal' }] : []
  const content: SlashItem[] = [...inserts, { kind: 'table', label: 'Table', icon: 'i-lucide-table' }]
  return [[...questions, ...sections], content].filter(group => group.length)
}

/** Handlers for the menu kinds Nuxt UI doesn't know. Each returns a chain, as its menus expect. */
export function useInsertHandlers(callbacks: InsertCallbacks) {
  const always = () => true
  const never = () => false
  return {
    // Nuxt UI's mark handler knows only its own marks; these two are ours (§2.2)
    subscript: {
      canExecute: (editor: Editor) => editor.can().toggleSubscript(),
      isActive: (editor: Editor) => editor.isActive('subscript'),
      execute: (editor: Editor) => editor.chain().focus().toggleSubscript(),
    },
    superscript: {
      canExecute: (editor: Editor) => editor.can().toggleSuperscript(),
      isActive: (editor: Editor) => editor.isActive('superscript'),
      execute: (editor: Editor) => editor.chain().focus().toggleSuperscript(),
    },
    image: {
      canExecute: always,
      isActive: never,
      execute: (editor: Editor) => {
        callbacks.pickImage()
        return editor.chain()
      },
    },
    math: {
      canExecute: always,
      isActive: never,
      execute: (editor: Editor, item: { display?: boolean }) => editor.chain().focus().insertMath(Boolean(item.display)),
    },
    table: {
      canExecute: always,
      isActive: never,
      execute: (editor: Editor) => editor.chain().focus().insertTable({ rows: 3, cols: 2, withHeaderRow: true }),
    },
    question: {
      canExecute: always,
      isActive: never,
      execute: (editor: Editor, item: { questionType: 'MCQ' | 'MSQ' | 'NUMERICAL' }) => {
        callbacks.command({ kind: 'question', questionType: item.questionType })
        return editor.chain()
      },
    },
    section: {
      canExecute: always,
      isActive: never,
      execute: (editor: Editor) => {
        callbacks.command({ kind: 'section' })
        return editor.chain()
      },
    },
  }
}
