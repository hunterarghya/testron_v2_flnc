<!-- T-08 Audience: who sits it. Students can be added any time; those who haven't begun can
     be removed (E-11). Groups only helped pick: later group changes don't touch the list. -->
<script setup lang="ts">
import { ref } from 'vue'
import type { AssignmentDetail, BulkResult } from '~/api/types'
import PickStudentsDialog from '~/shared/components/PickStudentsDialog.vue'

const props = defineProps<{
  detail: AssignmentDetail
  pending: boolean
  add: (ids: string[]) => Promise<BulkResult | undefined>
  remove: (ids: string[]) => Promise<BulkResult | undefined>
}>()

const adding = ref(false)
const editing = ref(false)
const cancelled = () => props.detail.state === 'CANCELLED'

async function onAdd(ids: string[]): Promise<void> {
  if (await props.add(ids)) adding.value = false
}
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex items-center gap-2">
        <h3 class="font-medium">
          Audience ({{ detail.audience.count }})
        </h3>
        <span class="text-sm text-muted">{{ detail.audience.summary }}</span>
        <UButton
          v-if="!cancelled()"
          class="ms-auto"
          :label="editing ? 'Done' : 'Edit'"
          size="xs"
          variant="outline"
          @click="editing = !editing"
        />
      </div>
    </template>
    <ul class="max-h-80 space-y-1 overflow-y-auto">
      <li v-for="student in detail.audience_students" :key="student.id" class="flex items-center gap-2 text-sm">
        <span>{{ student.name }}</span>
        <span class="text-muted">{{ student.group_names.join(', ') }}</span>
        <UBadge v-if="student.has_attempt" label="Started" size="sm" variant="subtle" />
        <UButton
          v-if="editing && !student.has_attempt"
          class="ms-auto"
          icon="i-lucide-x"
          :aria-label="`Remove ${student.name}`"
          color="error"
          variant="ghost"
          size="xs"
          :loading="pending"
          @click="remove([student.id])"
        />
      </li>
    </ul>
    <UButton v-if="editing" class="mt-3" icon="i-lucide-plus" label="Add students" variant="outline" size="sm" @click="adding = true" />
    <PickStudentsDialog
      v-model:open="adding"
      :member-ids="detail.audience_students.map(student => student.id)"
      description="Only active students can be added."
      :pending="pending"
      @add="students => onAdd(students.map(student => student.id))"
    />
  </UCard>
</template>
