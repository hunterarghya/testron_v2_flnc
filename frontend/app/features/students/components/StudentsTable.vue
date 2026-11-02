<!-- T-14 Students: one tab per status, search, a selectable table and the bulk bar. -->
<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { ListedStatus } from '~/api/types'
import StudentsBulkActions from '~/features/students/components/StudentsBulkActions.vue'
import { PAGE_SIZE, TABS, useStudents } from '~/features/students/composables/useStudents'
import { studentColumns } from '~/features/students/utils/columns'
import DataTable from '~/shared/components/DataTable.vue'

const LABELS: Record<ListedStatus, string> = {
  ACTIVE: 'Active',
  PENDING: 'Pending',
  DECLINED: 'Declined',
  DEACTIVATED: 'Deactivated',
}
const EMPTY: Record<ListedStatus, string> = {
  ACTIVE: 'No active students yet. Approve join requests on the Pending tab.',
  PENDING: 'No one is waiting for approval.',
  DECLINED: 'No declined requests.',
  DEACTIVATED: 'No deactivated students.',
}

const students = useStudents()
const { tab, search, page, list, counts } = students
const selected = ref<string[]>([])
const rows = computed(() => list.data.value?.items ?? [])
const selectedRows = computed(() => rows.value.filter(row => selected.value.includes(row.id)))
const columns = computed(() => studentColumns(tab.value, Date.now()))
const tabs = computed(() => TABS.map(status => ({
  value: status,
  label: LABELS[status],
  badge: counts.data.value?.[status] || undefined,
})))
const canAct = computed(() => tab.value !== 'DECLINED')

watch(tab, () => {
  selected.value = []
  page.value = 1
})
onMounted(students.refresh)
</script>

<template>
  <div class="space-y-4">
    <UTabs v-model="tab" :items="tabs" :content="false" />
    <UInput v-model="search" icon="i-lucide-search" placeholder="Search name or email" class="w-full max-w-sm" aria-label="Search students" />
    <DataTable
      v-model:selected="selected"
      :rows="rows"
      :columns="columns"
      :loading="list.pending.value"
      :error="list.error.value"
      :empty-title="EMPTY[tab]"
      :selectable="canAct"
      @retry="students.refresh"
    >
      <template #bulk>
        <StudentsBulkActions
          :tab="tab"
          :selected="selectedRows"
          :act="students.act"
          :anonymize="students.anonymize"
          @done="selected = []"
        />
      </template>
    </DataTable>
    <UPagination
      v-if="(list.data.value?.total ?? 0) > PAGE_SIZE"
      v-model:page="page"
      :total="list.data.value?.total ?? 0"
      :items-per-page="PAGE_SIZE"
    />
  </div>
</template>
