import { describe, expect, it } from 'vitest'
import { bulkSummary } from '~/features/students/utils/bulk-summary'

describe('bulkSummary', () => {
  it('says how many were changed', () => {
    expect(bulkSummary({ succeeded: ['a', 'b'], skipped: [] }, 'approve')).toBe('2 approved')
  })

  it('names the reasons for skipped students once each', () => {
    const result = {
      succeeded: ['a'],
      skipped: [
        { id: 'b', reason: 'status_active' },
        { id: 'c', reason: 'status_active' },
        { id: 'd', reason: 'not_found' },
      ],
    }

    expect(bulkSummary(result, 'approve')).toBe('1 approved, 3 skipped (already active, not found)')
  })

  it('shows an unknown reason as it came', () => {
    const result = { succeeded: [], skipped: [{ id: 'a', reason: 'something_new' }] }

    expect(bulkSummary(result, 'deactivate')).toBe('0 deactivated, 1 skipped (something_new)')
  })
})
