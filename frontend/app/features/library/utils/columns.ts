// T-02's columns after the name (which TestLibrary links to the editor).
import type { TableColumn } from '@nuxt/ui'
import type { TestRow } from '~/api/types'
import { formatDecimal } from '~/shared/utils/decimals'
import { formatDateTime } from '~/shared/utils/time'

const TIMING: Record<TestRow['timing_kind'], string> = {
  TOTAL: 'Total',
  PER_QUESTION: 'Per question',
  SECTIONED: 'Sections',
}

export function testColumns(): TableColumn<TestRow>[] {
  return [
    { accessorKey: 'question_count', header: 'Qs' },
    { id: 'marks', header: 'Marks', cell: ({ row }) => formatDecimal(row.original.total_marks) },
    { id: 'timing', header: 'Timing', cell: ({ row }) => TIMING[row.original.timing_kind] },
    {
      id: 'last_used',
      header: 'Last used',
      cell: ({ row }) => (row.original.last_assigned_at ? formatDateTime(row.original.last_assigned_at) : 'never'),
    },
  ]
}
