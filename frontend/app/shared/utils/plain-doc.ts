// Plain text <-> rich-content documents, for the editor's interim text fields (ADR-065) until
// the TipTap editor arrives (step 3.8). One paragraph per line; nothing else is produced.
import type { RichDoc } from '~/api/types'

interface Node {
  type: string
  text?: string
  marks?: unknown[]
  content?: Node[]
}

export const EMPTY_DOC: RichDoc = { v: 1, type: 'doc', content: [] }

function blocks(doc: RichDoc | null | undefined): Node[] {
  const content = doc?.content
  return Array.isArray(content) ? (content as Node[]) : []
}

/** True when the document is only unformatted paragraphs, so plain text can edit it safely. */
export function isPlainDoc(doc: RichDoc | null | undefined): boolean {
  return blocks(doc).every(block =>
    block.type === 'paragraph'
    && (block.content ?? []).every(inline => (inline.type === 'text' && !inline.marks?.length) || inline.type === 'hardBreak'),
  )
}

export function docToText(doc: RichDoc | null | undefined): string {
  return blocks(doc)
    .map(block => (block.content ?? []).map(inline => (inline.type === 'text' ? inline.text ?? '' : '\n')).join(''))
    .join('\n')
}

export function textToDoc(text: string): RichDoc {
  const lines = text.split('\n')
  const content = lines.map(line => (line ? { type: 'paragraph', content: [{ type: 'text', text: line }] } : { type: 'paragraph' }))
  // Empty paragraphs at either end are trimmed by the server too (editor_content_spec.md §3)
  while (content.length && !('content' in content[0]!)) content.shift()
  while (content.length && !('content' in content[content.length - 1]!)) content.pop()
  return { v: 1, type: 'doc', content }
}

/** The visible text of any document, for previews of formatted fields and empty checks. */
export function summaryText(doc: RichDoc | null | undefined): string {
  const walk = (nodes: Node[]): string => nodes.map(node => node.text ?? walk(node.content ?? [])).join(' ')
  return walk(blocks(doc)).replace(/\s+/g, ' ').trim()
}
