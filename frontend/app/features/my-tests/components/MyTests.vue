<!-- P-01 My Tests: what the student can start, join or resume now, and what's coming up.
     Refreshes every 60 s while visible, which also re-syncs the server clock. -->
<script setup lang="ts">
import { computed } from 'vue'
import { listMyTests } from '~/features/my-tests/composables/myTestsApi'
import { BUTTON, cardFacts, cardStatus } from '~/features/my-tests/utils/card-text'
import ErrorState from '~/shared/components/ErrorState.vue'
import { useApiData } from '~/shared/composables/useApiData'
import { usePolling } from '~/shared/composables/usePolling'
import { useServerClock } from '~/shared/composables/useServerClock'

// api_contract.md §4: My Tests polls every 60 s
const MY_TESTS_INTERVAL_MS = 60_000

const tests = useApiData(listMyTests)
const clock = useServerClock()
const available = computed(() => tests.data.value?.available ?? [])
const upcoming = computed(() => tests.data.value?.upcoming ?? [])
const empty = computed(() => tests.data.value !== null && !available.value.length && !upcoming.value.length)

usePolling(() => tests.refresh(), MY_TESTS_INTERVAL_MS)
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-xl font-semibold">
      My Tests
    </h1>
    <ErrorState v-if="tests.error.value" :problem="tests.error.value" @retry="tests.refresh" />
    <p v-else-if="empty" class="text-muted">
      No tests right now. Your teacher will assign them here.
    </p>
    <section v-if="available.length" class="space-y-3">
      <h2 class="font-medium">
        Available now
      </h2>
      <UCard v-for="card in available" :key="card.assignment_id">
        <div class="flex flex-wrap items-center gap-3">
          <div class="min-w-0 flex-1 space-y-1">
            <p class="flex items-center gap-2 font-medium">
              {{ card.title }}
              <UIcon v-if="card.locked" name="i-lucide-lock" class="size-4 text-muted" aria-label="Locked" />
            </p>
            <p class="text-sm text-muted">
              {{ cardFacts(card) }}
            </p>
            <p class="text-sm">
              {{ cardStatus(card, clock.now()) }}
            </p>
          </div>
          <UButton :label="BUTTON[card.state]" trailing-icon="i-lucide-chevron-right" :to="`/tests/${card.assignment_id}`" />
        </div>
      </UCard>
    </section>
    <section v-if="upcoming.length" class="space-y-2">
      <h2 class="font-medium">
        Upcoming
      </h2>
      <ul class="space-y-1 text-sm">
        <li v-for="card in upcoming" :key="card.assignment_id">
          <span class="font-medium">{{ card.title }}</span>
          <span class="text-muted"> · {{ cardStatus(card, clock.now()) }}</span>
        </li>
      </ul>
    </section>
  </div>
</template>
