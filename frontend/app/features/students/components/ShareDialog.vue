<!-- D-06 Share performance: with the ticked students (a switch each; Off removes their access)
     or with everyone in a group [I-3]. -->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Group, StudentRow } from '~/api/types'
import { isEmptyChange, type ShareChange, studentsChange } from '~/features/students/utils/share-plan'

const props = defineProps<{
  students: StudentRow[]
  groups: Group[]
  pending: boolean
}>()
const emit = defineEmits<{ save: [change: ShareChange] }>()
const open = defineModel<boolean>('open', { required: true })

const WITH = [{ value: 'students', label: 'The selected students' }, { value: 'group', label: 'A whole group' }]
const target = ref<'students' | 'group'>('students')
const switches = ref<Record<string, boolean>>({})
const groupId = ref<string>()
const groupItems = computed(() => props.groups.map(group => ({ label: group.name, value: group.id })))
const change = computed<ShareChange | null>(() => {
  if (target.value === 'group') return groupId.value ? { kind: 'group', groupId: groupId.value } : null
  return studentsChange(props.students, switches.value)
})

watch(open, (isOpen) => {
  if (!isOpen) return
  target.value = 'students'
  groupId.value = undefined
  switches.value = Object.fromEntries(props.students.map(student => [student.id, student.performance_shared]))
})
</script>

<template>
  <UModal v-model:open="open" title="Share performance" description="Students see their own chapters and trend, from published results only.">
    <template #body>
      <div class="space-y-4">
        <URadioGroup v-model="target" :items="WITH" legend="Share with" orientation="horizontal" />
        <ul v-if="target === 'students'" class="max-h-72 divide-y divide-default overflow-y-auto">
          <li v-for="student in students" :key="student.id" class="flex items-center justify-between gap-3 py-2">
            <span class="truncate">{{ student.name }}</span>
            <USwitch v-model="switches[student.id]" :label="switches[student.id] ? 'On' : 'Off'" />
          </li>
        </ul>
        <div v-else class="space-y-1">
          <USelect v-model="groupId" :items="groupItems" placeholder="Choose a group" class="w-full" aria-label="Group" />
          <p class="text-sm text-muted">Everyone in the group now gets access. Students who join later don't.</p>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Cancel" color="neutral" variant="ghost" @click="open = false" />
        <UButton label="Save" :loading="pending" :disabled="!change || isEmptyChange(change)" @click="change && emit('save', change)" />
      </div>
    </template>
  </UModal>
</template>
