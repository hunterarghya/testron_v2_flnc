<!-- P-09 Result View: exactly what the publish options allow [H-2], through the same sheet
     the teacher sees. An unpublished or unknown result shows the not-found state. -->
<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { getMyResult } from '~/features/past-tests/composables/pastTestsApi'
import ErrorState from '~/shared/components/ErrorState.vue'
import ResultSheet from '~/shared/components/result/ResultSheet.vue'
import { useApiData } from '~/shared/composables/useApiData'

const props = defineProps<{ attemptId: string }>()

const result = useApiData(() => getMyResult(props.attemptId))
// A disqualified attempt comes without a score unless the teacher overrode it (DM-5)
const disqualified = computed(() => result.data.value?.end_reason === 'DISQUALIFIED' && result.data.value.score == null)

onMounted(() => result.refresh())
</script>

<template>
  <div class="space-y-4">
    <UButton icon="i-lucide-arrow-left" label="Past Tests" variant="link" color="neutral" to="/past" />
    <ErrorState v-if="result.error.value" :problem="result.error.value" @retry="result.refresh" />
    <template v-else-if="result.data.value">
      <h1 class="text-xl font-semibold">
        {{ result.data.value.label }}
      </h1>
      <ResultSheet :result="result.data.value" :disqualified="disqualified" />
    </template>
  </div>
</template>
