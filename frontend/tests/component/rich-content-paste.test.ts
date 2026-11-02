// The paste pipeline end to end (editor_content_spec.md §4.3, §7): cleaned HTML read through the
// editor's own schema, then saved in the stored format. Fixtures: tests/component/fixtures/paste.
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { describe, expect, it } from 'vitest'
import type { RichDoc } from '~/api/types'
import { fromEditor, type PmNode } from '~/shared/components/rich-content/convert'
import { type Profile, richExtensions, starterKitOptions } from '~/shared/components/rich-content/extensions'
import { cleanPastedHtml } from '~/shared/components/rich-content/paste'

const ALLOWED_NODES = new Set(['paragraph', 'text', 'hardBreak', 'bulletList', 'orderedList', 'listItem', 'table', 'tableRow', 'tableHeader', 'tableCell', 'image', 'math'])
const ALLOWED_MARKS = new Set(['bold', 'italic', 'underline', 'subscript', 'superscript'])
const ZWJ = String.fromCodePoint(0x200D)
const RLO = String.fromCodePoint(0x202E)

function fixture(name: string): string {
  return readFileSync(join(process.cwd(), 'tests/component/fixtures/paste', name), 'utf8')
}

function pasted(name: string, profile: Profile = 'full') {
  const cleaned = cleanPastedHtml(fixture(name))
  const editor = new Editor({
    element: document.createElement('div'),
    extensions: [StarterKit.configure(starterKitOptions(profile)), ...richExtensions(profile)],
    content: cleaned.html,
  })
  const doc = fromEditor(editor.getJSON() as PmNode)
  editor.destroy()
  return { doc, cleaned }
}

function nodes(doc: RichDoc): PmNode[] {
  const walk = (list: PmNode[] = []): PmNode[] => list.flatMap(node => [node, ...walk(node.content)])
  return walk(doc.content as PmNode[])
}

function text(doc: RichDoc): string {
  return nodes(doc).map(node => node.text ?? '').join('')
}

function marksOn(doc: RichDoc, fragment: string): string[] {
  return nodes(doc).find(node => node.text?.includes(fragment))?.marks?.map(mark => mark.type) ?? []
}

function onlyAllowed(doc: RichDoc): void {
  for (const node of nodes(doc)) {
    expect(ALLOWED_NODES).toContain(node.type)
    for (const mark of node.marks ?? []) {
      expect(ALLOWED_MARKS).toContain(mark.type)
      expect(mark.attrs ?? {}).toEqual({})
    }
  }
}

describe.each(['word-windows.html', 'google-docs.html', 'web-page.html', 'pdf-viewer.html'])('pasting %s', (name) => {
  it('keeps only allowed nodes and marks, with no styling attached', () => {
    onlyAllowed(pasted(name).doc)
  })
})

describe('Word (Windows)', () => {
  const { doc, cleaned } = pasted('word-windows.html')

  it('keeps Bengali, bold, sub- and superscript, and drops colours and Word furniture', () => {
    expect(text(doc)).toContain('কোষের শক্তিঘর কোনটি?')
    expect(marksOn(doc, 'কোষের')).toEqual(['bold'])
    expect(marksOn(doc, '2')).toContain('subscript')
    expect(text(doc)).not.toContain('Style Definitions')
    expect(text(doc)).not.toContain('·')
  })

  it('turns Word\'s list paragraphs into real lists, bulleted and numbered', () => {
    const types = nodes(doc).map(node => node.type)
    expect(types).toContain('bulletList')
    expect(types).toContain('orderedList')
    expect(nodes(doc).filter(node => node.type === 'listItem')).toHaveLength(3)
    expect(text(doc)).toContain('মাইটোকন্ড্রিয়া')
  })

  it('keeps the table and reports the image it couldn\'t copy', () => {
    expect(nodes(doc).filter(node => node.type === 'tableRow')).toHaveLength(2)
    expect(marksOn(doc, 'Protein')).toEqual(['underline'])
    expect(cleaned.remoteImages).toBe(1)
  })
})

describe('Google Docs', () => {
  const { doc, cleaned } = pasted('google-docs.html')

  it('reads Google\'s styled spans as marks: bold, subscript, italic, underline', () => {
    expect(marksOn(doc, 'বাংলা')).toEqual(['bold'])
    expect(marksOn(doc, ' CO')).toEqual([])
    expect(marksOn(doc, '2')).toEqual(['subscript'])
    expect(marksOn(doc, 'red italic')).toEqual(['italic'])
    expect(marksOn(doc, 'দুই')).toEqual(['underline'])
  })

  it('keeps the joiner Bengali needs and removes the bidi override', () => {
    expect(text(doc)).toContain(`র${ZWJ}্যাব`)
    expect(text(doc)).not.toContain(RLO)
    expect(text(doc)).toContain('spoof')
  })

  it('takes the embedded image out to upload it', () => {
    expect(cleaned.dataImages).toHaveLength(1)
    expect(cleaned.dataImages[0]).toMatch(/^data:image\/png;base64,/)
    expect(nodes(doc).filter(node => node.type === 'bulletList')).toHaveLength(1)
  })
})

describe('a web page', () => {
  const { doc, cleaned } = pasted('web-page.html')

  it('keeps the words of headings, links, code and quotes, but not their formatting', () => {
    expect(text(doc)).toContain('The cell')
    expect(text(doc)).toContain('mitochondrion')
    expect(text(doc)).toContain('atp()')
    expect(text(doc)).toContain('কোষ হল জীবনের একক।')
    expect(marksOn(doc, 'powerhouse')).toEqual(['bold'])
  })

  it('never keeps scripts, page titles or event handlers', () => {
    expect(text(doc)).not.toContain('pasted script')
    expect(text(doc)).not.toContain('Cell biology notes')
    expect(JSON.stringify(doc)).not.toContain('steal')
    expect(cleaned.remoteImages).toBe(1)
  })

  it('keeps a numbered list\'s starting number', () => {
    expect(nodes(doc).find(node => node.type === 'orderedList')?.attrs?.start).toBe(3)
  })
})

describe('a PDF viewer', () => {
  it('keeps each line\'s Bengali text and drops page-break characters', () => {
    const { doc } = pasted('pdf-viewer.html')

    expect(text(doc)).toContain('কোনটি ক্লোরোফিল ধারণ করে?')
    expect(text(doc)).toContain('(A) Chloroplast')
    expect(text(doc)).not.toContain(String.fromCodePoint(12))
  })
})

describe('options (compact profile)', () => {
  it('a pasted list becomes plain paragraphs, never a list', () => {
    const { doc } = pasted('google-docs.html', 'compact')

    expect(nodes(doc).some(node => node.type === 'bulletList')).toBe(false)
  })
})
