import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'
import type { EditorQuestion, TestSettings } from '~/api/types'
import OverridePopover from '~/features/editor/components/OverridePopover.vue'
import NumericAnswer from '~/features/editor/components/NumericAnswer.vue'
import OptionsEditor from '~/features/editor/components/OptionsEditor.vue'
import TagPills from '~/shared/components/TagPills.vue'
import { textToDoc } from '../docs'
import { RichFieldStub } from '../rich-field-stub'

const SETTINGS: TestSettings = {
  timing: { kind: 'PER_QUESTION', default_question_s: 45 }, shuffle_questions: false, shuffle_options: false,
  marking: { marks: '4.00', negative_marks: '1.00' }, integrity: { grace_s: 5, max_warnings: 3, action: 'AUTO_SUBMIT' },
}

function question(changes: Partial<EditorQuestion> = {}): EditorQuestion {
  return {
    id: 'q1', section_id: 's1', position: 0, type: 'MSQ', stem: textToDoc('Q'), solution: null,
    marks_override: null, negative_marks_override: null, time_override_s: null,
    options: [{ id: 'o1', content: textToDoc('A'), is_correct: true }, { id: 'o2', content: textToDoc('B'), is_correct: false }],
    numeric_answer: null, numeric_tolerance: '0', chapter_tags: [], topic_tags: [], ...changes,
  }
}

function bodyButton(label: string): HTMLButtonElement {
  return [...document.querySelectorAll('button')].find(b => b.textContent?.trim() === label)!
}

describe('marks and time overrides', () => {
  it('shows the default, then a custom value, then the default again', async () => {
    const q = question()
    const wrapper = await mountSuspended(OverridePopover, { props: { question: q, settings: SETTINGS, kind: 'marks' } })
    expect(wrapper.text()).toContain('Marks: default (+4/−1)')

    await wrapper.find('button').trigger('click')
    await flushPromises()
    const inputs = document.querySelectorAll<HTMLInputElement>('form input')
    inputs[0]!.value = '2.5'
    inputs[0]!.dispatchEvent(new Event('input'))
    bodyButton('Apply').click()
    await flushPromises()
    expect(q.marks_override).toBe('2.5')
    expect(wrapper.emitted('changed')).toHaveLength(1)

    await wrapper.find('button').trigger('click')
    await flushPromises()
    bodyButton('Reset to default').click()
    await flushPromises()
    expect([q.marks_override, q.negative_marks_override]).toEqual([null, null])
    wrapper.unmount()
  })

  it('time reads the per-question default', async () => {
    const wrapper = await mountSuspended(OverridePopover, { props: { question: question({ time_override_s: 90 }), settings: SETTINGS, kind: 'time' } })

    expect(wrapper.text()).toContain('Time: 90 s (custom)')
  })
})

describe('options and answers', () => {
  it('MSQ options toggle independently; options can be added and removed', async () => {
    // The editor's test is deeply reactive; so is this one
    const q = reactive(question())
    const wrapper = await mountSuspended(OptionsEditor, { props: { question: q }, global: { stubs: { RichField: RichFieldStub } } })

    await wrapper.find('button[aria-label="Mark option B correct"]').trigger('click')
    await wrapper.findAll('button').find(b => b.text() === 'Add option')!.trigger('click')
    await wrapper.find('button[aria-label="Remove option A"]').trigger('click')

    expect(q.options.map(o => o.is_correct)).toEqual([true, false])
    expect(q.options).toHaveLength(2)
    expect(wrapper.emitted('changed')).toHaveLength(3)
  })

  it('a numerical answer is kept as text', async () => {
    const q = question({ type: 'NUMERICAL', options: [] })
    const wrapper = await mountSuspended(NumericAnswer, { props: { question: q } })

    const [answer, tolerance] = wrapper.findAll('input')
    await answer!.setValue(' 6.02 ')
    await tolerance!.setValue('')

    expect([q.numeric_answer, q.numeric_tolerance]).toEqual(['6.02', '0'])
  })
})

describe('fields', () => {
  it('tag pills add a new name once, ignoring case', async () => {
    const suggest = vi.fn(() => Promise.resolve(['Cell']))
    const wrapper = await mountSuspended(TagPills, { props: { modelValue: ['Cell'], label: 'Chapter', suggest } })

    wrapper.findComponent({ name: 'UInputMenu' }).vm.$emit('create', ' cell ')
    wrapper.findComponent({ name: 'UInputMenu' }).vm.$emit('create', 'Cell  cycle')

    expect(wrapper.emitted('update:modelValue')).toEqual([[['Cell', 'Cell cycle']]])
  })
})
