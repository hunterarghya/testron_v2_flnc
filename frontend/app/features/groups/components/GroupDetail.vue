<!-- T-17 Group detail: name and description, members, and sharing performance with everyone
     in the group. Assignments and the group's performance arrive in Phases 5 and 7. -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Group } from '~/api/types'
import GroupFormDialog from '~/features/groups/components/GroupFormDialog.vue'
import GroupMembers from '~/features/groups/components/GroupMembers.vue'
import { useGroup } from '~/features/groups/composables/useGroup'
import ErrorState from '~/shared/components/ErrorState.vue'

const props = defineProps<{ groupId: string }>()

const { detail, pending, addMembers, removeMembers, shareWithAll } = useGroup(props.groupId)
const editing = ref(false)
const tab = ref('students')
const group = computed<Group | undefined>(() => detail.data.value?.group)
const members = computed(() => detail.data.value?.members ?? [])
const tabs = computed(() => [
  { value: 'students', label: 'Students', badge: members.value.length },
  { value: 'assignments', label: 'Assignments' },
  { value: 'performance', label: 'Performance' },
])
const crumbs = computed(() => [
  { label: 'Groups', to: '/admin/groups' },
  { label: group.value?.name ?? '…' },
])

onMounted(detail.refresh)
</script>

<template>
  <ErrorState v-if="detail.error.value" :problem="detail.error.value" @retry="detail.refresh" />
  <div v-else-if="group" class="space-y-4">
    <UBreadcrumb :items="crumbs" />
    <div class="flex flex-wrap items-start gap-3">
      <div class="min-w-0 flex-1">
        <h1 class="text-xl font-semibold">
          {{ group.name }}
          <UBadge v-if="group.archived_at" label="Archived" color="neutral" variant="subtle" class="ms-2 align-middle" />
        </h1>
        <p v-if="group.description" class="text-muted">{{ group.description }}</p>
      </div>
      <UButton label="Edit" icon="i-lucide-pencil" color="neutral" variant="outline" @click="editing = true" />
    </div>
    <UTabs v-model="tab" :items="tabs" :content="false" />
    <GroupMembers
      v-if="tab === 'students'"
      :members="members"
      :archived="Boolean(group.archived_at)"
      :pending="pending"
      :add="addMembers"
      :remove="removeMembers"
    />
    <UEmpty
      v-else-if="tab === 'assignments'"
      icon="i-lucide-clipboard-list"
      title="No assignments yet."
      description="Tests assigned to this group will be listed here."
    />
    <div v-else class="space-y-3">
      <UEmpty icon="i-lucide-chart-column" title="No results yet." description="The group's chapter-by-chapter accuracy appears after its first published test." />
      <UButton
        label="Share performance with everyone in the group"
        icon="i-lucide-share-2"
        color="neutral"
        variant="outline"
        :disabled="!members.length"
        :loading="pending"
        @click="shareWithAll"
      />
    </div>
    <GroupFormDialog v-model:open="editing" :group="group" @saved="detail.refresh" />
  </div>
  <USkeleton v-else class="h-40 w-full" />
</template>
