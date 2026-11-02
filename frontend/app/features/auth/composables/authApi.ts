// The auth screens' calls to the API (api_contract.md §2.1). Every error is thrown as an
// ApiProblem; the forms show it through useSubmit.
import { api, unwrap } from '~/api/client'
import type { SessionUser } from '~/api/types'

export function logIn(email: string, password: string): Promise<SessionUser> {
  return unwrap(api.POST('/api/v1/auth/login', { body: { email, password } }))
}

export async function signUp(name: string, email: string, password: string): Promise<string> {
  const accepted = await unwrap(api.POST('/api/v1/auth/sign-up', { body: { name, email, password } }))
  return accepted.email_masked
}

export function verifyEmail(email: string, code: string): Promise<SessionUser> {
  return unwrap(api.POST('/api/v1/auth/email-verification', { body: { email, code } }))
}

export async function resendCode(email: string): Promise<void> {
  await api.POST('/api/v1/auth/email-verification/resend', { body: { email } })
}

export async function requestPasswordReset(email: string): Promise<void> {
  await api.POST('/api/v1/auth/password-reset', { body: { email } })
}

export async function confirmPasswordReset(
  email: string,
  code: string,
  newPassword: string,
): Promise<void> {
  await api.POST('/api/v1/auth/password-reset/confirm', {
    body: { email, code, new_password: newPassword },
  })
}

export async function changePassword(currentPassword: string | null, newPassword: string): Promise<void> {
  await api.POST('/api/v1/auth/password', {
    body: { current_password: currentPassword, new_password: newPassword },
  })
}

export function updateName(name: string): Promise<SessionUser> {
  return unwrap(api.PATCH('/api/v1/auth/profile', { body: { name } }))
}
