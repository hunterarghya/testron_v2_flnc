import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import { ApiProblem } from '~/api/problems'
import type { EditorQuestion, TestDocument, TestMutation } from '~/api/types'
import TestEditor from '~/features/editor/components/TestEditor.vue'
import { textToDoc } from '~/shared/utils/plain-doc'
import { type FakeApi, ok } from '../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
const PROBLEM = { code: 'stem_empty', message: 'Question 1 has no question text.', section_id: 's1', question_id: 'q1' }

function question(): EditorQuestion {
  return {
    id: 'q1', section_id: 's1', position: 0, type: 'MCQ', stem: textToDoc(''), solution: null,
    marks_override: null, negative_marks_override: null, time_override_s: null,
    options: [
      { id: 'o1', content: textToDoc('Mitochondria'), is_correct: true },
      { id: 'o2', content: textToDoc('Golgi'), is_correct: false },
    ],
    numeric_answer: null, numeric_tolerance: '0', chapter_tags: [], topic_tags: [],
  }
}

function document(): TestDocument {
  return {
    id: 't1', title: 'Cell Biology', instructions: null, revision: 3, archived_at: null, last_assigned_at: null,
    settings: {
      timing: { kind: 'TOTAL', duration_s: 3600 }, shuffle_questions: false, shuffle_options: false,
      marking: { marks: '4.00', negative_marks: '1.00' }, integrity: { grace_s: 5, max_warnings: 3, action: 'AUTO_SUBMIT' },
    },
    totals: { questions: 1, marks: '4.00', duration_s: 3600 },
    sections: [{ id: 's1', position: 0, title: '', instructions: null, duration_s: null, questions: [question()] }],
    problems: [PROBLEM],
  }
}

const saved = (revision: number): TestMutation & { question: EditorQuestion } => ({
  revision, problems: [], totals: { questions: 1, marks: '4.00', duration_s: 3600 }, question: question(),
})

async function mountEditor() {
  const wrapper = await mountSuspended(TestEditor, { props: { testId: 't1' } })
  await flushPromises()
  return wrapper
}

describe('TestEditor (T-03)', () => {
  beforeEach(() => {
    localStorage.clear()
    fake.GET.mockReset().mockImplementation(() => ok(document()))
    fake.PATCH.mockReset().mockImplementation(() => ok(saved(4)))
  })
  afterEach(() => localStorage.clear())

  it('shows the test, its outline, totals and problems', async () => {
    const wrapper = await mountEditor()

    expect(wrapper.find('input[aria-label="Test title"]').element).toHaveProperty('value', 'Cell Biology')
    expect(wrapper.text()).toContain('Q1')
    expect(wrapper.text()).toContain('Marks: default (+4/−1)')
    expect(wrapper.text()).toContain('1 Qs · 4 marks · 1 h')
    expect(wrapper.text()).toContain('Question 1 has no question text.')
    expect(wrapper.text()).toContain('Saved')
  })

  it('a change is saved as the whole question on the current revision', async () => {
    const wrapper = await mountEditor()

    const stem = wrapper.find('textarea[aria-label="Question text"]')
    await stem.setValue('Which organelle makes energy?')
    await stem.trigger('blur')
    await flushPromises()

    const [path, init] = fake.PATCH.mock.calls[0]!
    expect(path).toBe('/api/v1/admin/questions/{question_id}')
    expect(init).toMatchObject({
      params: { path: { question_id: 'q1' } },
      body: { revision: 3, type: 'MCQ', stem: textToDoc('Which organelle makes energy?') },
    })
    // The outline takes the answer's problems without refetching the test
    expect(wrapper.text()).toContain('None. This test can be assigned.')
    expect(fake.GET).toHaveBeenCalledTimes(1)
  })

  it('marking an MCQ option correct unmarks the others', async () => {
    const wrapper = await mountEditor()

    await wrapper.find('button[aria-label="Mark option B correct"]').trigger('click')
    await wrapper.find('textarea[aria-label="Question text"]').trigger('blur')
    await flushPromises()

    const body = (fake.PATCH.mock.calls[0]![1] as { body: { options: { is_correct: boolean }[] } }).body
    expect(body.options.map(o => o.is_correct)).toEqual([false, true])
  })

  it('another tab\'s change stops editing and offers a reload', async () => {
    fake.PATCH.mockReset().mockImplementation(() => Promise.reject(new ApiProblem({ status: 409, code: 'test_changed_elsewhere', detail: 'x' })))
    const wrapper = await mountEditor()

    const stem = wrapper.find('textarea[aria-label="Question text"]')
    await stem.setValue('Mine')
    await stem.trigger('blur')
    await flushPromises()

    expect(wrapper.text()).toContain('This test was changed in another tab.')
    expect(wrapper.find('textarea[aria-label="Question text"]').attributes('disabled')).toBeDefined()
    expect(localStorage.getItem('editor:recovery:t1')).toContain('Mine')
    expect(localStorage.getItem('editor:pending:t1')).toBeNull()
  })

  it('a test that is gone shows the error state', async () => {
    fake.GET.mockReset().mockImplementation(() => Promise.reject(new ApiProblem({ status: 404, code: 'not_found', detail: 'x' })))

    const wrapper = await mountEditor()

    expect(wrapper.text()).toContain('couldn\'t find')
  })
})
