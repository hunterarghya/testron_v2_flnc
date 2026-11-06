import { mockNuxtImport, mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import { ApiProblem } from '~/api/problems'
import type { SessionUser } from '~/api/types'
import ProfileForm from '~/features/auth/components/ProfileForm.vue'
import TeacherLayout from '~/layouts/teacher.vue'
import LogoutButton from '~/shared/components/LogoutButton.vue'
import authMiddleware from '~/middleware/auth.global'
import { useSession } from '~/shared/composables/useSession'
import { type FakeApi, ok } from '../fake-api'

const mocks = vi.hoisted(() => ({
  auth: { updateName: vi.fn(), changePassword: vi.fn() },
  navigateTo: vi.fn((target: unknown) => target),
}))
vi.mock('~/features/auth/composables/authApi', () => mocks.auth)
vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../fake-api')
  return fakeClientModule(fakeApi())
})
mockNuxtImport('navigateTo', () => mocks.navigateTo)

const fake = api as unknown as FakeApi
const RINA: SessionUser = {
  id: 'u1', name: 'Rina', email: 'rina@x.in', role: 'STUDENT', status: 'ACTIVE', has_password: true, performance_shared: false,
}

beforeEach(() => {
  mocks.auth.updateName.mockReset()
  mocks.auth.changePassword.mockReset()
  mocks.navigateTo.mockClear()
  fake.GET.mockReset().mockImplementation(path =>
    ok(path.endsWith('/session') ? { user: RINA, server_now: '2026-11-12T04:30:00Z' } : undefined))
  fake.POST.mockReset().mockImplementation(() => ok())
})

describe('useSession', () => {
  it('loads the CSRF cookie, then who is logged in', async () => {
    const user = await useSession().load()

    expect(fake.GET.mock.calls.map(call => call[0])).toEqual(['/api/v1/auth/csrf', '/api/v1/auth/session'])
    expect(user).toEqual(RINA)
    expect(useSession().loaded.value).toBe(true)
  })

  it('forgets the user after logging out', async () => {
    useSession().set(RINA)

    await useSession().logOut()

    expect(fake.POST).toHaveBeenCalledWith('/api/v1/auth/logout')
    expect(useSession().user.value).toBeNull()
  })
})

function dialogButton(label: string): HTMLButtonElement {
  return [...document.querySelectorAll('button')].filter(b => b.textContent?.trim() === label).at(-1)!
}

describe('Log out', () => {
  beforeEach(() => {
    useSession().set(RINA)
    fake.POST.mockReset().mockImplementation(() => ok(undefined))
    mocks.navigateTo.mockClear()
  })

  it('asks first: Cancel keeps the session', async () => {
    const wrapper = await mountSuspended(LogoutButton)

    await wrapper.find('button').trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('Log out?')
    dialogButton('Cancel').click()
    await flushPromises()

    expect(fake.POST).not.toHaveBeenCalled()
    expect(useSession().user.value).toEqual(RINA)
    wrapper.unmount()
  })

  it('confirming ends the session and goes to the login page', async () => {
    const wrapper = await mountSuspended(LogoutButton)

    await wrapper.find('button').trigger('click')
    await flushPromises()
    dialogButton('Log out').click()
    await flushPromises()

    expect(fake.POST).toHaveBeenCalledWith('/api/v1/auth/logout')
    expect(useSession().user.value).toBeNull()
    expect(mocks.navigateTo).toHaveBeenCalledWith('/login')
    wrapper.unmount()
  })

  it('the teacher menu says Log out, not the teacher name', async () => {
    useSession().set({ ...RINA, name: 'Mrs Sen', role: 'TEACHER', status: null })
    fake.GET.mockImplementation(() => ok({ pending_students: 0, results_to_publish: 0 }))
    const wrapper = await mountSuspended(TeacherLayout)

    const labels = wrapper.findAll('button').map(b => b.text())
    expect(labels).toContain('Log out')
    expect(labels).not.toContain('Mrs Sen')
    // Red, and left-aligned like the menu items above it
    const logout = wrapper.findAll('button').find(b => b.text() === 'Log out')!
    expect(logout.classes()).toEqual(expect.arrayContaining(['text-error', 'justify-start']))
    expect(logout.classes()).not.toContain('justify-center')
    wrapper.unmount()
  })
})

describe('the route middleware', () => {
  type Middleware = (to: { path: string, fullPath: string }) => Promise<unknown>
  const run = authMiddleware as unknown as Middleware

  it('loads the session once, then lets an active student stay', async () => {
    useSession().loaded.value = false

    expect(await run({ path: '/', fullPath: '/' })).toBeUndefined()
    expect(fake.GET).toHaveBeenCalledWith('/api/v1/auth/session')
  })

  it('sends a student away from the teacher area', async () => {
    useSession().set(RINA)

    await run({ path: '/admin/students', fullPath: '/admin/students' })

    expect(mocks.navigateTo).toHaveBeenCalledWith('/')
  })
})

describe('ProfileForm (P-11)', () => {
  it('saves a new name', async () => {
    useSession().set(RINA)
    mocks.auth.updateName.mockResolvedValue({ ...RINA, name: 'Rina Das' })
    const wrapper = await mountSuspended(ProfileForm)

    await wrapper.find('input').setValue('Rina Das')
    await wrapper.findAll('form')[0]!.trigger('submit')
    await flushPromises()

    expect(mocks.auth.updateName).toHaveBeenCalledWith('Rina Das')
    expect(useSession().user.value?.name).toBe('Rina Das')
  })

  it('asks for the current password, and shows when it is wrong', async () => {
    useSession().set(RINA)
    mocks.auth.changePassword.mockRejectedValue(new ApiProblem({ status: 403, code: 'current_password_incorrect', detail: 'x' }))
    const wrapper = await mountSuspended(ProfileForm)

    await wrapper.findAll('form')[1]!.trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Change password')
    expect(wrapper.text()).toContain('Your current password is not correct.')
  })

  it('lets a Google-only account set a first password', async () => {
    useSession().set({ ...RINA, has_password: false })
    mocks.auth.changePassword.mockResolvedValue(undefined)
    const wrapper = await mountSuspended(ProfileForm)
    expect(wrapper.text()).toContain('Set a password')
    expect(wrapper.text()).not.toContain('Current password')

    await wrapper.findAll('form')[1]!.trigger('submit')
    await flushPromises()

    expect(mocks.auth.changePassword).toHaveBeenCalledWith(null, '')
  })
})
