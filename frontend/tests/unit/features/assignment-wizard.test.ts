import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { NewAssignment } from '~/api/types'
import { useAssignmentWizard } from '~/features/assignments/composables/useAssignmentWizard'
import { type FakeApi, ok } from '../../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi

const TEST = {
  id: 't1',
  title: 'Cell Biology',
  settings: { timing: { kind: 'TOTAL', duration_s: 3000 }, integrity: { grace_s: 5, max_warnings: 3, action: 'AUTO_SUBMIT' } },
  sections: [],
  totals: { questions: 30, marks: '120.00', duration_s: 3000 },
  problems: [],
}
const CANDIDATES = [
  { student_id: 's1', name: 'Aditi', email: 'a@x.in', group_names: ['11A'] },
  { student_id: 's2', name: 'Arjun', email: 'b@x.in', group_names: ['11A'] },
]
const EARLIER = {
  test_id: 't1',
  title: 'Cell Biology – Take 2',
  window_kind: 'OPEN',
  window_summary: { late_entry_s: null },
  gate: { requires_activation: false, has_password: true },
  integrity: TEST.settings.integrity,
  publication: { mode: 'AUTO_IMMEDIATE', delay_s: null, content: 'SCORE_ONLY', show_paper: false, show_solutions: false, show_rank_and_stats: false, published_at: null, publish_at: null },
  source_group_ids: ['g1'],
  audience_students: [{ id: 's1', name: 'Aditi' }, { id: 's9', name: 'Riya' }],
}

function answer(path: string) {
  if (path === '/api/v1/admin/tests/{test_id}') return ok(TEST)
  if (path === '/api/v1/admin/audience-preview') return ok(CANDIDATES)
  return ok(EARLIER)
}

describe('useAssignmentWizard (T-07)', () => {
  beforeEach(() => {
    fake.GET.mockReset().mockImplementation(answer)
    fake.POST.mockReset().mockImplementation(() => ok({ id: 'a1' }))
  })

  it('builds the request from the four steps', async () => {
    const wizard = useAssignmentWizard()
    await wizard.pickTest('t1')
    await wizard.pickGroups(['g1'])
    wizard.addStudents([{ id: 's9', name: 'Riya' }])
    wizard.form.value = { ...wizard.form.value!, password: '1234', passwordConfirm: '1234' }

    expect(wizard.title.value).toBe('Cell Biology')
    expect(await wizard.create()).toEqual({ id: 'a1' })
    const body = (fake.POST.mock.calls[0]![1] as { body: NewAssignment }).body
    expect(body.student_ids).toEqual(['s1', 's2', 's9'])
    expect(body.source_group_ids).toEqual(['g1'])
    expect(body.window).toEqual({ kind: 'MANUAL', planned_at: undefined, late_entry_s: undefined })
    expect(body.gate).toEqual({ requires_activation: true, password: '1234', password_confirm: '1234' })
    expect(body.timing_override).toBeNull()
  })

  it('assign again keeps the test, groups and who sat it, but not the password', async () => {
    const wizard = useAssignmentWizard()
    await wizard.startFrom('a0')

    expect(wizard.title.value).toBe('Cell Biology – Take 2')
    expect(wizard.form.value!.windowKind).toBe('OPEN')
    expect(wizard.form.value!.password).toBe('')
    expect(wizard.audience.value.map(entry => [entry.studentId, entry.ticked])).toEqual([['s1', true], ['s2', false], ['s9', true]])
  })

  it('only continues past a step once it is answered', async () => {
    const wizard = useAssignmentWizard()
    expect(wizard.canContinue.value).toBe(false)
    await wizard.pickTest('t1')
    expect(wizard.canContinue.value).toBe(true)
    wizard.step.value = 1
    expect(wizard.canContinue.value).toBe(false)
  })
})
