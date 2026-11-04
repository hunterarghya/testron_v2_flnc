<!-- Chapters or topics, weakest first: a bar for the score, then accuracy and how much was
     answered (domain_model.md §6.5). -->
<script setup lang="ts">
import type { TagPerformance } from '~/api/types'
import { barColor, barValue } from '~/shared/utils/performance'

defineProps<{ rows: TagPerformance[] }>()
</script>

<template>
  <ul class="divide-y divide-default">
    <li v-for="row in rows" :key="row.tag.id" class="grid grid-cols-[minmax(0,1fr)_minmax(0,2fr)_auto] items-center gap-3 py-2">
      <span class="truncate font-medium">{{ row.tag.name }}</span>
      <UProgress :model-value="barValue(row.score_pct)" :color="barColor(row.score_pct)" size="sm" :aria-label="`${row.tag.name} score`" />
      <span class="text-end tabular-nums">{{ row.score_pct }}%</span>
      <span class="col-span-3 text-xs text-muted">
        Accuracy {{ row.accuracy_pct }}% · Answered {{ row.attempted_pct }}% · {{ row.questions }} question{{ row.questions === 1 ? '' : 's' }}
      </span>
    </li>
  </ul>
</template>
