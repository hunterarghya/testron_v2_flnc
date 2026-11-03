<!-- T-17 Students tab: the members, tick to remove, and "Add students". -->
<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { computed, h, ref } from 'vue'
import { ULink } from '#components'
import type { GroupMember } from '~/api/types'
import PickStudentsDialog from '~/shared/components/PickStudentsDialog.vue'
import DataTable from '~/shared/components/DataTable.vue'
import { formatDateTime } from '~/shared/utils/time'

const props = defineProps<{
  members: GroupMember[]
  archived: boolean
  pending: boolean
  add: (ids: string[]) => Promise<boolean>
  remove: (ids: string[]) => Promise<boolean>
}>()

const selected = ref<string[]>([])
const adding = ref(false)
const memberIds = computed(() => props.members.map(member => member.id))
const columns: TableColumn<GroupMember>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    cell: ({ row }) => h(ULink, { to: `/admin/students/${row.original.id}` }, () => row.original.name),
  },
  { accessorKey: 'email', header: 'Email' },
  { accessorKey: 'status', header: 'Status', cell: ({ row }) => (row.original.status === 'ACTIVE' ? 'Active' : 'Deactivated') },
  { accessorKey: 'added_at', header: 'Added', cell: ({ row }) => formatDateTime(row.original.added_at) },
  { id: 'shared', header: 'Performance', cell: ({ row }) => (row.original.performance_shared ? '📊 Shared' : '') },
]

async function onAdd(ids: string[]): Promise<void> {
  if (await props.add(ids)) {
    adding.value = false
  }
}

async function onRemove(): Promise<void> {
  if (await props.remove(selected.value)) {
    selected.value = []
  }
}
</script>

<template>
  <div class="space-y-3">
    <UAlert v-if="archived" color="neutral" variant="subtle" title="This group is archived. Restore it to change its members." />
    <UButton v-else label="Add students" icon="i-lucide-user-plus" @click="adding = true" />
    <DataTable
      v-model:selected="selected"
      :rows="members"
      :columns="columns"
      empty-title="No students in this group yet."
      :selectable="!archived"
    >
      <template #bulk>
        <UButton label="Remove from group" color="error" variant="outline" :loading="pending" @click="onRemove" />
      </template>
    </DataTable>
    <PickStudentsDialog
      v-model:open="adding"
      :member-ids="memberIds"
      description="Only active students can join a group."
      :pending="pending"
      @add="students => onAdd(students.map(student => student.id))"
    />
  </div>
</template>
