<!-- T-15 Student profile: details, groups, performance sharing, deactivate/reactivate.
     The Attempts and Performance tabs fill in Phases 6 and 7. -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useStudent } from '~/features/students/composables/useStudent'
import ConfirmDialog from '~/shared/components/ConfirmDialog.vue'
import ErrorState from '~/shared/components/ErrorState.vue'
import { formatDateTime } from '~/shared/utils/time'

const props = defineProps<{ studentId: string }>()

const STATUS = { ACTIVE: 'Active', PENDING: 'Pending', DECLINED: 'Declined', DEACTIVATED: 'Deactivated' } as const
const TABS = [{ value: 'attempts', label: 'Attempts' }, { value: 'performance', label: 'Performance' }]

const page = useStudent(props.studentId)
const { detail, joinable, pending } = page
const tab = ref('attempts')
const confirmingDeactivate = ref(false)
const student = computed(() => detail.data.value?.student)
const admitted = computed(() => student.value?.status === 'ACTIVE' || student.value?.status === 'DEACTIVATED')
const crumbs = computed(() => [{ label: 'Students', to: '/admin/students' }, { label: student.value?.name ?? '…' }])
const joinItems = computed(() => joinable.value.map(group => ({ label: group.name, onSelect: () => page.joinGroup(group.id) })))

async function deactivate(): Promise<void> {
  await page.deactivate()
  confirmingDeactivate.value = false
}

onMounted(page.load)
</script>

<template>
  <ErrorState v-if="detail.error.value" :problem="detail.error.value" @retry="page.load" />
  <div v-else-if="student" class="space-y-4">
    <UBreadcrumb :items="crumbs" />
    <div class="flex flex-wrap items-start gap-3">
      <div class="min-w-0 flex-1 space-y-1">
        <h1 class="text-xl font-semibold">{{ student.name }} <UBadge :label="STATUS[student.status]" color="neutral" variant="subtle" class="ms-2 align-middle" /></h1>
        <p class="text-muted">{{ student.email }} · Joined {{ formatDateTime(student.joined_at) }}</p>
      </div>
      <UButton v-if="student.status === 'ACTIVE'" label="Deactivate" color="error" variant="outline" @click="confirmingDeactivate = true" />
      <UButton v-else-if="student.status === 'DEACTIVATED'" label="Reactivate" :loading="pending" @click="page.reactivate" />
    </div>
    <div v-if="admitted" class="flex flex-wrap items-center gap-2">
      <span class="text-sm font-medium">Groups:</span>
      <UBadge v-for="group in detail.data.value?.groups" :key="group.id" color="neutral" variant="outline">
        <ULink :to="`/admin/groups/${group.id}`">{{ group.name }}</ULink>
        <UButton icon="i-lucide-x" size="xs" color="neutral" variant="link" :aria-label="`Remove from ${group.name}`" @click="page.leaveGroup(group.id)" />
      </UBadge>
      <UDropdownMenu :items="joinItems" :disabled="!joinItems.length">
        <UButton icon="i-lucide-plus" label="Add to group" size="xs" color="neutral" variant="ghost" />
      </UDropdownMenu>
    </div>
    <div v-if="admitted" class="flex items-center gap-2">
      <span class="text-sm">{{ student.performance_shared ? '📊 Performance shared with the student' : 'Performance not shared' }}</span>
      <UButton v-if="student.performance_shared" label="Unshare" size="xs" color="neutral" variant="outline" :loading="pending" @click="page.unshare" />
      <UButton v-else label="Share" size="xs" color="neutral" variant="outline" :loading="pending" @click="page.share" />
    </div>
    <UTabs v-model="tab" :items="TABS" :content="false" />
    <UEmpty v-if="tab === 'attempts'" icon="i-lucide-file-text" title="No attempts yet." description="Tests this student takes will be listed here." />
    <UEmpty v-else icon="i-lucide-chart-column" title="No performance yet." description="Chapter-by-chapter accuracy appears after their first published result." />
    <ConfirmDialog
      v-model:open="confirmingDeactivate"
      :title="`Deactivate ${student.name}?`"
      description="They lose access at once. Their history is kept, and you can reactivate them later."
      confirm-label="Deactivate"
      danger
      :pending="pending"
      @confirm="deactivate"
    />
  </div>
  <USkeleton v-else class="h-40 w-full" />
</template>
