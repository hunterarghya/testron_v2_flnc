import { mockNuxtImport, mountSuspended } from '@nuxt/test-utils/runtime'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiProblem } from '~/api/problems'
import type { SessionUser } from '~/api/types'
import LoginForm from '~/features/auth/components/LoginForm.vue'

const { logIn, navigateTo, route } = vi.hoisted(() => ({
  logIn: vi.fn(),
  navigateTo: vi.fn(),
  route: { query: {} as Record<string, string> },
}))

vi.mock('~/features/auth/composables/authApi', () => ({ logIn }))
mockNuxtImport('navigateTo', () => navigateTo)
mockNuxtImport('useRoute', () => () => route)

const STUDENT: SessionUser = {
  id: 'u1',
  name: 'Rina Das',
  email: 'rina@example.com',
  role: 'STUDENT',
  status: 'ACTIVE',
  has_password: true,
  performance_shared: false,
}

async function submitWith(email: string, password: string) {
  const wrapper = await mountSuspended(LoginForm)
  await wrapper.find('input[type="email"]').setValue(email)
  await wrapper.find('input[type="password"]').setValue(password)
  await wrapper.find('form').trigger('submit')
  await vi.waitFor(() => expect(logIn).toHaveBeenCalled())
  await new Promise(resolve => setTimeout(resolve, 0))
  return wrapper
}

describe('LoginForm (S-01)', () => {
  beforeEach(() => {
    logIn.mockReset()
    navigateTo.mockReset()
    route.query = {}
  })

  it('sends the person home after logging in', async () => {
    logIn.mockResolvedValue(STUDENT)

    await submitWith('rina@example.com', 'secret-pass')

    expect(logIn).toHaveBeenCalledWith('rina@example.com', 'secret-pass')
    expect(navigateTo).toHaveBeenCalledWith('/')
  })

  it('returns to the page they came from, if it is on this site', async () => {
    logIn.mockResolvedValue(STUDENT)
    route.query = { next: '/profile' }

    await submitWith('rina@example.com', 'secret-pass')

    expect(navigateTo).toHaveBeenCalledWith('/profile')
  })

  it('shows one message for every failed login', async () => {
    logIn.mockRejectedValue(new ApiProblem({ status: 401, code: 'invalid_credentials', detail: 'x' }))

    const wrapper = await submitWith('rina@example.com', 'wrong')

    expect(wrapper.text()).toContain('The email or password is not correct.')
    expect(navigateTo).not.toHaveBeenCalled()
  })

  it('sends an unverified account to the code screen', async () => {
    logIn.mockRejectedValue(new ApiProblem({ status: 403, code: 'email_not_verified', detail: 'x' }))

    await submitWith('rina@example.com', 'secret-pass')

    expect(navigateTo).toHaveBeenCalledWith({ path: '/verify-email', query: { email: 'rina@example.com' } })
  })
})
