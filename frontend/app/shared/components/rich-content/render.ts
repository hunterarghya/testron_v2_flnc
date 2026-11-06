// Stored rich content -> Vue elements (editor_content_spec.md §6). Each allowed node and mark maps
// to one element; text is a text node, so Vue escapes it. Anything unknown is left out (the server
// never stores it, so it can only mean a newer format than this page knows).
import { h, type VNode } from 'vue'
import type { PmNode } from '~/shared/components/rich-content/convert'
import { displayUrl, type ImageSize, SIZE_CLASS } from '~/shared/components/rich-content/image-url'
import MathSpan from '~/shared/components/rich-content/MathSpan.vue'

const MARK_TAGS: Record<string, string> = { bold: 'strong', italic: 'em', underline: 'u', subscript: 'sub', superscript: 'sup' }

type Renderer = (node: PmNode, children: () => (VNode | string)[]) => VNode | string | null

const RENDERERS: Record<string, Renderer> = {
  paragraph: (node, children) => h('p', { class: node.attrs?.textAlign === 'center' ? 'text-center' : undefined }, children()),
  text: node => marked(node),
  hardBreak: () => h('br'),
  bulletList: (_node, children) => h('ul', { class: 'list-disc ps-6' }, children()),
  orderedList: (node, children) => h('ol', { class: 'list-decimal ps-6', start: node.attrs?.start ?? undefined }, children()),
  listItem: (_node, children) => h('li', children()),
  table: (_node, children) => h('table', { class: 'my-2 border-collapse' }, [h('tbody', children())]),
  tableRow: (_node, children) => h('tr', children()),
  tableHeader: (_node, children) => h('th', { class: 'border border-default px-2 py-1 font-semibold' }, children()),
  tableCell: (_node, children) => h('td', { class: 'border border-default px-2 py-1' }, children()),
  math: node => h(MathSpan, { latex: String(node.attrs?.latex ?? ''), display: Boolean(node.attrs?.display) }),
  image: node => image(node),
}

export function renderNodes(nodes: PmNode[] | undefined, eagerImages = false): (VNode | string)[] {
  return (nodes ?? []).flatMap((node) => {
    const render = RENDERERS[node.type]
    const result = render ? render(withLoading(node, eagerImages), () => renderNodes(node.content, eagerImages)) : null
    return result === null ? [] : [result]
  })
}

function marked(node: PmNode): VNode | string {
  // Innermost first, so the first mark is the outer element
  return [...(node.marks ?? [])].reverse().reduce<VNode | string>((inner, mark) => {
    const tag = MARK_TAGS[mark.type]
    return tag ? h(tag, [inner]) : inner
  }, node.text ?? '')
}

function withLoading(node: PmNode, eager: boolean): PmNode {
  return node.type === 'image' ? { ...node, attrs: { ...node.attrs, eager } } : node
}

function image(node: PmNode): VNode {
  const attrs = node.attrs ?? {}
  const size = (attrs.size ?? 'M') as ImageSize
  const caption = String(attrs.caption ?? '')
  return h('figure', { class: ['my-2 max-w-full', SIZE_CLASS[size]] }, [
    h('img', {
      src: displayUrl(String(attrs.src ?? ''), size),
      alt: String(attrs.alt ?? ''),
      width: attrs.width,
      height: attrs.height,
      // Lazy everywhere except the exam hall's current question (§5.2)
      loading: attrs.eager ? 'eager' : 'lazy',
      class: 'h-auto max-w-full rounded',
    }),
    caption ? h('figcaption', { class: 'text-center text-sm text-muted break-words' }, caption) : null,
  ])
}
