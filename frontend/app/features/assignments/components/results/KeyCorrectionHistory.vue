<!-- T-11 Questions tab: every answer key correction, newest first, with what changed and why
     (security.md T-05). The audit log keeps the same record. -->
<script setup lang="ts">
import type { KeyCorrection } from '~/api/types'
import { entryText } from '~/features/assignments/utils/answer-key'
import { formatDateTime } from '~/shared/utils/time'

defineProps<{ corrections: KeyCorrection[] }>()
</script>

<template>
  <UCard v-if="corrections.length">
    <template #header>
      <h2 class="font-semibold">
        Answer key corrections ({{ corrections.length }})
      </h2>
    </template>
    <ul class="divide-y divide-default text-sm">
      <li v-for="fix in corrections" :key="fix.version" class="space-y-1 py-2">
        <p>
          <span class="font-medium">Q{{ fix.number }}:</span>
          {{ entryText(fix.before) }} → {{ entryText(fix.after) }}
          <span class="text-muted">· {{ formatDateTime(fix.corrected_at) }} · key version {{ fix.version }}</span>
        </p>
        <p class="text-muted">
          “{{ fix.reason }}”
        </p>
      </li>
    </ul>
  </UCard>
</template>
