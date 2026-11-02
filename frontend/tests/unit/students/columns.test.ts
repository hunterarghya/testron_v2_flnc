import { describe, expect, it } from 'vitest'
import type { StudentRow } from '~/api/types'
import { studentColumns } from '~/features/students/utils/columns'

const NOW = Date.parse('2026-11-12T10:00:00Z')
const ROW: StudentRow = {
  id: 's1',
  name: 'Rina Das',
  email: 'rina@example.com',
  status: 'PENDING',
  joined_at: '2026-11-01T10:00:00Z',
  requested_at: '2026-11-12T08:00:00Z',
  decided_at: null,
  deactivated_at: null,
  performance_shared: true,
  group_names: ['Class 11 A', 'Class 12 B'],
}

type Cell = (context: { row: { original: StudentRow } }) => unknown

function cellText(tab: StudentRow['status'], index: number, row: StudentRow = ROW): string {
  const column = studentColumns(tab, NOW)[index] as { cell: Cell }
  const rendered = column.cell({ row: { original: row } })
  return typeof rendered === 'string' ? rendered : String((rendered as { children: unknown }).children)
}

describe('student table columns (T-14)', () => {
  it.each([
    ['ACTIVE', 'Joined'],
    ['PENDING', 'Requested'],
    ['DECLINED', 'Declined'],
    ['DEACTIVATED', 'Deactivated'],
  ] as const)('the %s tab shows the %s time', (tab, header) => {
    expect(studentColumns(tab, NOW).map(column => column.header)).toEqual(['Email', 'Groups', header, 'Performance'])
  })

  it('shows times relatively', () => {
    expect(cellText('PENDING', 2)).toBe('2 hours ago')
  })

  it('shows a dash for a missing time', () => {
    expect(cellText('DECLINED', 2)).toBe('—')
  })

  it('marks shared performance', () => {
    expect(cellText('ACTIVE', 3)).toBe('📊 Shared')
    expect(cellText('ACTIVE', 3, { ...ROW, performance_shared: false })).toBe('')
  })

  it('lists the groups', () => {
    expect(cellText('ACTIVE', 1)).toBe('Class 11 A, Class 12 B')
  })
})
