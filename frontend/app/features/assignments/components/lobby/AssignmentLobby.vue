<!-- T-09 Lobby: who has the gate open (polled every 5 s), the password, and Start for
     everyone. After Start the teacher goes on to the live monitor (T-10). -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { navigateTo } from '#imports'
import { problemMessage } from '~/api/problem-messages'
import PasswordCard from '~/features/assignments/components/overview/PasswordCard.vue'
import { getLobby, startAssignment } from '~/features/assignments/composables/assignmentsApi'
import { useAssignment } from '~/features/assignments/composables/useAssignment'
import ConfirmDialog from '~/shared/components/ConfirmDialog.vue'
import ErrorState from '~/shared/components/ErrorState.vue'
import { useApiData } from '~/shared/composables/useApiData'
import { usePolling } from '~/shared/composables/usePolling'
import { useSubmit } from '~/shared/composables/useSubmit'
import { formatDuration, formatTime } from '~/shared/utils/time'

// api_contract.md §4: the lobby refreshes every 5 s
const LOBBY_INTERVAL_MS = 5000

const props = defineProps<{ assignmentId: string }>()

const assignment = useAssignment(props.assignmentId)
const lobby = useApiData(() => getLobby(props.assignmentId))
const starting = useSubmit(() => startAssignment(props.assignmentId))
const confirming = ref(false)
const detail = computed(() => assignment.detail.data.value)
const startText = computed(() => {
  const seconds = detail.value?.timing.total_duration_s ?? 0
  const end = formatTime(new Date(Date.now() + seconds * 1000))
  return `Everyone gets ${formatDuration(seconds)}, ending at about ${end}.`
})

async function start(): Promise<void> {
  if (await starting.submit()) await navigateTo(`/admin/assignments/${props.assignmentId}/monitor`)
}

usePolling(() => lobby.refresh(), LOBBY_INTERVAL_MS)
onMounted(() => assignment.detail.refresh())
</script>

<template>
  <ErrorState v-if="assignment.detail.error.value" :problem="assignment.detail.error.value" @retry="assignment.detail.refresh" />
  <div v-else-if="detail" class="space-y-4">
    <div class="flex flex-wrap items-center gap-4">
      <h2 class="text-lg font-semibold">
        {{ detail.title }} › Lobby
      </h2>
      <span class="text-sm text-muted">Joined {{ lobby.data.value?.counts.joined ?? 0 }} / {{ lobby.data.value?.counts.audience ?? 0 }}</span>
    </div>
    <!-- The lobby keeps polling, so a failed refresh fixes itself; say the list may be stale -->
    <UAlert v-if="lobby.error.value" color="warning" variant="subtle" icon="i-lucide-wifi-off" title="Couldn't refresh who has joined. Trying again…" />
    <PasswordCard
      v-if="detail.gate.has_password"
      has-password
      :can-change="false"
      :reveal="assignment.reveal.submit"
      :save="assignment.password.submit"
      :pending="false"
      :problem="null"
    />
    <div class="grid gap-4 md:grid-cols-2">
      <UCard>
        <template #header>
          Joined ({{ lobby.data.value?.joined.length ?? 0 }})
        </template>
        <ul class="space-y-1 text-sm">
          <li v-for="student in lobby.data.value?.joined ?? []" :key="student.student_id" class="flex gap-2">
            <UIcon name="i-lucide-circle" class="size-3 self-center text-success" />
            <span>{{ student.name }}</span>
            <span class="ms-auto text-muted">{{ formatTime(student.last_seen_at) }}</span>
          </li>
        </ul>
      </UCard>
      <UCard>
        <template #header>
          Not joined ({{ lobby.data.value?.not_joined.length ?? 0 }})
        </template>
        <ul class="space-y-1 text-sm">
          <li v-for="student in lobby.data.value?.not_joined ?? []" :key="student.student_id" class="text-muted">
            {{ student.name }}
          </li>
        </ul>
      </UCard>
    </div>
    <p class="text-sm text-muted">
      Students who join later can still enter until the late-entry cut-off.
    </p>
    <UAlert v-if="starting.problem.value" color="error" variant="subtle" :title="problemMessage(starting.problem.value)" />
    <UButton
      v-if="!detail.activated_at"
      size="xl"
      icon="i-lucide-play"
      label="Start test for everyone"
      :loading="starting.pending.value"
      @click="confirming = true"
    />
    <ConfirmDialog
      v-model:open="confirming"
      title="Start now?"
      :description="startText"
      confirm-label="Start"
      :pending="starting.pending.value"
      @confirm="start"
    />
  </div>
  <USkeleton v-else class="h-40 w-full" />
</template>
