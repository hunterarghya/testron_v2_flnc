import { describe, expect, it } from 'vitest'
import { isEmptyChange, shareSummary, studentsChange } from '~/features/students/utils/share-plan'

const STUDENTS = [
  { id: 'a', performance_shared: false },
  { id: 'b', performance_shared: true },
  { id: 'c', performance_shared: false },
]

describe('D-06 share plan', () => {
  it('sends only the switches that moved', () => {
    const change = studentsChange(STUDENTS, { a: true, b: false, c: false })
    expect(change).toEqual({ kind: 'students', on: ['a'], off: ['b'] })
  })

  it('knows when nothing changed', () => {
    expect(isEmptyChange(studentsChange(STUDENTS, {}))).toBe(true)
    expect(isEmptyChange({ kind: 'group', groupId: 'g1' })).toBe(false)
  })

  it('sums up the save', () => {
    expect(shareSummary(2, 1)).toBe('2 now see their performance, 1 no longer sees it')
    expect(shareSummary(1, 0)).toBe('1 now sees their performance')
    expect(shareSummary(0, 0)).toBe('Nothing changed')
  })
})
