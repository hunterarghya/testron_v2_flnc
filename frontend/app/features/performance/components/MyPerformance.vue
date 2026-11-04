<!-- P-10 My Performance: only while the teacher shares it, and only from published results
     (domain_model.md §6.5 [I-3, I-4]). Otherwise the server answers Not found. -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { getMyPerformance } from '~/features/performance/composables/performanceApi'
import ErrorState from '~/shared/components/ErrorState.vue'
import PerformanceReport from '~/shared/components/performance/PerformanceReport.vue'
import { useApiData } from '~/shared/composables/useApiData'
import { basisText } from '~/shared/utils/performance'

const report = useApiData(getMyPerformance)

onMounted(report.refresh)
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-xl font-semibold">
      My Performance
    </h1>
    <ErrorState v-if="report.error.value" :problem="report.error.value" @retry="report.refresh" />
    <template v-else-if="report.data.value">
      <UEmpty
        v-if="!report.data.value.based_on_attempts"
        icon="i-lucide-chart-column"
        title="Nothing to show yet."
        description="Your chapters and trend appear once your first result is published."
      />
      <PerformanceReport
        v-else
        :basis="basisText(report.data.value.based_on_attempts, true)"
        :chapters="report.data.value.chapters"
        :topics="report.data.value.topics"
        :trend="report.data.value.trend"
      />
    </template>
    <USkeleton v-else class="h-40 w-full" />
  </div>
</template>
