// D-06: what the share dialog changes. Only students whose switch moved are sent, so an
// untouched student is never shared or unshared by accident [I-3].
import type { StudentRow } from '~/api/types'

export type ShareChange =
  | { kind: 'students', on: string[], off: string[] }
  | { kind: 'group', groupId: string }

type Shareable = Pick<StudentRow, 'id' | 'performance_shared'>

export function studentsChange(students: readonly Shareable[], switches: Record<string, boolean>): ShareChange {
  const moved = students.filter(student => (switches[student.id] ?? student.performance_shared) !== student.performance_shared)
  return {
    kind: 'students',
    on: moved.filter(student => !student.performance_shared).map(student => student.id),
    off: moved.filter(student => student.performance_shared).map(student => student.id),
  }
}

export function isEmptyChange(change: ShareChange): boolean {
  return change.kind === 'students' && !change.on.length && !change.off.length
}

export function shareSummary(shared: number, unshared: number): string {
  const parts = [
    shared ? `${shared} now see${shared === 1 ? 's' : ''} their performance` : '',
    unshared ? `${unshared} no longer see${unshared === 1 ? 's' : ''} it` : '',
  ]
  return parts.filter(Boolean).join(', ') || 'Nothing changed'
}
