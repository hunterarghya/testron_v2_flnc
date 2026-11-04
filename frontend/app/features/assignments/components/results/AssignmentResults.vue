<!-- T-11 Results: the class's stats, every student (absent ones too, one row per take) and
     how each question went. Publish (D-01) or, once published, edit or unpublish; export the
     gradebook; unlock retakes for the selected; correct a key (D-05); count a disqualified
     attempt (D-09). -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { GradebookRow, QuestionStat } from '~/api/types'
import RetakeDialog from '~/features/assignments/components/monitor/RetakeDialog.vue'
import KeyCorrectionDialog from '~/features/assignments/components/results/KeyCorrectionDialog.vue'
import OverrideDialog from '~/features/assignments/components/results/OverrideDialog.vue'
import PublishDialog from '~/features/assignments/components/results/PublishDialog.vue'
import QuestionStatsTable from '~/features/assignments/components/results/QuestionStatsTable.vue'
import { useAssignment } from '~/features/assignments/composables/useAssignment'
import { useAssignmentResults } from '~/features/assignments/composables/useAssignmentResults'
import { gradebookColumns, type GradebookTableRow } from '~/features/assignments/utils/gradebook-columns'
import DataTable from '~/shared/components/DataTable.vue'
import ErrorState from '~/shared/components/ErrorState.vue'

const props = defineProps<{ assignmentId: string }>()

const results = useAssignmentResults(props.assignmentId)
const detail = useAssignment(props.assignmentId).detail
const toast = useToast()
const tab = ref('students')
const selected = ref<string[]>([])
const publishing = ref(false)
const retaking = ref(false)
const correcting = ref<QuestionStat | null>(null)
const overriding = ref<GradebookRow | null>(null)
const book = computed(() => results.book.data.value)
const rows = computed<GradebookTableRow[]>(() => (book.value?.rows ?? []).map(r => ({ ...r, id: r.attempt_id ?? r.student_id })))
const sectionTitles = computed(() => book.value?.rows.find(r => r.sections.length)?.sections.map(s => s.title) ?? [])
const columns = computed(() => gradebookColumns(sectionTitles.value.length > 1 ? sectionTitles.value : [], (row) => {
  overriding.value = row
}))
// The page adds the browser exports here (features can't import each other)
const selectedAttemptIds = computed(() => rows.value.filter(r => selected.value.includes(r.id) && r.attempt_id).map(r => r.attempt_id!))
const chosen = computed(() => rows.value.filter(r => selected.value.includes(r.id)).map(r => ({ id: r.student_id, name: r.name })))
const published = computed(() => book.value?.publication_state === 'PUBLISHED')
const menu = computed(() => [
  { label: 'Edit options', icon: 'i-lucide-settings-2', onSelect: () => { publishing.value = true } },
  { label: 'Unpublish', icon: 'i-lucide-eye-off', onSelect: () => void results.unpublish() },
])

function corrected(regraded: number): void {
  toast.add({ title: `Answer corrected. ${regraded} attempt(s) regraded.`, color: 'success' })
  void results.refresh()
}

onMounted(() => {
  void results.refresh()
  void detail.refresh()
})
</script>

<template>
  <ErrorState v-if="results.book.error.value" :problem="results.book.error.value" @retry="results.refresh" />
  <div v-else-if="book" class="space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h2 class="text-lg font-semibold">
        {{ book.title }} › Results
      </h2>
      <UBadge :label="published ? 'Published' : book.publication_state === 'SCHEDULED' ? 'Auto-publish' : 'Unpublished'" :color="published ? 'success' : 'neutral'" variant="subtle" />
      <div class="ms-auto flex gap-2">
        <slot name="export" :title="book.title" :attempt-ids="selectedAttemptIds" />
        <UButton label="Gradebook (CSV)" icon="i-lucide-download" color="neutral" variant="outline" :href="results.csvUrl" external download />
        <UDropdownMenu v-if="published" :items="menu">
          <UButton label="Published ✓" trailing-icon="i-lucide-chevron-down" color="success" variant="soft" />
        </UDropdownMenu>
        <UButton v-else label="Publish" @click="publishing = true" />
      </div>
    </div>
    <p class="text-sm text-muted">
      {{ results.statsLine.value }}
    </p>
    <UTabs v-model="tab" :items="[{ label: 'Students', value: 'students' }, { label: 'Questions', value: 'questions' }]" :content="false" />
    <DataTable v-if="tab === 'students'" v-model:selected="selected" :rows="rows" :columns="columns" empty-title="No students" selectable>
      <template #bulk>
        <UButton size="sm" label="Unlock retake" variant="soft" @click="retaking = true" />
      </template>
    </DataTable>
    <QuestionStatsTable v-else :stats="results.stats.data.value ?? []" :keyed="results.keyed.data.value" @correct="stat => correcting = stat" />
    <PublishDialog v-model:open="publishing" :assignment-id="assignmentId" :current="detail.data.value?.publication ?? null" @done="results.refresh" />
    <RetakeDialog v-model:open="retaking" :assignment-id="assignmentId" :students="chosen" @done="n => toast.add({ title: `Retake unlocked for ${n}`, color: 'success' })" />
    <KeyCorrectionDialog
      :open="correcting !== null"
      :assignment-id="assignmentId"
      :stat="correcting"
      :keyed="results.keyed.data.value"
      :ended="results.endedCount.value"
      @update:open="v => { if (!v) correcting = null }"
      @done="corrected"
    />
    <OverrideDialog
      :open="overriding !== null"
      :attempt-id="overriding?.attempt_id ?? null"
      :name="overriding?.name ?? ''"
      @update:open="v => { if (!v) overriding = null }"
      @done="results.refresh"
    />
  </div>
</template>
