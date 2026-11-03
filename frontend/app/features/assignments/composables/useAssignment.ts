// T-08's data: one assignment and every change the overview makes, each followed by a
// fresh read so the screen always shows the server's view.
import type { AssignmentChanges, AssignmentDetail, BulkResult } from '~/api/types'
import {
  cancelAssignment,
  changeAudience,
  getAssignment,
  revealPassword,
  setPassword,
  updateAssignment,
} from '~/features/assignments/composables/assignmentsApi'
import { useApiData } from '~/shared/composables/useApiData'
import { useSubmit } from '~/shared/composables/useSubmit'

export function useAssignment(assignmentId: string) {
  const detail = useApiData<AssignmentDetail>(() => getAssignment(assignmentId))

  // Every change: run it, then show the assignment as it is now
  function change<Args extends unknown[], Result>(action: (...args: Args) => Promise<Result>) {
    return useSubmit(async (...args: Args) => {
      const result = await action(...args)
      await detail.refresh()
      return result
    })
  }

  return {
    detail,
    update: change((changes: AssignmentChanges) => updateAssignment(assignmentId, changes)),
    addStudents: change((ids: string[]): Promise<BulkResult> => changeAudience(assignmentId, ids, true)),
    removeStudents: change((ids: string[]): Promise<BulkResult> => changeAudience(assignmentId, ids, false)),
    password: change((password: string | null, confirm?: string) => setPassword(assignmentId, password, confirm)),
    cancel: change(() => cancelAssignment(assignmentId)),
    reveal: useSubmit(() => revealPassword(assignmentId)),
  }
}
