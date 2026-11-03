<!-- T-08 Overview: state, summary, audience and password, with ⋯ Edit settings, Assign
     again and Cancel (before Start, while no one has begun). -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { navigateTo } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import AudienceCard from '~/features/assignments/components/overview/AudienceCard.vue'
import EditSettingsDialog from '~/features/assignments/components/overview/EditSettingsDialog.vue'
import PasswordCard from '~/features/assignments/components/overview/PasswordCard.vue'
import { useAssignment } from '~/features/assignments/composables/useAssignment'
import { STATE_LABELS, summaryRows } from '~/features/assignments/utils/describe'
import ConfirmDialog from '~/shared/components/ConfirmDialog.vue'
import ErrorState from '~/shared/components/ErrorState.vue'

const props = defineProps<{ assignmentId: string }>()

const assignment = useAssignment(props.assignmentId)
const { detail } = assignment
const editing = ref(false)
const cancelling = ref(false)
const data = computed(() => detail.data.value)
const cancelled = computed(() => data.value?.state === 'CANCELLED')
// The lobby before the start; the live monitor (T-10) once it is running or over
const live = computed(() => data.value?.state === 'LIVE' || data.value?.state === 'CLOSED')
const hasLobby = computed(() => Boolean(data.value && !cancelled.value && !live.value
  && (data.value.window_kind === 'MANUAL' || data.value.gate.requires_activation)))
const menu = computed(() => [
  ...(cancelled.value ? [] : [{ label: 'Edit settings', icon: 'i-lucide-settings', onSelect: () => { editing.value = true } }]),
  { label: 'Assign again', icon: 'i-lucide-copy', to: `/admin/assignments/new?from=${props.assignmentId}` },
  ...(!cancelled.value && !data.value?.activated_at
    ? [{ label: 'Cancel assignment', icon: 'i-lucide-ban', color: 'error' as const, onSelect: () => { cancelling.value = true } }]
    : []),
])

async function cancel(): Promise<void> {
  await assignment.cancel.submit()
  if (!assignment.cancel.problem.value) cancelling.value = false
}

onMounted(() => detail.refresh())
</script>

<template>
  <ErrorState v-if="detail.error.value" :problem="detail.error.value" @retry="detail.refresh" />
  <div v-else-if="data" class="space-y-4">
    <div class="flex flex-wrap items-center gap-2">
      <h2 class="text-lg font-semibold">
        {{ data.title }}
      </h2>
      <UBadge v-bind="STATE_LABELS[data.state]" variant="subtle" />
      <div class="ms-auto flex gap-2">
        <UButton v-if="hasLobby" label="Open lobby" icon="i-lucide-door-open" @click="navigateTo(`/admin/assignments/${assignmentId}/lobby`)" />
        <UButton v-if="live" label="Open monitor" icon="i-lucide-activity" @click="navigateTo(`/admin/assignments/${assignmentId}/monitor`)" />
        <UDropdownMenu :items="menu">
          <UButton icon="i-lucide-ellipsis" aria-label="More actions" color="neutral" variant="outline" />
        </UDropdownMenu>
      </div>
    </div>
    <div class="grid gap-4 lg:grid-cols-2">
      <UCard>
        <template #header>
          <h3 class="font-medium">
            Summary
          </h3>
        </template>
        <dl class="grid grid-cols-[8rem_1fr] gap-y-1 text-sm">
          <template v-for="[label, value] in summaryRows(data)" :key="label">
            <dt class="text-muted">
              {{ label }}
            </dt>
            <dd>{{ value }}</dd>
          </template>
        </dl>
      </UCard>
      <div class="space-y-4">
        <AudienceCard
          :detail="data"
          :pending="assignment.addStudents.pending.value || assignment.removeStudents.pending.value"
          :add="assignment.addStudents.submit"
          :remove="assignment.removeStudents.submit"
        />
        <UAlert
          v-if="assignment.removeStudents.problem.value"
          color="error"
          variant="subtle"
          :title="problemMessage(assignment.removeStudents.problem.value)"
        />
        <PasswordCard
          :has-password="data.gate.has_password"
          :can-change="!cancelled"
          :reveal="assignment.reveal.submit"
          :save="assignment.password.submit"
          :pending="assignment.password.pending.value"
          :problem="assignment.password.problem.value"
        />
      </div>
    </div>
    <EditSettingsDialog
      v-model:open="editing"
      :detail="data"
      :save="assignment.update.submit"
      :pending="assignment.update.pending.value"
      :problem="assignment.update.problem.value"
    />
    <ConfirmDialog
      v-model:open="cancelling"
      title="Cancel this assignment?"
      :description="`${data.title} will be called off. Students won't see it any more. This can't be undone.`"
      confirm-label="Cancel assignment"
      danger
      :pending="assignment.cancel.pending.value"
      @confirm="cancel"
    />
  </div>
</template>
