<!-- T-12 Student answer sheet (teacher view): the same sheet as the student's P-09, with
     everything shown, the status, a disqualified score in brackets, and the flags panel. -->
<script setup lang="ts">
import { computed, onMounted } from 'vue'
import SheetFlagsPanel from '~/features/assignments/components/results/SheetFlagsPanel.vue'
import { STATUS } from '~/features/assignments/utils/gradebook-columns'
import ErrorState from '~/shared/components/ErrorState.vue'
import ResultSheet from '~/shared/components/result/ResultSheet.vue'
import { useApiData } from '~/shared/composables/useApiData'
import { getAnswerSheet } from '~/shared/composables/resultDocumentsApi'
import { formatDecimal } from '~/shared/utils/decimals'

const props = defineProps<{ attemptId: string }>()

const sheet = useApiData(() => getAnswerSheet(props.attemptId))
const data = computed(() => sheet.data.value)
const status = computed(() => STATUS[data.value?.end_reason ?? 'IN_PROGRESS'])

onMounted(() => sheet.refresh())
</script>

<template>
  <ErrorState v-if="sheet.error.value" :problem="sheet.error.value" @retry="sheet.refresh" />
  <div v-else-if="data" class="space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <h2 class="text-lg font-semibold">
        {{ data.student.name }} · {{ data.label }}
      </h2>
      <UBadge v-if="status" :label="status.label" :color="status.color" variant="subtle" />
      <span v-if="data.disqualified_score" class="text-sm text-muted">(scored {{ formatDecimal(data.disqualified_score) }})</span>
      <div class="ms-auto">
        <slot name="download" :sheet="data" />
      </div>
    </div>
    <SheetFlagsPanel :sheet="data" />
    <ResultSheet :result="data" />
  </div>
</template>
