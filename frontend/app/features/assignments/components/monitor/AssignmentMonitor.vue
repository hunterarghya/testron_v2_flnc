<!-- T-10 Live monitor, polled every 10 s: each student's sitting, how far they are, warnings
     and when they were last heard from. Extend (D-03) and End for everyone (D-04) for all;
     for the selected: Extend, Force submit and Unlock retake (D-02). -->
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { MonitorFilter, MonitorRow } from '~/api/types'
import { formatCountdown } from '~/engine/clock'
import ExtendTimeDialog from '~/features/assignments/components/monitor/ExtendTimeDialog.vue'
import IntegrityEventsPanel from '~/features/assignments/components/monitor/IntegrityEventsPanel.vue'
import RetakeDialog from '~/features/assignments/components/monitor/RetakeDialog.vue'
import { endForEveryone, forceSubmit, getMonitor } from '~/features/assignments/composables/monitorApi'
import { useAssignment } from '~/features/assignments/composables/useAssignment'
import { monitorColumns, type MonitorTableRow } from '~/features/assignments/utils/monitor-columns'
import { summaryLine } from '~/features/assignments/utils/monitor-text'
import ConfirmDialog from '~/shared/components/ConfirmDialog.vue'
import DataTable from '~/shared/components/DataTable.vue'
import { useApiData } from '~/shared/composables/useApiData'
import { useSubmit } from '~/shared/composables/useSubmit'
import { usePolling } from '~/shared/composables/usePolling'
import { formatTime } from '~/shared/utils/time'

// api_contract.md §4: the monitor refreshes every 10 s
const MONITOR_INTERVAL_MS = 10_000
const FILTERS: { value: MonitorFilter, label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'not_started', label: 'Not started' },
  { value: 'ended', label: 'Finished' },
  { value: 'flagged', label: 'With warnings' },
]

const props = defineProps<{ assignmentId: string }>()

const filter = ref<MonitorFilter>('all')
const monitor = useApiData(() => getMonitor(props.assignmentId, filter.value))
const detail = useAssignment(props.assignmentId).detail
const toast = useToast()
const selected = ref<string[]>([])
type Dialog = 'extend' | 'extend-selected' | 'end' | 'retake' | 'force'
const dialog = ref<Dialog | null>(null)
const ending = useSubmit((confirm: string) => endForEveryone(props.assignmentId, confirm))
const eventsFor = ref<MonitorRow | null>(null)
const data = computed(() => monitor.data.value)
const nowMs = computed(() => (data.value ? Date.parse(data.value.server_now) : Date.now()))
const rows = computed<MonitorTableRow[]>(() => (data.value?.rows ?? []).map(row => ({ ...row, id: row.student_id })))
const chosen = computed(() => rows.value.filter(row => selected.value.includes(row.id)))
const running = computed(() => chosen.value.filter(row => row.status === 'IN_PROGRESS' && row.attempt_id))
const columns = computed(() => monitorColumns(nowMs.value, (row) => {
  eventsFor.value = row
}))
const endsText = computed(() => {
  const ends = data.value?.ends_at
  if (!ends) return 'Open'
  return `ends ${formatTime(ends)} (${formatCountdown(Math.max(0, Date.parse(ends) - nowMs.value))} left)`
})
const currentStage = computed(() => {
  const stages = rows.value.map(row => row.current_stage_index).filter((s): s is number => s !== null)
  return stages.length ? Math.max(...stages) : null
})
function shown(open: boolean): void {
  if (!open) dialog.value = null
}

async function endNow(typed: string): Promise<void> {
  const result = await ending.submit(typed)
  if (!result) return
  toast.add({ title: `Ended ${result.ended_attempts} test(s)`, color: 'success' })
  dialog.value = null
  await monitor.refresh()
}

async function forceSelected(): Promise<void> {
  for (const row of running.value) await forceSubmit(row.attempt_id!)
  toast.add({ title: `Submitted ${running.value.length} test(s)`, color: 'success' })
  dialog.value = null
  await monitor.refresh()
}

function changeFilter(value: MonitorFilter): void {
  filter.value = value
  void monitor.refresh()
}

usePolling(() => monitor.refresh(), MONITOR_INTERVAL_MS)
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h2 class="text-lg font-semibold">
        {{ data?.title }} › Monitor
      </h2>
      <UBadge color="info" variant="subtle" :label="endsText" />
    </div>
    <div class="flex flex-wrap items-center gap-2">
      <UButton icon="i-lucide-plus" label="Extend for all" @click="dialog = 'extend'" />
      <UButton icon="i-lucide-square" label="End for everyone" color="error" variant="soft" @click="dialog = 'end'" />
      <USelect :model-value="filter" :items="FILTERS" class="ms-auto w-44" aria-label="Filter" @update:model-value="value => changeFilter(value as MonitorFilter)" />
    </div>
    <DataTable
      v-model:selected="selected"
      :rows="rows"
      :columns="columns"
      :loading="monitor.pending.value && !data"
      :error="monitor.error.value"
      empty-title="No students here"
      selectable
      @retry="monitor.refresh"
    >
      <template #bulk>
        <UButton size="sm" label="Extend…" @click="dialog = 'extend-selected'" />
        <UButton size="sm" label="Force submit" color="warning" variant="soft" :disabled="!running.length" @click="dialog = 'force'" />
        <UButton size="sm" label="Unlock retake" variant="soft" @click="dialog = 'retake'" />
      </template>
    </DataTable>
    <p v-if="data" class="text-sm text-muted">
      Summary: {{ summaryLine(data) }}
    </p>
    <ExtendTimeDialog
      :open="dialog === 'extend' || dialog === 'extend-selected'"
      :assignment-id="assignmentId"
      :student-ids="dialog === 'extend-selected' ? selected : []"
      :sectioned="detail.data.value?.timing.kind === 'SECTIONED'"
      :current-stage="currentStage"
      @update:open="shown"
      @done="monitor.refresh"
    />
    <ConfirmDialog
      :open="dialog === 'end'"
      title="End the test for everyone?"
      :description="`${data?.summary.IN_PROGRESS ?? 0} still answering. Every test still running is submitted and graded now. This can't be undone.`"
      confirm-label="End for everyone"
      typed-confirmation="END"
      danger
      :pending="ending.pending.value"
      @update:open="shown"
      @confirm="endNow"
    />
    <RetakeDialog
      :open="dialog === 'retake'"
      :assignment-id="assignmentId" :students="chosen.map(row => ({ id: row.id, name: row.name }))" @update:open="shown" @done="granted => toast.add({ title: `Retake unlocked for ${granted}`, color: 'success' })" />
    <ConfirmDialog
      :open="dialog === 'force'"
      title="Submit now?"
      :description="`${running.length} test(s) still running will be submitted and graded now.`"
      confirm-label="Force submit"
      @update:open="shown"
      @confirm="forceSelected"
    />
    <IntegrityEventsPanel :open="eventsFor !== null" :attempt-id="eventsFor?.attempt_id ?? null" :name="eventsFor?.name ?? ''" @update:open="value => { if (!value) eventsFor = null }" />
  </div>
</template>
