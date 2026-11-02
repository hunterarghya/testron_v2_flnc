// T-04 Settings, T-03 Import and T-05 Preview, and the option keys.
import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, reactive, ref } from 'vue'
import { api } from '~/api/client'
import type { EditorQuestion, TestDocument } from '~/api/types'
import ImportDialog from '~/features/editor/components/ImportDialog.vue'
import OptionsEditor from '~/features/editor/components/OptionsEditor.vue'
import SettingsPanel from '~/features/editor/components/SettingsPanel.vue'
import TestPreview from '~/features/editor/components/TestPreview.vue'
import { provideEditor } from '~/features/editor/composables/editorContext'
import { textToDoc } from '../docs'
import { type FakeApi, ok } from '../fake-api'
import { RichFieldStub } from '../rich-field-stub'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi

function testDoc(timing: TestDocument['settings']['timing'], sections = 1): TestDocument {
  return {
    id: 't1', title: 'Cell Biology', instructions: null, revision: 3, archived_at: null, last_assigned_at: null,
    settings: {
      timing, shuffle_questions: false, shuffle_options: false,
      marking: { marks: '4.00', negative_marks: '1.00' }, integrity: { grace_s: 5, max_warnings: 3, action: 'AUTO_SUBMIT' },
    },
    totals: { questions: 0, marks: '0', duration_s: 4200 },
    sections: Array.from({ length: sections }, (_, i) => ({ id: `s${i + 1}`, position: i, title: '', instructions: null, duration_s: 600, questions: [] })),
    problems: [],
  }
}

/** Mounts `child` inside a fake editor context, as TestEditor provides it. */
function withEditor(doc: TestDocument, child: ReturnType<typeof defineComponent>, props: Record<string, unknown> = {}) {
  const actions = { saveSettings: vi.fn(() => Promise.resolve(true)), importQuestions: vi.fn(() => Promise.resolve(2)) }
  const editor = { doc: ref(doc), readOnly: ref(false), current: ref<string | null>(null) }
  const host = defineComponent({
    setup() {
      provideEditor({ testId: 't1', editor: editor as never, actions: actions as never })
      return () => h(child, props)
    },
  })
  return { host, actions, editor }
}

function bodyButton(label: string): HTMLButtonElement {
  return [...document.querySelectorAll('button')].find(b => b.textContent?.trim() === label)!
}

function radio(label: string): HTMLElement {
  return [...document.querySelectorAll('label')].find(l => l.textContent?.includes(label))!
}

describe('Settings panel (T-04)', () => {
  it('switching to per-question saves only the new kind', async () => {
    const { host, actions } = withEditor(testDoc({ kind: 'TOTAL', duration_s: 3600 }), SettingsPanel, { open: true })
    const wrapper = await mountSuspended(host)
    await flushPromises()

    radio('Per question').click()
    await flushPromises()

    expect(actions.saveSettings).toHaveBeenCalledWith(expect.objectContaining({ timing: { kind: 'PER_QUESTION' }, marking: { marks: '4.00', negative_marks: '1.00' } }))
    wrapper.unmount()
  })

  it('leaving sectioned with two sections asks first, and cancelling keeps them', async () => {
    const { host, actions } = withEditor(testDoc({ kind: 'SECTIONED', allow_return: false }, 2), SettingsPanel, { open: true })
    const wrapper = await mountSuspended(host)
    await flushPromises()

    expect(document.body.textContent).toContain('Total time: 1 h 10 min')
    radio('Total timer').click()
    await flushPromises()
    expect(document.body.textContent).toContain('Remove sections?')
    expect(actions.saveSettings).not.toHaveBeenCalled()

    bodyButton('Remove sections').click()
    await flushPromises()
    expect(actions.saveSettings).toHaveBeenCalledWith(expect.objectContaining({ timing: { kind: 'TOTAL' } }))
    wrapper.unmount()
  })
})

describe('Import (T-03)', () => {
  beforeEach(() => {
    fake.GET.mockReset().mockImplementation(() => ok({
      items: [
        { id: 'x1', test_id: 'o1', test_title: 'Old test', type: 'MCQ', stem: textToDoc('Which organelle?'), chapter_tags: [{ id: 'c', kind: 'CHAPTER', name: 'Cell' }], topic_tags: [] },
        { id: 'x2', test_id: 'o1', test_title: 'Old test', type: 'NUMERICAL', stem: textToDoc('How many?'), chapter_tags: [], topic_tags: [] },
      ],
      page: 1, page_size: 50, total: 2,
    }))
  })

  it('lists other tests\' questions and copies the ticked ones after the current question', async () => {
    const doc = testDoc({ kind: 'TOTAL', duration_s: 3600 })
    doc.sections[0]!.questions = [{ id: 'q1' } as EditorQuestion, { id: 'q2' } as EditorQuestion]
    const { host, actions, editor } = withEditor(doc, ImportDialog, { open: true })
    editor.current.value = 'q1'
    const wrapper = await mountSuspended(host)
    await flushPromises()

    expect(document.body.textContent).toContain('Which organelle?')
    expect(fake.GET.mock.calls[0]![1]).toMatchObject({ params: { query: { exclude_test_id: 't1' } } })
    document.querySelector<HTMLElement>('[aria-label="Select all on this page"]')!.click()
    await flushPromises()
    bodyButton('Import 2').click()
    await flushPromises()

    expect(actions.importQuestions).toHaveBeenCalledWith(['x1', 'x2'], 's1', 'q1')
    wrapper.unmount()
  })
})

describe('Preview (T-05)', () => {
  const PAPER = {
    test_id: 't1', title: 'Cell Biology', instructions: textToDoc('Read carefully'),
    timing: { kind: 'SECTIONED', allow_return: false }, integrity: { grace_s: 5, max_warnings: 3, action: 'AUTO_SUBMIT' },
    stages: [
      { index: 0, kind: 'SECTION', title: 'Botany', instructions: null, duration_s: 600, question_ids: ['q1'] },
      { index: 1, kind: 'SECTION', title: null, instructions: null, duration_s: null, question_ids: ['q2'] },
    ],
    questions: [
      { id: 'q1', number: 1, type: 'MCQ', stem: textToDoc('Which organelle?'), marks: '4.00', negative_marks: '1.00', time_s: null, options: [{ id: 'o1', label: 'A', content: textToDoc('Mitochondria') }, { id: 'o2', label: 'B', content: textToDoc('Golgi') }] },
      { id: 'q2', number: 2, type: 'NUMERICAL', stem: textToDoc('How many?'), marks: '2.50', negative_marks: '0.00', time_s: null, options: [] },
    ],
    answers: [] as unknown[],
  }

  beforeEach(() => {
    fake.GET.mockReset().mockImplementation((_path, init) => {
      const show = (init as { params: { query: { show_answers: boolean } } }).params.query.show_answers
      const answers = show ? [{ question_id: 'q1', correct_option_ids: ['o1'], numeric_answer: null, numeric_tolerance: '0', solution: textToDoc('Powerhouse') }] : []
      return ok({ ...PAPER, answers })
    })
  })

  it('shows one stage at a time with its time, and answers only when asked', async () => {
    const wrapper = await mountSuspended(TestPreview, { props: { testId: 't1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('Botany · 10 min')
    expect(wrapper.text()).toContain('Which organelle?')
    expect(wrapper.text()).not.toContain('How many?')
    expect(wrapper.text()).toContain('+4 / −1')
    expect(wrapper.find('[aria-label="Correct"]').exists()).toBe(false)

    wrapper.findComponent({ name: 'USwitch' }).vm.$emit('update:modelValue', true)
    await flushPromises()

    expect(wrapper.find('[aria-label="Correct"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Powerhouse')
  })
})

describe('option keys (T-03)', () => {
  it('Enter in the last option adds one; Backspace in an empty option removes it, keeping two', async () => {
    const q = reactive({
      id: 'q1', type: 'MCQ', options: [{ id: 'o1', content: textToDoc('A'), is_correct: false }, { id: 'o2', content: textToDoc('B'), is_correct: false }],
    }) as unknown as EditorQuestion
    const wrapper = await mountSuspended(OptionsEditor, { props: { question: q }, global: { stubs: { RichField: RichFieldStub } } })

    wrapper.findAllComponents(RichFieldStub)[1]!.vm.$emit('enter')
    await flushPromises()
    expect(q.options).toHaveLength(3)

    wrapper.findAllComponents(RichFieldStub)[2]!.vm.$emit('emptyBackspace')
    await flushPromises()
    expect(q.options).toHaveLength(2)

    wrapper.findAllComponents(RichFieldStub)[0]!.vm.$emit('emptyBackspace')
    expect(q.options).toHaveLength(2)
  })
})
