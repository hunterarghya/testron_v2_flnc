// RichContentView and RichContentEditor (editor_content_spec.md §4, §6, §7).
import { Editor } from '@tiptap/core'
import { NodeSelection } from '@tiptap/pm/state'
import StarterKit from '@tiptap/starter-kit'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import type { RichDoc } from '~/api/types'
import { fromEditor, type PmNode, toEditor } from '~/shared/components/rich-content/convert'
import { richExtensions, starterKitOptions } from '~/shared/components/rich-content/extensions'
import { withinCompactLimits } from '~/shared/components/rich-content/extensions/limits'
import { showFormatBar, slashItems, toolbarItems, useInsertHandlers } from '~/shared/components/rich-content/menus'
import RichContentEditor from '~/shared/components/rich-content/RichContentEditor.vue'
import RichContentView from '~/shared/components/rich-content/RichContentView.vue'
import { startUpload } from '~/shared/components/rich-content/uploads'

// No real uploads: these tests are about what reaches the editor
vi.mock('~/api/uploads', async original => ({ ...(await original<typeof import('~/api/uploads')>()), uploadImage: vi.fn(() => new Promise(() => {})) }))

const EVERYTHING: RichDoc = {
  v: 1,
  type: 'doc',
  content: [
    { type: 'paragraph', attrs: { textAlign: 'center' }, content: [
      { type: 'text', text: 'H' },
      { type: 'text', text: '2', marks: [{ type: 'subscript' }] },
      { type: 'text', text: 'O is ', marks: [{ type: 'bold' }, { type: 'italic' }] },
      { type: 'math', attrs: { latex: 'x^2', display: false } },
      { type: 'hardBreak' },
      { type: 'text', text: '<script>alert(1)</script>' },
    ] },
    { type: 'bulletList', content: [{ type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'one' }] }] }] },
    { type: 'orderedList', attrs: { start: 3 }, content: [{ type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'three' }] }] }] },
    { type: 'table', content: [{ type: 'tableRow', content: [
      { type: 'tableHeader', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Organelle' }] }] },
      { type: 'tableCell', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Job', marks: [{ type: 'underline' }] }] }] },
    ] }] },
    { type: 'image', attrs: { provider: 'imagekit', fileId: 'golgi_01', src: 'https://ik.imagekit.io/acme/tests/golgi.png', width: 640, height: 420, size: 'L', alt: 'Golgi', caption: 'Golgi body' } },
    { type: 'math', attrs: { latex: '\\frac{a}{b}', display: true } },
  ],
}

function editorFor(doc: RichDoc, profile: 'full' | 'compact' = 'full'): Editor {
  return new Editor({
    element: document.createElement('div'),
    extensions: [StarterKit.configure(starterKitOptions(profile)), ...richExtensions(profile)],
    content: toEditor(doc) as Record<string, unknown>,
  })
}

describe('RichContentView', () => {
  it('draws every allowed node and mark, and escapes text', async () => {
    const wrapper = await mountSuspended(RichContentView, { props: { doc: EVERYTHING } })
    const html = wrapper.html()

    expect(html).toContain('<sub>2</sub>')
    expect(html).toContain('<strong><em>O is </em></strong>')
    expect(html).toContain('&lt;script&gt;')
    expect(wrapper.find('p.text-center').exists()).toBe(true)
    expect(wrapper.find('ol').attributes('start')).toBe('3')
    expect(wrapper.find('th').text()).toBe('Organelle')
    expect(wrapper.find('td u').text()).toBe('Job')
    expect(wrapper.findAll('.katex')).toHaveLength(2)
  })

  it('content can shrink inside an option card, so a wide image or long caption stays in it', async () => {
    const golgi = EVERYTHING.content.find(node => node.type === 'image')!
    const wrapper = await mountSuspended(RichContentView, { props: { doc: { v: 1, type: 'doc', content: [golgi] } } })

    expect(wrapper.classes()).toEqual(expect.arrayContaining(['min-w-0', 'max-w-full', 'break-words']))
    expect(wrapper.find('figure').classes()).toContain('max-w-full')
    expect(wrapper.find('img').classes()).toContain('max-w-full')
    expect(wrapper.find('figcaption').classes()).toContain('break-words')
  })

  it('images are resized by the CDN, lazy by default, eager when asked', async () => {
    const lazy = await mountSuspended(RichContentView, { props: { doc: EVERYTHING } })
    const eager = await mountSuspended(RichContentView, { props: { doc: EVERYTHING, eagerImages: true } })

    const image = lazy.find('img')
    expect(image.attributes('src')).toMatch(/golgi\.png\?tr=w-\d+,q-80,f-auto$/)
    expect([image.attributes('loading'), eager.find('img').attributes('loading')]).toEqual(['lazy', 'eager'])
    expect(lazy.find('figcaption').text()).toBe('Golgi body')
  })

  it('an equation with \\href is an error, never a link', async () => {
    const attack: RichDoc = { v: 1, type: 'doc', content: [{ type: 'math', attrs: { latex: '\\href{javascript:alert(1)}{click}', display: false } }] }

    const wrapper = await mountSuspended(RichContentView, { props: { doc: attack } })

    // Shown as red error text; the LaTeX source stays only as escaped text for screen readers
    expect(wrapper.find('a').exists()).toBe(false)
    expect(wrapper.html()).not.toContain('href=')
    expect(wrapper.find('.katex [style*="color"]').text()).toContain('\\href')
  })

  it('empty content shows nothing', async () => {
    const wrapper = await mountSuspended(RichContentView, { props: { doc: { v: 1, type: 'doc', content: [] } } })

    expect(wrapper.find('.rich-content').exists()).toBe(false)
  })
})

describe('the editor schema', () => {
  it('every allowed node and mark goes through the editor unchanged', () => {
    const editor = editorFor(EVERYTHING)

    const saved = fromEditor(editor.getJSON() as PmNode)
    editor.destroy()

    expect(JSON.stringify(saved)).toContain('"display":true')
    expect(saved.content).toHaveLength(EVERYTHING.content!.length)
    expect(saved.content![4]).toEqual(EVERYTHING.content![4])
  })

  it('sub- and superscript exclude each other', () => {
    const editor = editorFor({ v: 1, type: 'doc', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'x', marks: [{ type: 'subscript' }] }] }] })

    editor.chain().selectAll().toggleSuperscript().run()

    expect(editor.getJSON().content?.[0]?.content?.[0]?.marks?.map(m => m.type)).toEqual(['superscript'])
    editor.destroy()
  })

  it('an option keeps to 3 paragraphs and 1 image', () => {
    const editor = editorFor({ v: 1, type: 'doc', content: [1, 2, 3].map(n => ({ type: 'paragraph', content: [{ type: 'text', text: String(n) }] })) }, 'compact')

    editor.commands.insertContentAt(editor.state.doc.content.size, { type: 'paragraph', content: [{ type: 'text', text: '4' }] })

    expect(editor.state.doc.childCount).toBe(3)
    expect(withinCompactLimits(editor.state.doc)).toBe(true)
    editor.destroy()
  })

  it('a second image in an option is refused with a reason, and never uploaded', () => {
    const notify = vi.fn()
    // The test DOM's File isn't the Blob Node's URL expects; the preview link itself doesn't matter
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:preview')
    const revoked = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    const golgi = EVERYTHING.content.find(node => node.type === 'image')!
    const option = editorFor({ v: 1, type: 'doc', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Golgi' }] }, golgi] }, 'compact')
    // The cursor in the option's text, as after typing it
    option.commands.setTextSelection(3)

    startUpload(option, new File(['x'], 'cell.png', { type: 'image/png' }), notify)

    expect(JSON.stringify(option.getJSON())).not.toContain('imageUpload')
    expect(notify.mock.calls.map(([problem]) => problem.code)).toEqual(['image_limit'])
    expect(revoked).toHaveBeenCalledWith('blob:preview')
    option.destroy()
    vi.restoreAllMocks()
  })

  it('an option has no lists, tables or displayed equations', () => {
    const editor = editorFor({ v: 1, type: 'doc', content: [] }, 'compact')

    expect(Object.keys(editor.schema.nodes)).not.toEqual(expect.arrayContaining(['bulletList']))
    expect(editor.schema.nodes.table).toBeUndefined()
    expect(editor.schema.nodes.mathBlock).toBeUndefined()
    editor.destroy()
  })
})

describe('menus', () => {
  it('the format bar shows for selected text only, never above a selected image', () => {
    const golgi = EVERYTHING.content.find(node => node.type === 'image')!
    const editor = editorFor({ v: 1, type: 'doc', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Golgi body' }] }, golgi] })
    const element = document.createElement('div')
    vi.spyOn(editor.view, 'hasFocus').mockReturnValue(true)
    const shown = () => showFormatBar({ editor, state: editor.state, element })

    editor.commands.setTextSelection({ from: 1, to: 6 })
    expect(shown()).toBe(true)
    editor.commands.setTextSelection(3)
    expect(shown()).toBe(false)
    editor.view.dispatch(editor.state.tr.setSelection(NodeSelection.create(editor.state.doc, editor.state.doc.child(0).nodeSize)))
    expect(shown()).toBe(false)

    editor.commands.setTextSelection({ from: 1, to: 6 })
    vi.mocked(editor.view.hasFocus).mockReturnValue(false)
    expect(shown()).toBe(false)
    editor.destroy()
  })

  it('the "/" menu offers question inserts only where asked, and fewer things in options', () => {
    const labels = (groups: ReturnType<typeof slashItems>) => groups.flat().map(item => item.label)

    expect(labels(slashItems('full', ['question', 'section']))).toEqual(['MCQ (single correct)', 'MSQ (multiple correct)', 'Numerical', 'Section', 'Image', 'Equation', 'Table'])
    expect(labels(slashItems('full'))).toEqual(['Image', 'Equation', 'Table'])
    expect(labels(slashItems('compact'))).toEqual(['Image', 'Equation'])
    expect(toolbarItems('compact')).toHaveLength(1)
  })

  it('inserts run in the editor or go to the page around it', () => {
    const commands: unknown[] = []
    let picked = 0
    const handlers = useInsertHandlers({ pickImage: () => picked++, command: c => commands.push(c) })
    const inserted = (run: (editor: Editor) => void) => {
      const editor = editorFor({ v: 1, type: 'doc', content: [] })
      run(editor)
      const types = (editor.getJSON().content ?? []).map(node => node.type)
      editor.destroy()
      return types
    }

    expect(inserted(editor => handlers.math.execute(editor, { display: true }).run())).toContain('mathBlock')
    expect(inserted(editor => handlers.table.execute(editor).run())).toContain('table')
    expect(inserted((editor) => {
      handlers.image.execute(editor).run()
      handlers.question.execute(editor, { questionType: 'MSQ' }).run()
      handlers.section.execute(editor).run()
    })).toEqual(['paragraph'])
    expect(picked).toBe(1)
    expect(commands).toEqual([{ kind: 'question', questionType: 'MSQ' }, { kind: 'section' }])
  })
})

describe('RichContentEditor', () => {
  it('shows the stored content and saves edits in the stored format', async () => {
    const doc: RichDoc = { v: 1, type: 'doc', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'কোষ' }] }] }
    const wrapper = await mountSuspended(RichContentEditor, { props: { modelValue: doc, profile: 'full', label: 'Question text' } })
    await flushPromises()

    expect(wrapper.text()).toContain('কোষ')
    const editor = (wrapper.findComponent({ name: 'UEditor' }).vm as unknown as { editor: Editor }).editor
    editor.commands.insertContentAt(editor.state.doc.content.size, { type: 'paragraph', content: [{ type: 'text', text: 'H' }, { type: 'text', text: '2', marks: [{ type: 'subscript' }] }] })
    await flushPromises()

    const saved = wrapper.emitted('update:modelValue')!.at(-1)![0] as RichDoc
    expect(saved.v).toBe(1)
    expect(saved.content).toHaveLength(2)
    expect(JSON.stringify(saved)).toContain('"subscript"')
  })

  it('offers an Add image button beside the field that opens the file picker, unless read-only', async () => {
    const empty: RichDoc = { v: 1, type: 'doc', content: [] }
    const picked = vi.spyOn(HTMLInputElement.prototype, 'click').mockImplementation(() => {})
    const option = await mountSuspended(RichContentEditor, { props: { modelValue: empty, profile: 'compact', label: 'Option A' } })

    await option.find('button[aria-label="Add image to Option A"]').trigger('click')
    expect(picked).toHaveBeenCalledTimes(1)
    expect(option.find('input[type="file"]').attributes('accept')).toContain('image/png')

    const locked = await mountSuspended(RichContentEditor, { props: { modelValue: empty, profile: 'full', label: 'Question text', disabled: true } })
    expect(locked.find('button[aria-label="Add image to Question text"]').exists()).toBe(false)
    picked.mockRestore()
  })
})
