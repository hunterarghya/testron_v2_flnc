// T-07 step ② "Confirm students" [D-1]: groups fill the list, ticked; the teacher unticks
// anyone to leave them out and adds individuals. What's saved is the ticked list.
import type { AudienceCandidate } from '~/api/types'

export interface AudienceEntry {
  studentId: string
  name: string
  groupNames: string[]
  ticked: boolean
  // Added by hand, not from a picked group
  individual: boolean
}

/** The list after the picked groups changed: their members (keeping earlier unticks), then
 *  the individuals added by hand who aren't in those groups. */
export function mergeGroups(previous: AudienceEntry[], candidates: AudienceCandidate[]): AudienceEntry[] {
  const before = new Map(previous.map(entry => [entry.studentId, entry]))
  const fromGroups = candidates.map(candidate => ({
    studentId: candidate.student_id,
    name: candidate.name,
    groupNames: candidate.group_names,
    ticked: before.get(candidate.student_id)?.ticked ?? true,
    individual: false,
  }))
  const inGroups = new Set(fromGroups.map(entry => entry.studentId))
  const individuals = previous.filter(entry => entry.individual && !inGroups.has(entry.studentId))
  return [...fromGroups, ...individuals]
}

export function addIndividuals(list: AudienceEntry[], students: { id: string, name: string }[]): AudienceEntry[] {
  const present = new Set(list.map(entry => entry.studentId))
  const added = students
    .filter(student => !present.has(student.id))
    .map(student => ({ studentId: student.id, name: student.name, groupNames: [], ticked: true, individual: true }))
  return [...list, ...added]
}

export function tickedIds(list: AudienceEntry[]): string[] {
  return list.filter(entry => entry.ticked).map(entry => entry.studentId)
}

/** "81 of 82 selected · 1 added individually" */
export function selectionSummary(list: AudienceEntry[]): string {
  const individuals = list.filter(entry => entry.individual).length
  const base = `${tickedIds(list).length} of ${list.length} selected`
  return individuals ? `${base} · ${individuals} added individually` : base
}
