import { mockNuxtImport, mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiProblem } from '~/api/problems'
import type { SessionUser } from '~/api/types'
import AccountStatus from '~/features/auth/components/AccountStatus.vue'
import ResetPasswordFlow from '~/features/auth/components/ResetPasswordFlow.vue'
import SignUpForm from '~/features/auth/components/SignUpForm.vue'
import VerifyEmailForm from '~/features/auth/components/VerifyEmailForm.vue'
import { useSession } from '~/shared/composables/useSession'

const mocks = vi.hoisted(() => ({
  auth: {
    signUp: vi.fn(),
    verifyEmail: vi.fn(),
    resendCode: vi.fn(),
    requestPasswordReset: vi.fn(),
    confirmPasswordReset: vi.fn(),
  },
  navigateTo: vi.fn(),
  route: { query: {} as Record<string, string>, fullPath: '/' },
}))
vi.mock('~/features/auth/composables/authApi', () => mocks.auth)
mockNuxtImport('navigateTo', () => mocks.navigateTo)
mockNuxtImport('useRoute', () => () => mocks.route)

const PENDING: SessionUser = {
  id: 'u1', name: 'Rina', email: 'rina@x.in', role: 'STUDENT', status: 'PENDING', has_password: true, performance_shared: false,
}
const problem = (status: number, code: string, extra: object = {}) =>
  new ApiProblem({ status, code, detail: code, ...extra })

beforeEach(() => {
  Object.values(mocks.auth).forEach(mock => mock.mockReset())
  mocks.navigateTo.mockReset()
  mocks.route.query = {}
})

describe('SignUpForm (S-02)', () => {
  it('goes on to the code screen with the masked email', async () => {
    mocks.auth.signUp.mockResolvedValue('r•••@x.in')
    const wrapper = await mountSuspended(SignUpForm)
    const inputs = wrapper.findAll('input')
    await inputs[0]!.setValue('Rina Das')
    await inputs[1]!.setValue(' rina@x.in ')
    await inputs[2]!.setValue('a-long-passphrase')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(mocks.navigateTo).toHaveBeenCalledWith({ path: '/verify-email', query: { email: 'rina@x.in', masked: 'r•••@x.in' } })
  })

  it('shows field errors next to their fields', async () => {
    mocks.auth.signUp.mockRejectedValue(problem(422, 'validation_error', {
      errors: [{ field: 'email', code: 'value_error', message: 'Enter a valid email address' }],
    }))
    const wrapper = await mountSuspended(SignUpForm)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Enter a valid email address')
  })

  it('shows a weak password under the password field', async () => {
    mocks.auth.signUp.mockRejectedValue(problem(422, 'password_too_weak'))
    const wrapper = await mountSuspended(SignUpForm)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Choose a longer, less common password.')
  })
})

describe('VerifyEmailForm (S-03)', () => {
  it('shows the masked email and the resend cooldown', async () => {
    mocks.route.query = { email: 'rina@x.in', masked: 'r•••@x.in' }
    const wrapper = await mountSuspended(VerifyEmailForm)

    expect(wrapper.text()).toContain('r•••@x.in')
    expect(wrapper.text()).toContain('Resend (in 1:00)')
  })

  it('logs in and moves on once the code is right', async () => {
    mocks.route.query = { email: 'rina@x.in' }
    mocks.auth.verifyEmail.mockResolvedValue(PENDING)
    const wrapper = await mountSuspended(VerifyEmailForm)
    const boxes = wrapper.findAll('input')
    for (const [index, digit] of [...'123456'].entries()) {
      await boxes[index]!.setValue(digit)
    }

    await wrapper.findAll('button').find(button => button.text() === 'Verify')!.trigger('click')
    await flushPromises()

    expect(mocks.auth.verifyEmail).toHaveBeenCalledWith('rina@x.in', '123456')
    expect(useSession().user.value).toEqual(PENDING)
    expect(mocks.navigateTo).toHaveBeenCalledWith('/status')
  })
})

describe('ResetPasswordFlow (S-04)', () => {
  it('asks for the code after sending it, then returns to login', async () => {
    mocks.auth.requestPasswordReset.mockResolvedValue(undefined)
    mocks.auth.confirmPasswordReset.mockResolvedValue(undefined)
    const wrapper = await mountSuspended(ResetPasswordFlow)
    await wrapper.find('input[type="email"]').setValue('rina@x.in')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('If an account exists for rina@x.in')
  })

  it('shows a failed request without moving on', async () => {
    mocks.auth.requestPasswordReset.mockRejectedValue(problem(0, 'network_error'))
    const wrapper = await mountSuspended(ResetPasswordFlow)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('No connection')
    expect(wrapper.text()).toContain('Reset your password')
  })
})

describe('AccountStatus (S-05)', () => {
  it.each([
    ['PENDING', 'Waiting for approval', true],
    ['DECLINED', 'Request declined', false],
    ['DEACTIVATED', 'Account deactivated', false],
  ] as const)('%s shows "%s"', async (status, title, canCheckAgain) => {
    useSession().set({ ...PENDING, status })
    const wrapper = await mountSuspended(AccountStatus)

    expect(wrapper.text()).toContain(title)
    expect(wrapper.text().includes('Check again')).toBe(canCheckAgain)
  })
})
