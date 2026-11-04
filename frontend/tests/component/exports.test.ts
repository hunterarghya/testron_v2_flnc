import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { AnswerSheet } from '~/api/types'
import DownloadSheetButton from '~/features/exports/components/DownloadSheetButton.vue'
import { titleOf } from '~/features/exports/composables/useExports'
import ExportMenu from '~/features/exports/components/ExportMenu.vue'
import { type FakeApi, ok } from '../fake-api'
import { DOC } from '../hall-fixtures'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi

const SHEET: AnswerSheet = {
  attempt_id: 'att1', label: 'Cell Biology — 12 Nov 2026, 10:00 — Take 2', take_number: 2, ended_at: '2026-11-12T05:20:00Z',
  time_taken_s: 3000, end_reason: 'SUBMITTED', score: '4.00', max_score: '8.00', sections: [], tags: [], rank_and_stats: null,
  questions: [{ id: 'q1', number: 1, type: 'NUMERICAL', stem: DOC, marks: '4.00', negative_marks: '0.00', options: [],
    your_answer: { v: 1, kind: 'NUMERIC', value: '46' }, correct_answer: { value: '46', tolerance: '0' },
    outcome: 'CORRECT', marks_awarded: '4.00', solution: DOC }],
  student: { id: 's1', name: 'Mou Ghosh' },
  integrity_events: [{ kind: 'TAB_HIDDEN', left_at: '2026-11-12T05:00:00Z', returned_at: '2026-11-12T05:00:12Z', counted: true }],
  disqualified_score: null,
  flags: { warning_count: 1, max_warnings: 3, action: 'AUTO_SUBMIT', overridden_at: null, override_reason: null },
}

afterEach(() => {
  vi.restoreAllMocks()
})

function captureDownloads(): { name: string, blob: Blob }[] {
  const saved: { name: string, blob: Blob }[] = []
  vi.spyOn(URL, 'createObjectURL').mockImplementation((blob) => {
    saved.push({ name: '', blob: blob as Blob })
    return 'blob:x'
  })
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
    saved[saved.length - 1]!.name = this.download
  })
  return saved
}

describe('answer sheet download (T-12, ADR-019)', () => {
  it('builds one self-contained file named after the student, test, date and take', async () => {
    const saved = captureDownloads()
    const wrapper = await mountSuspended(DownloadSheetButton, { props: { sheet: SHEET } })

    await wrapper.find('button').trigger('click')
    await flushPromises()
    await vi.waitFor(() => expect(saved).toHaveLength(1))

    const html = await saved[0]!.blob.text()
    expect(saved[0]!.name).toMatch(/^Mou Ghosh - Cell Biology - \d{4}-\d{2}-\d{2} - Take 2\.html$/)
    expect(html.startsWith('<!doctype html>')).toBe(true)
    expect(html).toContain('@font-face{font-family:\'Noto Sans Bengali\'')
    expect(html).toContain('Mou Ghosh')
    expect(html).toContain('Solution')
    expect(html).toContain('Tab hidden')
    expect(html).not.toContain('Wrong</button>')
    wrapper.unmount()
  })

  it('reads the test title from the label', () => {
    expect(titleOf(SHEET)).toBe('Cell Biology')
  })
})

describe('all answer sheets as a ZIP (T-11 Export)', () => {
  it('asks for the selected sheets and saves one ZIP', async () => {
    fake.GET.mockReset().mockImplementation(() => ok([SHEET, { ...SHEET, attempt_id: 'att2', student: { id: 's2', name: 'Arjun Das' } }]))
    const saved = captureDownloads()
    const wrapper = await mountSuspended(ExportMenu, { props: { assignmentId: 'a1', title: 'Cell Biology', attemptIds: ['att1', 'att2'] } })

    await wrapper.find('button').trigger('click')
    await flushPromises()
    const item = [...document.querySelectorAll('[role="menuitem"]')].find(el => el.textContent?.includes('2 selected'))!
    ;(item as HTMLElement).click()
    await vi.waitFor(() => expect(saved).toHaveLength(1), { timeout: 5000 })

    expect(fake.GET.mock.calls[0]![1]).toMatchObject({ params: { query: { attempt_ids: 'att1,att2' } } })
    expect(saved[0]!.name).toMatch(/^Cell Biology - \d{4}-\d{2}-\d{2} - Answer Sheets\.zip$/)
    wrapper.unmount()
  })
})
