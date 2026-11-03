import { describe, expect, it } from 'vitest'
import { formatDateTime, formatTime, fromIndianLocal, toIndianLocal } from '~/shared/utils/time'

describe('formatDateTime', () => {
  it('shows UTC instants in Indian time', () => {
    expect(formatDateTime('2026-11-12T04:30:00Z')).toBe('12 Nov 2026, 10:00')
  })

  it('crosses midnight correctly', () => {
    expect(formatDateTime('2026-11-12T19:00:00Z')).toBe('13 Nov 2026, 00:30')
  })
})

describe('Indian-time inputs', () => {
  it('reads a datetime-local value as Indian time', () => {
    expect(fromIndianLocal('2026-11-12T10:00')).toBe('2026-11-12T04:30:00.000Z')
  })

  it('writes UTC back as the same local value', () => {
    expect(toIndianLocal('2026-11-12T04:30:00Z')).toBe('2026-11-12T10:00')
  })

  it('formats a clock time', () => {
    expect(formatTime('2026-11-12T05:28:00Z')).toBe('10:58')
  })
})
