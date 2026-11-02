// Rich-content documents for tests: one paragraph per line.
import type { RichDoc } from '~/api/types'

export const EMPTY_DOC: RichDoc = { v: 1, type: 'doc', content: [] }

const NEWLINE = String.fromCodePoint(10)

export function textToDoc(text: string): RichDoc {
  const content = text.split(NEWLINE).filter(Boolean).map(line => ({ type: 'paragraph', content: [{ type: 'text', text: line }] }))
  return { v: 1, type: 'doc', content }
}
