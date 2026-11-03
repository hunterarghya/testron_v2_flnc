import { describe, expect, it } from 'vitest'
import type { AssignmentDetail, TestDocument } from '~/api/types'
import { addIndividuals, mergeGroups, selectionSummary, tickedIds } from '~/features/assignments/utils/audience'
import { toTimingOverride, timingEditFrom } from '~/features/assignments/utils/timing'
import {
  applyPreset,
  emptyWhenForm,
  presetOf,
  toChanges,
  toPublication,
  toWindow,
  whenFormFrom,
} from '~/features/assignments/utils/when-form'

const INTEGRITY = { grace_s: 5, max_warnings: 3, action: 'AUTO_SUBMIT' as const }
const candidate = (id: string, groups: string[]) => ({ student_id: id, name: id.toUpperCase(), email: `${id}@x.in`, group_names: groups })

describe('presets [D-2]', () => {
  it('starts Locked: manual, activation, password, manual results', () => {
    const form = emptyWhenForm(INTEGRITY)
    expect([form.windowKind, form.requiresActivation, form.usePassword, form.publication.mode]).toEqual(['MANUAL', true, true, 'MANUAL'])
    expect(presetOf(form)).toBe('LOCKED')
  })

  it('Open suggests auto-publish, and any later edit makes it Custom', () => {
    const open = applyPreset(emptyWhenForm(INTEGRITY), 'OPEN')
    expect([open.windowKind, open.publication.mode]).toEqual(['OPEN', 'AUTO_IMMEDIATE'])
    expect(presetOf({ ...open, usePassword: true })).toBeNull()
  })
})

describe('form to API', () => {
  it('sends windows in UTC with late entry in seconds', () => {
    const form = { ...emptyWhenForm(INTEGRITY), windowKind: 'SCHEDULED' as const, startsAt: '2026-11-12T10:00', lateEntryMin: 10 }
    expect(toWindow(form)).toEqual({ kind: 'SCHEDULED', starts_at: '2026-11-12T04:30:00.000Z', late_entry_s: 600 })
  })

  it('sends a delay only for delayed publication', () => {
    const form = emptyWhenForm(INTEGRITY)
    expect(toPublication(form).delay_s).toBeNull()
    const delayed = { ...form, publication: { ...form.publication, mode: 'AUTO_DELAYED' as const }, delayValue: 2, delayUnit: 'hours' as const }
    expect(toPublication(delayed).delay_s).toBe(7200)
  })

  it('edits send only the fields the server still accepts', () => {
    const changes = toChanges(emptyWhenForm(INTEGRITY), 'New name', ['title', 'publication', 'password'])
    expect(Object.keys(changes)).toEqual(['title', 'publication'])
  })

  it('reads a saved assignment back into the form', () => {
    const detail = {
      window_kind: 'DEADLINE',
      window_summary: { opens_at: '2026-11-12T04:30:00Z', closes_at: '2026-11-13T04:30:00Z', late_entry_s: null },
      gate: { requires_activation: false, has_password: false },
      integrity: INTEGRITY,
      publication: { mode: 'AUTO_DELAYED', delay_s: 172_800, content: 'SCORE_ONLY', show_paper: false, show_solutions: false, show_rank_and_stats: false, published_at: null, publish_at: null },
    } as unknown as AssignmentDetail
    const form = whenFormFrom(detail)
    expect([form.windowKind, form.opensAt, form.closesAt]).toEqual(['DEADLINE', '2026-11-12T10:00', '2026-11-13T10:00'])
    expect([form.delayValue, form.delayUnit, form.usePassword]).toEqual([2, 'days', false])
  })
})

describe('audience [D-1]', () => {
  it('groups fill the list once per student, keeping unticks and individuals', () => {
    let list = mergeGroups([], [candidate('a', ['11A']), candidate('b', ['11A', '12B'])])
    list = list.map(entry => (entry.studentId === 'a' ? { ...entry, ticked: false } : entry))
    list = addIndividuals(list, [{ id: 'c', name: 'C' }, { id: 'b', name: 'B' }])
    list = mergeGroups(list, [candidate('a', ['11A']), candidate('b', ['11A', '12B']), candidate('d', ['12B'])])

    expect(list.map(entry => entry.studentId)).toEqual(['a', 'b', 'd', 'c'])
    expect(tickedIds(list)).toEqual(['b', 'd', 'c'])
    expect(selectionSummary(list)).toBe('3 of 4 selected · 1 added individually')
  })
})

describe('timing override', () => {
  it('keeps the test kind and converts minutes', () => {
    const test = {
      settings: { timing: { kind: 'SECTIONED', allow_return: true } },
      sections: [{ id: 's1', duration_s: 1200 }, { id: 's2', duration_s: 1800 }],
    } as unknown as TestDocument
    const edit = timingEditFrom(test)
    expect(edit.sectionMin).toEqual({ s1: 20, s2: 30 })
    expect(toTimingOverride(test, { ...edit, sectionMin: { s1: 25, s2: 30 } }))
      .toEqual({ kind: 'SECTIONED', section_durations_s: { s1: 1500, s2: 1800 } })
  })
})
