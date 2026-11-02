// Stored rich content <-> the editor's document (editor_content_spec.md §2). They differ in
// two places only: the stored document has `"v": 1`, and stored math is one `math` node with a
// `display` flag, where the editor needs an inline node and a block node. Upload placeholders
// exist only in the editor and are never saved (§5.1).
import type { RichDoc } from '~/api/types'

export interface PmNode {
  type: string
  attrs?: Record<string, unknown>
  content?: PmNode[]
  marks?: { type: string, attrs?: Record<string, unknown> }[]
  text?: string
}

export const EMPTY_DOC: RichDoc = { v: 1, type: 'doc', content: [] }

export const MATH_INLINE = 'mathInline'
export const MATH_BLOCK = 'mathBlock'
export const IMAGE_UPLOAD = 'imageUpload'
// The server's limit for one equation (editor_content_spec.md §2.1)
export const MAX_LATEX = 2000

function mapNodes(nodes: PmNode[] | undefined, map: (node: PmNode) => PmNode | null): PmNode[] | undefined {
  if (!nodes) return undefined
  return nodes.flatMap((node) => {
    const mapped = map(node)
    if (!mapped) return []
    return [{ ...mapped, ...(mapped.content ? { content: mapNodes(mapped.content, map) } : {}) }]
  })
}

/** What the editor loads. */
export function toEditor(doc: RichDoc | null | undefined): PmNode {
  const content = mapNodes((doc?.content as PmNode[] | undefined) ?? [], (node) => {
    if (node.type !== 'math') return node
    return { ...node, type: node.attrs?.display ? MATH_BLOCK : MATH_INLINE, attrs: { latex: node.attrs?.latex ?? '' } }
  }) ?? []
  // ProseMirror needs at least one block to put the cursor in
  return { type: 'doc', content: content.length ? content : [{ type: 'paragraph' }] }
}

/** What is saved: math back to one node type, upload placeholders left out. */
export function fromEditor(json: PmNode): RichDoc {
  const content = mapNodes(json.content, (node) => {
    if (node.type === IMAGE_UPLOAD) return null
    if (node.type === MATH_INLINE || node.type === MATH_BLOCK) {
      return { type: 'math', attrs: { latex: node.attrs?.latex ?? '', display: node.type === MATH_BLOCK } }
    }
    return node
  }) ?? []
  return { v: 1, type: 'doc', content: trimEmpty(content) }
}

/** Empty paragraphs at either end are not content (the server trims them too). */
function trimEmpty(blocks: PmNode[]): PmNode[] {
  const isEmpty = (node: PmNode | undefined) => node?.type === 'paragraph' && !node.content?.length
  let start = 0
  let end = blocks.length
  while (start < end && isEmpty(blocks[start])) start++
  while (end > start && isEmpty(blocks[end - 1])) end--
  return blocks.slice(start, end)
}
