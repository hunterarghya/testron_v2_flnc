<!-- P-08 Past Tests: one card per take, newest first, and "Missed" for a test never sat. A
     score shows only once published; rank only if the teacher shows it. -->
<script setup lang="ts">
import { computed, onMounted } from 'vue'
import type { PastTest } from '~/api/types'
import { listPastTests } from '~/features/past-tests/composables/pastTestsApi'
import ErrorState from '~/shared/components/ErrorState.vue'
import { useApiData } from '~/shared/composables/useApiData'
import { scoreText } from '~/shared/utils/result-text'
import { formatDateTime } from '~/shared/utils/time'

const past = useApiData(listPastTests)
const cards = computed(() => past.data.value?.items ?? [])

const STATE: Record<PastTest['state'], { label: string, color: 'neutral' | 'success' | 'warning' | 'error' }> = {
  AWAITING_RESULTS: { label: 'Awaiting results', color: 'neutral' },
  PUBLISHED: { label: 'Published', color: 'success' },
  MISSED: { label: 'Missed', color: 'warning' },
  DISQUALIFIED: { label: 'Disqualified', color: 'error' },
}

function facts(card: PastTest): string {
  if (card.state !== 'PUBLISHED' || card.max_score == null) return ''
  const rank = card.rank ? ` · Rank ${card.rank} of ${card.rank_pool}` : ''
  return scoreText(card.score, card.max_score) + rank
}

onMounted(() => past.refresh())
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-xl font-semibold">
      Past Tests
    </h1>
    <ErrorState v-if="past.error.value" :problem="past.error.value" @retry="past.refresh" />
    <p v-else-if="past.data.value && !cards.length" class="text-muted">
      No past tests yet.
    </p>
    <UCard v-for="card in cards" :key="card.attempt_id ?? card.assignment_id">
      <div class="flex flex-wrap items-center gap-3">
        <div class="min-w-0 flex-1 space-y-1">
          <p class="font-medium">
            {{ card.label }}
          </p>
          <p class="flex flex-wrap items-center gap-2 text-sm">
            <UBadge :label="STATE[card.state].label" :color="STATE[card.state].color" variant="subtle" />
            <span v-if="card.state === 'MISSED' && card.at" class="text-muted">{{ formatDateTime(card.at) }}</span>
            <span>{{ facts(card) }}</span>
          </p>
        </div>
        <UButton v-if="card.state === 'PUBLISHED'" label="View" trailing-icon="i-lucide-chevron-right" variant="soft" :to="`/past/${card.attempt_id}`" />
      </div>
    </UCard>
  </div>
</template>
