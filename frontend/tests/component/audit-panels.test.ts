import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import type { AnswerSheet, KeyCorrection } from '~/api/types'
import KeyCorrectionHistory from '~/features/assignments/components/results/KeyCorrectionHistory.vue'
import SheetFlagsPanel from '~/features/assignments/components/results/SheetFlagsPanel.vue'

const CORRECTIONS: KeyCorrection[] = [
  { question_id: 'q3', number: 3, before: { labels: [], answer: '46.000000', tolerance: '0.000000' },
    after: { labels: [], answer: '46', tolerance: '1' }, reason: 'Accept 45 to 47', version: 3, corrected_at: '2026-11-12T06:00:00Z' },
  { question_id: 'q1', number: 1, before: { labels: ['A'], answer: null, tolerance: null },
    after: { labels: ['B', 'C'], answer: null, tolerance: null }, reason: 'B and C are right', version: 2, corrected_at: '2026-11-12T05:50:00Z' },
]

describe('T-11 answer key corrections', () => {
  it('lists each correction, newest first, with what changed and why', async () => {
    const wrapper = await mountSuspended(KeyCorrectionHistory, { props: { corrections: CORRECTIONS } })
    const items = wrapper.findAll('li').map(li => li.text())

    expect(wrapper.text()).toContain('Answer key corrections (2)')
    expect(items[0]).toContain('Q3: 46 ± 0 → 46 ± 1')
    expect(items[0]).toContain('“Accept 45 to 47”')
    expect(items[1]).toContain('Q1: A → B, C')
  })

  it('shows nothing when the key was never corrected', async () => {
    const wrapper = await mountSuspended(KeyCorrectionHistory, { props: { corrections: [] } })
    expect(wrapper.text()).toBe('')
  })
})

function sheet(flags: Partial<AnswerSheet['flags']>, events: AnswerSheet['integrity_events'] = []): AnswerSheet {
  return {
    flags: { warning_count: 0, max_warnings: 3, action: 'AUTO_SUBMIT', overridden_at: null, override_reason: null, ...flags },
    integrity_events: events,
  } as AnswerSheet
}

describe('T-12 flags panel', () => {
  it('counts warnings against the limit and lists each time the student left', async () => {
    const left = [{ kind: 'TAB_HIDDEN' as const, left_at: '2026-11-12T05:00:00Z', returned_at: '2026-11-12T05:00:12Z', counted: true }]
    const wrapper = await mountSuspended(SheetFlagsPanel, { props: { sheet: sheet({ warning_count: 1, action: 'DISQUALIFY' }, left) } })

    expect(wrapper.text()).toContain('⚑ 1 of 3 warnings (the last one would disqualify)')
    expect(wrapper.text()).toContain('Tab hidden')
    expect(wrapper.text()).not.toContain('overridden')
  })

  it('shows a counted disqualification with its reason', async () => {
    const wrapper = await mountSuspended(SheetFlagsPanel, {
      props: { sheet: sheet({ warning_count: 3, action: 'DISQUALIFY', overridden_at: '2026-11-12T06:00:00Z', override_reason: 'Power cut' }) },
    })

    expect(wrapper.text()).toContain('Disqualification overridden on')
    expect(wrapper.text()).toContain('“Power cut”')
    expect(wrapper.text()).toContain('Never left the test.')
  })
})
