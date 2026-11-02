// The words of rich content on one line, for lists and pickers (equations as their LaTeX).
import type { RichDoc } from '~/api/types'
import type { PmNode } from '~/shared/components/rich-content/convert'

function words(nodes: PmNode[] = []): string[] {
  return nodes.flatMap((node) => {
    if (node.type === 'text') return [node.text ?? '']
    if (node.type === 'math') return [` ${String(node.attrs?.latex ?? '')} `]
    if (node.type === 'image') return [' [image] ']
    return [...words(node.content), ' ']
  })
}

export function plainText(doc: RichDoc | null | undefined): string {
  return words(doc?.content as PmNode[] | undefined).join('').replace(/\s+/g, ' ').trim()
}
