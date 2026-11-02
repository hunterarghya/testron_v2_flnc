// The columns of each T-14 tab. Times show exactly on hover and relatively in the cell.
import type { TableColumn } from '@nuxt/ui'
import { h } from 'vue'
import type { ListedStatus, StudentRow } from '~/api/types'
import { formatDateTime, relativeTime } from '~/shared/utils/time'

type TimeField = 'joined_at' | 'requested_at' | 'decided_at' | 'deactivated_at'

const TIME_COLUMN: Record<ListedStatus, { field: TimeField, header: string }> = {
  ACTIVE: { field: 'joined_at', header: 'Joined' },
  PENDING: { field: 'requested_at', header: 'Requested' },
  DECLINED: { field: 'decided_at', header: 'Declined' },
  DEACTIVATED: { field: 'deactivated_at', header: 'Deactivated' },
}

export function studentColumns(tab: ListedStatus, nowMs: number): TableColumn<StudentRow>[] {
  const time = TIME_COLUMN[tab]
  return [
    { accessorKey: 'name', header: 'Name' },
    { accessorKey: 'email', header: 'Email' },
    {
      id: time.field,
      header: time.header,
      cell: ({ row }) => timeCell(row.original[time.field], nowMs),
    },
    {
      id: 'shared',
      header: 'Performance',
      cell: ({ row }) => (row.original.performance_shared ? '📊 Shared' : ''),
    },
  ]
}

function timeCell(iso: string | null | undefined, nowMs: number) {
  if (!iso) {
    return '—'
  }
  return h('span', { title: formatDateTime(iso) }, relativeTime(iso, nowMs))
}
