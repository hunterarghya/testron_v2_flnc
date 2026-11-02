import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '~/api/client'
import * as auth from '~/features/auth/composables/authApi'
import { type FakeApi, ok } from '../../fake-api'

vi.mock('~/api/client', async () => {
  const { fakeApi, fakeClientModule } = await import('../../fake-api')
  return fakeClientModule(fakeApi())
})

const fake = api as unknown as FakeApi

describe('auth API calls (api_contract.md §2.1)', () => {
  beforeEach(() => {
    fake.POST.mockReset().mockImplementation(() => ok({ email_masked: 'r•••@x.in', id: 'u1' }))
    fake.PATCH.mockReset().mockImplementation(() => ok({ id: 'u1', name: 'New' }))
  })

  it.each([
    ['logIn', () => auth.logIn('a@x.in', 'pw'), '/api/v1/auth/login', { email: 'a@x.in', password: 'pw' }],
    ['signUp', () => auth.signUp('A', 'a@x.in', 'pw'), '/api/v1/auth/sign-up', { name: 'A', email: 'a@x.in', password: 'pw' }],
    ['verifyEmail', () => auth.verifyEmail('a@x.in', '123456'), '/api/v1/auth/email-verification', { email: 'a@x.in', code: '123456' }],
    ['resendCode', () => auth.resendCode('a@x.in'), '/api/v1/auth/email-verification/resend', { email: 'a@x.in' }],
    ['requestPasswordReset', () => auth.requestPasswordReset('a@x.in'), '/api/v1/auth/password-reset', { email: 'a@x.in' }],
    ['confirmPasswordReset', () => auth.confirmPasswordReset('a@x.in', '123456', 'new-pass'), '/api/v1/auth/password-reset/confirm', { email: 'a@x.in', code: '123456', new_password: 'new-pass' }],
    ['changePassword', () => auth.changePassword(null, 'new-pass'), '/api/v1/auth/password', { current_password: null, new_password: 'new-pass' }],
  ])('%s posts to the right endpoint', async (_name, call, path, body) => {
    await call()

    expect(fake.POST).toHaveBeenCalledWith(path, { body })
  })

  it('signUp answers with the masked email', async () => {
    expect(await auth.signUp('A', 'a@x.in', 'pw')).toBe('r•••@x.in')
  })

  it('updateName patches the profile', async () => {
    const user = await auth.updateName('New')

    expect(fake.PATCH).toHaveBeenCalledWith('/api/v1/auth/profile', { body: { name: 'New' } })
    expect(user).toMatchObject({ name: 'New' })
  })
})
