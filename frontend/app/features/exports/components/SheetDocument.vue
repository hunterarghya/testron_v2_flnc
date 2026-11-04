<!-- The body of an exported answer sheet [H-5, H-6]: who and what, then the same result sheet
     as T-12, every part shown, and the times the student left the test. -->
<script setup lang="ts">
import type { AnswerSheet } from '~/api/types'
import ResultSheet from '~/shared/components/result/ResultSheet.vue'
import { formatDecimal } from '~/shared/utils/decimals'
import { eventText } from '~/shared/utils/result-text'

defineProps<{ sheet: AnswerSheet }>()
</script>

<template>
  <article class="space-y-4">
    <header>
      <h1 class="text-xl font-semibold">
        {{ sheet.student.name }}
      </h1>
      <p class="text-muted">
        {{ sheet.label }}
        <span v-if="sheet.disqualified_score"> · Disqualified (scored {{ formatDecimal(sheet.disqualified_score) }})</span>
      </p>
    </header>
    <ResultSheet :result="sheet" printable />
    <section v-if="sheet.integrity_events.length" class="space-y-1 text-sm">
      <h2 class="font-medium">
        Left the test
      </h2>
      <p v-for="event in sheet.integrity_events" :key="event.left_at">
        {{ eventText(event) }}
      </p>
    </section>
  </article>
</template>
