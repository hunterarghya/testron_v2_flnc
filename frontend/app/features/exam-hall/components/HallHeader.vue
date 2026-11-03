<!-- The hall's top bar (P-03): title, the server-time countdown (amber in the last 5 minutes,
     announced once), the save status, the palette button on phones, and Submit. -->
<script setup lang="ts">
import { computed } from 'vue'
import { formatCountdown } from '~/engine/clock'
import { useHall } from '~/features/exam-hall/composables/useExamSession'
import { hallTitle, LAST_MINUTES_MS, saveStatus } from '~/features/exam-hall/utils/hall-text'

const props = defineProps<{ remainingMs: number, palette: boolean }>()
defineEmits<{ submit: [], palette: [] }>()

const hall = useHall()
const title = computed(() => (hall.state.value ? hallTitle(hall.state.value.title, hall.state.value.take_number) : ''))
const status = computed(() => saveStatus(hall.queueStatus.value.waiting, hall.queueStatus.value.offline))
const lastMinutes = computed(() => props.remainingMs <= LAST_MINUTES_MS)
const shown = computed(() => (Number.isFinite(props.remainingMs) ? formatCountdown(props.remainingMs) : '--:--:--'))
</script>

<template>
  <header class="flex flex-wrap items-center gap-3 border-b border-default px-4 py-2">
    <h1 class="min-w-0 flex-1 truncate font-medium">
      {{ title }}
    </h1>
    <span class="flex items-center gap-1 font-mono text-lg" :class="lastMinutes ? 'text-warning' : ''">
      <UIcon name="i-lucide-timer" class="size-5" />
      <span role="timer">{{ shown }}</span>
    </span>
    <span class="sr-only" aria-live="polite">{{ lastMinutes ? '5 minutes left' : '' }}</span>
    <UBadge :icon="status.icon" :label="status.label" :color="status.tone" variant="subtle" />
    <UButton v-if="palette" icon="i-lucide-grid-3x3" aria-label="Questions" color="neutral" variant="ghost" class="lg:hidden" @click="$emit('palette')" />
    <UButton label="Submit" @click="$emit('submit')" />
  </header>
</template>
