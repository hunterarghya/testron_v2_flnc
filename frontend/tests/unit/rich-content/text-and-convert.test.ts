import { describe, expect, it } from 'vitest'
import { cleanText } from '~/shared/components/rich-content/clean-text'
import { EMPTY_DOC, fromEditor, IMAGE_UPLOAD, MATH_BLOCK, MATH_INLINE, toEditor } from '~/shared/components/rich-content/convert'
import { displayUrl } from '~/shared/components/rich-content/image-url'

// Bengali, built from code points so no invisible character hides in the source
const KA = String.fromCodePoint(0x0995)
const E_SIGN = String.fromCodePoint(0x09C7)
const AA_SIGN = String.fromCodePoint(0x09BE)
const O_SIGN = String.fromCodePoint(0x09CB)
const ZWJ = String.fromCodePoint(0x200D)
const ZWNJ = String.fromCodePoint(0x200C)
const RLO = String.fromCodePoint(0x202E)
const LRI = String.fromCodePoint(0x2066)
const BOM = String.fromCodePoint(0xFEFF)

describe('cleanText (same rules as the server)', () => {
  it('composes Bengali (NFC) and keeps the joiners', () => {
    expect(cleanText(`${KA}${E_SIGN}${AA_SIGN} র${ZWJ}্য${ZWNJ}`)).toBe(`${KA}${O_SIGN} র${ZWJ}্য${ZWNJ}`)
  })

  it('removes bidi overrides, the byte-order mark and control characters; a tab is a space', () => {
    expect(cleanText(`${RLO}cell${LRI} wall${BOM}\u0007\tok\nnext\u000C`)).toBe('cell wall ok\nnext')
  })
})

describe('stored <-> editor format', () => {
  const stored = {
    v: 1,
    type: 'doc',
    content: [
      { type: 'paragraph', content: [{ type: 'text', text: 'x is ' }, { type: 'math', attrs: { latex: 'x^2', display: false } }] },
      { type: 'math', attrs: { latex: '\\frac{a}{b}', display: true } },
    ],
  }

  it('math becomes inline and block nodes in the editor, and one node type again when saved', () => {
    const editor = toEditor(stored)

    expect(editor.content?.[0]?.content?.[1]).toEqual({ type: MATH_INLINE, attrs: { latex: 'x^2' } })
    expect(editor.content?.[1]).toEqual({ type: MATH_BLOCK, attrs: { latex: '\\frac{a}{b}' } })
    expect(fromEditor(editor)).toEqual(stored)
  })

  it('an empty document opens with one paragraph and saves as empty', () => {
    expect(toEditor(EMPTY_DOC)).toEqual({ type: 'doc', content: [{ type: 'paragraph' }] })
    expect(toEditor(null)).toEqual({ type: 'doc', content: [{ type: 'paragraph' }] })
    expect(fromEditor({ type: 'doc', content: [{ type: 'paragraph' }, { type: 'paragraph' }] })).toEqual(EMPTY_DOC)
  })

  it('upload placeholders are never saved', () => {
    const json = { type: 'doc', content: [{ type: IMAGE_UPLOAD, attrs: { uploadId: 'u1' } }, { type: 'paragraph', content: [{ type: 'text', text: 'kept' }] }] }

    expect(fromEditor(json).content).toEqual([{ type: 'paragraph', content: [{ type: 'text', text: 'kept' }] }])
  })
})

describe('image display', () => {
  it.each([
    ['S', 1, 400],
    ['M', 1, 400],
    ['M', 2, 800],
    ['L', 2, 1200],
    ['FULL', 3, 2400],
  ] as const)('size %s at %ix fetches %ipx', (size, ratio, width) => {
    expect(displayUrl('https://ik.imagekit.io/acme/tests/a.png', size, ratio)).toBe(`https://ik.imagekit.io/acme/tests/a.png?tr=w-${width},q-80,f-auto`)
  })
})
