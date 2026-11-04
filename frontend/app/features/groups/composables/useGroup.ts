// T-17's data: one group with its members, and what the teacher does there. Each action
// reports its outcome as a toast and reloads the group.
import { ref } from 'vue'
import { useToast } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import { toProblem } from '~/api/problems'
import type { BulkResult } from '~/api/types'
import { changeMembers, getGroup, getGroupPerformance, shareWithGroup } from '~/features/groups/composables/groupsApi'
import { useApiData } from '~/shared/composables/useApiData'

export function outcome(result: BulkResult, verb: string): string {
  const done = `${result.succeeded.length} ${verb}`
  return result.skipped.length ? `${done}, ${result.skipped.length} skipped` : done
}

export function useGroup(groupId: string) {
  const toast = useToast()
  const pending = ref(false)
  const detail = useApiData(() => getGroup(groupId))
  const performance = useApiData(() => getGroupPerformance(groupId))

  async function run(action: () => Promise<BulkResult>, verb: string): Promise<boolean> {
    pending.value = true
    try {
      toast.add({ title: outcome(await action(), verb), color: 'success' })
      await detail.refresh()
      return true
    }
    catch (caught) {
      toast.add({ title: problemMessage(toProblem(caught)), color: 'error' })
      return false
    }
    finally {
      pending.value = false
    }
  }

  return {
    detail,
    performance,
    pending,
    addMembers: (ids: string[]) => run(() => changeMembers(groupId, ids, true), 'added'),
    removeMembers: (ids: string[]) => run(() => changeMembers(groupId, ids, false), 'removed'),
    shareWithAll: () => run(() => shareWithGroup(groupId), 'now see their performance'),
  }
}
