import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import type { AppSettings, StudentDetail } from '~/api/types'
import BrandingForm from '~/features/settings/components/BrandingForm.vue'
import DefaultsForm from '~/features/settings/components/DefaultsForm.vue'
import StudentProfile from '~/features/students/components/StudentProfile.vue'
import { useAppInfo } from '~/shared/composables/useAppInfo'
import { type FakeApi, ok } from '../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi
const SETTINGS: AppSettings = {
  coaching_name: 'Test Platform', logo_url: null, default_marks: '4.00', default_negative_marks: '1.00',
  default_integrity_grace_s: 5, default_integrity_max_warnings: 3, default_integrity_action: 'AUTO_SUBMIT', updated_at: null,
}

describe('Settings (T-19)', () => {
  const save = vi.fn()

  beforeEach(() => {
    save.mockReset().mockImplementation((changes: Partial<AppSettings>) => Promise.resolve({ ...SETTINGS, ...changes }))
  })

  it('defaults are sent with marks as decimal strings', async () => {
    const wrapper = await mountSuspended(DefaultsForm, { props: { settings: SETTINGS, save } })

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(save).toHaveBeenCalledWith({
      default_marks: '4.00', default_negative_marks: '1.00', default_integrity_grace_s: 5,
      default_integrity_max_warnings: 3, default_integrity_action: 'AUTO_SUBMIT',
    })
  })

  it('branding saves the name and can remove the logo', async () => {
    const wrapper = await mountSuspended(BrandingForm, { props: { settings: { ...SETTINGS, logo_url: '/dev-media/tests/l.png' }, save } })

    await wrapper.find('input:not([type="file"])').setValue('Sen\'s Biology')
    await wrapper.find('form').trigger('submit')
    await wrapper.findAll('button').find(b => b.text() === 'Remove')!.trigger('click')
    await flushPromises()

    expect(save.mock.calls).toEqual([[{ coaching_name: 'Sen\'s Biology' }], [{ logo_url: null }]])
    expect(wrapper.find('img[alt="Current logo"]').exists()).toBe(true)
  })

  it('app info keeps only the name and logo', () => {
    const app = useAppInfo()
    app.set(SETTINGS)

    expect(app.info.value).toEqual({ coaching_name: 'Test Platform', logo_url: null })
  })
})

describe('StudentProfile (T-15)', () => {
  const DETAIL: StudentDetail = {
    student: {
      id: 's1', name: 'Aditi Roy', email: 'aditi@x.in', status: 'ACTIVE', joined_at: '2026-11-01T00:00:00Z',
      requested_at: null, decided_at: null, deactivated_at: null, performance_shared: false, group_names: ['Class 11 A'],
    },
    groups: [{ id: 'g1', name: 'Class 11 A' }],
  }

  beforeEach(() => {
    fake.GET.mockReset().mockImplementation(path => ok(path === '/api/v1/admin/groups' ? [] : DETAIL))
    fake.POST.mockReset().mockImplementation(() => ok({ succeeded: ['s1'], skipped: [] }))
  })

  it('shows details and groups, and shares performance', async () => {
    const wrapper = await mountSuspended(StudentProfile, { props: { studentId: 's1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('aditi@x.in')
    expect(wrapper.find('a[href="/admin/groups/g1"]').exists()).toBe(true)
    await wrapper.findAll('button').find(b => b.text() === 'Share')!.trigger('click')
    await flushPromises()

    expect(fake.POST).toHaveBeenCalledWith('/api/v1/admin/performance-shares', { body: { student_ids: ['s1'] } })
  })

  it('removes the student from a group', async () => {
    const wrapper = await mountSuspended(StudentProfile, { props: { studentId: 's1' } })
    await flushPromises()

    await wrapper.find('button[aria-label="Remove from Class 11 A"]').trigger('click')
    await flushPromises()

    expect(fake.POST.mock.calls[0]![0]).toBe('/api/v1/admin/groups/{group_id}/members/remove')
  })
})
