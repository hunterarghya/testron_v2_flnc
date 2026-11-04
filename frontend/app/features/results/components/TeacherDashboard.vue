<!-- T-01 Dashboard, refreshed every 15 s: tests running now, what needs the teacher, the
     week ahead, recent results and quick actions. Each "needs attention" line links to the
     list it describes. -->
<script setup lang="ts">
import { computed } from 'vue'
import { getDashboard } from '~/features/results/composables/resultsInboxApi'
import ErrorState from '~/shared/components/ErrorState.vue'
import { useApiData } from '~/shared/composables/useApiData'
import { usePolling } from '~/shared/composables/usePolling'
import { formatDateTime, formatTime } from '~/shared/utils/time'

// api_contract.md §4: the dashboard refreshes every 15 s
const DASHBOARD_INTERVAL_MS = 15_000

const board = useApiData(getDashboard)
const data = computed(() => board.data.value)
const attention = computed(() => [
  ...(data.value?.pending_students ? [{ text: `${data.value.pending_students} student(s) waiting for approval`, to: '/admin/students' }] : []),
  ...(data.value?.results_to_publish ? [{ text: `${data.value.results_to_publish} result(s) ready to publish`, to: '/admin/results' }] : []),
])

usePolling(() => board.refresh(), DASHBOARD_INTERVAL_MS)
</script>

<template>
  <ErrorState v-if="board.error.value" :problem="board.error.value" @retry="board.refresh" />
  <div v-else-if="data" class="grid gap-4 lg:grid-cols-2">
    <UCard>
      <template #header>
        Live now
      </template>
      <p v-if="!data.live.length" class="text-sm text-muted">
        No test running.
      </p>
      <div v-for="test in data.live" :key="test.assignment_id" class="flex items-center gap-3 py-1">
        <div class="min-w-0 flex-1">
          <p class="font-medium">
            ● {{ test.title }}
          </p>
          <p class="text-sm text-muted">
            {{ test.in_progress }}/{{ test.audience }} in progress<span v-if="test.ends_at"> · ends {{ formatTime(test.ends_at) }}</span>
          </p>
        </div>
        <UButton label="Monitor" size="sm" :to="`/admin/assignments/${test.assignment_id}/monitor`" />
      </div>
    </UCard>
    <UCard>
      <template #header>
        Needs your attention
      </template>
      <p v-if="!attention.length" class="text-sm text-muted">
        All caught up.
      </p>
      <ULink v-for="item in attention" :key="item.to" :to="item.to" class="flex justify-between py-1 text-sm">
        {{ item.text }} <span>›</span>
      </ULink>
    </UCard>
    <UCard>
      <template #header>
        Upcoming (next 7 days)
      </template>
      <p v-if="!data.upcoming.length" class="text-sm text-muted">
        Nothing planned.
      </p>
      <div v-for="test in data.upcoming" :key="test.assignment_id" class="flex items-center gap-3 py-1 text-sm">
        <span class="w-36 text-muted">{{ test.starts_at ? formatDateTime(test.starts_at) : 'When you start it' }}</span>
        <span class="flex-1">{{ test.title }}</span>
        <UButton label="View" size="xs" variant="soft" :to="`/admin/assignments/${test.assignment_id}`" />
      </div>
    </UCard>
    <UCard>
      <template #header>
        Recent results
      </template>
      <p v-if="!data.recent.length" class="text-sm text-muted">
        No results yet.
      </p>
      <ULink v-for="row in data.recent" :key="row.assignment_id" :to="`/admin/assignments/${row.assignment_id}/results`" class="flex justify-between py-1 text-sm">
        <span>{{ row.title }}<span v-if="row.average_pct != null"> · avg {{ row.average_pct }}%</span></span>
        <span class="text-muted">{{ row.publication_state === 'PUBLISHED' ? 'Published' : 'Unpublished' }}</span>
      </ULink>
    </UCard>
    <UCard class="lg:col-span-2">
      <div class="flex flex-wrap gap-2">
        <UButton label="New test" icon="i-lucide-plus" to="/admin/tests" />
        <UButton label="Assign a test" icon="i-lucide-send" variant="soft" to="/admin/assignments/new" />
      </div>
    </UCard>
  </div>
</template>
