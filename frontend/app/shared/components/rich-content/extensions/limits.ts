// An option's content is short (editor_content_spec.md §1, compact profile): at most 3 paragraphs
// and 1 image. A change that would go past that is refused, as the server would refuse it.
import { Extension } from '@tiptap/core'
import { Plugin } from '@tiptap/pm/state'
import type { Node as PmNode } from '@tiptap/pm/model'
import { IMAGE_UPLOAD } from '~/shared/components/rich-content/convert'

export const MAX_OPTION_PARAGRAPHS = 3
export const MAX_OPTION_IMAGES = 1

export function withinCompactLimits(doc: PmNode): boolean {
  let paragraphs = 0
  let images = 0
  doc.forEach((block) => {
    if (block.type.name === 'paragraph') paragraphs++
    if (block.type.name === 'image' || block.type.name === IMAGE_UPLOAD) images++
  })
  return paragraphs <= MAX_OPTION_PARAGRAPHS && images <= MAX_OPTION_IMAGES
}

export const CompactLimits = Extension.create({
  name: 'compactLimits',
  addProseMirrorPlugins: () => [
    new Plugin({
      filterTransaction: transaction => !transaction.docChanged || withinCompactLimits(transaction.doc),
    }),
  ],
})
