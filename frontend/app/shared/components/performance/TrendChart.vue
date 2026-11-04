<!-- How the score went over time, one dot per test (P-10 "Trend"). Screen readers get the
     same numbers as a list. -->
<script setup lang="ts">
import { computed } from 'vue'
import { CHART, type TrendItem, trendPoints } from '~/shared/utils/performance'

const props = defineProps<{ items: TrendItem[] }>()

const points = computed(() => trendPoints(props.items))
const line = computed(() => points.value.map(p => `${p.x},${p.y}`).join(' '))
</script>

<template>
  <figure class="space-y-2">
    <svg :viewBox="`-6 -6 ${CHART.width + 12} ${CHART.height + 12}`" class="h-40 w-full text-primary" aria-hidden="true" preserveAspectRatio="none">
      <polyline :points="line" class="fill-none stroke-current" stroke-width="2" vector-effect="non-scaling-stroke" />
      <circle v-for="(point, index) in points" :key="index" :cx="point.x" :cy="point.y" r="3" class="fill-current">
        <title>{{ items[index]?.label }}: {{ items[index]?.score_pct }}%</title>
      </circle>
    </svg>
    <figcaption class="flex justify-between text-xs text-muted">
      <span>{{ items[0]?.label }}</span>
      <span v-if="items.length > 1">{{ items[items.length - 1]?.label }}</span>
    </figcaption>
    <ul class="sr-only">
      <li v-for="item in items" :key="item.label + item.ended_at">{{ item.label }}: {{ item.score_pct }}%</li>
    </ul>
  </figure>
</template>
