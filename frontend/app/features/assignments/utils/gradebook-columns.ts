// T-11's Students table: Student (a link to the sheet), Take, Rank, Score (in brackets when
// disqualified), one column per section, Time, Flags and Status, plus the ⋯ menu that lets a
// disqualified attempt count again (D-09).
import type { TableColumn } from '@nuxt/ui'
import { h } from 'vue'
import { NuxtLink, UBadge, UButton } from '#components'
import type { GradebookRow } from '~/api/types'
import { formatDecimal } from '~/shared/utils/decimals'
import { formatDuration } from '~/shared/utils/time'

export type GradebookTableRow = GradebookRow & { id: string }

export const STATUS: Record<string, { label: string, color: 'success' | 'info' | 'warning' | 'error' | 'neutral' }> = {
  SUBMITTED: { label: 'Submitted', color: 'success' },
  TIMED_OUT: { label: 'Timed out', color: 'neutral' },
  AUTO_SUBMITTED: { label: 'Auto-submit', color: 'warning' },
  DISQUALIFIED: { label: 'Disq.', color: 'error' },
  FORCE_SUBMITTED: { label: 'Force-submitted', color: 'neutral' },
  ENDED_BY_TEACHER: { label: 'Ended', color: 'neutral' },
  IN_PROGRESS: { label: 'In progress', color: 'info' },
  NOT_STARTED: { label: 'Not started', color: 'neutral' },
  ABSENT: { label: 'Absent', color: 'neutral' },
}

export function scoreCell(row: GradebookRow): string {
  if (row.score == null) return '–'
  const score = formatDecimal(row.score)
  return row.status === 'DISQUALIFIED' && !row.overridden ? `(${score})` : score
}

export function gradebookColumns(sectionTitles: string[], onOverride: (row: GradebookRow) => void): TableColumn<GradebookTableRow>[] {
  return [
    {
      id: 'name',
      header: 'Student',
      cell: ({ row }) => (row.original.attempt_id
        ? h(NuxtLink, { to: `/admin/attempts/${row.original.attempt_id}`, class: 'text-primary' }, () => `${row.original.name} ›`)
        : row.original.name),
    },
    { id: 'take', header: 'Take', cell: ({ row }) => row.original.take_number ?? '–' },
    { id: 'rank', header: 'Rank', cell: ({ row }) => row.original.rank ?? '–' },
    { id: 'score', header: 'Score', cell: ({ row }) => scoreCell(row.original) },
    ...sectionTitles.map((title, i): TableColumn<GradebookTableRow> => ({
      id: `section-${i}`,
      header: title,
      cell: ({ row }) => (row.original.sections[i] ? formatDecimal(row.original.sections[i].score) : '–'),
    })),
    { id: 'time', header: 'Time', cell: ({ row }) => (row.original.time_taken_s == null ? '–' : formatDuration(row.original.time_taken_s)) },
    { id: 'flags', header: 'Flags', cell: ({ row }) => (row.original.warning_count ? `⚑ ${row.original.warning_count}` : '') },
    {
      id: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const status = STATUS[row.original.status] ?? STATUS.NOT_STARTED!
        const badge = h(UBadge, { label: row.original.overridden ? 'Counted' : status.label, color: status.color, variant: 'subtle' })
        if (row.original.status !== 'DISQUALIFIED' || row.original.overridden) return badge
        return h('span', { class: 'flex items-center gap-1' }, [
          badge,
          h(UButton, { 'label': 'Count', 'size': 'xs', 'variant': 'link', 'aria-label': `Count ${row.original.name}'s attempt`, 'onClick': () => onOverride(row.original) }),
        ])
      },
    },
  ]
}
