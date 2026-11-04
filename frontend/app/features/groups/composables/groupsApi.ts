// Every groups call the screens make (api_contract.md §2.3), in one place.
import { api, unwrap } from '~/api/client'
import type { BulkResult, Group, GroupDetail, GroupPerformance } from '~/api/types'

export interface GroupFields {
  name: string
  description: string
}

export function listGroups(archived: boolean, search: string): Promise<Group[]> {
  return unwrap(api.GET('/api/v1/admin/groups', {
    params: { query: { archived, q: search.trim() || undefined } },
  }))
}

export function getGroup(groupId: string): Promise<GroupDetail> {
  return unwrap(api.GET('/api/v1/admin/groups/{group_id}', { params: { path: { group_id: groupId } } }))
}

export function createGroup(fields: GroupFields): Promise<Group> {
  return unwrap(api.POST('/api/v1/admin/groups', { body: fields }))
}

export function updateGroup(groupId: string, fields: GroupFields): Promise<Group> {
  return unwrap(api.PATCH('/api/v1/admin/groups/{group_id}', {
    params: { path: { group_id: groupId } },
    body: fields,
  }))
}

export function setArchived(groupId: string, archived: boolean): Promise<Group> {
  const params = { path: { group_id: groupId } }
  return archived
    ? unwrap(api.POST('/api/v1/admin/groups/{group_id}/archive', { params }))
    : unwrap(api.POST('/api/v1/admin/groups/{group_id}/restore', { params }))
}

export function changeMembers(groupId: string, studentIds: string[], add: boolean): Promise<BulkResult> {
  const init = { params: { path: { group_id: groupId } }, body: { student_ids: studentIds } }
  return add
    ? unwrap(api.POST('/api/v1/admin/groups/{group_id}/members', init))
    : unwrap(api.POST('/api/v1/admin/groups/{group_id}/members/remove', init))
}

export function shareWithGroup(groupId: string): Promise<BulkResult> {
  return unwrap(api.POST('/api/v1/admin/performance-shares', { body: { group_id: groupId } }))
}

export function getGroupPerformance(groupId: string): Promise<GroupPerformance> {
  return unwrap(api.GET('/api/v1/admin/groups/{group_id}/performance', { params: { path: { group_id: groupId } } }))
}
