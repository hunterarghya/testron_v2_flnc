// T-15's data: one student, the groups they could join, and the actions on the page. Each
// action reports its outcome as a toast and reloads the student.
import { computed, ref } from 'vue'
import { useToast } from '#imports'
import { api, unwrap } from '~/api/client'
import { problemMessage } from '~/api/problem-messages'
import { toProblem } from '~/api/problems'
import { useApiData } from '~/shared/composables/useApiData'

export function useStudent(studentId: string) {
  const toast = useToast()
  const pending = ref(false)
  const detail = useApiData(() => unwrap(api.GET('/api/v1/admin/students/{student_id}', {
    params: { path: { student_id: studentId } },
  })))
  const groups = useApiData(() => unwrap(api.GET('/api/v1/admin/groups', { params: { query: { archived: false } } })))
  const joinable = computed(() => {
    const joined = new Set(detail.data.value?.groups.map(group => group.id))
    return (groups.data.value ?? []).filter(group => !joined.has(group.id))
  })
  const ids = { student_ids: [studentId] }

  async function run(action: () => Promise<unknown>, done: string): Promise<void> {
    pending.value = true
    try {
      await action()
      toast.add({ title: done, color: 'success' })
      await detail.refresh()
    }
    catch (caught) {
      toast.add({ title: problemMessage(toProblem(caught)), color: 'error' })
    }
    finally {
      pending.value = false
    }
  }

  const member = (groupId: string) => ({ params: { path: { group_id: groupId } }, body: ids })

  return {
    detail,
    groups,
    joinable,
    pending,
    load: () => Promise.all([detail.refresh(), groups.refresh()]),
    joinGroup: (groupId: string) => run(() => api.POST('/api/v1/admin/groups/{group_id}/members', member(groupId)), 'Added to the group'),
    leaveGroup: (groupId: string) => run(() => api.POST('/api/v1/admin/groups/{group_id}/members/remove', member(groupId)), 'Removed from the group'),
    share: () => run(() => api.POST('/api/v1/admin/performance-shares', { body: ids }), 'Performance shared'),
    unshare: () => run(() => api.POST('/api/v1/admin/performance-shares/remove', { body: ids }), 'Performance no longer shared'),
    deactivate: () => run(() => api.POST('/api/v1/admin/students/deactivate', { body: ids }), 'Student deactivated'),
    reactivate: () => run(() => api.POST('/api/v1/admin/students/reactivate', { body: ids }), 'Student reactivated'),
  }
}
