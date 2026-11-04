<!-- The performance widgets shared by P-10, T-15 and T-17: chapters and topics weakest
     first, and the score trend. The page says where the numbers come from. -->
<script setup lang="ts">
import { ref } from 'vue'
import type { TagPerformance } from '~/api/types'
import TagPerformanceList from '~/shared/components/performance/TagPerformanceList.vue'
import TrendChart from '~/shared/components/performance/TrendChart.vue'
import type { TrendItem } from '~/shared/utils/performance'

defineProps<{
  basis: string
  chapters: TagPerformance[]
  topics: TagPerformance[]
  trend: TrendItem[]
}>()

const TABS = [{ value: 'chapters', label: 'Chapters' }, { value: 'topics', label: 'Topics' }]
const tab = ref('chapters')
</script>

<template>
  <div class="space-y-4">
    <p class="text-muted">{{ basis }}</p>
    <UCard>
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h2 class="font-semibold">Weakest first</h2>
          <UTabs v-model="tab" :items="TABS" :content="false" size="xs" />
        </div>
      </template>
      <TagPerformanceList v-if="(tab === 'chapters' ? chapters : topics).length" :rows="tab === 'chapters' ? chapters : topics" />
      <p v-else class="text-sm text-muted">No questions in these tests had a {{ tab === 'chapters' ? 'chapter' : 'topic' }} tag.</p>
    </UCard>
    <UCard>
      <template #header>
        <h2 class="font-semibold">Trend</h2>
      </template>
      <TrendChart :items="trend" />
    </UCard>
  </div>
</template>
