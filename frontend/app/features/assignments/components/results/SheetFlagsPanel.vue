<!-- T-12 flags panel: the warnings against the test's limit, each time the student left the
     test (and whether it counted), and a disqualification the teacher counted anyway (D-09). -->
<script setup lang="ts">
import { computed } from 'vue'
import type { AnswerSheet } from '~/api/types'
import { eventText } from '~/shared/utils/result-text'
import { formatDateTime } from '~/shared/utils/time'

const props = defineProps<{ sheet: AnswerSheet }>()

const flags = computed(() => props.sheet.flags)
const limit = computed(() => {
  const then = flags.value.action === 'DISQUALIFY' ? 'disqualify' : 'submit automatically'
  return `⚑ ${flags.value.warning_count} of ${flags.value.max_warnings} warnings (the last one would ${then})`
})
</script>

<template>
  <UCard>
    <template #header>
      <h2 class="font-semibold">
        Flags
      </h2>
    </template>
    <div class="space-y-3 text-sm">
      <p>{{ limit }}</p>
      <UAlert
        v-if="flags.overridden_at"
        icon="i-lucide-shield-check"
        color="info"
        variant="subtle"
        :title="`Disqualification overridden on ${formatDateTime(flags.overridden_at)}`"
        :description="flags.override_reason ? `“${flags.override_reason}”` : undefined"
      />
      <p v-if="!sheet.integrity_events.length" class="text-muted">
        Never left the test.
      </p>
      <ul v-else class="space-y-1">
        <li v-for="event in sheet.integrity_events" :key="event.left_at" class="flex items-center gap-2">
          <UIcon :name="event.counted ? 'i-lucide-flag' : 'i-lucide-circle'" class="size-4 shrink-0" :class="event.counted ? 'text-warning' : 'text-muted'" />
          {{ eventText(event) }}
        </li>
      </ul>
    </div>
  </UCard>
</template>
