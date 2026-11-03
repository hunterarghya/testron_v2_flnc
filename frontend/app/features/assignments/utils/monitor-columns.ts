// T-10's table columns: Student, Status, Section, Answered, Flags (⚑ n opens the events),
// Last seen (amber when quiet for over a minute).
import type { TableColumn } from '@nuxt/ui'
import { h } from 'vue'
import { UBadge, UButton } from '#components'
import type { MonitorRow } from '~/api/types'
import { answeredText, lastSeen, STATUS_LABEL } from '~/features/assignments/utils/monitor-text'

export type MonitorTableRow = MonitorRow & { id: string }

const TONE: Partial<Record<MonitorRow['status'], 'success' | 'info' | 'warning' | 'error' | 'neutral'>> = {
  IN_PROGRESS: 'info',
  SUBMITTED: 'success',
  AUTO_SUBMITTED: 'warning',
  DISQUALIFIED: 'error',
}

export function monitorColumns(nowMs: number, openEvents: (row: MonitorRow) => void): TableColumn<MonitorTableRow>[] {
  return [
    { accessorKey: 'name', header: 'Student' },
    {
      id: 'status',
      header: 'Status',
      cell: ({ row }) => h(UBadge, { label: STATUS_LABEL[row.original.status], color: TONE[row.original.status] ?? 'neutral', variant: 'subtle' }),
    },
    {
      id: 'section',
      header: 'Section',
      cell: ({ row }) => (row.original.current_stage_index === null ? '–' : `S${row.original.current_stage_index + 1}`),
    },
    { id: 'answered', header: 'Answered', cell: ({ row }) => answeredText(row.original) },
    {
      id: 'flags',
      header: 'Flags',
      cell: ({ row }) => (row.original.warning_count > 0 && row.original.attempt_id
        ? h(UButton, {
            'label': `⚑ ${row.original.warning_count}`,
            'aria-label': `Warnings for ${row.original.name}`,
            'color': 'warning',
            'variant': 'ghost',
            'size': 'xs',
            'trailingIcon': 'i-lucide-chevron-right',
            'onClick': () => openEvents(row.original),
          })
        : ''),
    },
    {
      id: 'last',
      header: 'Last',
      cell: ({ row }) => {
        const seen = lastSeen(row.original, nowMs)
        return h('span', { class: seen.quiet ? 'text-warning' : '' }, seen.text)
      },
    },
  ]
}
