<!-- P-07 review before submitting: what is answered, not answered and marked, the time left,
     and the warning that answers can't change after. Offline, it says the answers are safe
     on this device and asks to reconnect. -->
<script setup lang="ts">
import { computed } from 'vue'
import { problemMessage } from '~/api/problem-messages'
import type { ApiProblem } from '~/api/problems'
import { formatCountdown } from '~/engine/clock'
import { useHall } from '~/features/exam-hall/composables/useExamSession'
import { paletteCounts } from '~/features/exam-hall/utils/palette'

const props = defineProps<{ remainingMs: number, offline: boolean, problem: ApiProblem | null }>()
defineEmits<{ submit: [], back: [] }>()
const open = defineModel<boolean>('open', { required: true })

const hall = useHall()
const counts = computed(() => paletteCounts(hall.questions.value.map(q => q.id), hall.responses.value))
const submitting = computed(() => hall.phase.value === 'submitting')
const rows = computed(() => [
  { label: 'Answered', value: String(counts.value.answered) },
  { label: 'Not answered', value: String(counts.value.not_answered + counts.value.not_visited) },
  { label: 'Marked for review', value: String(counts.value.marked) },
  { label: 'Time left', value: Number.isFinite(props.remainingMs) ? formatCountdown(props.remainingMs) : '—' },
])
</script>

<template>
  <UModal v-model:open="open" title="Submit test?" :dismissible="!submitting">
    <template #body>
      <dl class="grid grid-cols-2 gap-y-2 text-sm">
        <template v-for="row in rows" :key="row.label">
          <dt>{{ row.label }}</dt>
          <dd class="text-end font-mono">
            {{ row.value }}
          </dd>
        </template>
      </dl>
      <UAlert
        v-if="offline"
        class="mt-4"
        color="warning"
        variant="subtle"
        icon="i-lucide-wifi-off"
        title="Can't submit while offline. Your answers are saved on this device. Reconnect to submit."
      />
      <UAlert v-else-if="problem" class="mt-4" color="error" variant="subtle" :title="problemMessage(problem)" />
      <UAlert v-else class="mt-4" color="warning" variant="subtle" icon="i-lucide-triangle-alert" title="You can't change answers after submitting." />
    </template>
    <template #footer>
      <div class="flex w-full justify-end gap-2">
        <UButton label="Back to test" color="neutral" variant="outline" :disabled="submitting" @click="$emit('back')" />
        <UButton label="Submit" :loading="submitting" @click="$emit('submit')" />
      </div>
    </template>
  </UModal>
</template>
