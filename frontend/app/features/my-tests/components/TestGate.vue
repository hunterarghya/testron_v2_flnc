<!-- P-02 Test Gate: (a) the rules always come first; then (b) waiting for the teacher,
     (d) the countdown to a scheduled start, or (c) the password and Start. -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import GatePassword from '~/features/my-tests/components/GatePassword.vue'
import { useGate } from '~/features/my-tests/composables/useGate'
import { lateJoinMessage, markingLine, ruleBullets, rulesFacts, stagesLine } from '~/features/my-tests/utils/gate-text'
import ErrorState from '~/shared/components/ErrorState.vue'
import { formatCountdown } from '~/engine/clock'

const props = defineProps<{ assignmentId: string }>()

const { gate, state, rulesRead, remainingMs } = useGate(props.assignmentId)
const data = computed(() => gate.data.value)
const lateJoin = computed(() => (data.value ? lateJoinMessage(data.value) : null))
const ticked = ref(false)

onMounted(() => gate.refresh())
</script>

<template>
  <ErrorState v-if="gate.error.value" :problem="gate.error.value" @retry="gate.refresh" />
  <UCard v-else-if="data" class="mx-auto max-w-xl">
    <template #header>
      <h1 class="text-lg font-semibold">
        {{ data.title }}
      </h1>
    </template>

    <div v-if="!rulesRead" class="space-y-3">
      <p>{{ rulesFacts(data.rules) }}</p>
      <p v-if="stagesLine(data.rules)">
        {{ stagesLine(data.rules) }}
      </p>
      <p>{{ markingLine(data.rules) }}</p>
      <ul class="list-disc space-y-1 ps-5 text-sm">
        <li v-for="rule in ruleBullets(data.rules)" :key="rule">
          {{ rule }}
        </li>
      </ul>
      <UCheckbox v-model="ticked" label="I have read the rules" />
      <UButton label="Continue" block :disabled="!ticked" @click="rulesRead = true" />
    </div>

    <div v-else-if="state === 'WAITING_FOR_TEACHER'" class="space-y-2 py-6 text-center">
      <UIcon name="i-lucide-hourglass" class="size-8" />
      <p class="font-medium">
        Waiting for your teacher to start the test…
      </p>
      <p class="text-sm text-muted">
        Keep this page open.
      </p>
    </div>

    <div v-else-if="state === 'NOT_OPEN'" class="space-y-2 py-6 text-center">
      <p>Starts in</p>
      <p class="font-mono text-3xl" aria-live="polite">
        {{ formatCountdown(remainingMs) }}
      </p>
      <p class="text-sm text-muted">
        (server time) The test opens here automatically.
      </p>
    </div>

    <div v-else-if="state === 'READY'" class="space-y-4">
      <UAlert v-if="lateJoin" color="warning" variant="subtle" :title="lateJoin" />
      <GatePassword :requires-password="data.requires_password" />
    </div>

    <UAlert v-else-if="state === 'IN_PROGRESS'" color="info" variant="subtle" title="You have already started this test." />
    <UAlert v-else-if="state === 'ENTRY_CLOSED'" color="neutral" variant="subtle" title="Entry closed" description="The time to join this test has passed." />
    <UAlert v-else color="neutral" variant="subtle" title="No attempts left" description="You have used every attempt for this test." />
  </UCard>
</template>
