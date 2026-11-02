import { describe, expect, it } from 'vitest'
import { formatDateTime } from '~/shared/utils/time'

describe('formatDateTime', () => {
  it('shows UTC instants in Indian time', () => {
    expect(formatDateTime('2026-11-12T04:30:00Z')).toBe('12 Nov 2026, 10:00')
  })

  it('crosses midnight correctly', () => {
    expect(formatDateTime('2026-11-12T19:00:00Z')).toBe('13 Nov 2026, 00:30')
  })
})
