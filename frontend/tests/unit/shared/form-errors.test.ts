import { describe, expect, it } from 'vitest'
import { ApiProblem } from '~/api/problems'
import { fieldErrors } from '~/shared/utils/form-errors'
import { relativeTime } from '~/shared/utils/time'

describe('fieldErrors', () => {
  it('maps each field to its first message', () => {
    const problem = new ApiProblem({
      status: 422,
      code: 'validation_error',
      detail: 'x',
      errors: [
        { field: 'email', code: 'value_error', message: 'Enter a valid email address' },
        { field: 'email', code: 'other', message: 'second message' },
        { field: 'name', code: 'value_error', message: 'Enter a name' },
      ],
    })

    expect(fieldErrors(problem)).toEqual({ email: 'Enter a valid email address', name: 'Enter a name' })
  })

  it('has nothing for other problems or none', () => {
    expect(fieldErrors(new ApiProblem({ status: 401, code: 'invalid_credentials', detail: 'x' }))).toEqual({})
    expect(fieldErrors(null)).toEqual({})
  })
})

describe('relativeTime', () => {
  const now = Date.parse('2026-11-12T10:00:00Z')

  it.each([
    ['2026-11-12T08:00:00Z', '2 hours ago'],
    ['2026-11-11T10:00:00Z', 'yesterday'],
    ['2026-11-12T09:55:00Z', '5 minutes ago'],
    ['2026-11-12T09:59:30Z', 'just now'],
    ['2026-11-12T10:30:00Z', 'in 30 minutes'],
  ])('%s → %s', (iso, text) => {
    expect(relativeTime(iso, now)).toBe(text)
  })
})
