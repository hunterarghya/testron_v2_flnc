// Equations (editor_content_spec.md §2.1, §4.1): inline inside text, or displayed on its own line
// (full profile only). Typing `$x^2$` makes an inline equation; click one to edit it.
import { mergeAttributes, Node, nodeInputRule } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import MathView from '~/shared/components/rich-content/MathView.vue'
import { MATH_BLOCK, MATH_INLINE } from '~/shared/components/rich-content/convert'

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    math: {
      /** An empty equation at the cursor; its editor opens at once. */
      insertMath: (display: boolean) => ReturnType
    }
  }
}

const latexAttribute = {
  latex: {
    default: '',
    parseHTML: (element: HTMLElement) => element.getAttribute('data-latex') ?? '',
    renderHTML: (attributes: Record<string, unknown>) => ({ 'data-latex': attributes.latex }),
  },
}

export const MathInline = Node.create({
  name: MATH_INLINE,
  group: 'inline',
  inline: true,
  atom: true,
  selectable: true,
  addAttributes: () => latexAttribute,
  parseHTML: () => [{ tag: 'span[data-type="math"]' }],
  renderHTML: ({ HTMLAttributes }) => ['span', mergeAttributes(HTMLAttributes, { 'data-type': 'math' })],
  addNodeView: () => VueNodeViewRenderer(MathView),
  addInputRules() {
    return [nodeInputRule({ find: /\$([^$\n]{1,2000})\$$/, type: this.type, getAttributes: match => ({ latex: match[1] }) })]
  },
  addCommands() {
    return {
      insertMath: display => ({ commands }) =>
        commands.insertContent({ type: display ? MATH_BLOCK : MATH_INLINE, attrs: { latex: '' } }),
    }
  },
})

export const MathBlock = Node.create({
  name: MATH_BLOCK,
  group: 'block',
  atom: true,
  selectable: true,
  addAttributes: () => latexAttribute,
  parseHTML: () => [{ tag: 'div[data-type="math"]' }],
  renderHTML: ({ HTMLAttributes }) => ['div', mergeAttributes(HTMLAttributes, { 'data-type': 'math' })],
  addNodeView: () => VueNodeViewRenderer(MathView),
})
