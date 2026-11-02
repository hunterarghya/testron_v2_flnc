// The editor's schema per profile: the same allow-list the server checks and RichContentView
// draws (editor_content_spec.md §1-§2, §4.1). Anything not here can't be typed or pasted in.
import type { AnyExtension } from '@tiptap/core'
import Subscript from '@tiptap/extension-subscript'
import Superscript from '@tiptap/extension-superscript'
import { TableKit } from '@tiptap/extension-table'
import TextAlign from '@tiptap/extension-text-align'
import { ImageKitImage, ImageUpload } from '~/shared/components/rich-content/extensions/image'
import { CompactLimits } from '~/shared/components/rich-content/extensions/limits'
import { MathBlock, MathInline } from '~/shared/components/rich-content/extensions/math'

export type Profile = 'full' | 'compact'

/** StarterKit parts that are off: no headings, quotes, code, rules, links or strike-through. */
export function starterKitOptions(profile: Profile): Record<string, unknown> {
  const off = {
    blockquote: false,
    code: false,
    codeBlock: false,
    heading: false,
    horizontalRule: false,
    link: false,
    strike: false,
    trailingNode: false,
  }
  // Options are a few words, an image, inline maths: no lists (§1)
  const compactOff = { bulletList: false, orderedList: false, listItem: false, listKeymap: false }
  return profile === 'compact' ? { ...off, ...compactOff } : off
}

export function richExtensions(profile: Profile): AnyExtension[] {
  const both: AnyExtension[] = [
    // Sub- and superscript can't both be on the same text (§2.2)
    Subscript.extend({ excludes: 'superscript' }),
    Superscript.extend({ excludes: 'subscript' }),
    MathInline,
    ImageKitImage,
    ImageUpload,
  ]
  if (profile === 'compact') return [...both, CompactLimits]
  return [
    ...both,
    MathBlock,
    TextAlign.configure({ types: ['paragraph'], alignments: ['left', 'center'] }),
    // No resizing or merging (§2.1)
    TableKit.configure({ table: { resizable: false, allowTableNodeSelection: false } }),
  ]
}
